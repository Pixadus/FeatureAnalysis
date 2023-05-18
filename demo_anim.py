import matplotlib.pyplot as plt
from matplotlib import animation
import numpy as np
from astropy.io import fits
from skimage import filters, data, color, morphology, segmentation, feature


f = fits.open("data/images/fits/nb.6563.ser_171115.bis.wid.23Apr2017.target2.all.fits")[0].data

# Create a Hessianified version of f
fh = np.copy(f)
for i in range(120):
    fhi = fh[i,:,:]
    fhi = (fhi*180).astype(np.uint8)
    fhi = filters.unsharp_mask(fhi, radius=1.0, amount=4.0)
    fhi_thresh = filters.threshold_otsu(fhi)-0.05
    fhi[fhi < fhi_thresh] = 0.70
    fhih = filters.hessian(fhi, range(1,5), black_ridges=True)
    fhih[fhi == 0.70] = 0
    fhih[fhih < 1] = 0
    fh[i,:,:] = fhih
    print(i)

fig, ax = plt.subplots(1,2, figsize=(10,10))

ax[0].set_title("Sharpened original")
ax[1].set_title("Otsu + Hessian filters")

artists = []
for i in range(120):
    if i == 0:
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
    artists.append([img0, title0, img1, title1])

ani = animation.ArtistAnimation(fig=fig, artists=artists, interval=300, blit=False)
writer = animation.FFMpegWriter(fps = 2.5, bitrate=16000)
ani.save("animation.mp4", writer=writer)
plt.show()