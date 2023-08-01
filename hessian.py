import numpy as np
import sys
float_formatter = "{:.2f}".format
np.set_printoptions(threshold=sys.maxsize, formatter={'float_kind':float_formatter})
import cv2
import csv
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
from scipy.sparse import csr_matrix
from scipy.sparse.csgraph import minimum_spanning_tree
import itertools

# Open the file
f_ts = fits.open("data/images/fits/nb.6563.ser_171115.bis.wid.23Apr2017.target2.all.fits")[0].data

for i in range(0, 120):
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

    # Run acwe
    # ls = segmentation.morphological_chan_vese(filt1, num_iter=10, 
    #                                         init_level_set=init_ls,
    #                                         smoothing=1, iter_callback=cb)
    
    # Run OCCULT-2
    ls_occ = AutoTracingOCCULT(data=filt1).run(
        nsm1=6,
        ngap=3, 
        rmin=25,
        qthresh2=0
    )

    # Plotting
    fig, ax = plt.subplots(1, 1)

    ax.imshow(filt1, origin="lower", cmap="gray")
    ax.set_title("OCCULT-2 tracings")
    ax.set_xlim(0, 1000)
    ax.set_ylim(0, 1000)
                
    # Plot OCCULT-2 tracings
    with open('ts_res/hess/{}.csv'.format(i), 'w') as csvfile:
        csvw = csv.writer(csvfile)
        for feat in ls_occ:
            fnum= ls_occ.index(feat)
            x = [c[0] for c in feat]
            y = [c[1] for c in feat]
            for xi, yi in zip(x,y):
                csvw.writerow([fnum, xi, yi])
            ax.plot(x,y, color='cyan')

    plt.savefig("ts_res/hess/{}.png".format(i), format='png')
    plt.close(fig)
    # plt.show()