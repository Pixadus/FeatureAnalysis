#!/usr/bin/python3
# -*- coding: utf-8 -*-
"""
Created on Fri 10.28.22
@title: Timeseries functions
@author: Parker Lamb
@description: Functions to analyze the evolution
of features over time.
"""

import tempfile
from tracing.tracing import AutoTracingOCCULT

# Quality estimation

# Analysis. 
# 1. Run on first image; assign numbers to each identified fibril.
# -- Problem: OCCULT-2 image analysis is very slow. Running for 300+ images will take a long while. 
# 2. Move on to second image; 

def run_analysis(full_image, analyze_frames):
    """
    Run the analysis on the supplied timeseries. 

    Parameters
    ----------
    full_image : ndarray (3D)
        Full timeseries image (equivalently the .fits data)
    analyze_frames : bool
        Run length/width/breadth analysis on each frame
    """
    # Get the total frame count
    num_frames = full_image.shape[0]

    # Run through every file in the timeseries and run OCCULT-2 on it. 
    for frame_num in num_frames:
        tracing_file = analyze_and_tempsave(full_image[frame_num,:,:])

def analyze_and_tempsave(image):
    """
    Run an image through OCCULT-2 and save results to a
    temporary directory. 

    Parameters
    ----------
    image : ndarray

    Returns
    -------
    fp : file
    """
    # Set up an autotracing instance
    at = AutoTracingOCCULT(data=image)

    # Run it
    tracings = at.run()

    # Save the results to a temporary directory
    fp = tempfile.NamedTemporaryFile()
    at.save(tracings, fp.name, fp)

    # Return the file
    return(fp)