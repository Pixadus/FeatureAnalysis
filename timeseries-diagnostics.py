# Name: diagnostics.py
# Date: Wed Aug. 2 2023
# Description: Get per-coordinate statistics for each OCCULT-2 fibril tracing, including comparison to other diagnostics
#              and analysis from analysis/analysis.py.

from astropy.io import fits
from analysis.analysis import Analysis
import matplotlib.pyplot as plt
import pandas as pd
import numpy as np
import ast

# Open timeseries files
f_bis_width = fits.open("data/images/fits/nb.6563.ser_171115.bis.wid.23Apr2017.target2.all.fits")[0].data
f_bis_vel = fits.open("data/images/fits/nb.6563.ser_171115.bisector.vel.23Apr2017.target2.all.fits")[0].data
f_core_int = fits.open("data/images/fits/nb.6563.ser_171115.core.int.23Apr2017.target2.all.fits")[0].data
f_core_vel = fits.open("data/images/fits/nb.6563.ser_171115.core.vel.23Apr2017.target2.all.fits")[0].data

# Open active and completed DataFrames
active = pd.read_csv("ts_res/lifetime_pdf/active.csv")
completed = pd.read_csv("ts_res/lifetime_pdf/completed.csv")

# Convert DataFrame values to lists - CSV import resolved to a string(lists) - can't iterate over
active_bvals = []
active_lvals = []
completed_bvals = []
completed_lvals = []
for index, row in active.iterrows():
    # Evaluate the imported string literally to convert datatypes automatically
    bvals = ast.literal_eval(row.bvals)
    lvals = ast.literal_eval(row.lvals)

    # Append to each list - not flattened so we can do later frame-by-frame comparisons
    active_bvals.extend(bvals)
    active_lvals.extend(lvals)

for index, row in completed.iterrows():
    bvals = ast.literal_eval(row.bvals)
    lvals = ast.literal_eval(row.lvals)
    completed_bvals.extend(bvals)
    completed_lvals.extend(lvals)

# Create subplots for active frame readths/lengths
fig, ax = plt.subplots(1,2)
fig.suptitle("Active frame")

# Flatten bvals and lvals
active_bvals_flattened = [item for sublist in active_bvals for item in sublist]
active_lvals_flattened = [max(sublist) for sublist in active_lvals]

# Create a histogram of breadths and lengths for active frames
abcounts, abbins = np.histogram(active_bvals_flattened)
alcounts, albins = np.histogram(active_lvals_flattened, range=(min(active_lvals_flattened), np.mean(active_lvals_flattened) + np.std(active_lvals_flattened)))

# Plot histograms
ax[0].stairs(abcounts, abbins, fill=True)
# for bin, cnt in zip(abbins, abcounts):
#     # This will put bin count values on the tops of each bar. Disabled for now due to layout issues. 
#     ax[0].text(bin, cnt+(max(abcounts)/100), cnt)
ax[0].vlines(abbins, 0, abcounts.max(), colors='w')
ax[0].grid(color='b', linestyle='-', alpha=0.2)
ax[0].set_title("Feature breadth histogram")
ax[0].set_xlabel("Breadth")
ax[0].set_ylabel("Count")

ax[1].stairs(alcounts, albins, fill=True)
ax[1].vlines(albins, 0, alcounts.max(), colors='w')
ax[1].grid(color='b', alpha=0.2)
ax[1].set_title("Feature length histogram (max within 1 std)")
ax[1].set_xlabel("Length")
ax[1].set_ylabel("Count")
fig.tight_layout()
fig.savefig("ts_res/diagnostics/active_bl_hists.png", dpi=400, format="png")

# 