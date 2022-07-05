#!/usr/bin/python3
# -*- coding: utf-8 -*-
"""
Created on Tue 6.30.22
@title: Analysis GUI components
@author: Parker Lamb
@description: Contains Qt6 widgets for analyzing
curvilinear features, including length, breadth 
and custom parameters.
"""

from PySide6.QtGui import QPalette
from PySide6.QtWidgets import (QCheckBox, QFileDialog, QFormLayout, QGroupBox, QHBoxLayout, QLineEdit, QPushButton, QVBoxLayout, QWidget)
from matplotlib import (pyplot, colors)
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg
from astropy.io import fits
import csv

class AnalysisWidget(QWidget):
    def __init__(self):
        """
        Container widget used when the "Analysis" tab
        is selected.
        """
        super().__init__()
        
        # Layout for the whole tab window
        layout = QVBoxLayout(self)

        # Add top option bar to layout
        topBarLayout = QHBoxLayout()
        layout.addLayout(topBarLayout)

        # Add setup group box
        setupBox = QGroupBox("Setup")
        setupLayout = QVBoxLayout()
        setupBox.setLayout(setupLayout)
        topBarLayout.addWidget(setupBox)

        # Add open buttons to setup box
        openImageButton = QPushButton("Open tracing image")
        setupLayout.addWidget(openImageButton)
        self.openDataButton = QPushButton("Open tracing data")
        setupLayout.addWidget(self.openDataButton)

        # Disable openDataButton until openImageButton
        self.openDataButton.setEnabled(False)

        # Add setup onclick events
        openImageButton.clicked.connect(self.open_image)
        self.openDataButton.clicked.connect(self.open_data)

        # Add options group box
        optionsBox = QGroupBox("Options")
        optionsLayout = QVBoxLayout()
        optionsBox.setLayout(optionsLayout)
        topBarLayout.addWidget(optionsBox)

        # Add check boxes to options
        checkLength = QCheckBox("Calculate length")
        checkBreadth = QCheckBox("Calculate breadth")
        checkLength.setChecked(True)
        checkBreadth.setChecked(True)
        optionsLayout.addWidget(checkLength)
        optionsLayout.addWidget(checkBreadth)

        # Add custom options box
        custBox = QGroupBox("Custom options")
        self.custLayout = QHBoxLayout()
        custBox.setLayout(self.custLayout)
        topBarLayout.addWidget(custBox)

        # "Add" and "Remove" buttons
        addButton = QPushButton("+")
        addButton.setMaximumWidth(30)
        self.remButton = QPushButton("-")
        self.remButton.setMaximumWidth(30)
        buttonLayout = QVBoxLayout()
        topBarLayout.addLayout(buttonLayout)
        buttonLayout.addWidget(addButton)
        buttonLayout.addWidget(self.remButton)  

        # Add onclick behaviour to + and - buttons
        addButton.clicked.connect(self.add_option)  
        self.remButton.clicked.connect(self.rem_option)    

        # Disable remButton by default
        self.remButton.setEnabled(False)

        # Create "lower" container layout
        bottomLayout = QHBoxLayout()
        layout.addLayout(bottomLayout)
        
        # Add matplotlib canvas to layout
        self.figure = pyplot.figure()
        self.ax = self.figure.add_axes([0,0,1,1])
        self.canvas = FigureCanvasQTAgg(self.figure)
        bottomLayout.addWidget(self.canvas)

        # Set the background color of the canvas
        win_color = self.palette().color(QPalette.Window).getRgbF()
        plot_color = colors.rgb2hex(win_color)
        self.figure.set_facecolor(plot_color)

        # Hide the axes
        self.ax.get_xaxis().set_visible(False)
        self.ax.get_yaxis().set_visible(False)

        # Create a "Results" sidebar
        resultLayout = QVBoxLayout()
        bottomLayout.addLayout(resultLayout)
        
        # Create a "Analyze" button
        self.analyzeButton = QPushButton("Analyze")
        self.analyzeButton.setMinimumWidth(175)
        resultLayout.addWidget(self.analyzeButton)

        # Disable analyze button by default
        self.analyzeButton.setEnabled(False)

        # Create a results box
        resultsBox = QGroupBox("Results")
        resultsLayout = QFormLayout()
        resultsBox.setLayout(resultsLayout)
        resultLayout.addWidget(resultsBox)


    def open_image(self):
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
            self.ax.cla()
            self.ax.imshow(f[0].data, origin="lower")
            # Refresh the canvas
            self.ax.draw_artist(self.ax.patch)
            self.canvas.update()
            self.canvas.flush_events()
            self.canvas.draw()
            self.openDataButton.setEnabled(True)
        except:
            print("Error opening image.")
    
    def open_data(self):
        """
        Open file browser and select a .csv feature
        data file.
        """
        dialog = QFileDialog()
        # Only allow single, existing files
        dialog.setFileMode(QFileDialog.ExistingFile)
        # Image is a tuple of (path, file_type)
        data_path = dialog.getOpenFileName(self, "Open datafile", filter="CSV file (*.csv)")[0]
        if len(data_path) == 0:
            return
        # Try to open data and set graph data
        with open(data_path) as datafile:
            data = csv.reader(datafile)
            fibril_num = 0
            x = []
            y = []
            for row in data:
                if row[0] == fibril_num:
                    x.append(float(row[1]))
                    y.append(float(row[2]))
                else:
                    fibril_num = row[0]
                    self.ax.plot(x,y, color="blue")
                    x = [float(row[1])]
                    y = [float(row[2])]
        # Refresh the canvas
        self.ax.draw_artist(self.ax.patch)
        self.canvas.update()
        self.canvas.flush_events()
        self.canvas.draw()
        # Enable analyze button
        self.analyzeButton.setEnabled(True)

    def add_option(self):
        """
        Adds an option to the Custom Options box. 
        """
        # Create a custom option container widget
        custOptWidget = QWidget()
        # Vertical layout
        custOptLayout = QVBoxLayout()
        custOptWidget.setLayout(custOptLayout)
        # Includes a line edit + a push button
        line = QLineEdit()
        line.setPlaceholderText("Label")
        custOptLayout.addWidget(line)
        custOptLayout.addWidget(QPushButton("Add image"))
        # Add to the custom options box layout
        self.custLayout.addWidget(custOptWidget)
        # Enable the "remButton"
        self.remButton.setEnabled(True)

    def rem_option(self):
        """
        Removes the latest option from the Custom Options box.
        """
        # Remove the last entry in the layout
        self.custLayout.itemAt(self.custLayout.count()-1).widget().setParent(None)
        if self.custLayout.count() == 0:
            self.remButton.setEnabled(False)