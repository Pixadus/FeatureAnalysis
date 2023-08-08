# Name: diagnostics.py
# Date: Wed Aug. 2 2023
# Description: Get per-coordinate statistics for each OCCULT-2 fibril tracing, including comparison to other diagnostics
#              and analysis from analysis/analysis.py.

from astropy.io import fits
from analysis.analysis import Analysis
import pandas as pd

# Open timeseries files
f_bis_width = fits.open("data/images/fits/nb.6563.ser_171115.bis.wid.23Apr2017.target2.all.fits")[0].data
f_bis_vel = fits.open("data/images/fits/nb.6563.ser_171115.bisector.vel.23Apr2017.target2.all.fits")[0].data
f_core_int = fits.open("data/images/fits/nb.6563.ser_171115.core.int.23Apr2017.target2.all.fits")[0].data
f_core_vel = fits.open("data/images/fits/nb.6563.ser_171115.core.vel.23Apr2017.target2.all.fits")[0].data

# Open active and completed DataFrames
active = pd.read_csv("ts_res/lifetime_pdf/active.csv")
completed = pd.read_csv("ts_res/lifetime_pdf/completed.csv")

# Run analysis of core width