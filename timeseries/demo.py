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
from astropy.io import fits

# Open the file
fname = "data/images/fits/nb.6563.ser_171115.bis.wid.23Apr2017.target2.all.fits"
f = fits.open(fname)
dat = f[0].data

# Create subplots to display image data on
fig, ax = plt.subplots()

# Iterate through all images on animation
ims = []
for i in range(f[0].data.shape[0]):
    im = ax.imshow(f[0].data[i,:,:], animated=True, origin="lower")
    if i==0:
        ax.imshow(f[0].data[i,:,:], origin="lower")
    ims.append([im])

# Animate it
ani = animation.ArtistAnimation(fig, ims, interval=50, blit=True,
                                repeat_delay=1000)

plt.show()