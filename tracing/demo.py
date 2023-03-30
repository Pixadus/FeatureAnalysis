#!/usr/bin/python3
# -*- coding: utf-8 -*-
"""
Created on Sun 1.15.21
@title: Timeseries demo
@author: Parker Lamb
@description: Demo a FITS timeseries
"""

import matplotlib.pyplot as plt
import matplotlib.animation as animation
from tracing import AutoTracingOCCULT
from astropy.io import fits

# Open the file
fname = "data/images/fits/nb.6563.ser_171115.bis.wid.23Apr2017.target2.all.fits"
f = fits.open(fname)
dat = f[0].data

# Create subplots to display image data on
fig, ax = plt.subplots(2)

# Set up occult on the first two images
occult_img1 = AutoTracingOCCULT(data = dat[0,:,:])
occult_img2 = AutoTracingOCCULT(data = dat[1,:,:])

# Get results for both
print("Running OCCULT-2 for image 1")
res1 = occult_img1.run()
print("Running OCCULT-2 for image 2")
res2 = occult_img2.run()

# Display both results
ax[0].imshow(dat[0,:,:], origin="lower")
ax[1].imshow(dat[1,:,:], origin="lower")
for result in res1:
    x = []
    y = []
    for coord in result:
        x.append(coord[0])
        y.append(coord[1])
    ax[0].plot(x,y, color="red", linewidth=1)

for result in res2:
    x = []
    y = []
    for coord in result:
        x.append(coord[0])
        y.append(coord[1])
    ax[1].plot(x,y, color="red", linewidth=1)

plt.show()