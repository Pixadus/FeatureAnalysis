#!/usr/bin/python3
# -*- coding: utf-8 -*-
"""
Created on Fri 10.28.22
@title: Timeseries functions
@author: Parker Lamb
@description: Functions to analyze the evolution
of features over time.
"""

import csv
import os
from tracing.tracing import AutoTracingOCCULT
from analysis.analysis import Analysis
from collections import OrderedDict

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
    for frame_num in range(num_frames):
        print("Running OCCULT-2 for frame {}".format(frame_num))
        tracings = trace_image(full_image[frame_num,:,:])

        # Analyze each frame if true
        if analyze_frames:
            print("Running analysis for frame {}".format(frame_num))
            an = Analysis(full_image[frame_num,:,:], tracings)
            an.set_opts()
            # Run the analysis
            results = an.run()
            # Save the results
            if not os.path.exists("timeseries_results"):
                os.mkdir("timeseries_results")
            save_file("timeseries_results/{}.csv".format(frame_num), results, lb=True)
            # Calculate and print averages
            print("Features detected: {}".format(len(results)))
            f_avg = {}
            # Populate dictionary
            for key in ['length', 'breadth']:
                f_avg[key] = 0
            # Create a running tally of coordinates
            coord_count = 0
            for f_num in results.keys():
                for coord in results[f_num]:
                    coord_count += 1
                    for key in ['length','breadth']:
                        if coord[key]:
                            f_avg[key] += coord[key]
            # Average out the coordinates
            for key in f_avg.keys():
                f_avg[key] = f_avg[key]/coord_count
                print("Average {}".format(key), f_avg[key])
            
        else:
            # Save the results
            if not os.path.exists("timeseries_results"):
                os.mkdir("timeseries_results")
            save_file("timeseries_results/{}.csv".format(frame_num), tracings, lb=False)

def trace_image(image):
    """
    Run an image through OCCULT-2. 

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

    # Convert tracings to a dictionary
    f_num = 0
    f_data = OrderedDict()
    for feature in tracings:
        f_data[f_num] = []
        for coord in feature:
            c = {"coord" : (float(coord[0]), float(coord[1]))}
            f_data[f_num].append(c)
        f_num += 1

    # Return the tracings
    return(f_data)

def save_file(save_path, f_data, lb=True):
    """
    Save data to a file, including analyzed options if specified.
    """
    # Save format will be { feature_id, x, y, len, bre, [cust] }
    with open(save_path, 'w') as outfile:
        resultwriter = csv.writer(outfile)
        if lb:
            resultwriter.writerow(["f_num", 'x', 'y', 'length', 'breadth'])
            for f_num in f_data.keys():
                for coord in f_data[f_num]:
                    resultwriter.writerow([
                        f_num, 
                        coord['coord'][0], 
                        coord['coord'][1],
                        coord['length'],
                        coord['breadth']
                        ]
                    )
        else:
            resultwriter.writerow(["f_num", 'x', 'y'])
            for f_num in f_data.keys():
                for coord in f_data[f_num]:
                    resultwriter.writerow([
                        f_num, 
                        coord['coord'][0], 
                        coord['coord'][1]
                        ]
                    )
