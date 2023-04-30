#!/usr/bin/python
# -*- coding: utf-8 -*-
"""
Created on Sun 4.30.23
@title: Timeseries demo
@author: Parker Lamb
@description: Demo a FITS timeseries
"""

import matplotlib.pyplot as plt
from tracing.tracing import AutoTracingOCCULT
from astropy.io import fits
import time

# Open the file
fname = "data/images/fits/nb.6563.ser_171115.bis.wid.23Apr2017.target2.all.fits"
f = fits.open(fname)
dat = f[0].data

# Set up subplots
fig, ax = plt.subplots(2,2)

# Get two frames
frame0 = dat[0,:,:]
frame1 = dat[1,:,:]

# Trace out data on each frame
t0 = AutoTracingOCCULT(data=frame0)
t1 = AutoTracingOCCULT(data=frame1)

# Get tracing results
print("Tracing")
t0_res = t0.run()
t1_res = t1.run()

# Display t0_res on frame0
print("Displaying tracings on f0")
ts = time.time()
ax[0,0].set_title("Initial frame0 with tracing")
ax[0,0].imshow(frame0, origin="lower")
for line in t0_res:
    x = [coord[0] for coord in line]
    y = [coord[1] for coord in line]
    ax[0,0].plot(x,y)
print("Time:", time.time()-ts)

# Display t1_res on frame1
print("Displaying tracings on f1")
ts = time.time()
ax[0,1].set_title("Initial frame1 with tracing")
ax[0,1].imshow(frame1, origin="lower")
for line in t1_res:
    x = [coord[0] for coord in line]
    y = [coord[1] for coord in line]
    ax[0,1].plot(x,y)
print("Time:", time.time()-ts)

# Display patch on ax 3
print("Displaying t0 patch on ax 3")
ts = time.time()
ax[1,0].set_title("t0 blit")
fig[1,0].canvas.blit(fig[0,0].bbox)
print("Time:", time.time()-ts)

# Display patch on ax 4
print("Displaying t1 patch on ax 4")
ts = time.time()
ax[1,1].set_title("t1 patch")
fig[1,1].canvas.blit(fig[0,1].bbox)
print("Time:", time.time()-ts)

plt.show()