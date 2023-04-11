#!/usr/bin/python

import csv
import matplotlib.pyplot as plt
import numpy as np
from scipy import stats
from astropy.io import fits

# Set up the plots
fig, ax = plt.subplots(ncols=2)
timeseries = fits.open("data/images/fits/timeseries-cropped.fits")[0].data
timeseries_0 = timeseries[0,:,:]
timeseries_1 = timeseries[1,:,:]
ax[0].set_title("Frame 0")
ax[1].set_title("Frame 1")
ax[0].imshow(timeseries_0, origin="lower")
ax[1].imshow(timeseries_1, origin="lower")

# Open and plot 0th tracings
with open("timeseries_results/0-tracings.csv") as csvfile:
    csvreader = csv.reader(csvfile)
    feature_id = None
    feature_coords = []
    for row in csvreader:
        # If the row is a new FID, plot the previous list and append to it
        if int(row[0]) != feature_id:
            if feature_id is not None:
                x = [c[0] for c in feature_coords]
                y = [c[1] for c in feature_coords]
                ax[0].plot(x,y, color="blue")
                ax[0].text(np.mean(x), np.mean(y), feature_id, color="white", fontsize=4)
            feature_id = int(row[0])
            feature_coords = [(float(row[1]), float(row[2]))]
        # Otherwise, append to it
        else:
            feature_coords.append((float(row[1]), float(row[2])))
    # Plot the last feature too
    x = [c[0] for c in feature_coords]
    y = [c[1] for c in feature_coords]
    ax[0].plot(x,y, color="blue")

# Open and plot 1st tracings
with open("timeseries_results/1-tracings.csv") as csvfile:
    csvreader = csv.reader(csvfile)
    feature_id = None
    feature_coords = []
    for row in csvreader:
        # If the row is a new FID, plot the previous list and append to it
        if int(row[0]) != feature_id:
            if feature_id is not None:
                x = [c[0] for c in feature_coords]
                y = [c[1] for c in feature_coords]
                ax[1].plot(x,y, color="blue")
                ax[1].text(np.mean(x), np.mean(y), feature_id, color="white", fontsize=4)
            feature_id = int(row[0])
            feature_coords = [(float(row[1]), float(row[2]))]
        # Otherwise, append to it
        else:
            feature_coords.append((float(row[1]), float(row[2])))

# Open and plot matches
with open("timeseries_results/1-matches.csv") as csvfile:
    csvreader = csv.reader(csvfile)
    feature_id = None
    feature_coords = []
    match_ids = []
    for row in csvreader:
        # If the row is a new FID, plot the previous list and append to it
        if int(row[0]) != feature_id:
            if feature_id is not None:
                x = [c[0] for c in feature_coords]
                y = [c[1] for c in feature_coords]
                ax[0].plot(x,y, color="red", alpha=0.4)
                max_id = max(set(match_ids), key=match_ids.count)
                if len(max_id) == 0:
                    ax[0].text(np.mean(x), np.mean(y), "None", color="white", fontsize=4)
                else:
                    ax[0].text(np.mean(x), np.mean(y), max_id, color="white", fontsize=4)
            feature_id = int(row[0])
            feature_coords = [(float(row[1]), float(row[2]))]
            match_ids = [row[3]]
        # Otherwise, append to it
        else:
            feature_coords.append((float(row[1]), float(row[2])))
            match_ids.append(row[3])

plt.show()