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
import numpy as np
import scipy
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
        print("------- Matching frames -------")
        # Iterate over tracings
        for tracing in self.sequence_tracings:
            current_index = self.sequence_tracings.index(tracing)
            # Skip the initial tracing
            if current_index == 0:
                continue
            print("Matching frame {} to frame {}".format(current_index, current_index-1))
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
            ix = [c['x'] for c in if_coords]
            iy = [c['y'] for c in if_coords]
            icoords = np.transpose(np.array([ix,iy]))
            # In the current frame, iterate over all features
            for feature_id in self.sequence_tracings[current_index]:
                # iterate over all coordinates in feature 
                for coord in self.sequence_tracings[current_index][feature_id]:
                    coord['match_id'] = None
                    c = (coord['coord'][0], coord['coord'][1])
                    dist = scipy.spatial.distance.cdist(
                                icoords,
                                np.array([c])
                            )
                    indexes = [ind for ind, item in enumerate(dist)]
                    distind = np.insert(dist, 1, indexes, axis=1)
                    # Only consider the distances that are less than 20 pixels away
                    distind = distind[distind[:,0] < 20]
                    try:
                        min_dist = distind[np.argmin(distind[:,0])]
                    except ValueError:
                        continue
                    # get the index data corresponding to the min_dist
                    try:
                        min_if_coord = if_coords[int(min_dist[1])]
                    except:
                        continue
                        print("Error", min_dist[1], len(if_coords))
                    # set the coord match to the initial frame match
                    coord['match_id'] = min_if_coord['feature_id']
                    coord['match_coord'] = (min_if_coord['x'], min_if_coord['y'])
                    # remove the index from icoords to mark it as "taken"
                    if_coords.pop(int(min_dist[1]))
                    icoords = np.delete(icoords, (int(min_dist[1])), axis=0)
        
        # Write the initial frame and current frame coordinates to a file
        print("Writing tracings 0")
        with open("timeseries_results/0-tracings.csv", 'w') as csvfile:
            csvwriter = csv.writer(csvfile)
            for feature_id in self.sequence_tracings[0]:
                for coord in self.sequence_tracings[0][feature_id]:
                    csvwriter.writerow([
                        feature_id,
                        coord['coord'][0],
                        coord['coord'][1]
                    ])
        print("Writing tracings 1")
        with open("timeseries_results/1-tracings.csv", 'w') as csvfile:
            csvwriter = csv.writer(csvfile)
            for feature_id in self.sequence_tracings[1]:
                for coord in self.sequence_tracings[1][feature_id]:
                    csvwriter.writerow([
                        feature_id,
                        coord['coord'][0],
                        coord['coord'][1]
                    ])
        print("Writing matches 1")
        with open("timeseries_results/1-matches.csv", 'w') as csvfile:
            csvwriter = csv.writer(csvfile)
            for feature_id in self.sequence_tracings[1]:
                for coord in self.sequence_tracings[1][feature_id]:
                    if coord['match_id'] is not None:
                        csvwriter.writerow([
                            feature_id,
                            coord['coord'][0],
                            coord['coord'][1],
                            coord['match_id'],
                            coord['match_coord'][0],
                            coord['match_coord'][1]
                        ])
                    else:
                        csvwriter.writerow([
                            feature_id,
                            coord['coord'][0],
                            coord['coord'][1],
                            coord['match_id'],
                            None,
                            None
                        ])

        
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