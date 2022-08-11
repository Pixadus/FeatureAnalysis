#!/usr/bin/python3
# -*- coding: utf-8 -*-
"""
Created on Tue 8.9.22
@title: Optimization GUI components
@author: Parker Lamb
@description: Contains Qt6 widgets for optimizing
parameter sets compared to manual tracing.
"""

from PySide6.QtWidgets import (QWidget, QHBoxLayout, QGroupBox,
                            QPushButton, QVBoxLayout, QFileDialog,
                            QLabel)
from PySide6.QtCore import Qt
from helper.functions import erase_layout_widgets
import numpy as np
import matplotlib.pyplot as plt
import csv
import os

# Constants
MAX_DISTANCE = 10.0
PLOT_MATCHES = False

class OptimizationWidget(QWidget):
    def __init__(self):
        """
        Container widget used when the "Optimization"
        tab is selected.
        """
        super().__init__()

        # Create container widgets
        self.manFiles = []
        self.autoFiles = []

        # Set up the global widget layout
        layout = QHBoxLayout(self)

        # Manual tracing selection
        manLayout = QVBoxLayout()
        layout.addLayout(manLayout)
        
        # Create box and buttons
        manSelButton = QPushButton("Select manual tracing")
        manLayout.addWidget(manSelButton)
        manBox = QGroupBox("Selected manual files")
        self.manBoxLayout = QVBoxLayout()
        manBox.setLayout(self.manBoxLayout)
        manLayout.addWidget(manBox)

        # Automatic tracing section
        autoLayout = QVBoxLayout()
        layout.addLayout(autoLayout)

        # Create box and buttons
        autoSelButton = QPushButton("Select automatic tracings")
        autoBox = QGroupBox("Selected automatic files")
        self.autoBoxLayout = QVBoxLayout()
        autoBox.setLayout(self.autoBoxLayout)
        autoLayout.addWidget(autoSelButton)
        autoLayout.addWidget(autoBox)

        # Set alignment for both boxes
        self.manBoxLayout.setAlignment(Qt.AlignTop)
        self.autoBoxLayout.setAlignment(Qt.AlignTop)
        
        # Set button actions
        manSelButton.clicked.connect(self.open_manual)
        autoSelButton.clicked.connect(self.open_automatic)

        # Optimize button
        optButton = QPushButton("Optimize")
        optButton.clicked.connect(self.optimize)
        layout.addWidget(optButton)

        # Results section
        resultBox = QGroupBox("Results")
        self.resultLayout = QVBoxLayout()
        resultBox.setLayout(self.resultLayout)
        layout.addWidget(resultBox)
    
    def open_manual(self):
        """
        Open manually traced CSV file.
        """
        dialog = QFileDialog()
        # Only allow 1+ existing files
        dialog.setFileMode(QFileDialog.ExistingFile)
        # Data is a tuple of ([paths], file_type)
        data = dialog.getOpenFileName(self, "Open data", filter="CSV file (*.csv)")
        if len(data[0]) == 0:
            return
        # Erase previous data, if any
        erase_layout_widgets(self.manBoxLayout)
        # Manfile dict entry -> feature list -> ['x'],['y'],['matched'],['avgx'],['avgy']
        self.manFiles = {}
        with open(data[0]) as csvfile:
            reader = csv.reader(csvfile)
            f_num = None
            features = []
            feature = {
                'x' : [],
                'y' : []
            }
            for row in reader:
                # If we're on the same feature, continue adding to it
                if f_num == int(row[0]):
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
                    f_num = int(row[0])
            # Calculate coordinate averages
            for feature in features:
                feature['avgx'] = np.mean(feature['x'])
                feature['avgy'] = np.mean(feature['y'])
                feature['matched'] = False
            self.manFiles[data[0]] = features
        self.manBoxLayout.addWidget(QLabel(os.path.basename(data[0])))

    def open_automatic(self):
        """
        Open automatically traced CSV files.
        """
        dialog = QFileDialog()
        # Only allow 1+ existing files
        dialog.setFileMode(QFileDialog.ExistingFiles)
        # Data is a tuple of ([paths], file_type)
        data = dialog.getOpenFileNames(self, "Open data", filter="CSV file (*.csv)")
        if len(data[0]) == 0:
            return
        # Erase previous data, if any
        erase_layout_widgets(self.autoBoxLayout)
        # Autofile dict entry -> feature list -> ['x'],['y'],['matched'],['avgx'],['avgy']
        self.autoFiles = {}
        for path in data[0]:
            with open(path) as csvfile:
                reader = csv.reader(csvfile)
                f_num = None
                features = []
                feature = {
                    'x' : [],
                    'y' : []
                }
                for row in reader:
                    # If we're on the same feature, continue adding to it
                    if f_num == int(row[0]):
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
                        f_num = int(row[0])
                # Calculate coordinate averages
                for feature in features:
                    feature['avgx'] = np.mean(feature['x'])
                    feature['avgy'] = np.mean(feature['y'])
                    feature['matched'] = False
                self.autoFiles[path] = features
            self.autoBoxLayout.addWidget(QLabel(os.path.basename(path)))

    def optimize(self):
        """
        Compare the automatic and manual measurements,
        and set resultBox to a list of the "best matched"
        measurements.
        """
        erase_layout_widgets(self.resultLayout)
        for manFile in self.manFiles.keys():
            for autoFile in self.autoFiles.keys():
                # Iterate through manual features
                for mf in self.manFiles[manFile]:
                    # Reset matches
                    mf['matched'] = False
                    closest_match = None
                    closest_distance = np.Infinity
                    # Iterate over all auto features. Look for closest match.
                    for af in self.autoFiles[autoFile]:
                        if not af['matched']:
                            mf_avgc = np.array([mf['avgx'], mf['avgy']])
                            af_avgc = np.array([af['avgx'], af['avgy']])
                            dist = np.linalg.norm(np.abs(mf_avgc-af_avgc))
                            # Check if distance between two lines is within the threshold, and closest
                            if dist <= MAX_DISTANCE and dist < closest_distance:
                                closest_match = af
                                closest_distance = dist
                    if closest_match is not None:
                        ind = self.autoFiles[autoFile].index(closest_match)
                        self.autoFiles[autoFile][ind]['matched'] = True
                        mf['matched'] = True
                if PLOT_MATCHES:
                    for mf in self.manFiles[manFile]:
                        if mf['matched']:
                            plt.plot(mf['x'], mf['y'], color='green')
                        else:
                            plt.plot(mf['x'], mf['y'], color='red')
                    for af in self.autoFiles[autoFile]:
                        if af['matched']:
                            plt.plot(af['x'], af['y'], color='blue')
                        else:
                            plt.plot(af['x'], af['y'], color='orange')
                    plt.show()
                # Calculate matched percentages
                mf_count = len(self.manFiles[manFile])
                mf_matched = 0
                for mf in self.manFiles[manFile]:
                    if mf['matched']:
                        mf_matched+=1
                af_count = len(self.autoFiles[autoFile])
                af_matched = 0
                for af in self.autoFiles[autoFile]:
                    if af['matched']:
                        af_matched+=1
                mf_percentage = (mf_matched/mf_count)*100
                af_percentage = (af_matched/af_count)*100
                print(af_matched, af_count)
                print(mf_matched, mf_count)

                # Add the results to the resultBox
                self.resultLayout.addWidget(
                    QLabel(
                            os.path.basename(autoFile)+' | M: {:.2f}% | A: {:.2f}%'.format(mf_percentage, af_percentage)
                        ))