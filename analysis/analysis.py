#!/usr/bin/python3
# -*- coding: utf-8 -*-
"""
Created on Tue 7.5.22
@title: Analysis
@author: Parker Lamb
@description: Script used to characterize OCCULT-2 identified features, including
both breadth and length, as well as optionally supplied features.
"""

from preprocessing import processing
import numpy as np
import cv2

class Analysis:
    def __init__(self, img_data, feature_data, axes):
        """
        Looks at characteristics of features. 

        Parameters
        ----------
        img_data : ndarray
            Data of the original image used for tracing
        feature_data : OrderedDict
            Format {f_num : [{'coord' : (x,y)}, {'coord' : (x,y)}, ... ]}
        axes : pyplot.axes
            Axes used to plot feature calculations on
        """
        super().__init__()

        # Set variables
        self.f_data = feature_data
        self.img_data = img_data
        self.ax = axes

    def run(self):
        """
        Run the analysis.

        Returns
        -------
        f_data : dict
            Format {f_num : [
                {'coord':(x,y), 'length':l, 'breadth':b ...},
                {'coord':(x,y), 'length':l, 'breadth':b ...}
                ...
                ]}
        """
        # Take a look at all the custom options
        self.analyze_cust()

        # Get the length + breadth of the features
        self.get_breadth()
        self.get_length()

        # Return the feature dictionary
        return(self.f_data)
    
    def set_opts(self, opt_breadth=True, opt_length=True, opt_cust={}):
        """
        Set options for the analysis. External/internal.

        Parameters
        ----------
        opt_breadth : bool
            Enable per-coordinate breadth calculations.
        opt_length : bool
            Enable per-feature length calculations.
        opt_cust : dict
            Custom features, such as velocity, intensity, etc. of
            format {param : image_path}. Image dimensions must match
            those of the base image used for tracing.
        """
        self.opt_breadth = opt_breadth
        self.opt_length = opt_length
        self.opt_cust = opt_cust

    def analyze_cust(self):
        """
        Analyze custom options.
        """
        for feature_num in self.f_data.keys():
            for coord in self.f_data[feature_num]:
                x = int(round(coord["coord"][0]))
                y = int(round(coord["coord"][1]))
                # Get values from custom options
                for opt in self.opt_cust.keys():
                    coord[opt] = self.opt_cust[opt][y,x]
                # Remove any keys not in x,y or opt_cust
                bad_keys = []
                for key in coord.keys():
                    if key not in ["coord"]+[k for k in self.opt_cust.keys()]:
                        bad_keys.append(key)
                for key in bad_keys:
                    coord.pop(key)

    def get_breadth(self):
        """
        Get the feature breadth on a per-coordinate basis.
        """
        # Convert to a format that CV2 can easily recognize
        img_data = self.img_data*325
        img_data = img_data.astype(np.uint8)
        
        # Create a sharpened image, then blur it a bit to get rid of noise
        id_sharp = processing.unsharp_mask(img_data, amount=10.0)
        id_sharp_gauss = cv2.GaussianBlur(id_sharp, (5,5), 8.0)

        # Get edges in the image
        edges = cv2.Canny(id_sharp_gauss, threshold1=260, threshold2=280, apertureSize=7)

        # Iterate over all features
        for feature_num in self.f_data.keys():
            # Counter to represent density of width segments
            wctr = 0
            # Get a list of all coordinates in feature
            coords = [c['coord'] for c in self.f_data[feature_num]]
            for dict_coord, coord in zip(self.f_data[feature_num], coords):
                # Increment the width counter
                wctr +=1
                # Get next and previous coordinates
                nextcoord = next((i for i, val in enumerate(coords) if np.all(val == coord)), -1)+1
                prevcoord = next((i for i, val in enumerate(coords) if np.all(val == coord)), -1)-1
                if nextcoord > len(coords)-1:
                    nextcoord = len(coords)-1
                if prevcoord < 0:
                    prevcoord = 0
                nextcoord = coords[nextcoord]
                prevcoord = coords[prevcoord]
                # Calculate the slope at the coordinate
                dx = nextcoord[1]-prevcoord[1]
                dy = nextcoord[0]-prevcoord[0]
                v = np.array([dx,dy])
                # Get perpendicular vector
                dp = np.empty_like(v)
                dp[0] = -v[1]
                dp[1] = v[0]
                # Convert to unit vector
                mag = np.sqrt(dp[0]**2+dp[1]**2)
                dp[0] = dp[0]/mag
                dp[1] = dp[1]/mag
                # Array indices must be integers, rounding
                dp[0] = round(dp[0])
                dp[1] = round(dp[1])
                # Variables to store x and y displacement vectors for width visualization
                xs = []
                ys = []
                # Move in positive dp until we hit a Canny-identified edge
                bp= 0
                coord_offset = np.array([round(coord[1]),round(coord[0])])
                try:
                    while edges[coord_offset[0],coord_offset[1]] == 0:
                        bp+=1
                        xs.append(coord_offset[0])
                        ys.append(coord_offset[1])
                        coord_offset[0] = coord_offset[0]+dp[0]
                        coord_offset[1] = coord_offset[1]+dp[1]
                    # Move in negative dp until we hit a Canny-identified edge
                    bn = 0
                    coord_offset = np.array([round(coord[1]),round(coord[0])])
                    while edges[coord_offset[0],coord_offset[1]] == 0:
                        bn+=1
                        xs.append(coord_offset[0])
                        ys.append(coord_offset[1])
                        coord_offset[0] = coord_offset[0]-dp[0]
                        coord_offset[1] = coord_offset[1]-dp[1]
                except IndexError:
                    pass
                if (wctr % 5) == 0:
                    self.ax.plot(ys,xs,markersize=1,linewidth=1, color='#a09516', alpha=0.7)
                # Add width to coord characteristics
                coord = np.append(coord,np.array([bp+bn]))
                dict_coord['breadth'] = bp+bn
                # TODO compare with previous coordinate width. If significantly larger, (i.e. 4 -> 12), set to previous
                # coordinate width, as it's implied there is a error width here. 
    
    def get_length(self):
        """
        Calculate the length of all individual
        features.
        """
        # Iterate over all features
        for f_num in self.f_data.keys():
            prevcoord = None
            length = 0
            # Iterate over all coordinate dictionaries in the feature
            for coord_dict in self.f_data[f_num]:
                # Retrieve coordinate from the c. dict
                coord = coord_dict['coord']
                # If it's the first coord, don't calculate anything
                if self.f_data[f_num].index(coord_dict) == 0:
                    prevcoord = coord
                else:
                    # Calculate distance between coords
                    diff = tuple(map(lambda i, j: i - j, coord, prevcoord))
                    length += np.linalg.norm(np.abs(diff))
                    prevcoord = coord
                # Add the current length to the coord_dict
                coord_dict['length'] = length