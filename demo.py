import numpy as np
import cv2
import os
import matplotlib.pyplot as plt
from astropy.io import fits

f_norm = fits.open("data/images/fits/halpha_width_mfbd_m300.fits")[0].data
f_sharp = fits.open("data/images/fits/halpha_width_sharpened.fits")[0].data

f = f_sharp

img_data = f.astype(np.uint8)

# Blur + threshold
blur = cv2.GaussianBlur(img_data,(7,7),0)
th = cv2.adaptiveThreshold(blur, 255, cv2.ADAPTIVE_THRESH_MEAN_C, cv2.THRESH_BINARY_INV, 15, 2)

fig, ax = plt.subplots(1,2)
ax[0].imshow(th, origin="lower")
ax[1].imshow(f, origin="lower")

# Edges + contours
edges = cv2.Canny(img_data, threshold1=100, threshold2=150, apertureSize=7)

contours, hierarchy = cv2.findContours(edges, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)

ctr_map = np.zeros_like(edges)
cv2.drawContours(ctr_map, contours, -1, (255,255,255), 1)

plt.show()