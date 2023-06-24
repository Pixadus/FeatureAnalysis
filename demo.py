import numpy as np
import sys
float_formatter = "{:.2f}".format
np.set_printoptions(threshold=sys.maxsize, formatter={'float_kind':float_formatter})
import cv2
import matplotlib.pyplot as plt
import matplotlib as mpl
mpl.rcParams['savefig.format'] = 'svg'
import matplotlib.animation as animation
from astropy.io import fits
from skimage import filters, data, color, morphology, segmentation, feature, measure, transform, restoration, exposure
from tracing.tracing import AutoTracingOCCULT
from helper.functions import CurvatureSegmentation
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

# Use global Otsu's method
otsu_thresh = filters.threshold_otsu(f_sharpened)-0.05
otsu_img = np.copy(f_sharpened)
otsu_img[otsu_img < otsu_thresh] = 0.70


# Apply Hessian to get a binary map
hsm4 = filters.hessian(otsu_img, range(1,6), black_ridges=True)
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
filt1 = filters.meijering(ero, sigmas=range(1,7,1), black_ridges=False)
filt1 = filters.median(filt1)
filt1[filt1 < 0.33] = 0

init_ls = segmentation.checkerboard_level_set(filt1.shape, 3)

evo = []
cb = store_evolution_in(evo)

ls = segmentation.morphological_chan_vese(filt1, num_iter=10, 
                                          init_level_set=init_ls,
                                          smoothing=1, iter_callback=cb)

# ls = segmentation.morphological_geodesic_active_contour(filt1, num_iter=100, init_level_set=hyst,
#                              smoothing=1, balloon=-1, iter_callback=cb)

# Plotting
fig, ax = plt.subplots(1, 2)

# ls = morphology.remove_small_holes(ls, 128)
ax[0].imshow(f_sharpened, origin="lower", cmap="gray")
ax[0].set_title("get_centerlines centerlines (sm=0.25, simp=0.2)")
ax[1].imshow(f_sharpened, origin="lower", cmap="gray")
ax[1].set_title("np.polylines centerlines (deg=2)")
contours = measure.find_contours(ls, 0.5)
# Convert contours to shapely polygons + run curvature segmentation
polygons = []
for contour in contours:
    polygon = shapely.Polygon([(x,y) for x,y in zip(contour[:,1], contour[:,0])])
    if polygon.area > 100:
        seg = CurvatureSegmentation(polygon=polygon, min_area=150, percent_thresh=0.2).run()
        polygons.append(seg)

# Display contents of multipolygons
for multipolygon in polygons:
    for polygon in multipolygon.geoms:
        if polygon.area > 150:
            x,y = polygon.exterior.xy
            ax[0].plot(x,y, linewidth=0.75)
            centerline = get_centerline(polygon, segmentize_maxlen=0.25, simplification=0.2)
            x,y = centerline.xy
            ax[0].plot(x,y, color='cyan')

# Display contents of multipolygons
for multipolygon in polygons:
    for polygon in multipolygon.geoms:
        if polygon.area > 150:
            x,y = polygon.exterior.xy
            ax[1].plot(x,y, linewidth=0.75)
            if abs(np.min(x) - np.max(x)) > abs(np.min(y) - np.max(y)):
                pf = np.polyfit(x,y, 2)
                p = np.poly1d(pf)
                dy = p(x)
                ax[1].plot(x,dy, color='cyan')
            else:
                pf = np.polyfit(y,x,2)
                p = np.poly1d(pf)
                dx = p(y)
                ax[1].plot(dx, y, color='cyan')

# Move "interior" polygons to interiors of polygons TODO
# newpolygons = []
# for polygon in polygons:
#     newpoly = polygon
#     within = np.where(np.array([p.within(polygon) for p in polygons]))
#     for w in within[0]:
#         if w != 0:
#             newpoly = newpoly - polygons[w]
#             print(len(newpoly.interiors))
#     newpolygons.append(newpoly)

# for i in range(len(evo)):
#     ax.cla()
#     ax.imshow(filt1, origin="lower", cmap="gray")
#     ax.set_title("GAC, iter={}".format(i))
#     ax.contour(evo[i], [0.25], colors="c")
#     fig.savefig("artist{}.png".format(i), format="png", dpi=400)
#     print(i)

fig.tight_layout()
plt.show()