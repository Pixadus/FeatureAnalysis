import numpy as np
import cv2
import matplotlib.pyplot as plt
from astropy.io import fits
from skimage import filters, data, color, morphology, segmentation, feature
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

# Apply Hessian to get a binary map
hsm4 = filters.hessian(otsu_img, range(1,5), black_ridges=True)
hsm4[otsu_img == 0.70] = 0
hsm4[hsm4 < 1] = 0

# Try out reconstruction to get rid of little gaps
# footprint2 = morphology.disk(2)
# footprint1 = morphology.disk(2)

# closing = morphology.binary_closing(hsm4, footprint1)

# try out some segmentation algorithms

# --------------
# Plot everything
fig, ax = plt.subplots(1, 2)

# ax.set_title("Trying to clean up the edges")
# ax.imshow(median, origin="lower", cmap="gray")

ax[0].set_title("OCCULT-2 on sharpened original")
ax[0].imshow(f_sharpened, origin="lower", cmap="gray")
ax[1].set_title("OCCULT-2 on Hessian")
ax[1].imshow(hsm4, origin="lower", cmap="gray")

# # OCCULT tracing

# ogtr = AutoTracingOCCULT(data=f_sharpened).run(rmin=35)
# hstr = AutoTracingOCCULT(data=hsm4).run(nsm1=6, ngap=3, rmin=35)

# xs = []
# ys = []
# for fibril in ogtr:
#     xs.extend([c[0] for c in fibril])
#     ys.extend([c[1] for c in fibril])
#     xs.append(None)
#     ys.append(None)
# ax[0].plot(xs, ys, color="cyan")

# xs = []
# ys = []
# for fibril in hstr:
#     xs.extend([c[0] for c in fibril])
#     ys.extend([c[1] for c in fibril])
#     xs.append(None)
#     ys.append(None)
# ax[1].plot(xs, ys, color="cyan")

plt.show()
# ------------- Other segmentation methods below

# def store_evolution_in(lst):
#     """Returns a callback function to store the evolution of the level sets in
#     the given list.
#     """

#     def _store(x):
#         lst.append(np.copy(x))

#     return _store


# # Morphological ACWE
# image = hsm4

# # Initial level set
# init_ls = segmentation.checkerboard_level_set(image.shape, 2)
# # List with intermediate results for plotting the evolution
# evolution = []
# callback = store_evolution_in(evolution)
# ls = segmentation.morphological_chan_vese(image, num_iter=5, init_level_set=init_ls,
#                              smoothing=2, iter_callback=callback)

# fig, axes = plt.subplots(1, 2, figsize=(8, 8))
# ax = axes.flatten()

# ax[0].imshow(image, cmap="gray", origin="lower")
# ax[0].set_axis_off()
# ax[0].contour(ls, [0.5], colors='r')
# ax[0].set_title("ACWE segmentation (ck2, s2)", fontsize=12)

# ax[1].imshow(ls, cmap="gray", origin="lower")
# ax[1].set_axis_off()
# contour = ax[1].contour(evolution[1], [0.5], colors='g')
# contour.collections[0].set_label("g, Iteration 1")
# contour = ax[1].contour(evolution[2], [0.5], colors='y')
# contour.collections[0].set_label("y, Iteration 2")
# contour = ax[1].contour(evolution[3], [0.5], colors='r')
# contour.collections[0].set_label("r, Iteration 3")
# ax[1].legend(loc="upper right")
# title = "Morphological ACWE evolution"
# ax[1].set_title(title, fontsize=12)

# fig.tight_layout()
# plt.show()