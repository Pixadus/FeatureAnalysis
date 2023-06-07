import numpy as np
import cv2
import matplotlib.pyplot as plt
from astropy.io import fits
from skimage import filters, data, color, morphology, segmentation, feature, measure
from tracing.tracing import AutoTracingOCCULT
import shapely
from label_centerlines import get_centerline

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

# ------------- Other segmentation methods below

def store_evolution_in(lst):
    """Returns a callback function to store the evolution of the level sets in
    the given list.
    """

    def _store(x):
        lst.append(np.copy(x))

    return _store


# Morphological ACWE
image = hsm4.astype(bool)

# Initial level set
init_ls = segmentation.checkerboard_level_set(image.shape, 2)
# List with intermediate results for plotting the evolution
# acwe = segmentation.morphological_chan_vese(image, num_iter=3, init_level_set=init_ls, smoothing=2)

# Dilate a bit
fp = morphology.square(1)
dial = morphology.binary_dilation(image, fp)

# Remove small holes
sh = morphology.remove_small_holes(dial, 64)
filtered = morphology.remove_small_objects(sh, 10)

# Erosion
fp = morphology.square(1)
ero = morphology.binary_erosion(filtered, fp)

contours = measure.find_contours(ero, 0.5)

# Plotting
fig, ax = plt.subplots(1, 1, figsize=(8,8))

ax.imshow(ero, origin="lower", cmap="gray")
ax.set_title("Contours")

polygons = []
for contour in contours:
    ax.plot(contour[:, 1], contour[:, 0], linewidth=0.5, color="red")
    # Create polygon
    polygon = shapely.Polygon(contour)
    polygons.append(polygon)

avg = 0
for polygon in polygons:
    avg += polygon.area
avg = avg / len(polygons)

# Create a polyfit for polygons larger than avg
for polygon, contour in zip(polygons, contours):
    if polygon.area > avg:
        pf = np.polyfit(contour[:,1], contour[:,0], deg=3)

# for contour in gicnt:
#     ax[1].plot(contour[:, 1], contour[:, 0], linewidth=0.5, color="red")

fig.tight_layout()
plt.show()