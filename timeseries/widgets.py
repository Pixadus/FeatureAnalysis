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

        # Add a current frame layout
        frameLayout = QHBoxLayout()
        controlsLayout.addLayout(frameLayout)

        # Add current frame indicator
        frameLayout.addStretch()
        frameTextLabel = QLabel("Frame:")
        self.frameLabel = QLabel("0")
        frameLayout.addWidget(frameTextLabel)
        frameLayout.addWidget(self.frameLabel)
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

        # Add a pause/play button 
        self.ppButton = QPushButton("Pause/play")
        controlsLayout.addWidget(self.ppButton)

        # Create sidebar layout
        sidebarLayout = QVBoxLayout()
        layout.addLayout(sidebarLayout)

        # Add open timeseries button to right sidebar
        self.openTsButton = QPushButton("Open timeseries (.fits)")
        self.openTsButton.clicked.connect(self.open_timeseries)
        sidebarLayout.addWidget(self.openTsButton)

        # Add button to open previous data (non-functional for now)
        prevDataLayout = QHBoxLayout()
        self.prevMatchesButton = QPushButton("Open previous matches")
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
        configLayout.addRow(QLabel("Run qualitative analysis:"), self.analysisCheck)

        # Add a "Analyze timeseries" button
        self.goTsButton = QPushButton("Analyze timeseries")
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
        self.goTsButton.setDisabled(True)
        self.writeMatchesBtn.setDisabled(True)
        self.writeAnalysisBtn.setDisabled(True)
        self.ppButton.setDisabled(True)

        # Add a status block
        status = QGroupBox("Status")
        statusLayout = QVBoxLayout()
        status.setLayout(statusLayout)
        self.statusLabel = QLabel("")
        statusLayout.addWidget(self.statusLabel)
        statusLayout.addStretch()
        sidebarLayout.addWidget(status)
        
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
            self.prevMatchesButton.setDisabled(True) # Disabled until functional
            self.upperInput.setDisabled(False)
            self.lowerInput.setDisabled(False)
            self.analysisCheck.setDisabled(False)
            self.goTsButton.setDisabled(False)
            self.ppButton.setDisabled(False)
            self.setup_properties()
        except:
            print("Error opening image.")
            return
        self.tsimg.set_ts_index(self.img_orig,0)
        self.reset_axis()
    
    def update_from_slider(self):
        """
        Update the index and window properties with the value of the slider.
        Normally called whenever the value of the slider changes.
        """
        new_index = self.slider.value()
        self.tsimg.set_ts_index(self.img_orig,new_index)
        self.frameLabel.setText(str(new_index))
    
    def setup_properties(self):
        """
        Gather image properties and add them to the tab. 
        """
        lowerBounds = 0
        upperBounds = self.img_orig.shape[0]

        # Set the values of the sidebar spinboxes
        self.lowerInput.setMinimum(int(lowerBounds))
        self.upperInput.setMaximum(int(upperBounds))
        self.lowerInput.setValue(int(lowerBounds))
        self.upperInput.setValue(int(upperBounds))

        # Set slider bounds
        self.sliderLeftText.setText(str(lowerBounds))
        self.sliderRightText.setText(str(upperBounds))
        self.slider.setMaximum(int(upperBounds))
        self.slider.setSingleStep(1)
    
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
