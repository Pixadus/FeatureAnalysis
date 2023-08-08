# Name: lifetime_analysis.py
# Created: just now
# Description: Look at lifetime results from lifetime.py, and generate usable statistics from them. 

import pandas as pd
import numpy as np
from scipy.spatial.distance import cdist
import scipy.stats as stats
import matplotlib.pyplot as plt
import ast

# Variables
max_completed_distance = 10         # Max completed distance to match completed features to one another

# Open active and completed DataFrames
active = pd.read_csv("ts_res/lifetime_pdf/active.csv")
completed = pd.read_csv("ts_res/lifetime_pdf/completed.csv")

# Results from active
active_life = (120 - active.start_frame).to_numpy()

# Remove 0-frame active results (i.e. those that started on frame 120) & sort low-to-high for PDF
active_life = active_life[np.where(active_life > 0)]
active_life.sort()

# Quantify results for active
active_life_mean = np.mean(active_life)
active_life_std = np.std(active_life)
active_life_pdf = stats.norm.pdf(active_life, active_life_mean, active_life_std)
print("Active mean:", active_life_mean, "Active std:", active_life_std)

# Let's look at results from completed without matching. 
comp_life_nomatch_full = (completed.end_frame - completed.start_frame).to_numpy()
comp_life_nomatch_full.sort()

# Quantify results for nomatch full
comp_life_nomatch_full_mean = np.mean(comp_life_nomatch_full)
comp_life_nomatch_full_std = np.std(comp_life_nomatch_full)
comp_life_nomatch_full_pdf = stats.norm.pdf(comp_life_nomatch_full, comp_life_nomatch_full_mean, comp_life_nomatch_full_std)
print("Comp_nomatch_full mean:", comp_life_nomatch_full_mean, "Comp_nomatch_full std:", comp_life_nomatch_full_std)

# Now - try to match completed features together. Create lifetimes for both. 
comp_life_nomatch = []
comp_life_match = []
# First, generate mean x and mean y values for all completed features
completed.insert(4, "x_mean", 0.0)
completed.insert(5, "y_mean", 0.0)
for index, row in completed.iterrows():
    x_mean = 0.0
    y_mean = 0.0

    # Reading from CSV has given us a list as a string by default
    xvals = ast.literal_eval(row.xvals)
    yvals = ast.literal_eval(row.yvals)
    for xlist, ylist in zip(xvals, yvals):
        x_mean += np.mean(xlist)
        y_mean += np.mean(ylist)
    completed.loc[index, 'x_mean'] = x_mean / len(xvals)
    completed.loc[index, 'y_mean'] = y_mean / len(yvals)

# Now - iterate over all completed rows, and try to conditionally match to one another
for index, row in completed.iterrows():
    x_mean = row.x_mean
    y_mean = row.y_mean

    # Calculate distances from current 
    mcoords = np.array([completed.x_mean, completed.y_mean]).T
    mcoords_details = np.array([completed.start_frame, completed.end_frame])
    dists = cdist(np.array([[x_mean],[y_mean]]).T, mcoords)
    dists_full = np.concatenate([dists.T, mcoords_details.T], axis=1)

    # Sort by distance
    dists_full = dists_full[dists_full[:,0].argsort()]

    # Get frames less than max_complete_distance away and more than 0 away
    dists_full = dists_full[np.where(
        (dists_full[:,0] > 0) &
        (dists_full[:,0] < max_completed_distance)
    )]

    # Don't allow for overlapping frames
    overlaprows = []
    def overlaps(x, y):
        return max(x.start,y.start) < min(x.stop,y.stop)
    
    for row_sup in dists_full:
        for row_sub in dists_full:
            if overlaps(range(int(row_sup[1]), int(row_sup[2])), range(int(row_sub[1]), int(row_sub[2]))) and (row_sup != row_sub).all():
                overlaprows.append([row_sup[0], row_sub[0]])
    
    # Remove reversed duplicates
    olr_unique = {tuple(item) for item in map(sorted,overlaprows)}
    for olr in olr_unique:
        # olr[1] holds the more distant duplicate - so get rid of it
        dists_full = dists_full[np.where(dists_full[:,0] != olr[1])]
    
    # If there are some matches, add to match lifetimes
    lifetime = 0
    if len(dists_full):
        for startframe, endframe in zip(dists_full[:,1], dists_full[:,2]):
            lifetime += endframe - startframe
        comp_life_match.append(lifetime)

    # Otherwise, add to unmatched lifetimes
    else:
        lifetime = row.end_frame - row.start_frame
        comp_life_nomatch.append(lifetime)
    # dear lord this was exhausting. 

# Sort match and nomatch
comp_life_nomatch.sort()
comp_life_match.sort()

# Quantify results for both nomatch and match
comp_life_nomatch_mean = np.mean(comp_life_nomatch)
comp_life_nomatch_std = np.mean(comp_life_nomatch)
comp_life_nomatch_pdf = stats.norm.pdf(comp_life_nomatch, comp_life_nomatch_mean, comp_life_nomatch_std)
print("Comp_nomatch mean:", comp_life_nomatch_mean, "Comp_nomatch std:", comp_life_nomatch_std)
comp_life_match_mean = np.mean(comp_life_match)
comp_life_match_std = np.std(comp_life_match)
comp_life_match_pdf = stats.norm.pdf(comp_life_match, comp_life_match_mean, comp_life_match_std)
print("Comp_match mean:", comp_life_match_mean, "Comp_match std:", comp_life_match_std)

# Set up subplots
fig, ax = plt.subplots(1, 3)

# Plot results for active_life, comp_life_nomatch and comp_life_match
ax[0].plot(active_life, active_life_pdf)
ax[0].set_title("Active lifetime density function")
ax[0].set_xlabel("Lifetime (frames)")
ax[0].set_ylabel("Occurence")
# ax[0].axvline(x=active_life_mean, color="red")
ax[0].grid(True, alpha=0.3, linestyle="--")

ax[1].plot(comp_life_nomatch, comp_life_nomatch_pdf)
ax[1].set_title("Completed lifetime (isolated) density function")
ax[1].set_xlabel("Lifetime (frames)")
ax[1].set_ylabel("Occurrence")
# ax[1].axvline(x=comp_life_nomatch_mean, color="red")
ax[1].grid(True, alpha=0.3, linestyle="--")

ax[2].plot(comp_life_match, comp_life_match_pdf)
ax[2].set_title("Completed lifetime (matched) density function")
ax[2].set_xlabel("Lifetime (frames)")
ax[2].set_ylabel("Occurrence")
# ax[2].axvline(x=comp_life_match_mean, color="red")
ax[2].grid(True, alpha=0.3, linestyle="--")

# fig.tight_layout()
plt.show()