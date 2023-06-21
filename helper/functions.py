#!/usr/bin/python3
# -*- coding: utf-8 -*-
"""
Created on Tue 8.5.22
@title: Helper functions
@author: Parker Lamb
@description: Contains miscellaneous functions
for FeatureTracing.
"""

import numpy as np
import pandas as pd
from shapely import MultiPolygon, Polygon, Point, LineString, polygonize
from shapely.ops import split

# This was from a StackExchange answer - see https://stackoverflow.com/a/19829987.
class ZoomPan:
    def __init__(self, ax=None):
        self.press = None
        self.cur_xlim = None
        self.cur_ylim = None
        self.x0 = None
        self.y0 = None
        self.x1 = None
        self.y1 = None
        self.xpress = None
        self.ypress = None
        self.pan = True
        self.ax = ax
    
        if self.ax:
            self.zoom_factory(self.ax)
            self.pan_factory(self.ax)

    def zoom_factory(self, ax, base_scale = 1.1):
        def zoom(event):
            cur_xlim = ax.get_xlim()
            cur_ylim = ax.get_ylim()

            xdata = event.xdata # get event x location
            ydata = event.ydata # get event y location

            if event.button == 'down':
                # deal with zoom in
                scale_factor = 1 / base_scale
            elif event.button == 'up':
                # deal with zoom out
                scale_factor = base_scale
            else:
                # deal with something that should never happen
                scale_factor = 1
                print(event.button)

            new_width = (cur_xlim[1] - cur_xlim[0]) * scale_factor
            new_height = (cur_ylim[1] - cur_ylim[0]) * scale_factor

            relx = (cur_xlim[1] - xdata)/(cur_xlim[1] - cur_xlim[0])
            rely = (cur_ylim[1] - ydata)/(cur_ylim[1] - cur_ylim[0])

            ax.set_xlim([xdata - new_width * (1-relx), xdata + new_width * (relx)])
            ax.set_ylim([ydata - new_height * (1-rely), ydata + new_height * (rely)])
            ax.figure.canvas.draw()

        fig = ax.get_figure() # get the figure of interest
        fig.canvas.mpl_connect('scroll_event', zoom)

        return(zoom)

    def pan_factory(self, ax):
        def onPress(event):
            if event.inaxes != ax: return
            if self.pan:
                self.cur_xlim = ax.get_xlim()
                self.cur_ylim = ax.get_ylim()
                self.press = self.x0, self.y0, event.xdata, event.ydata
                self.x0, self.y0, self.xpress, self.ypress = self.press

        def onRelease(event):
            if self.pan:
                self.press = None
                ax.figure.canvas.draw()

        def onMotion(event):
            if self.press is None: return
            if event.inaxes != ax: return
            if self.pan:
                dx = event.xdata - self.xpress
                dy = event.ydata - self.ypress
                self.cur_xlim -= dx
                self.cur_ylim -= dy
                ax.set_xlim(self.cur_xlim)
                ax.set_ylim(self.cur_ylim)

                ax.figure.canvas.draw()

        fig = ax.get_figure() # get the figure of interest

        # attach the call back
        fig.canvas.mpl_connect('button_press_event',onPress)
        fig.canvas.mpl_connect('button_release_event',onRelease)
        fig.canvas.mpl_connect('motion_notify_event',onMotion)

        # return the function
        return(onMotion)

def erase_layout_widgets(layout):
    """
    Function to remove all widgets contained inside
    a given layout.

    Parameters
    ----------
    layout : QLayout
    """
    for i in reversed(range(layout.count())):
        layout.itemAt(i).widget().setParent(None)

def Identify_NonOutliers(df, percent=0.1):
    Q1 = df.quantile(percent)
    Q3 = df.quantile(1-percent)
    IQR = Q3 - Q1
    trueList = ~((df < (Q1 - 1.5 * IQR)) |(df > (Q3 + 1.5 * IQR)))
    return trueList

class CurvatureSegmentation:
    def __init__(self, polygon=None, min_arc_dist=10, max_spatial_dist=20, min_area=300):
        """
        Parameters
        ----------
        polygon : shapely.Polygon
            Polygon to segment.
        min_arc_dist : int (default 10)
            Minimum arc length distance between neighboring identified curves
        max_spatial_dist : int (default 20)
            Maximum Euclidian distance between matched curves
        """
        self.polygon = polygon
        self.min_arc_dist = min_arc_dist
        self.max_spatial_dist = max_spatial_dist
        self.min_area = min_area
    
    def run(self):
        """
        Run the segmentation of the polygon. 

        Returns
        -------
        polygons : shapely.MultiPolygon 
        """
