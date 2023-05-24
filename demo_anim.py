import matplotlib.pyplot as plt
from matplotlib import animation
import numpy as np
from astropy.io import fits
from skimage import filters
from tracing.tracing import AutoTracingOCCULT
from analysis.analysis import Analysis
import csv

f = fits.open("data/images/fits/nb.6563.ser_171115.bis.wid.23Apr2017.target2.all.fits")[0].data

# Frame start/stop values
start = 0
stop = 120

# Create a Hessianified version of f
fh = np.copy(f)
for i in range(start, stop):
    fhi = fh[i,:,:]
    fhi = (fhi*180).astype(np.uint8)
    fhi = filters.unsharp_mask(fhi, radius=1.0, amount=4.0)
    fhi_thresh = filters.threshold_otsu(fhi)
    fhi[fhi < fhi_thresh] = 0.70
    fhih = filters.hessian(fhi, range(1,5), black_ridges=True)
    fhih[fhi == 0.70] = 0
    fhih[fhih < 1] = 0
    fh[i,:,:] = fhih
    print(i)

fig, ax = plt.subplots(1,2, figsize=(10,10))

ax[0].set_title("Sharpened original")
ax[1].set_title("Otsu + Hessian filters")

# Run OCCULT-2
orig_tr = []
hess_tr = []
for i in range(start, stop):
    print("O{}".format(i))
    trm = AutoTracingOCCULT(data=f[i,:,:]).run(rmin=35)
    trh = AutoTracingOCCULT(data=fh[i,:,:]).run(nsm1=6, ngap=3, rmin=35)

    # Convert tracings to a dictionary
    f_num = 0
    fh_data = {}
    for feature in trh:
        fh_data[f_num] = []
        for coord in feature:
            c = {"coord" : (float(coord[0]), float(coord[1]))}
            fh_data[f_num].append(c)
        f_num += 1
    # Convert tracings to a dictionary
    f_num = 0
    fb_data = {}
    for feature in trh:
        fb_data[f_num] = []
        for coord in feature:
            c = {"coord" : (float(coord[0]), float(coord[1]))}
            fb_data[f_num].append(c)
        f_num += 1

    # Run analysis
    print("Analyzing base {}".format(i))
    an = Analysis(f[i,:,:], fb_data)
    an.set_opts()
    trm_results = an.run()

    print("Analyzing hess {}".format(i))
    an = Analysis(f[i,:,:], fh_data)
    an.set_opts()
    trh_results = an.run()

    with open("ts_res/base/{}.csv".format(i), 'w') as csvfile:
        writer = csv.writer(csvfile)
        for fib in trm_results.keys():
            for coord in trm_results[fib]:
                writer.writerow([
                    fib,
                    coord['coord'][0],
                    coord['coord'][1],
                    coord['length'],
                    coord['breadth']
                ])
    with open("ts_res/hess/{}.csv".format(i), 'w') as csvfile:
        writer = csv.writer(csvfile)
        for fib in trh_results.keys():
            for coord in trh_results[fib]:
                writer.writerow([
                    fib,
                    coord['coord'][0],
                    coord['coord'][1],
                    coord['length'],
                    coord['breadth']
                ])

    xs = []
    ys = []
    for fib in trm:
        xs.extend([c[0] for c in fib])
        ys.extend([c[1] for c in fib])
        xs.append(None)
        ys.append(None)
    ln, = ax[0].plot(xs, ys, color="cyan")
    orig_tr.append(ln)
    xs = []
    ys = []
    for fib in trh:
        xs.extend([c[0] for c in fib])
        ys.extend([c[1] for c in fib])
        xs.append(None)
        ys.append(None)
    ln, = ax[1].plot(xs,ys, color="cyan")
    hess_tr.append(ln)

artists = []
for i in range(start, stop):
    if (i-start) == 0:
        ax[0].imshow(f[i,:,:], origin="lower", cmap="gray")
        ax[1].imshow(fh[i,:,:], origin="lower", cmap="gray")
    img0 = ax[0].imshow(f[i,:,:], origin="lower", cmap="gray", animated=True)
    title0 = ax[0].text(0.5,-0.15,"Frame {}".format(i), 
                size=plt.rcParams["axes.titlesize"],
                ha="center", transform=ax[0].transAxes, )
    img1 = ax[1].imshow(fh[i,:,:], origin="lower", cmap="gray", animated=True)
    title1 = ax[1].text(0.5,-0.15,"Frame {}".format(i), 
            size=plt.rcParams["axes.titlesize"],
            ha="center", transform=ax[1].transAxes, )
    artists.append([img0, orig_tr[i-start], title0, img1, hess_tr[i-start], title1])

ani = animation.ArtistAnimation(fig=fig, artists=artists, interval=300, blit=False)
writer = animation.FFMpegWriter(fps = 2.5, bitrate=16000)
ani.save("animation.mp4", writer=writer)
plt.show()