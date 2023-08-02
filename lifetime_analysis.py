# Name: lifetime_analysis.py
# Created: just now
# Description: Look at lifetime results from lifetime.py, and generate usable statistics from them. 

import pandas as pd
import numpy as np
import scipy.stats as stats
import matplotlib.pyplot as plt

# Open active and completed DataFrames
active = pd.read_csv("ts_res/lifetime_pdf/active.csv")
completed = pd.read_csv("ts_res/lifetime_pdf/completed.csv")

# Set up subplots
fig, ax = plt.subplots(1, 2)

# Results from active
active_life = (120 - active.start_frame).to_numpy()

# Remove 0-frame active results (i.e. those that started on frame 120) & sort low-to-high for PDF
active_life = active_life[np.where(active_life > 0)]
active_life.sort()

# Quantify results for active
active_life_mean = np.mean(active_life)
active_life_std = np.std(active_life)
active_life_pdf = stats.norm.pdf(active_life, active_life_mean, active_life_std)

# Let's look at results from completed without matching. 
comp_life_nomatch = (completed.end_frame - completed.start_frame).to_numpy()
comp_life_nomatch.sort()

# Quantify results for nomatch
comp_life_nomatch_mean = np.mean(comp_life_nomatch)
comp_life_nomatch_std = np.std(comp_life_nomatch)
comp_life_nomatch_pdf = stats.norm.pdf(comp_life_nomatch, comp_life_nomatch_mean, comp_life_nomatch_std)

# Plot results for comp_life_nomatch and active_life
ax[0].plot(active_life, active_life_pdf)
ax[0].set_title("Active lifetime density function")
ax[0].set_xlabel("Lifetime (frames)")
ax[0].set_ylabel("Occurence")
ax[0].grid(True, alpha=0.3, linestyle="--")

ax[1].plot(comp_life_nomatch, comp_life_nomatch_pdf)
ax[1].set_title("Completed lifetime density function")
ax[1].set_xlabel("Lifetime (frames)")
ax[1].set_ylabel("Occurrence")
ax[1].grid(True, alpha=0.3, linestyle="--")

fig.tight_layout()
plt.show()