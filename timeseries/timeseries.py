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
        self.trace_full = False
        self.trace_matches = True
        self.start = 0
        self.end = full_image.shape[0]
        self.sequence_tracings = []
        self.match_tracings = []
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
        
    def get_matching_features(self):
        """
        Match features on frame 2 to frame 1, then features on frame 3 to frame 2, and so on.
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
                    # calculate distance to all prevframe coords
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
        
        # Convert each frame data to a dict
        new_sequence_tracings = []
        for tracing in self.sequence_tracings:
            f_dict = {}
            current_frame = self.sequence_tracings.index(tracing)
            if current_frame == 0:
                for feature_id in self.sequence_tracings[current_frame]:
                    f_dict[feature_id] = {
                            "coords" : self.sequence_tracings[current_frame][feature_id],
                    }
                new_sequence_tracings.append(f_dict)
                continue
            for feature_id in self.sequence_tracings[current_frame]:
                f_dict[feature_id] = {
                        "coords" : self.sequence_tracings[current_frame][feature_id],
                        "matching_feature" : None
                    }
                # Create a list of match ids, and get the most common ID
                match_ids = [coord["match_id"] for coord in f_dict[feature_id]["coords"]]
                f_dict[feature_id]["matching_feature"] = max(set(match_ids), key=match_ids.count)
            new_sequence_tracings.append(f_dict)
        # Update global format - now, looks like list(dictframe0(dictfeat1, dictfeat2))
        self.sequence_tracings = new_sequence_tracings

    def follow_feature_matches(self):
        """
        Starting from frame 0, follow each feature down the frames
        until either a None value is hit or the end of the frames. 
        """
        # Create a list to contain successful match traces
        match_traces = []

        # Iterate over all frame 0 features
        for feature_id in self.sequence_tracings[0]:
            # Create a per-feature list of successful matches
            feature_matches = []
            
            # Create a variable to store the n-1 match_id, initially holding the f0 feature_id
            previous_match_id = feature_id

            # Follow feature_id through all frame matching values. +1 to skip f0, incl.
            for frame in range(self.start+1, self.end+1):
                found_match = False
                for frame_feature_id in self.sequence_tracings[frame]:
                    # Get the matching_feature ID from the frame's feature
                    current_match_id = self.sequence_tracings[frame][frame_feature_id]["matching_feature"]
                    # If the matching_feature ID matches our feature ID, add coords to the list and move on
                    if current_match_id == previous_match_id:
                        found_match = True
                        feature_matches.append(
                            self.sequence_tracings[frame][frame_feature_id]["coords"]
                        )
                        # Update the previous_match_id for the current frame
                        previous_match_id = frame_feature_id
                        # Break out of frame_feature_id iteration
                        break
                # If we haven't found a match by the end of the frame's features, reset, break and move on
                if found_match == False:
                    feature_matches = []
                    break
                
            # If the feature_matches list is empty, don't append and move on. Otherwise, append.
            if len(feature_matches) == 0:
                 continue
            else:
                feature_dict = {
                    'id': feature_id,
                    'match_coords': feature_matches
                    }
                match_traces.append(feature_dict)

            self.match_tracings = match_traces
    
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