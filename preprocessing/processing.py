#!/usr/bin/python3
# -*- coding: utf-8 -*-
"""
Created on Tue 7.12.22
@title: Preprocessing algorithms
@author: Parker Lamb
@description: Contains algorithms for preprocessing
images.
"""

from scipy.ndimage import gaussian_filter
import cv2
import numpy as np

def gaussian_smoothing(img_data, params):
    """
    Run a Gaussian filter on the img data.

    Parameters
    ----------
    img_data : ndarray
    params : list
        sigma : float
            Standard deviation for Gaussian kernel, acting on all axes.
        mode : str
            Determines how the input array is extended when the filter 
            overlaps a border.
    """
    sigma = float(params[0])
    mode = str(params[1])

    gs = gaussian_filter(
        img_data, 
        sigma, 
        mode=mode
        )

    return(gs)

def sharpen(img_data, params):
    """
    Return a sharpened version of the image, using an unsharp mask.

    Params
    ------
    img_data : ndarray
    params : list
        kern : tuple
        sigma : float
        amount : float
        threshold : float
    """
    kernel_size = params[0]
    sigma = float(params[1])
    amount = float(params[2])
    threshold = float(params[3])

    def unsharp_mask(image, kernel_size=(5, 5), sigma=1.0, amount=1.0, threshold=0):
        """Return a sharpened version of the image, using an unsharp mask."""
        # From https://codingdeekshi.com/python-3-opencv-script-to-smoothen-or-sharpen-input-image-using-numpy-library/
        blurred = cv2.GaussianBlur(image, kernel_size, sigma)
        sharpened = float(amount + 1) * image - float(amount) * blurred
        sharpened = np.maximum(sharpened, np.zeros(sharpened.shape))
        sharpened = np.minimum(sharpened, 255 * np.ones(sharpened.shape))
        sharpened = sharpened.round().astype(np.uint8)
        if threshold > 0:
            low_contrast_mask = np.absolute(image - blurred) < threshold
            np.copyto(sharpened, image, where=low_contrast_mask)
        return sharpened

    if np.average(img_data) < 20:
        img_data = img_data*325
    img_data = img_data.astype(np.uint8)
    sharp = unsharp_mask(img_data, kernel_size, sigma, amount, threshold)
    return(sharp)