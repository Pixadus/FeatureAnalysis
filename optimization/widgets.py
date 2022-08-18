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
from optimization.functions import (get_tracing_data, get_matches_avg_center, get_matches_avg_line, interpolate)
import numpy as np
import matplotlib.pyplot as plt
import os

# Constants
MAX_DISTANCE = 30.0
PLOT_MATCHES = False

# It's worth working on this more - i.e. check length matches.

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
        self.manFiles = get_tracing_data([data[0]])
        # Interpolate per-pixel coordinates. 
        for manFile in self.manFiles.keys():
            for man_line in self.manFiles[manFile]:
                if len(man_line['x']) >= 2 and len(man_line['y']) >= 2:
                    man_line['x'], man_line['y'] = interpolate(man_line['x'], man_line['y'])
                    man_line['avgx'] = np.mean(man_line['x'])
                    man_line['avgy'] = np.mean(man_line['y'])
        for path in self.manFiles.keys():
            self.manBoxLayout.addWidget(QLabel(os.path.basename(path)))

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
        self.autoFiles = get_tracing_data(data[0])
        for path in self.autoFiles.keys():
            self.autoBoxLayout.addWidget(QLabel(os.path.basename(path)))

    def optimize(self):
        """
        Compare the automatic and manual measurements,
        and set resultBox to a list of the "best matched"
        measurements.
        """
        erase_layout_widgets(self.resultLayout)
        self.manFiles, self.autoFiles = get_matches_avg_center(self.manFiles, self.autoFiles, 30.0)
        manFiles, autoFiles = get_matches_avg_line(self.manFiles, self.autoFiles, 30.0)
        for manFile in self.manFiles:
            for autoFile in self.autoFiles:
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
                self.resultLayout.addWidget(QLabel(
                            os.path.basename(autoFile)+' | M: {:.2f}% | A: {:.2f}%'.format(mf_percentage, af_percentage)
                        ))
    