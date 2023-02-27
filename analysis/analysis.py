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
import scipy

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
        canvas : pyplot.canvas
            Canvas element used to refresh and redraw on
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
        # profiler = cProfile.Profile()
        # profiler.enable()
        self.get_breadth_nearest()
        # profiler.disable()
        # profiler.print_stats(sort='time')

        self.get_breadth_perpendicular()


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
        Get the feature breadth on a per-coordinate basis, using the nearest identified fibril edges above and below
        the centerline. 
        """
        # Convert to a format that CV2 can easily recognize
        img_data = self.img_data
        img_data = img_data.astype(np.uint8)
        
        # Create a sharpened image, then blur it a bit to get rid of noise
        id_sharp = processing.unsharp_mask(img_data)
        id_sharp_gauss = cv2.GaussianBlur(id_sharp, (5,5), 8.0)

        # Get edges in the image
        edges = cv2.Canny(id_sharp_gauss, threshold1=100, threshold2=200, apertureSize=7)

        # Combine the image and the edges and display it
        comboimg = cv2.addWeighted(img_data, 1, edges, 0.5, 0)
        self.ax.imshow(comboimg, origin="lower")

        total_avg_width = []
        # Iterate over all features
        for feature_num in self.f_data.keys():
            feature_widths = []
            # Get a list of all coordinates per feature
            coords = [c['coord'] for c in self.f_data[feature_num]]
            # dict_coord is the coordinate entry so we can reverse-index it; 
            # coord is the actual coordinate
            for dict_coord, coord in zip(self.f_data[feature_num], coords):
                # Each coordinate is going to be at least 1 pixel in width (the centerline)
                coord_width = 1
                # Get next and previous coordinates
                nextcoord = next((i for i, val in enumerate(coords) if np.all(val == coord)), -1)+1
                prevcoord = next((i for i, val in enumerate(coords) if np.all(val == coord)), -1)-1
                if nextcoord > len(coords)-1:
                    nextcoord = len(coords)-1
                if prevcoord < 0:
                    prevcoord = 0
                nextcoord = coords[nextcoord]
                prevcoord = coords[prevcoord]
                # Calculate the slope at the coordinate, so we can find "above" and "below" or "left" and "right"
                dx = nextcoord[1]-prevcoord[1]
                dy = nextcoord[0]-prevcoord[0]
                # Convert both dx and dy to unit vectors
                dx = np.around(dx/np.linalg.norm(np.array([dx,dy])))
                dy = np.around(dy/np.linalg.norm(np.array([dx,dy])))
                nearest = self.find_nearest_edges(coord, edges)
                try:
                    # If we have a nonzero change in x, we'll have an "above" and "below" coordinate. 
                    if abs(dx) > 0:
                        # Arbitrarily pick the nearest edge as the "closest"
                        edge_one = nearest[0]
                        # If edge one is above the coordinate, look for edge_two below the coordinate
                        if edge_one[2] > coord[1]:
                            try:
                                edge_two = [e for e in nearest if e[2] < coord[1]][0]
                            except:
                                edge_two = nearest[1]
                        # If edge one is below the coordinate, look for edge_two above the coordinate
                        elif edge_one[2] < coord[1]:
                            try:
                                edge_two = [e for e in nearest if e[2] > coord[1]][0]
                            except:
                                edge_two = nearest[1]
                        # If edge_one[2] == coord[1], then select edge two as the second closest edge
                        else:
                            edge_two = nearest[1]
                    # Otherwise, if we have a nonzero change in y, we'll have a "left" and "right" coordinate.
                    elif abs(dy) > 0:
                        # Arbitrarily pick the nearest edge as the closest
                        edge_one = nearest[0]
                        # If edge_one is right of the coordinate, look for edge_two left of the coordinate
                        if edge_one[1] > coord[0]:
                            # Try to get the first edge otherwise. If this fails, no edge, assign to coord. 
                            try:
                                edge_two = [e for e in nearest if e[1] < coord[0]][0]
                            except IndexError:
                                edge_two = nearest[1]
                        # If edge_one left of the coordinate, look for edge_two right of the coordinate
                        elif edge_one[1] < coord[0]:
                            try:
                                edge_two = [e for e in nearest if e[1] > coord[0]][0]
                            except IndexError:
                                edge_two = nearest[1]
                        # If edge_one[1] == coord[0], select second-nearest edge as edge two
                        else:
                            edge_two = nearest[1]
                    # Otherwise, if dy and dx are both zero, skip this particular coordinate
                    else:
                        continue
                except IndexError:
                    continue

                coord_e1 = np.array([edge_one[1], edge_one[2]])
                coord_e2 = np.array([edge_two[1], edge_two[2]])
                
                self.ax.plot([coord_e1[0],coord_e2[0]], [coord_e1[1],coord_e2[1]], markersize=1,linewidth=1, color='red', alpha=0.7)
                feature_widths.append(np.linalg.norm(coord_e2-coord_e1))

            total_avg_width.append(np.mean(feature_widths))
        print(np.mean(feature_widths))

    def find_nearest_edges(self, coord, edges):
        """
        Returns a list of the 10 nearest edges to the coordinate.

        Parameters
        ----------
        coord : tuple
            Format {x,y}
        edges : list
            Map of Canny-identified edges. 1 if edge, 0 otherwise.

        Returns
        -------
        nearest_edges : list
            List of length 10, setup [(distance, (x,y)), (...)]
        """
        # Create a "subsection" of the edge map around the coordinate
        shape = self.img_data.shape # (m, n) == (y, x)
        xbound = [np.floor(coord[0]-shape[1]/8).astype(np.int64), np.floor(coord[0]+shape[1]/8).astype(np.int64)]
        ybound = [np.floor(coord[1]-shape[0]/8).astype(np.int64), np.floor(coord[1]+shape[0]/8).astype(np.int64)]
        if (xbound[0] < 0):
            xbound[0] = 0
        if (xbound[1] > shape[0]):
            xbound[1] = shape[0]
        if (ybound[0] < 0):
            ybound[0] = 0
        if (ybound[1] > shape[0]):
            ybound[1] = shape[0]
        
        # Compare distances
        nze = np.transpose(edges.nonzero())
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
        # Return the 10 closest edges
        return(distances[:10])

    def get_breadth_perpendicular(self):
        """
        Get the feature breadth on a per-coordinate basis, using a vector perpendicular to the local derivative. 
        """
        # Convert to a format that CV2 can easily recognize
        img_data = self.img_data*325
        img_data = img_data.astype(np.uint8)
        
        # Create a sharpened image, then blur it a bit to get rid of noise
        id_sharp = processing.unsharp_mask(img_data, kernel_size=(5, 5), sigma=1.0, amount=1.0, threshold=0)
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
                if np.isnan(dp[0]) or np.isnan(dp[1]):
                    dict_coord['breadth'] = 0.0
                    continue
                # Convert to unit vector
                mag = np.sqrt(dp[0]**2+dp[1]**2)
                if mag == 0:
                    dict_coord['breadth'] = 0.0
                    continue
                dp[0] = dp[0]/mag
                dp[1] = dp[1]/mag
                # Array indices must be integers, rounding
                dp[0] = round(dp[0])
                dp[1] = round(dp[1])
                # Variables to store x and y displacement vectors for width visualization
                xs = []
                ys = []
                # Move in positive dp until we hit a Canny-identified edge
                bp = 0
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
                # if wctr % 5 ==0:
                    # self.ax.plot(ys,xs,markersize=1,linewidth=1, color='#a09516', alpha=0.7)
                # Add width to coord characteristics
                dict_coord['breadth'] = bp+bn
            # Filter through the coordinates and reject breadth outliers
            widths_filtered = np.array([dict_coord['breadth'] for dict_coord in self.f_data[feature_num]])
            # Using an m value of 3.5 to filter out outliers
            # from https://www.itl.nist.gov/div898/handbook/eda/section3/eda35h.htm
            # and https://stackoverflow.com/questions/11686720/is-there-a-numpy-builtin-to-reject-outliers-from-a-list
            d = np.abs(widths_filtered - np.median(widths_filtered))
            mdev = np.median(d)
            s = d/mdev if mdev else 0.
            widths_filtered = widths_filtered[s<3.5]
            for dict_coord in self.f_data[feature_num]:
                dict_coord = {key:val for key, val in dict_coord.items() if val in widths_filtered}

    def get_breadth_triangle(self):
        """
        Get the feature breadth on a per-coordinate basis, using Zhang's triangle method (DOI 10.1109/TIP.2006.887731)
        """
        # Convert to a format that CV2 can easily recognize
        img_data = self.img_data*325
        img_data = img_data.astype(np.uint8)
        
        # Create a sharpened image, then blur it a bit to get rid of noise
        id_sharp = processing.unsharp_mask(img_data, kernel_size=(5, 5), sigma=1.0, amount=1.0, threshold=0)
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
                # Increment the width counter to account for the centerline pixel
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
                if np.isnan(dp[0]) or np.isnan(dp[1]):
                    dict_coord['breadth'] = 0.0
                    continue
                # Convert to unit vector
                mag = np.sqrt(dp[0]**2+dp[1]**2)
                if mag == 0:
                    dict_coord['breadth'] = 0.0
                    continue
                dp[0] = dp[0]/mag
                dp[1] = dp[1]/mag
                # Array indices must be integers, rounding
                dp[0] = round(dp[0])
                dp[1] = round(dp[1])
                # Variables to store x and y displacement vectors for width visualization
                xs = []
                ys = []
                # Move in positive dp until we hit a Canny-identified edge
                bp = 0
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
                if wctr % 5 ==0:
                    self.ax.plot(ys,xs,markersize=1,linewidth=1, color='#a09516', alpha=0.7)
                # Add width to coord characteristics
                dict_coord['breadth'] = bp+bn
            # Filter through the coordinates and reject breadth outliers
            widths_filtered = np.array([dict_coord['breadth'] for dict_coord in self.f_data[feature_num]])
            # Using an m value of 3.5 to filter out outliers
            # from https://www.itl.nist.gov/div898/handbook/eda/section3/eda35h.htm
            # and https://stackoverflow.com/questions/11686720/is-there-a-numpy-builtin-to-reject-outliers-from-a-list
            d = np.abs(widths_filtered - np.median(widths_filtered))
            mdev = np.median(d)
            s = d/mdev if mdev else 0.
            widths_filtered = widths_filtered[s<3.5]
            for dict_coord in self.f_data[feature_num]:
                dict_coord = {key:val for key, val in dict_coord.items() if val in widths_filtered}

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
