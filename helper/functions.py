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
from scipy.signal import savgol_filter

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
    def __init__(self, polygon, min_arc_dist=10, max_spatial_dist=20, min_area=300, percent_thresh=0.15):
        """
        Parameters
        ----------
        polygon : shapely.Polygon
            Polygon to segment.
        min_arc_dist : int (default 10)
            Minimum arc length distance between neighboring identified curves
        max_spatial_dist : int (default 20)
            Maximum Euclidian distance between matched curves
        pecent_thresh : float (default 0.15)
            Only consider the upper (percent) curves. Higher values increase runtime.
        """
        self.polygon = polygon
        self.min_arc_dist = min_arc_dist
        self.max_spatial_dist = max_spatial_dist
        self.min_area = min_area
        self.percent_thresh = percent_thresh
    
    def run(self) -> MultiPolygon:
        """
        Run the segmentation of the polygon. 

        Returns
        -------
        polygons : shapely.MultiPolygon 
        """

        # TODO - only works with exteriors for now, even if interior specified
        x, y = self.polygon.exterior.xy
        x = savgol_filter(x, 30, 3)
        y = savgol_filter(y, 30, 3)

        # Recreate polygon with smoothed coordinates
        self.polygon = Polygon(list(zip(x,y)))

        # Calculating curvature at every point
        n=0
        xp, yp, xpp, ypp = None, None, None, None
        klist = []
        for xc, yc in zip(x,y):
            # Skip the first two entries; xpp/ypp not defined here
            if n <= 3:
                n+=1
                continue
            xp = xc-x[n-2]
            yp = yc-y[n-2]
            xp_r = x[n-2]-x[n-4]
            yp_r = y[n-2]-y[n-4]
            xpp = xp-xp_r
            ypp = yp-yp_r
            k = abs(xp*ypp-yp*xpp)/((xp**2+yp**2)**(3/2))
            klist.append((k,xc,yc))
            n+=1

        df = pd.DataFrame({
            'k': [k[0] for k in klist],
            'x': [k[1] for k in klist],
            'y': [k[2] for k in klist]
        })
        df_full = df.copy(deep=True)

        # Find all points that don't lie too far away from the mean (ext)
        nonOutlierList = Identify_NonOutliers(df, self.percent_thresh)
        df = df[~nonOutlierList.k]

        # Add a 'matched' variable
        df['matched'] = False

        s_index = 0
        shape = self.polygon
        shapelist = [shape]
        multisegments = []
        for xc,yc,kc in zip(df.x, df.y, df.k):
            s_index = 0
            for s in shapelist:
                if s.touches(Point([xc, yc])) or s.contains(Point([xc,yc])):
                    break
                # else s_index < len(shapelist)-1:
                #     s_index += 1
                else:
                    s_index += 1

            shape = shapelist[s_index]

            if df[df.k == kc].iloc[0].matched:
                continue
            df['dist'] = df.apply(lambda row: np.linalg.norm(np.array([row.x, row.y]) - np.array([xc, yc])), axis=1)
            df.sort_values('dist', ignore_index=True, inplace=True)

            # Don't consider already-matched curvature values
            df['considered'] = df.apply(lambda row: not row.matched, axis=1)

            # Don't consider curvatures too far away
            df['considered'] = df.apply(lambda row: row.considered and row.dist <= self.max_spatial_dist, axis=1)

            # Make sure values are far away from one another on the line
            orig_index = df_full[df_full.k == kc].index
            df['considered'] = df.apply(lambda row: row.considered and abs(df_full[df_full.k == row.k].index-orig_index) > self.min_arc_dist, axis=1)

            # Make sure the interpolated line between each curvature point lies entirely within the shape. 
            df['considered'] = df.apply(lambda row: row.considered and np.array([shape.contains(Point(c1,c2)) or Point(c1,c2).touches(shape) for c1,c2 in zip(np.linspace(row.x, xc, 10), np.linspace(row.y, yc, 10))]).all(),  axis=1)

            # Divide Polygon based on string
            try:
                connx = df[df.considered == True].iloc[0].x
                conny = df[df.considered == True].iloc[0].y
                connk = df[df.considered == True].iloc[0].k
                conn_full_ind = df_full[df_full.k == connk].index
            except IndexError:
                continue
            line = LineString([(xc, yc), (connx, conny)])
            res = split(shape, line)

            # Check if the resultant polygons are below the minimum area
            ptf = np.array([r.area > self.min_area for r in res.geoms])
            if not ptf.all():
                continue

            # Update the shape_list
            shapelist.pop(s_index)
            shapelist.extend([s for s in res.geoms])

            # Add LineString to multisegments if only 1 geom returned (i.e. didn't divide in two)
            if len(res.geoms) == 1:
                multisegments.append((orig_index, conn_full_ind))

            # Create subshape if multisegments form a closed shape
            if len(multisegments) == 2:
                df1_0 = df_full.iloc[multisegments[0][0]]
                df1_1 = df_full.iloc[multisegments[0][1]]
                df2_0 = df_full.iloc[multisegments[1][0]]
                df2_1 = df_full.iloc[multisegments[1][1]]

                line1 = LineString([(df1_0.x, df1_0.y), (df1_1.x, df1_1.y)])
                line2 = LineString([(df2_0.x, df2_0.y), (df2_1.x, df2_1.y)])
                if multisegments[0][0] > multisegments[1][0]:
                    line3_df = df_full.iloc[multisegments[1][0].values[0]:multisegments[0][0].values[0]+1]
                else:
                    line3_df = df_full.iloc[multisegments[0][0].values[0]:multisegments[1][0].values[0]+1]
                if multisegments[0][1] > multisegments[1][1]:
                    line4_df = df_full.iloc[multisegments[1][1].values[0]:multisegments[0][1].values[0]+1]
                else:
                    line4_df = df_full.iloc[multisegments[0][1].values[0]:multisegments[1][1].values[0]+1]
                line3 = LineString([(x,y) for x,y in zip(line3_df.x, line3_df.y)])
                line4 = LineString([(x,y) for x,y in zip(line4_df.x, line4_df.y)])

                intersect = polygonize([line1, line3, line2, line4]).geoms[0]

                s1 = shape-intersect
                        
                shapelist.pop(s_index)
                shapelist.extend([s1,intersect])
                multisegments = []

            # Mark both curvature points and nearby points on both sides as being matched
            df['matched'] = df.apply(lambda row: row.matched or abs(df_full[df_full.k == row.k].index - orig_index) < self.min_arc_dist, axis=1)
            opp_index = df_full[df_full.k == df[df.considered == True].iloc[0].k].index
            df['matched'] = df.apply(lambda row: row.matched or abs(df_full[df_full.k == row.k].index - opp_index) < self.min_arc_dist, axis=1)

        # Create multipolygon from shapelist and return it
        mp = MultiPolygon(shapelist)
        return(mp)
