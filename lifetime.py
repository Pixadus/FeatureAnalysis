# Name: lifetime.py
# Created: a few days ago
# Description: Iterate over OCCULT-2 tracings and match them together. Generate "active"
#              and "completed" DataFrames which contain frame-based lifetime information. 

import csv
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from astropy.io import fits
import scipy.spatial.distance as dist
import scipy.stats as stats

# Initial variables
init_frame = 0
final_frame = 120
max_coordinate_distance = 20
max_completed_distance = 10
save_figures = False                # Save figures to ts_res/lifetime
match_completed = True              # Match completed features to one another across time gaps
generate_normdist = True            # Generate normal distribution functions

# Load the Hessian tracings to memory 
tracings = []
for i in range(init_frame, final_frame):
    with open("ts_res/hess/{}.csv".format(i)) as csvfile:
        f = csv.reader(csvfile)
        columns = ['f_num', 'x', 'y']
        df = pd.DataFrame([row for row in f], columns=columns)
        df[columns] = df[columns].apply(pd.to_numeric)
        df.insert(3, "match_id", None)
        df.insert(4, "match_distance", 0.0)
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
                    } for x,y,i in zip(xs, ys, unique_ids))

# Open timeseries for visualization purposes
f = fits.open("data/images/fits/nb.6563.ser_171115.bis.wid.23Apr2017.target2.all.fits")[0].data

# Start the matching process
for i in range(init_frame, final_frame):
    # Skip the 0th frame
    if i == 0:
        continue

    # Print current status
    print("Matching {} to {}".format(i-1,i))

    # Assume inactive until proved otherwise
    active.alive = False

    # Retrieve ith frame
    ci = tracings[i]

    # Retrieve the i-1th frame
    mi = tracings[i-1]

    def match_frame_features(dfa, dfb, max_coordinate_distance):
        """
        Find feature matches in frame B (dfb) to features in frame A (dfa)

        Parameters
        ----------
        dfa : DataFrame
            DataFrame 1 (initial)
        dfb : DataFrame
            DataFrame 2 (final)
        max_coordinate_distance : float
            Max allowed distance between candidate coordiantes.

        Returns
        -------
        dfa : DataFrame
            Dataframe with updated values for match_id and match_distance
        """

        dfa.match_id = None
        dfa.match_distance = 0.0

        # Get all x,y coordinates of current frame (dfb), store in numpy array
        icoords = np.array([dfb.x, dfb.y]).T

        # Iterate over all x,y in previous frame (dfa)
        for x,y in zip(dfa.x, dfa.y):
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
            f_match = dfb[(dfb.x == min[1]) & (dfb.y == min[2])].iloc[0]
            fid = f_match.f_num

            # Set dfa match_id and match_distance
            dfa.loc[(dfa.x == x) & (dfa.y == y), 'match_id'] = fid
            dfa.loc[(dfa.x == x) & (dfa.y == y), 'match_distance'] = min[0]

            # Remove match from icoords to prevent multiple coordinates matching
            icoords = np.delete(icoords, np.where((icoords[:,0] == x) & (icoords[:,1] == y)), axis=0)

        # Return updated dfa DataFrame
        return(dfa)

    # Find closest coordinates from all i coordinates to i-1 coordinates.
    ci = match_frame_features(ci, mi, max_coordinate_distance)

    # Find closest coordinates from all i-1 coordinates to i coordinates. 
    mi = match_frame_features(mi, ci, max_coordinate_distance)

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

    for key in mici.keys():
        # If a feature matches in both mi-ci and ci-mi, add it to the active list. 
        try:
            if (key == cimi[mici[key]]):
                # The features match! 
                diff = ((i-active.start_frame) - 1).tolist() # Subtract 1 since we want to look for the i-1 index.
                f_nums = active.f_nums.tolist()

                # Use "diff" as a frame indicator to see where we should look
                try:
                    # cf_fn = [fn[d] for d, fn in zip(diff, f_nums)]
                    cf_fn = []
                    for d, fn in zip(diff, f_nums):
                        cf_fn.append(fn[d])
                except IndexError:
                    print("Error:", i, d, fn)

                x = ci[ci.f_num == mici[key]].x.tolist()
                y = ci[ci.f_num == mici[key]].y.tolist()

                # Check if key is already in active. 
                if key in cf_fn:
                    # Should never be duplicates. TODO confirm this. 
                    index = cf_fn.index(key)

                    # Add to the active entry
                    active.loc[index, 'f_nums'].append(mici[key])
                    active.loc[index, 'xvals'].append(x)
                    active.loc[index, 'yvals'].append(y)
                    active.loc[index, 'alive'] = True

                # If not, create a new active row.
                else:
                    active_slice = pd.DataFrame({
                            'start_frame': i,
                            'f_nums': [[mici[key]]],
                            'xvals': [[x]],
                            'yvals': [[y]],
                            'alive': True
                        })
                    
                    active = pd.concat([active, active_slice], ignore_index=True)
    
        except KeyError:
            # If the key wasn't found, the matching feature in ci didn't find a match. 
            # This would happen if the feature in ci was much longer than in mi, or has already been matched.  
            continue
    
    # Move all active=False entries to "completed", if they take place over 3+ frames
    
    # Iterate over rows + indexes
    for index, row in active[active.alive == False].iterrows():

        # Only move inactive rows if they span more than 3 frames. 
        if (i - row.start_frame) > 2:
            compl_slice = pd.DataFrame({
                "start_frame": row.start_frame,
                "end_frame": i,
                "xvals": [row.xvals],
                "yvals": [row.yvals]
            })
            completed = pd.concat([completed, compl_slice], ignore_index=True)
            active.drop(index, inplace=True)

        # Dismiss otherwise. (Assume lifetime greater than (3.65*2) = 7.3 seconds)
        else:
            active.drop(index, inplace=True)

    # Reset the indicies on active and completed to accomodate for the modified dataframes
    active.reset_index()
    completed.reset_index()

    if save_figures:
        print("Saving figure {} to ts_res/lifetime/".format(i))

        # Clear the plot
        plt.cla()

        # Let's try plotting everything.
        plt.imshow(f[i,:,:], origin="lower")
        
        # Plot the unmatched fibrils
        xs = []
        ys = []
        for uniq in tracings[i-1].f_num.unique():
            x = tracings[i-1][tracings[i-1].f_num == uniq].x.tolist()
            y = tracings[i-1][tracings[i-1].f_num == uniq].y.tolist()
            xs.extend(x)
            ys.extend(y)
            xs.append(None)
            ys.append(None)
        plt.plot(xs, ys, color="blue")

        # Plot the active fibrils
        xs = []
        ys = []
        for index, row in active.iterrows():
            coord_index = (i - row.start_frame) - 1
            x = row.xvals[coord_index]
            y = row.yvals[coord_index]
            xs.extend(x)
            ys.extend(y)
            xs.append(None)
            ys.append(None)
        plt.plot(xs, ys, color="red")

        # Plot the completed fibrils
        xs = []
        ys = []
        for index, row in completed[(completed.start_frame <= i) & (completed.end_frame >= i)].iterrows():
            coord_index = (i - row.start_frame) - 1
            x = row.xvals[coord_index]
            y = row.yvals[coord_index]
            xs.extend(x)
            ys.extend(y)
            xs.append(None)
            ys.append(None)
        plt.plot(xs, ys, color="green")
        plt.savefig("ts_res/lifetime/{}.png".format(i), format="png")

# Save completed dataframe + active dataframe
completed.to_csv("ts_res/lifetime_pdf/completed.csv")
active.to_csv("ts_res/lifetime_pdf/active.csv")

# if match_completed:
#     # Start "completed matching" - match completed sets to one another to account for changes in seeing
#     print("Matching completed features")
#     completed.insert(4, "mean_x", 0.0)
#     completed.insert(5, "mean_y", 0.0)
#     for index, row in completed.iterrows():
#         xs = row.xvals
#         ys = row.yvals
#         for fx,fy in zip(xs,ys):
#             xm = np.mean(fx)
#             ym = np.mean(fy)
#             row.mean_x += xm
#             row.mean_y += ym
#         row.mean_x = row.mean_x / (row.end_frame - row.start_frame)
#         row.mean_y = row.mean_y / (row.end_frame - row.start_frame)

#         # Set the x,y mean values as the row iteration is just a copy
#         completed.loc[index, 'mean_x'] = row.mean_x
#         completed.loc[index, 'mean_y'] = row.mean_y

#     # Iterate over rows & combine those less than max_completed_distance away with one another
#     completed.insert(6, 'matching_inds', np.empty((len(completed), 0)).tolist())

#     for index, row in completed.iterrows():
#         mxs = completed.mean_x
#         mys = completed.mean_y

#         # mcoords contains the mean coordinates - mcoords_se contains the start/end frames for later filtering
#         mcoords = np.array([completed.mean_x, completed.mean_y]).T
#         mcoords_se = np.array([completed.start_frame, completed.end_frame]).T

#         # Reduce mcoords + mcoords_se array
#         mc_reduced = mcoords[np.where(
#             (abs(mcoords[:,0]-row.mean_x) < max_completed_distance) &
#             (abs(mcoords[:,1]-row.mean_y) < max_completed_distance)
#         )]
#         mcse_reduced = mcoords_se[np.where(
#             (abs(mcoords[:,0]-row.mean_x) < max_completed_distance) &
#             (abs(mcoords[:,1]-row.mean_y) < max_completed_distance)
#         )]

#         # Calculate Euclidean distance to all filtered coordinates
#         dists = dist.cdist(np.array([[row.mean_x],[row.mean_y]]).T, mc_reduced)
#         dists_full = np.concatenate((dists.T, mc_reduced, mcse_reduced), axis=1)
#         try:
#             # Use np.where() to filter out self (where distance would of course be zero)
#             # Avoid frame intersection by:
#             #   - End frame of matched features must preceed the start frame of current feature
#             #   - End frame of current feature must preceed the start frame of matched features
#             matched_features = dists_full[np.where(
#                 (dists_full[:,0] > 0) & 
#                 (dists_full[:,0] < max_completed_distance) &
#                 ((dists_full[:,3] > row.end_frame) |
#                 (dists_full[:,4] < row.start_frame))
#                 )]
#         except ValueError:
#             # If there are no matches within max_coordinate_distance pixels. We could be more informative and provide a 
#             # quantative percentage here. 
#             continue

#         # If we're at this point, one or more matching completed features have been found. Find & associate indexes with the current feature.
#         matching_indexes = []
#         for r in matched_features:
#             mid = completed.index[(completed.mean_x == r[1]) & (completed.mean_y == r[2])].tolist()
#             matching_indexes.extend(mid)
#         completed.loc[index, 'matching_inds'].extend(matching_indexes)

#     # Lifetimes of completed (no matching inds)
#     # Pandas has no built-in method to evaluate the length of a contained list; hence the .map usage. 
#     cmp_noind = completed[completed['matching_inds'].map(len) == 0]
#     lt_cmp_noind = (cmp_noind.end_frame - cmp_noind.start_frame).to_numpy()

#     # Lifetimes of completed (with matching inds) 
#     # We need to modify the DataFrame to include the lifetimes
#     cmp_ind = completed[completed['matching_inds'].map(len) > 0]
#     cmp_ind.insert(7, 'consider', True)

#     # Create an "extended" DataFrame
#     complete_extended = pd.DataFrame(columns=["start_frames", "end_frames", "total_lifetime"])
#     for index, row in cmp_ind.iterrows():
#         if row.consider:
#             # Get the matching completed feature indices
#             inds = row.matching_inds

#             # Set up initial values for start_frames, end_frames and total_lifetime
#             start_frames = [row.start_frame]
#             end_frames = [row.end_frame]
#             total_lifetime = row.end_frame - row.start_frame
            
#             # Iterate over the matched features, and add their characteristics to this complete_extended entry
#             for ind in inds:
#                 sf = completed.loc[ind, "start_frame"]
#                 ef = completed.loc[ind, "end_frame"]
#                 start_frames.append(sf)
#                 end_frames.append(ef)
#                 total_lifetime += (ef - sf)

#                 # Disable from future consideration
#                 completed.loc[ind, "consider"] = False
            
#             # Set up a slice to append to completed_extended
#             ce_slice = pd.DataFrame({
#                 "start_frames": [[start_frames]],
#                 "end_frames": [[end_frames]],
#                 "total_lifetime": total_lifetime
#             })
#             complete_extended = pd.concat([complete_extended, ce_slice])