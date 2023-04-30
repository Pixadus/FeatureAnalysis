#!/usr/bin/python3
# -*- coding: utf-8 -*-
"""
Created on Fri 10.28.22
@title: Timeseries widgets
@author: Parker Lamb
@description: Widgets to contain mechanisms for working with
timeseries functions. 
"""

import csv
import numpy as np
from PySide6.QtWidgets import (QVBoxLayout, QFileDialog, QHBoxLayout, QFormLayout, QWidget, QCheckBox, QGroupBox, QLabel, QPlainTextEdit, QSlider, QSpinBox, QPushButton)
from PySide6.QtCore import Qt
from helper.widgets import MPLImage
from astropy.io import fits
from timeseries.timeseries import Timeseries

class TimeseriesWidget(QWidget):
    def __init__(self):
        """
        Container widget for analyzing timeseries data
        """
        super().__init__()

        # Global layout
        layout = QHBoxLayout(self)
        
        # Layout to contain image and controls
        leftLayout = QVBoxLayout(self)
        layout.addLayout(leftLayout)

        # Add image
        self.tsimg = self.MPLTSImage("")
        leftLayout.addWidget(self.tsimg)

        # Add controls area below the image
        controlsBox = QGroupBox("Controls")
        controlsLayout = QVBoxLayout()
        controlsBox.setLayout(controlsLayout)
        leftLayout.addWidget(controlsBox)

        # Add a current frame layout
        frameLayout = QHBoxLayout()
        controlsLayout.addLayout(frameLayout)

        # Add current frame indicator
        frameLayout.addStretch()
        frameTextLabel = QLabel("Frame:")
        self.frameSpin = QSpinBox()
        self.frameSpin.valueChanged.connect(self.update_from_spinbox)
        frameLayout.addWidget(frameTextLabel)
        frameLayout.addWidget(self.frameSpin)
        frameLayout.addStretch()
        
        # Create slider layout
        sliderLayout = QHBoxLayout()
        controlsLayout.addLayout(sliderLayout)

        # Create/add slider controls
        self.sliderLeftText = QLabel("")
        self.slider = QSlider(Qt.Horizontal)
        self.sliderRightText = QLabel("")
        sliderLayout.addWidget(self.sliderLeftText)
        sliderLayout.addWidget(self.slider)
        sliderLayout.addWidget(self.sliderRightText)

        # Add a slider signal processor
        self.slider.valueChanged.connect(self.update_from_slider)

        # Add a pause/play button (TODO)
        self.ppButton = QPushButton("Pause/play")
        # controlsLayout.addWidget(self.ppButton)

        # Create sidebar layout
        sidebarLayout = QVBoxLayout()
        layout.addLayout(sidebarLayout)

        # Add open timeseries button to right sidebar
        self.openTsButton = QPushButton("Open timeseries (.fits)")
        self.openTsButton.clicked.connect(self.open_timeseries)
        sidebarLayout.addWidget(self.openTsButton)

        # Add button to open previous data (non-functional for now)
        prevDataLayout = QHBoxLayout()
        self.prevMatchesButton = QPushButton("Open previous tracings")
        self.prevMatchesButton.clicked.connect(self.open_previous_data)
        prevDataLayout.addWidget(self.prevMatchesButton)
        sidebarLayout.addLayout(prevDataLayout)

        # Add config group box
        configBox = QGroupBox("Config")
        configLayout = QFormLayout()
        configBox.setLayout(configLayout)
        sidebarLayout.addWidget(configBox)

        # Add range widget
        rangeWidget = QWidget()
        rangeLayout = QHBoxLayout()
        self.lowerInput = QSpinBox()
        self.upperInput = QSpinBox()
        rangeLayout.addWidget(self.lowerInput)
        rangeLayout.addWidget(QLabel("to"))
        rangeLayout.addWidget(self.upperInput)
        rangeWidget.setLayout(rangeLayout)
        configLayout.addRow(QLabel("Analysis range:"), rangeWidget)

        # Check to see if the user wants to run analysis as well
        self.analysisCheck = QCheckBox()
        self.analysisCheck.setCheckState(Qt.Unchecked)
        configLayout.addRow(QLabel("Run per-frame analysis:"), self.analysisCheck)

        # Trace out all features?
        self.traceFullCheck = QCheckBox()
        self.traceFullCheck.setCheckState(Qt.Unchecked)
        configLayout.addRow(QLabel("Trace features on GUI:"), self.traceFullCheck)

        # Trace out matched features?
        self.traceMatchCheck = QCheckBox()
        self.traceMatchCheck.setCheckState(Qt.Checked)
        configLayout.addRow(QLabel("Trace matching features on GUI:"), self.traceMatchCheck)

        # Add a "save" checkmark
        self.saveCheck = QCheckBox()
        self.saveCheck.setCheckState(Qt.Checked)
        configLayout.addRow(QLabel("Save results to files"), self.saveCheck)

        # Add a "Analyze timeseries" button
        self.goTsButton = QPushButton("Analyze timeseries")
        self.goTsButton.clicked.connect(self.analyze_timeseries)
        sidebarLayout.addWidget(self.goTsButton)
        
        # Add a data writing section 
        saveBox = QGroupBox("Data writing")
        saveLayout = QHBoxLayout()
        saveBox.setLayout(saveLayout)
        sidebarLayout.addWidget(saveBox)

        # Add buttons to data writing section
        self.writeMatchesBtn = QPushButton("Save matches")
        self.writeAnalysisBtn = QPushButton("Save analysis")
        saveLayout.addWidget(self.writeMatchesBtn)
        saveLayout.addWidget(self.writeAnalysisBtn)

        # Disable everything until an image is opened
        self.prevMatchesButton.setDisabled(True)
        self.upperInput.setDisabled(True)
        self.lowerInput.setDisabled(True)
        self.analysisCheck.setDisabled(True)
        self.traceFullCheck.setDisabled(True)
        self.traceMatchCheck.setDisabled(True)
        self.goTsButton.setDisabled(True)
        self.writeMatchesBtn.setDisabled(True)
        self.writeAnalysisBtn.setDisabled(True)
        self.ppButton.setDisabled(True)
        self.frameSpin.setDisabled(True)

        # Add stretch to the sidebar
        sidebarLayout.addStretch()
    
    def analyze_timeseries(self):
        """
        Run the analysis. 
        """
        # Set variables
        self.ts.analyze_frames = self.analysisCheck.isChecked()
        self.ts.trace_full = self.traceFullCheck.isChecked()
        self.ts.trace_matches = self.traceMatchCheck.isChecked()
        self.ts.save_frames = self.saveCheck.isChecked()
        self.ts.start = self.lowerInput.value()
        self.ts.end = self.upperInput.value()

        # Update the frame to the min specified frame
        self.tsimg.set_ts_index(self.img_orig,self.ts.start)
        self.slider.setValue(self.ts.start)
        self.frameSpin.setValue(self.ts.start)

        # Start the analysis
        self.ts.trace_images()
        self.ts.get_matching_features()
        self.ts.follow_feature_matches()
        if self.ts.analyze_frames:
            self.ts.run_analysis()
        if self.ts.trace_full:
            self.ts.trace_features_full()
        if self.ts.trace_matches:
            self.ts.trace_feature_matches()
        if self.ts.save_frames:
            self.ts.save_files()
        print("Done!")
        
    def open_timeseries(self):
        """
        Open a file browser and select an image.
        """
        dialog = QFileDialog()
        # Only allow single, existing files
        dialog.setFileMode(QFileDialog.ExistingFile)
        # Image is a tuple of (path, file_type)
        image_path = dialog.getOpenFileName(self, "Open image", filter="FITS file (*.fits)")[0]
        # Try to open data and set graph image
        try:
            f = fits.open(image_path, ignore_missing_end=True)
            self.img_orig = f[0].data
            self.prevMatchesButton.setDisabled(False)
            self.upperInput.setDisabled(False)
            self.lowerInput.setDisabled(False)
            self.analysisCheck.setDisabled(False)
            self.traceFullCheck.setDisabled(False)
            self.traceMatchCheck.setDisabled(False)
            self.goTsButton.setDisabled(False)
            self.ppButton.setDisabled(False)
            self.frameSpin.setDisabled(False)
            self.setup_properties()
        except:
            print("Error opening image.")
            return
        self.tsimg.set_ts_index(self.img_orig,0)
        self.reset_axis()

        # Create a timeseries instance
        self.ts = Timeseries(self.img_orig)
    
    def open_previous_data(self):
        """
        Open previous tracing/analysis data, and set self.ts.sequence_tracings to it.
        TODO doesn't quite work yet. Finish on a day when we have a bit more time. 
        """
        dialog = QFileDialog()
        # Only allow single, existing files
        dialog.setFileMode(QFileDialog.ExistingFile)
        # Allow multiple
        previous_data = dialog.getOpenFileNames(self, "Select all previous data", filter="CSV file (*.csv)")[0]

        # Reset the Timeseries feature data
        self.ts.sequence_tracings = []

        # Run through files and import their contents
        for csvlink in previous_data:
            with open(csvlink) as datafile:
                data = csv.reader(datafile)
                f_num = 0
                self.f_data = {}
                # Initialize an empty coordinate list
                self.f_data[f_num] = []
                for row in data:
                    if 'f_num' in row:
                        continue
                    # Only tracings
                    if len(row) == 3:
                        # If a coordinate in the same feature
                        if int(row[0]) == f_num:
                            coord = {"coord" : (float(row[1]), float(row[2]))}
                            self.f_data[f_num].append(coord)
                        # If a new feature
                        else:
                            # Set the new feature number
                            f_num = int(row[0])
                            coord = {"coord" : (float(row[1]), float(row[2]))}
                            # Initialize the coordinate list, add current coord
                            self.f_data[f_num] = [coord]
                    # Tracings + analysis
                    elif len(row) == 5:
                        # If a coordinate in the same feature
                        if int(row[0]) == f_num:
                            coord = {
                                "coord" : (float(row[1]), float(row[2])),
                                "length" : float(row[3]),
                                "breadth" : float(row[4])
                            }
                            self.f_data[f_num].append(coord)
                        # If a new feature
                        else:
                            # Set the new feature number
                            f_num = int(row[0])
                            coord = {
                                "coord" : (float(row[1]), float(row[2])),
                                "length" : float(row[3]),
                                "breadth" : float(row[4])
                            }
                            # Initialize the coordinate list, add current coord
                            self.f_data[f_num] = [coord]

    def update_from_slider(self):
        """
        Update the index and window properties with the value of the slider.
        Normally called whenever the value of the slider changes.
        """
        new_index = self.slider.value()
        self.tsimg.set_ts_index(self.img_orig,new_index)
        self.frameSpin.setValue(new_index)
    
    def update_from_spinbox(self):
        """
        Update the index and window properties with the value of the spinbox.
        Normally called whenever the value of the spinbox changes.
        """
        new_index = self.frameSpin.value()
        self.tsimg.set_ts_index(self.img_orig,new_index)
        self.slider.setValue(new_index)
    
    def setup_properties(self):
        """
        Gather image properties and add them to the tab. 
        """
        lowerBounds = 0
        upperBounds = self.img_orig.shape[0]

        # Set the values of the sidebar spinboxes
        self.lowerInput.setMinimum(int(lowerBounds))
        self.upperInput.setMaximum(int(upperBounds)-1)
        self.lowerInput.setValue(int(lowerBounds))
        self.upperInput.setValue(int(upperBounds)-1)

        # Set slider bounds
        self.sliderLeftText.setText(str(lowerBounds))
        self.sliderRightText.setText(str(upperBounds-1))
        self.slider.setMaximum(int(upperBounds)-1)
        self.frameSpin.setMaximum(int(upperBounds)-1)
    
    def reset_axis(self):
        """
        Refresh the axis. 
        """
        # Refresh the canvas
        self.tsimg.ax.draw_artist(self.tsimg.ax.patch)
        self.tsimg.canvas.update()
        self.tsimg.canvas.flush_events()
        self.tsimg.canvas.draw()
    
    class MPLTSImage(MPLImage):
        """
        MPLImage subclass, with a new function.
        """
        def set_ts_index(self, image, index, tracings=None):
            """
            Update the 
            """
            self.set_image(image[index,:,:])
            if tracings is not None:
                self.plot(tracings)