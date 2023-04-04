#!/usr/bin/python3
# -*- coding: utf-8 -*-
"""
Created on Fri 8.12.22
@title: Optimization functions
@author: Parker Lamb
@description: Functions to compare manual
and automatic tracing sets to identify an
"optimum" parameter set. 
"""

from scipy.interpolate import interp1d
from matplotlib import pyplot as plt
import csv
import numpy as np

def get_tracing_data(tracing_list):
    """
    Open a list of tracing files, and return
    their contents in a dictionary. 

    Parameters
    ----------
    tracing_list : list
        List of paths to each .csv file.
    
    Returns
    -------
    contents : dict
        Format of {file_path : [{
            ['x'], 
            ['y'], 
            ['avgx'], 
            ['avgy'], 
            ['matched']
            }]
    """
    contents = {}
    for path in tracing_list:
        with open(path, newline='') as csvfile:
            reader = csv.reader(csvfile)
            f_num = None
            features = []
            feature = {
                'x' : [],
                'y' : []
            }
            for row in reader:
                # If we're on the same feature, continue adding to it
                if f_num == int(float(row[0])):
                    feature['x'].append(float(row[1]))
                    feature['y'].append(float(row[2]))
                # Otherwise, create a new feature
                else:
                    if len(feature['x']) != 0 and len(feature['y']) != 0:
                        features.append(feature)
                    feature = {
                        'x' : [float(row[1])],
                        'y' : [float(row[2])]
                    }
                    f_num = int(float(row[0]))
            # Calculate coordinate averages
            for feature in features:
                feature['avgx'] = np.mean(feature['x'])
                feature['avgy'] = np.mean(feature['y'])
                feature['matched'] = False
            contents[path] = features
    return(contents)

def get_matches_avg_center(manFile, autoFile, max_distance):
    """
    Get matches by matching the coordinate averages (centers-of-mass).

    Parameters
    ----------
    manFile : dict
    autoFile : dict
    max_distance : float

    Returns
    -------
    manFile : dict
    autoFile : dict
    """
    # Reset matches
    for mf in manFile:
        mf['matched'] = None
    # Iterate through manual features
    for mf in manFile:
        closest_match = None
        closest_distance = np.Infinity
        # Iterate over all auto features. Look for closest match.
        for af in autoFile:
            if not af['matched']:
                mf_avgc = np.array([mf['avgx'], mf['avgy']])
                af_avgc = np.array([af['avgx'], af['avgy']])
                dist = np.linalg.norm(np.abs(mf_avgc-af_avgc))
                # Check if distance between two lines is within the threshold, and closest
                if dist <= max_distance and dist < closest_distance:
                    closest_match = af
                    closest_distance = dist
        if closest_match is not None:
            ind = autoFile.index(closest_match)
            autoFile[ind]['matched'] = True
            mf['matched'] = True
            
            # Plot a line connecting matching features
            plt.plot(np.append(np.median(mf['x']), np.median(autoFile[ind]['x'])),
                    np.append(np.median(mf['y']), np.median(autoFile[ind]['y'])),
                    color="orange")
            plt.scatter(np.append(np.median(mf['x']), np.median(autoFile[ind]['x'])),
                    np.append(np.median(mf['y']), np.median(autoFile[ind]['y'])),
                    color="orange")
    return(manFile, autoFile)

def get_matches_avg_line(manFiles, autoFiles, max_distance=np.Infinity):
    """
    Get matches by matching on a per-pixel basis. Interpolates
    along supplied manual lines. 

    Parameters
    ----------
    manFiles : dict
    autoFiles : dict
    max_distance : float

    Returns
    -------
    manFiles : dict
    autoFiles : dict
    """
    # Limit to how many "close" features we should look at
    CLOSEST_LIMIT = 10
    MAX_DISTANCE = max_distance

    for manFile in manFiles.keys():
        for autoFile in autoFiles.keys():
            for man_line in manFiles[manFile]:
                # Calculate the CLOSEST_LIMIT closest auto lines
                distances = {}
                closest_auto = {}
                mavg = np.array([man_line['avgx'], man_line['avgy']])
                for auto_line in autoFiles[autoFile]:
                    aavg = np.array([auto_line['avgx'], auto_line['avgy']])
                    distance = np.around(np.linalg.norm(np.abs(mavg-aavg)), 3)
                    distances[distance] = auto_line
                sorted_distances = sorted(distances.keys())
                for dist in zip(sorted_distances, range(CLOSEST_LIMIT)):
                    dist = dist[0]
                    closest_auto[dist] = distances[dist]
                # Calculate the per-pixel distance to each of the 10 autofeatures
                closest_feature = None
                closest_distance = np.Infinity
                for dist in closest_auto.keys():
                    auto_line = closest_auto[dist]
                    auto_index = autoFiles[autoFile].index(auto_line)
                    distances = []
                    for mx, my in zip(man_line['x'], man_line['y']):
                        for ax, ay in zip(auto_line['x'], auto_line['y']):
                            mc = np.array([mx,my])
                            ac = np.array([ax,ay])
                            d = np.linalg.norm(np.abs(mc-ac))
                            distances.append(d)
                    avg_dist = np.mean(distances)
                    if avg_dist < closest_distance and avg_dist <= MAX_DISTANCE:
                        closest_feature = auto_index
                        closest_distance = avg_dist
                if closest_distance != np.Infinity and not man_line['matched'] and not autoFiles[autoFile][closest_feature]['matched']:
                    man_line['matched'] = True
                    autoFiles[autoFile][closest_feature]['matched'] = True
                    plt.plot(np.append(np.median(man_line['x']), np.median(autoFiles[autoFile][closest_feature]['x'])),
                            np.append(np.median(man_line['y']), np.median(autoFiles[autoFile][closest_feature]['y'])),
                            color="orange", label="Matching line")
                    plt.scatter(np.append(np.median(man_line['x']), np.median(autoFiles[autoFile][closest_feature]['x'])),
                            np.append(np.median(man_line['y']), np.median(autoFiles[autoFile][closest_feature]['y'])),
                            color="orange")
            for mf in manFiles[manFile]:
                if mf['matched']:
                    plt.plot(mf['x'], mf['y'], color='darkblue', label="Matched manual")
                else:
                    plt.plot(mf['x'], mf['y'], color='cyan', label="Unmatched manual")
            for af in autoFiles[autoFile]:
                if af['matched']:
                    plt.plot(af['x'], af['y'], color='forestgreen', label="Matched automatic")
                else:
                    plt.plot(af['x'], af['y'], color='lime', label="Unmatched automatic")
    # get legend handles and their corresponding labels
    handles, labels = plt.gca().get_legend_handles_labels()
    # zip labels as keys and handles as values into a dictionary, ...
    # so only unique labels would be stored 
    dict_of_labels = dict(zip(labels, handles))
    # use unique labels (dict_of_labels.keys()) to generate your legend
    plt.legend(dict_of_labels.values(), dict_of_labels.keys())
    plt.show()
    return(manFiles, autoFiles)

def interpolate(linex, liney):
    """
    Interpolate along a given line, and return a set of coordinates
    separated at 1 pixel increments. 

    Parameters
    ----------
    linex : list
    liney : list

    Returns
    -------
    linex : list
    liney : list
    """
    int_function = interp1d(linex,liney)
    if linex[0] < linex[-1]:
        line2x_new = np.arange(linex[0], linex[-1], 1)
    else:
        line2x_new = np.arange(linex[-1], linex[0])[::-1]
    line2y_new = int_function(line2x_new)
    return(line2x_new, line2y_new)