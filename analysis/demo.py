#!/usr/bin/python3
# -*- coding: utf-8 -*-
"""
Created on Tue 2.7.23
@title: Analysis upsize demo
@author: Parker Lamb
@description: Script used to scale input .fits files
"""

import matplotlib.pyplot as plt
import cv2
from astropy.io import fits

f = fits.open("data/images/fits/halpha_width_sharpened.fits")[0].data
# plt.subplot(2,2,1)
# plt.imshow(f, origin="lower")

fsd = cv2.resize(f, (f.shape[0]*2, f.shape[1]*2))
fsd = cv2.equalizeHist(f)
img2 = cv2.GaussianBlur(fsd, (7, 7), 0)
edges = cv2.Canny(fsd, 80,100)
contours, hierarchy = cv2.findContours(edges, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
cv2.drawContours(f, contours, -1, (0, 255, 0), 1)
plt.imshow(f, origin="lower")
plt.show()

