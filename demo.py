import numpy as np
import sys
float_formatter = "{:.2f}".format
np.set_printoptions(threshold=sys.maxsize, formatter={'float_kind':float_formatter})
import cv2
import matplotlib.pyplot as plt
import matplotlib as mpl
mpl.rcParams['savefig.format'] = 'svg'
mpl.rcParams['savefig.dpi'] = 300
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
f_ts = fits.open("data/images/fits/nb.6563.ser_171115.bis.wid.23Apr2017.target2.all.fits")[0].data

for i in range(109, 120):
    print(i)
    f = (f_ts[i]*180).astype(np.uint8)

    # f = (f[0,100:600,:500]*180).astype(np.uint8)

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
    # filt1[filt1 < 0.33] = 0

    init_ls = segmentation.checkerboard_level_set(filt1.shape, 3)

    evo = []
    cb = store_evolution_in(evo)

    # Run acwe
    ls = segmentation.morphological_chan_vese(filt1, num_iter=10, 
                                            init_level_set=init_ls,
                                            smoothing=1, iter_callback=cb)
    
    # Run OCCULT-2
    ls_occ = AutoTracingOCCULT(data=filt1).run(
        nsm1=6,
        ngap=3, 
        rmin=25,
        qthresh2=0
    )

    # Plotting
    fig, ax = plt.subplots(1, 2)

    ax[0].imshow(filt1, origin="lower", cmap="gray")
    ax[0].set_title("Polyline tracings")
    ax[0].set_xlim(0, 1000)
    ax[0].set_ylim(0, 1000)
    ax[1].imshow(filt1, origin="lower", cmap="gray")
    ax[1].set_title("OCCULT-2 tracings")
    ax[1].set_xlim(0, 1000)
    ax[1].set_ylim(0, 1000)
    contours = measure.find_contours(ls, 0.5)
    # Convert contours to shapely polygons + run curvature segmentation
    polygons = []
    for contour in contours:
        try:
            polygon = shapely.Polygon([(x,y) for x,y in zip(contour[:,1], contour[:,0])])
        except ValueError:
            continue
        if polygon.area > 100:
            try:
                seg = CurvatureSegmentation(polygon=polygon, min_area=150, percent_thresh=0.2, max_spatial_dist=30).run()
            except ValueError:
                print("ValErr")
                continue
            polygons.append(seg)

    # Display contents of multipolygons
    for multipolygon in polygons:
        for polygon in multipolygon.geoms:
            if polygon.area > 300:
                x,y = polygon.exterior.xy
                # ax.plot(x,y, linewidth=0.75)
                if abs(np.min(x) - np.max(x)) > abs(np.min(y) - np.max(y)):
                    pf = np.polyfit(x,y, 2)
                    p = np.poly1d(pf)
                    dy = p(x)
                    ax[0].plot(x,dy, color='cyan')
                else:
                    pf = np.polyfit(y,x,2)
                    p = np.poly1d(pf)
                    dx = p(y)
                    ax[0].plot(dx, y, color='cyan')
                
    # Plot OCCULT-2 tracings
    for feat in ls_occ:
        x = [c[0] for c in feat]
        y = [c[1] for c in feat]
        ax[1].plot(x,y, color='cyan')

    plt.savefig("ts_res/polyfit/{}.png".format(i), format='png')
    # plt.show()