#!/usr/bin/python3
# -*- coding: utf-8 -*-
"""
Created on Fri 10.28.22
@title: Timeseries widgets
@author: Parker Lamb
@description: Widgets to contain mechanisms for working with
timeseries functions. 
"""

from PySide6.QtWidgets import (QVBoxLayout, QFileDialog, QHBoxLayout, QFormLayout, QWidget, QCheckBox, QGroupBox, QLabel, QSlider, QSpinBox, QPushButton)
from PySide6.QtCore import Qt
from helper.widgets import MPLImage
from astropy.io import fits

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

        # Create sidebar layout
        sidebarLayout = QVBoxLayout()
        layout.addLayout(sidebarLayout)

        # Add open timeseries button to right sidebar
        self.openTsButton = QPushButton("Open timeseries")
        self.openTsButton.clicked.connect(self.open_timeseries)
        sidebarLayout.addWidget(self.openTsButton)

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
        self.analysisButton = QCheckBox()
        self.analysisButton.setCheckState(Qt.Unchecked)
        configLayout.addRow(QLabel("Run analysis:"), self.analysisButton)
        
        # Add button to open previous data (non-functional for now)
        self.prevDataButton = QPushButton("Open previous data")
        configLayout.addRow(self.prevDataButton)

        # Disable everything until an image is opened
        self.upperInput.setDisabled(True)
        self.lowerInput.setDisabled(True)
        self.analysisButton.setDisabled(True)
        self.prevDataButton.setDisabled(True)

        # Add a data writing section 
        saveBox = QGroupBox("Write data")
        saveLayout = QVBoxLayout()
        saveBox.setLayout(saveLayout)

        # Add buttons to data writing section
        

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
        except:
            print("Error opening image.")
            return
        self.tsimg.set_ts_index(self.img_orig,0)
        self.reset_axis()
    
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
        def set_ts_index(self, image, index):
            self.set_image(image[index,:,:])
