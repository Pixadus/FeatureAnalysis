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
from skimage import filters, morphology, segmentation, feature, measure, transform, restoration, exposure
from tracing.tracing import AutoTracingOCCULT
from analysis.analysis import Analysis

# Open the file
f_ts = fits.open("data/images/fits/nb.6563.ser_171115.bis.wid.23Apr2017.target2.all.fits")[0].data

# Try running on good seeing frames
for i in range(62, 87):
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
    print("Tracing frame {}".format(i))
    ls_occ = AutoTracingOCCULT(data=filt1).run(
        nsm1=6,
        ngap=3, 
        rmin=25,
        qthresh2=0
    )

    # Convert tracings to a dictionary
    f_num = 0
    f_data = {}
    for feature in ls_occ:
        f_data[f_num] = []
        for coord in feature:
            c = {"coord" : (float(coord[0]), float(coord[1]))}
            f_data[f_num].append(c)
        f_num += 1

    # Run analysis on the fibril
    print("Running analysis on frame {}".format(i))
    an = Analysis(f_sharpened, f_data)
    an.set_opts()
    res = an.run()

    # Plotting
    fig, ax = plt.subplots(1, 1)

    ax.imshow(filt1, origin="lower", cmap="gray")
    ax.set_title("OCCULT-2 tracings")
    ax.set_xlim(0, 1000)
    ax.set_ylim(0, 1000)
                
    # Plot OCCULT-2 tracings
    print("Writing frame {} data to ts_res/hess_good/{}.csv".format(i,i))
    with open('ts_res/hess/{}.csv'.format(i), 'w') as csvfile:
        csvw = csv.writer(csvfile)
        for fnum in res.keys():
            for coord_dict in res[fnum]:
                csvw.writerow([fnum, coord_dict['coord'][0], coord_dict['coord'][1], coord_dict['breadth'], coord_dict['length']])

    plt.savefig("ts_res/hess_good/{}.png".format(i), format='png')
    plt.close(fig)
    # plt.show()