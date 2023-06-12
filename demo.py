import numpy as np
import cv2
import matplotlib.pyplot as plt
import matplotlib.animation as animation
from astropy.io import fits
from skimage import filters, data, color, morphology, segmentation, feature, measure, transform, restoration, exposure
from tracing.tracing import AutoTracingOCCULT
import shapely
from scipy.signal import savgol_filter
from scipy import ndimage
from label_centerlines import get_centerline
from scipy.sparse import csr_matrix
from scipy.sparse.csgraph import minimum_spanning_tree
import itertools

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

image = hsm4.astype(bool)

# Dilate a bit
fp = morphology.square(1)
dial = morphology.binary_dilation(image, fp)

# Remove small holes
sh = morphology.remove_small_holes(dial, 64)
filtered = morphology.remove_small_objects(sh, 10)

# Erosion
fp = morphology.square(1)
ero = morphology.binary_erosion(filtered, fp)

# filter
filt1 = filters.meijering(ero, sigmas=range(1,7,1), alpha=-1/3, black_ridges=False)
filt1 = filters.median(filt1)
filt1[filt1 < 0.3] = 0
maxima = morphology.extrema.local_maxima(filt1)
# sobel = filters.sobel(filt1)

low = 0.2
high = 0.7
lowt = (filt1 > low).astype(int)
hight = (filt1 > high).astype(int)
hyst = filters.apply_hysteresis_threshold(filt1, low, high)

# filt2 = segmentation.inverse_gaussian_gradient(filt1, 10, 3)
# filt1[filt1 < 0.5] = 0

# filt2 = filters.rank.gradient(filters.median(filt1, morphology.disk(3)), morphology.disk(2))
filt2 = filters.laplace(filt1)
# filt2[filt2 < 10] = 0
# filt2 = filt2 + morphology.extrema.local_maxima(filt1)
# filt2[filt2 > 0] = 1

init_ls = segmentation.checkerboard_level_set(filt1.shape, 3)

evo = []
cb = store_evolution_in(evo)

ls = segmentation.morphological_chan_vese(np.gradient(filt1)[0] > 0, num_iter=200, 
                                          init_level_set=np.gradient(filt1)[0] > 0,
                                          smoothing=1, iter_callback=cb)

# ls = segmentation.morphological_geodesic_active_contour(filt1, num_iter=100, init_level_set=hyst,
#                              smoothing=1, balloon=-1, iter_callback=cb)

# Plotting
fig, ax = plt.subplots(1, 1)
ax.imshow(np.gradient(filt1)[0] > 0, origin="lower", cmap="gray")
# ax[1].imshow(filt2, origin="lower", cmap="gray")
# ax.contour(ls, [0.25], colors="c")

for i in range(len(evo)):
    ax.cla()
    ax.imshow(filt1, origin="lower", cmap="gray")
    ax.set_title("GAC, iter={}".format(i))
    ax.contour(evo[i], [0.25], colors="c")
    fig.savefig("artist{}.png".format(i), format="png", dpi=400)
    print(i)


# ax.imshow(filt1, origin="lower", cmap="gray")
# ax.set_title("MorphACWE and MorphGAC")
# ax.contour(ls1, [0.5], colors='cyan')
# ax.contour(ls2, [0.5], colors='blue')

fig.tight_layout()
plt.show()