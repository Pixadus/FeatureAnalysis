from astropy.io import fits
import matplotlib.pyplot as plt
import cv2
import numpy as np

f = fits.open("data/images/fits/sharp_crop_close.fits")[0].data

# Create subplots
fig, axs = plt.subplots(1,2)

# Calculate edges
edges = cv2.Canny(f, threshold1=100, threshold2=150, apertureSize=7)
ctrs = np.zeros_like(f)

# Calculate contours, disp on zeroed array
contours, hierarchy = cv2.findContours(edges, cv2.RETR_TREE, cv2.CHAIN_APPROX_TC89_L1)
cv2.drawContours(ctrs, contours, -1, (255, 0, 0), 1)

# Show plots
axs[0].imshow(edges, origin="lower")
axs[1].imshow(ctrs, origin="lower")
plt.show()