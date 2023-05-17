import numpy as np
import cv2
import matplotlib.pyplot as plt
from astropy.io import fits
from skimage import filters, data, color, morphology, segmentation
from tracing.tracing import AutoTracingOCCULT

# Open the file
f = fits.open("data/images/fits/nb.6563.ser_171115.bis.wid.23Apr2017.target2.all.fits")[0].data

f = (f[0,100:600,:500]*180).astype(np.uint8)

# Sharpen the image
f_sharpened = filters.unsharp_mask(f, radius=1, amount=4.0)

# Use Otsu's method
otsu_thresh = filters.threshold_otsu(f_sharpened)-0.05
otsu_img = np.copy(f_sharpened)
otsu_img[otsu_img < otsu_thresh] = 0.70

# Demo some segmentation methods
hsm4 = filters.hessian(otsu_img, range(1,5), black_ridges=True)
hsm4[otsu_img == 0.70] = 0

# Try some edge detection. Hessian results are a bit rough - how can we clean up?
random_walker = segmentation.random_walker(otsu_img, hsm4)

# --------------
# Plot everything
fig, ax = plt.subplots(1,1)

ax.set_title("Sobel edge detection")
ax.imshow(random_walker, origin="lower", cmap="gray")

# ax[0].set_title("Hessian")
# ax[0].imshow(hsm4, origin="lower", cmap="gray")


plt.show()
