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
from PySide6.QtWidgets import (QCheckBox, QFileDialog, QFormLayout, QGroupBox, QHBoxLayout, QLineEdit, QLabel, QPushButton, QVBoxLayout, QWidget)
from matplotlib import (pyplot, colors)
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg
from astropy.io import fits
from analysis.analysis import Analysis
from helper.functions import ZoomPan
from collections import OrderedDict
import csv

class AnalysisWidget(QWidget):
    def __init__(self):
        """
        Container widget used when the "Analysis" tab
        is selected.
        """
        super().__init__()

        # TODO we need a way to modify breadth params
        
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

        # Create the data variable
        self.img_data = None

        # Add setup onclick events
        openImageButton.clicked.connect(self.open_image)
        self.openDataButton.clicked.connect(self.open_data)

        # Add options group box
        optionsBox = QGroupBox("Options")
        optionsLayout = QVBoxLayout()
        optionsBox.setLayout(optionsLayout)
        topBarLayout.addWidget(optionsBox)

        # Add check boxes to options
        self.checkLength = QCheckBox("Calculate length")
        self.checkBreadth = QCheckBox("Calculate breadth")
        self.checkLength.setChecked(True)
        self.checkBreadth.setChecked(True)
        optionsLayout.addWidget(self.checkLength)
        optionsLayout.addWidget(self.checkBreadth)

        # Add custom options box
        custBox = QGroupBox("Custom options")
        self.custLayout = QHBoxLayout()
        custBox.setLayout(self.custLayout)
        topBarLayout.addWidget(custBox)
        self.custDict = {}

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

        # Add zoom and pan functionality
        self.zp = ZoomPan(self.ax)

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

        # Set the click functionality of the Analysis button
        self.analyzeButton.clicked.connect(self.run_analysis)

        # Disable analyze button by default
        self.analyzeButton.setEnabled(False)

        # Create a results box
        resultsBox = QGroupBox("Results")
        self.resultsBoxLayout = QFormLayout()
        resultsBox.setLayout(self.resultsBoxLayout)
        resultLayout.addWidget(resultsBox)

        # Create a 'save' button
        self.saveButton = QPushButton("Save data")
        resultLayout.addWidget(self.saveButton)

        # Set click functionality of the saveButton
        self.saveButton.clicked.connect(self.save_results)

        # Disable saveButton by default
        self.saveButton.setEnabled(False)

    def open_image(self, ex_img=None):
        """
        Open a file browser and select an image.

        Parameters
        ----------
        ex_img : ndarray
            External image data, sent by the tracing tab.
        """
        # External image is supplied
        if ex_img:
            self.img_data = ex_img[0]
            self.canvas.draw()

        # No external image is supplied
        else:
            dialog = QFileDialog()
            # Only allow single, existing files
            dialog.setFileMode(QFileDialog.ExistingFile)
            # Image is a tuple of (path, file_type)
            image_path = dialog.getOpenFileName(self, "Open image", filter="FITS file (*.fits)")[0]
            # Try to open data and set graph image
            try:
                f = fits.open(image_path, ignore_missing_end=True)
                self.img_data = f[0].data
            except:
                print("Error opening image.")
                return
        
        self.ax.cla()
        self.ax.imshow(self.img_data, origin="lower")
        # Refresh the canvas
        self.ax.draw_artist(self.ax.patch)
        self.canvas.update()
        self.canvas.flush_events()
        self.canvas.draw()
        self.openDataButton.setEnabled(True)
    
    def open_data(self, ex_data=None):
        """
        Open file browser and select a .csv feature
        data file.

        Parameters
        ----------
        ex_data : list
            List of lists, optionally supplied from 
            tracing tab.
        """
        # External data is supplied
        if ex_data:
            f_num = 0
            self.f_data = OrderedDict()
            for feature in ex_data:
                self.f_data[f_num] = []
                for coord in feature:
                    c = {"coord" : (float(coord[0]), float(coord[1]))}
                    self.f_data[f_num].append(c)
                x = [c["coord"][0] for c in self.f_data[f_num]]
                y = [c["coord"][1] for c in self.f_data[f_num]]
                self.ax.plot(x,y, color="blue", linewidth=1, markersize=1)
                f_num += 1

        # No external data is supplied
        else:
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
                f_num = 0
                self.f_data = OrderedDict()
                # Initialize an empty coordinate list
                self.f_data[f_num] = []
                for row in data:
                    # If a coordinate in the same feature
                    if int(float(row[0])) == f_num:
                        coord = {"coord" : (float(row[1]), float(row[2]))}
                        self.f_data[f_num].append(coord)
                    # If a new feature
                    else:
                        x = [c["coord"][0] for c in self.f_data[f_num]]
                        y = [c["coord"][1] for c in self.f_data[f_num]]
                        self.ax.plot(x,y, color="blue", linewidth=1, markersize=1)
                        # Set the new feature number
                        f_num = int(float(row[0]))
                        coord = {"coord" : (float(row[1]), float(row[2]))}
                        # Initialize the coordinate list, add current coord
                        self.f_data[f_num] = [coord]

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
        addImage = QPushButton("Add image")
        custOptLayout.addWidget(addImage)

        # Disable button by default
        addImage.setEnabled(False)

        # Add a event signal to button and text
        line.textChanged.connect(lambda: self.modify_text(line, addImage))
        addImage.clicked.connect(lambda: self.add_option_image(line))

        # Add to the custom options box layout
        self.custLayout.addWidget(custOptWidget)

        # Enable the "remButton"
        self.remButton.setEnabled(True)

    def add_option_image(self, line_edit):
        """
        Add an image to the option.
        """
        dialog = QFileDialog()
        # Only allow single, existing files
        dialog.setFileMode(QFileDialog.ExistingFile)
        # Image is a tuple of (path, file_type)
        img_path = dialog.getOpenFileName(self, "Open option image", filter="FITS file (*.fits)")[0]
        if len(img_path) == 0:
            return
        f = fits.open(img_path)
        f = f[0].data
        # Disable the line edit, so dict is correct
        line_edit.setEnabled(False)
        # Add the line text to the dict, associate it with the image data
        self.custDict[line_edit.text()] = f
    
    def modify_text(self, line_edit, button):
        """
        Enable "Add image" button only if text in param field.
        """
        if line_edit.displayText() == '':
            button.setEnabled(False)
        else:
            button.setEnabled(True)

    def rem_option(self):
        """
        Removes the latest option from the Custom Options box.
        """
        # Remove the related entry from the custom opts dict
        last_opt = self.custLayout.itemAt(self.custLayout.count()-1).widget()
        text = None
        for i in range(last_opt.layout().count()):
            w = last_opt.layout().itemAt(i).widget()
            try: 
                text = w.displayText()
                self.custDict.pop(text)
            except:
                pass
                
        # Remove the last entry in the layout
        self.custLayout.itemAt(self.custLayout.count()-1).widget().setParent(None)
        if self.custLayout.count() == 0:
            self.remButton.setEnabled(False)

    def current_state(self):
        """
        Returns a list enabled params.
        """
        params = []
        if self.checkBreadth.isChecked():
            params.append('breadth')
        if self.checkLength.isChecked():
            params.append('length')
        params = params + [c for c in self.custDict.keys()]
        return(params)

    def save_results(self):
        """
        Save the new data.
        """
        dialog = QFileDialog()
        # We're saving a file, not opening here
        dialog.setAcceptMode(QFileDialog.AcceptSave)
        dialog.setFileMode(QFileDialog.AnyFile)
        # Returned path is a tuple of (path, file_type)
        save_path = dialog.getSaveFileName(self, "Save results", filter="CSV file (*.csv)")[0]
        
        # Save format will be { feature_id, x, y, len, bre, [cust] }
        with open(save_path, 'w') as outfile:
            resultwriter = csv.writer(outfile)
            resultwriter.writerow(["f_num", 'x', 'y']+[state for state in self.current_state()])
            for f_num in self.f_data.keys():
                for coord in self.f_data[f_num]:
                    resultwriter.writerow([
                        f_num, 
                        coord['coord'][0], 
                        coord['coord'][1]
                        ] + [coord[state] for state in self.current_state()]
                        )

    def run_analysis(self):
        """
        Runs the analysis on self.data
        """
        analysis = Analysis(self.img_data, self.f_data, self.ax)

        analysis.set_opts(
            self.checkBreadth.isChecked(), 
            self.checkLength.isChecked(),
            self.custDict
            )

        self.f_data = analysis.run()

        # Enable the saveButton once analysis has been run
        self.saveButton.setEnabled(True)

        # Refresh the canvas after the breadth updates
        self.ax.draw_artist(self.ax.patch)
        self.canvas.update()
        self.canvas.flush_events()
        self.canvas.draw()

        # Calculate averages for each feature
        f_avg = {}
        # Populate dictionary
        for key in self.current_state():
            f_avg[key] = 0
        # Create a running tally of coordinates
        coord_count = 0
        for f_num in self.f_data.keys():
            for coord in self.f_data[f_num]:
                coord_count += 1
                for key in self.current_state():
                    if coord[key]:
                        f_avg[key] += coord[key]
        # Average out the coordinates
        for key in f_avg.keys():
            f_avg[key] = f_avg[key]/coord_count
        
        # Reset resultBox
        for i in reversed(range(self.resultsBoxLayout.rowCount())):
            self.resultsBoxLayout.removeRow(i)
        
        # Add average to resultBox
        self.resultsBoxLayout.insertRow(0, "Feature count:", QLabel(str(max([k for k in self.f_data.keys()]))))
        n=1
        for key in f_avg.keys():
            self.resultsBoxLayout.insertRow(n, "Average "+key+":", QLabel(str(round(f_avg[key],2))))
            n+=1