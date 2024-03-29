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
np.set_printoptions(suppress=True)
import cv2
import scipy

class Analysis:
    def __init__(self, img_data, feature_data, axes=None):
        """
        Looks at characteristics of features. 

        Parameters
        ----------
        img_data : ndarray
            Data of the original image used for tracing
        feature_data : OrderedDict
            Format {f_num : [{'coord' : (x,y)}, {'coord' : (x,y)}, ... ]}
        axes : pyplot.axes (optional)
            Axes used to plot feature calculations on
        """
        super().__init__()

        # Set variables
        self.f_data = feature_data
        self.img_data = img_data
        if len(img_data.shape) == 3:
            self.img_data = img_data[0,:,:]
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
        self.get_breadth_nearest()
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

    def get_breadth_nearest(self):
        """
        Get the feature breadth on a per-coordinate basis, using the 
        nearest identified fibril edges above and below the centerline. 
        """
        # Convert to a format that CV2 can easily recognize
        img_data = self.img_data
        if np.mean(img_data) < 2:
            img_data = np.round(img_data*180)
        img_data = img_data.astype(np.uint8)
        
        # Create a sharpened image, then blur it a bit to get rid of noise
        id_sharp = processing.unsharp_mask(img_data)
        id_sharp_gauss = cv2.GaussianBlur(id_sharp, (5,5), 8.0)

        # Get edges in the image
        edges = cv2.Canny(id_sharp_gauss, threshold1=100, threshold2=150, apertureSize=7)

        # Get contours on the image
        contours, hierarchy = cv2.findContours(edges, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)

        # Filter out all contours with a length less than 1
        ctr_filtered = []
        for ctr in contours:
            if cv2.arcLength(ctr, False) > 1:
                ctr_filtered.append(ctr)
        
        # Reset the contour map and draw contours on it
        self.ctr_map = np.zeros_like(edges)
        cv2.drawContours(
            self.ctr_map, 
            tuple(ctr_filtered), 
            -1, 
            (255,255,255), 
            1
        )
        edges = self.ctr_map

        # Get a list of indices where edges are nonzero
        nze = np.transpose(edges.nonzero()).astype(np.double)

        # Swap columns to make x,y
        nze[:,[0,1]] = nze[:,[1,0]]

        # Combine the image and the edges and display it
        if self.ax is not None:
            imgcmp = cv2.addWeighted(img_data,1, edges,0.8,0)
            self.ax.imshow(imgcmp, origin="lower")

        # Iterate over all features
        for feature_num in self.f_data.keys():

            # Get a list of all coordinates per feature
            coords = [c['coord'] for c in self.f_data[feature_num]]

            # Plot counter
            pctr = 0

            # dict_coord is the coordinate entry so we can reverse-index it; 
            # coord is the actual coordinate
            for dict_coord, coord in zip(self.f_data[feature_num], coords):
                dict_coord['breadth'] = 0
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
                dy = nextcoord[1]-prevcoord[1]
                dx = nextcoord[0]-prevcoord[0]

                # Find nearest edges to coordinate
                nearest = self.find_nearest_edges(coord, nze)
                
                # Calculate angle of the slope from horizontal
                try:
                    slope_angle = np.arctan(dy/dx)
                except:
                    continue

                # Calculate edge angles relative to perpendicular axis of slope at coordinate
                angles = self.calculate_edge_angles(nearest, slope_angle, coord)

                # Filter arrays for values close to zero and those close to pi
                zero_set = angles[
                    (np.cos(angles[:,3]) >= 0)
                ]
                pi_set = angles[
                    (np.cos(angles[:,3]) < 0)
                ]
                # print("Angles", angles[:,3], "Cosines", np.cos(angles[:,3]))
                
                # Get the closest feature for zero and pi
                try:
                    zero_closest = zero_set[zero_set[:,0].argmin()]
                    pi_closest = pi_set[pi_set[:,0].argmin()]
                except Exception as e:
                    continue

                # List of colors to use
                colors = ["red","blue","green","orange","purple","black","pink","cyan"]
                color = colors[np.random.randint(0,len(colors))]

                # Plot every third coord to reduce plot load
                if pctr % 3 == 0 and self.ax is not None:
                    self.ax.scatter(zero_set[:,1],zero_set[:,2],color="cyan", s=2)
                    self.ax.scatter(pi_set[:,1],pi_set[:,2],color="pink",s=2)

                    self.ax.scatter(
                        [zero_closest[1],coord[0],pi_closest[1]],
                        [zero_closest[2],coord[1],pi_closest[2]],
                        color=color, 
                        alpha=1,
                        s=1)
                    self.ax.plot(
                        [zero_closest[1],coord[0],pi_closest[1]],
                        [zero_closest[2],coord[1],pi_closest[2]],
                        color=color, 
                        alpha=1,
                        markersize=1)
                pctr += 1

                dict_coord['breadth'] =  np.linalg.norm(
                        (np.array([zero_closest[1],zero_closest[2]])-np.array([[pi_closest[1],pi_closest[2]]]))
                    )    
    def calculate_edge_angles(self, nearest, slope_angle, coord):
        """
        Calculates the angles to the nearest edges relative to the offset axis
        """
        angles = []
        for edge in nearest:
            edge_x = edge[1]
            edge_y = edge[2]
            dxp = edge_x - coord[0]
            dyp = edge_y - coord[1]
            theta = np.pi/2 - (np.arctan(dyp/dxp) - slope_angle)
            if dxp < 0:
                theta += np.pi
            angles.append(theta)
        nearest = np.insert(nearest, 3, np.array(angles).transpose(), axis=1)
        return(nearest)

    def find_nearest_edges(self, coord, nze):
        """
        Returns the 100 nearest edges to the coordinate.

        Parameters
        ----------
        coord : tuple
            Format {x,y}
        nze : tuple
            Set x,y of array indices where edges are nonzero

        Returns
        -------
        nearest_edges : ndarray
            List of length 100, setup np.array([distance, edge_x, edge_y], [d,x,y], ...)
        """
        # Create a "subsection" of the edge map around the coordinate
        shape = self.img_data.shape # (m, n) == (y, x)
        xbound = [np.floor(coord[0]-shape[1]/10).astype(np.int64), np.floor(coord[0]+shape[1]/10).astype(np.int64)]
        ybound = [np.floor(coord[1]-shape[0]/10).astype(np.int64), np.floor(coord[1]+shape[0]/10).astype(np.int64)]
        if (xbound[0] < 0):
            xbound[0] = 0
        if (xbound[1] > shape[0]):
            xbound[1] = shape[0]
        if (ybound[0] < 0):
            ybound[0] = 0
        if (ybound[1] > shape[0]):
            ybound[1] = shape[0]
            
        # Select all rows where index between bounds
        nze = nze[
            (nze[:,0] > xbound[0]) & 
            (nze[:,0] < xbound[1]) & 
            (nze[:,1] > ybound[0]) &
            (nze[:,1] < ybound[1])
        ]
        dist = scipy.spatial.distance.cdist(
            nze,
            np.array([coord])
        )
        # Insert the distances array to match the associated edge coordinate
        distances = np.insert(nze, 0, dist.transpose(), axis=1)
        # Filter out all distances greater than 20 to reduce array size (for large numbers of coordinates)
        distances = distances[distances[:,0] < 20]
        # Sort by distance
        distances = distances[distances[:,0].argsort()]
        # Return the 100 closest edges
        return(distances[:100])

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
