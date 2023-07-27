import csv
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from astropy.io import fits
import sys
import scipy.spatial.distance as dist

# Initial variables
max_coordinate_distance = 20

# Load the Hessian tracings to memory
tracings = []
for i in range(120):
    with open("ts_res/hess/{}.csv".format(i)) as csvfile:
        f = csv.reader(csvfile)
        columns = ['f_num', 'x', 'y', 'len', 'breadth']
        df = pd.DataFrame([row for row in f], columns=columns)
        df[columns] = df[columns].apply(pd.to_numeric)
        df.insert(5, "match_id", None)
        df.insert(6, "match_distance", 0.0)
        tracings.append(df)

# Create empty completed DataFrame
completed = pd.DataFrame(columns=["start_frame", "end_frame", "xvals", "yvals"])

# Create active features DataFrame
df = tracings[0]
unique_ids = df['f_num'].unique()
xs = []
ys = []
for i in unique_ids:
    x = df[df.f_num == i].x.tolist()
    y = df[df.f_num == i].y.tolist()
    xs.append(x)
    ys.append(y)
active = pd.DataFrame({'start_frame': 0,
                        'f_nums': [i],
                        'xvals': [x],
                        'yvals': [y],
                        'alive': False,
                    } for i,x,y in zip(xs, ys, unique_ids))

# Open timeseries for visualization purposes
f = fits.open("data/images/fits/nb.6563.ser_171115.bis.wid.23Apr2017.target2.all.fits")[0].data[1,:,:]

# Start the matching process
for i in range(120):
    # Skip the 0th frame
    if i == 0:
        continue

    # Assume nonactive until proved otherwise
    active.alive = False

    def match_frame_features(mi, ci, max_coordinate_distance):
        """
        Find feature matches in frame B (ci) to features in frame A (mi)

        Parameters
        ----------
        mi : DataFrame
            DataFrame 1 (initial)
        ci : DataFrame
            DataFrame 2 (final)
        max_coordinate_distance : float
            Max allowed distance between candidate coordiantes.

        Returns
        -------
        mi : DataFrame
            Dataframe with updated values for match_id and match_distance
        """
        # Get all x,y coordinates of current frame (ci), store in numpy array
        icoords = np.array([ci.x, ci.y]).T

        # Iterate over all x,y in previous frame (mi)
        for x,y in zip(mi.x, mi.y):
            # Reduce coordinate candidates to those that have an x & y both within 20 pixels
            ic_reduced = icoords[np.where(
                (abs(icoords[:,0]-x) < max_coordinate_distance) &
                (abs(icoords[:,1]-y) < max_coordinate_distance)
                )]
            
            # Calculate Euclidean distance to all filtered coordinates
            dists = dist.cdist(np.array([[x],[y]]).T, ic_reduced)
            dists_full = np.concatenate((dists.T, ic_reduced), axis=1)
            try:
                min = dists_full[np.argmin(dists_full[:,0])]
            except ValueError:
                # If there are no matches within 20 pixels. We could be more informative and provide a 
                # quantative percentage here. 
                continue
                
            # Get feature ID of closest coordinate
            # This takes a long time. Can we do this without getting this?
            f_match = df[(df.x == min[1]) & (df.y == min[2])].iloc[0]
            fid = f_match.f_num

            # Set mi match_id and match_distance
            mi.loc[(mi.x == x) & (mi.y == y), 'match_id'] = fid
            mi.loc[(mi.x == x) & (mi.y == y), 'match_distance'] = min[0]

            # Remove match from icoords to prevent multiple coordinates matching
            icoords = np.delete(icoords, np.where((icoords[:,0] == x) & (icoords[:,1] == y)), axis=0)

        # Return updated mi DataFrame
        return(mi)
    
    # Retrieve ith frame
    ci = tracings[i]
    ci.match_id = None
    ci.match_distance = 0.0

    # Retrieve the i-1 frame 
    mi = tracings[i-1]
    mi.match_id = None
    mi.match_distance = 0.0

    # Find closest coordinates from all i coordinates to i-1 coordinates.
    ci = match_frame_features(mi, ci, max_coordinate_distance)

    # Find closest coordinates from all i-1 coordinates to i coordinates. 
    mi = match_frame_features(ci, mi, max_coordinate_distance)

    mici = {}
    cimi = {}
    # Associate fibril in frame ci (i) with fibril in frame mi (i-1)
    for uniq in mi.f_num.unique():
        match_ids = mi[mi.f_num == uniq].match_id.tolist()
        mode_mid = max(match_ids, key=match_ids.count)
        mici[uniq] = mode_mid

    # Associate fibril in frame mi (i-1) with fibril in frame ci (i)
    for uniq in ci.f_num.unique():
        match_ids = ci[ci.f_num == uniq].match_id.tolist()
        mode_mid = max(match_ids, key=match_ids.count)
        cimi[uniq] = mode_mid

    # If mici match-pair equals cimi match-pair, then the pairing is valid. More restrictive, but closer match.































    # # Match features from i-1 to i by getting the mode of each feature's match_id
    # for u in mi['f_num'].unique():
    #     mode_mid = max(mi[mi.f_num == u].match_id, key=mi[mi.f_num == u].match_id.tolist().count)

    #     # Set all match_ids per feature to mode value
    #     mi.loc[mi.f_num == u, 'match_id'] = mode_mid

    #     # If the feature found a corresponding match in the next frame
    #     if mode_mid is not None:
    #         # Get x and y values
    #         x = mi[mi.f_num == u].x.tolist()
    #         y = mi[mi.f_num == u].y.tolist()
    #         # Look for the feature ID in active
    #         if u in active['f_num'].unique():
    #             # Append to the active list
    #             active.loc[active.f_num == u, 'xvals'].iloc[0].append(x)
    #             active.loc[active.f_num == u, 'yvals'].iloc[0].append(y)

    #             # Set active entry to "active"
    #             active.loc[active.f_num == u, 'alive'].iloc[0] = True

    #             # Modify the f_num to be the new (i) feature number
    #             active.loc[active.f_num == u, 'f_num_toupd'] = mode_mid
    #         else:
    #             # Start a new active entry - .loc[len(active.index)] is giving errors
    #             active_slice = pd.DataFrame({'start_frame': i,
    #                     'f_num': u,
    #                     'xvals': [[x]],
    #                     'yvals': [[y]],
    #                     'alive': True,
    #                     'f_num_toupd': u
    #                 })

    #             active = pd.concat([active, active_slice], ignore_index=True)

    # # If an active entry with "active=False" has more than 2 entries, move it to "completed".
    # completed_slice = active[
    #     (active.alive == False) & (active[active.alive == False].xvals.str.len() > 2)
    #     ][['start_frame', 'xvals', 'yvals']]
    
    # if len(completed_slice.index) > 0:
    #     completed_slice.insert(1, "end_frame", i)
    #     completed = pd.concat([completed, completed_slice], ignore_index=True)

    #     # Remove completed + len(xvals) < 2/(alive==False) sections from active frame
    #     active = active[active.alive == True]
    #     active.reset_index()
    
    # # Plot both the original dataframe coordinates + the active coordinates (in different color)
    # plt.imshow(f, origin="lower")
    # xs = []
    # ys = []
    # for u in tracings[i].f_num.unique():
    #     xs.extend(tracings[i][tracings[i].f_num == u].x.tolist())
    #     xs.append(None)
    #     ys.extend(tracings[i][tracings[i].f_num == u].y.tolist())
    #     ys.append(None)
    #     compl_slice = completed[(completed.start_frame <= i) & (completed.end_frame >= i)] 
    #     if len(compl_slice.index):
    #         print(i)
    #         xsc = []
    #         ysc = []
    #         for index, row in compl_slice.iterrows():
    #             diff = abs(i - row.start_frame + 1)
    #             # print(u, row.start_frame, row.end_frame, len(row.xvals), diff)
    #             # Honestly - redo all of this, plotting along the way. Use a slice of the frame. No idea where I'm at here anymore. 
    #             x = row.xvals[diff]
    #             y = row.yvals[diff]
    #             xsc.extend(x)
    #             ysc.extend(y)
    #             xsc.append(None)
    #             ysc.append(None)

    # plt.plot(xs,ys, color="blue")
    # if len(compl_slice.index):
    #     plt.plot(xsc, ysc, color="red", alpha=0.2)
    # plt.show()
    # plt.savefig("ts_res/lifetime/{}.png".format(i), format="png")
    # if i == 20:
    #     sys.exit(0)