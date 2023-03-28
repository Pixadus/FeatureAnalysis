#!/usr/bin/python3
# -*- coding: utf-8 -*-
"""
Created on Fri 10.28.22
@title: Timeseries functions
@author: Parker Lamb
@description: Functions to analyze the evolution
of features over time.
"""

from tracing.tracing import AutoTracingOCCULT

# Quality estimation

# Analysis. 
# 1. Run on first image; assign numbers to each identified fibril.
# -- Problem: OCCULT-2 image analysis is very slow. Running for 300+ images will take a long while. 
# 2. Move on to second image; 

def analyze_and_tempsave(image, image_index):
    """
    Run an image through OCCULT-2 and save results to a
    temporary directory. 

    Parameters
    ----------
    image : ndarray
    """
    # Set up an autotracing instance
    at = AutoTracingOCCULT(data=image)

    # Run it
    at.run()

    # Save the results to a temporary directory