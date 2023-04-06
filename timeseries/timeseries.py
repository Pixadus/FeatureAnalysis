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
import re
import glob
import cv2
import os
import numpy as np
from tracing.tracing import AutoTracingOCCULT
from analysis.analysis import Analysis

# Quality estimation

# Analysis. 
# 1. Run on first image; assign numbers to each identified fibril.
# -- Problem: OCCULT-2 image analysis is very slow. Running for 300+ images will take a long while. 
# 2. Move on to second image; 

class Timeseries():
    def __init__(self, full_image):
        """
        Timeseries class, with relevant functions. 

        Parameters
        ----------
        full_image : ndarray
            Full timeseries image.
        """
        # Variable setting
        self.full_image = full_image
        self.analyze_frames = False
        self.save_frames = True
        self.start = 0
        self.end = full_image.shape[0]
        self.sequence_tracings = []
        self.save_dir = "timeseries_results"

    def trace_images(self):
        """
        Run the supplied timeseries image frames through OCCULT-2.
        """
        print("------- Starting OCCULT-2 tracing -------")
        for frame_num in range(self.start, self.end+1):
            print("Tracing frame {}".format(frame_num))

            # Set up an autotracing instance
            at = AutoTracingOCCULT(data=self.full_image[frame_num,:,:])

            # Run it
            tracings = at.run()

            # Convert tracings to a dictionary
            f_num = 0
            f_data = {}
            for feature in tracings:
                f_data[f_num] = []
                for coord in feature:
                    c = {"coord" : (float(coord[0]), float(coord[1]))}
                    f_data[f_num].append(c)
                f_num += 1

            # Append tracing data to the sequence tracing list
            self.sequence_tracings.append(f_data)
    
    def run_analysis(self):
        """
        Run analysis on each OCCULT-2 tracing in sequence_tracings.
        """
        print("------- Analyzing tracings -------")
        # Iterate over all OCCULT-2 tracings, and run analysis on them
        for tracing in self.sequence_tracings:
            tracing_index = self.sequence_tracings.index(tracing)
            print("Analyzing frame {}".format(tracing_index))
            an = Analysis(self.full_image[tracing_index,:,:], tracing)
            an.set_opts()
            result = an.run()
            # Replace the tracing in sequence_tracing with the analyzed version
            self.sequence_tracings[tracing_index] = result
            print(result)
        
    def get_matching_features(self):
        """
        Match features on frame 2 to frame 1, then match features on frame 3 to frame 2. 
        """
        # Iterate over tracings
        for tracing in self.sequence_tracings:
            current_index = self.sequence_tracings.index(tracing)
            # Skip the initial tracing
            if current_index == 0:
                continue
            # Get all coordinates in the previous frame
            if_coords = []
            for feature_id in self.sequence_tracings[current_index-1]:
                coords = self.sequence_tracings[current_index-1][feature_id]
                for coord in coords:
                    if current_index-1 != 0:
                        if coord['match_id'] is not None:
                            if_coords.append({
                                'feature_id':feature_id, 
                                'x': coord['coord'][0],
                                'y': coord['coord'][1]
                            })
                    else:
                        if_coords.append({
                                'feature_id':feature_id, 
                                'x': coord['coord'][0],
                                'y': coord['coord'][1]
                            })
            for feature_id in self.sequence_tracings[current_index]:
                for coord in 

            # In current frame, iterate over all features
                # iterate over all coordinates in feature
                    # calculate the distances to frame n-1 coordinates. 
                    # get the coordinate with the smallest distance
                    # set frame['match_id'] to the n-1 id
                    # set frame['match_x'] and y to the n-1 coordinate
                    # set frame['match_dist'] to the distance

        
    def save_files(self):
        """
        Save tracing data to the disk inside self.save_folder. 
        """
        if not os.path.exists(self.save_dir):
            print("Creating directory {}".format(self.save_dir))
            os.mkdir(self.save_dir)
        
        print("Saving results ...")
        for result in self.sequence_tracings:
            save_path = "{}.csv".format(self.sequence_tracings.index(result))
            with open(save_path, 'w') as outfile:
                resultwriter = csv.writer(outfile)
                if self.analyze_frames:
                    resultwriter.writerow(["f_num", 'x', 'y', 'length', 'breadth'])
                    for f_num in result.keys():
                        for coord in result[f_num]:
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
                    for f_num in result.keys():
                        for coord in result[f_num]:
                            resultwriter.writerow([
                                f_num, 
                                coord['coord'][0], 
                                coord['coord'][1]
                                ]
                            )