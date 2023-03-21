#!/usr/bin/python3
# -*- coding: utf-8 -*-
"""
Created on Fri 10.28.22
@title: Timeseries widgets
@author: Parker Lamb
@description: Widgets to contain mechanisms for working with
timeseries functions. 
"""

from PySide6.QtWidgets import (QVBoxLayout, QHBoxLayout, QWidget, QGroupBox,
                               QLabel, QSlider)
from PySide6.QtCore import Qt
from helper.widgets import MPLImage

class TimeseriesWidget(QWidget):
    def __init__(self):
        """
        Container widget for analyzing timeseries data
        """
        super().__init__()

        # Global layout
        layout = QVBoxLayout(self)
        
        # Layout to contain image and controls
        leftLayout = QVBoxLayout(self)
        layout.addLayout(leftLayout)

        # Add image
        self.tsimg = MPLImage("")
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