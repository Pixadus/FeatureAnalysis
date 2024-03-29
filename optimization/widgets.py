#!/usr/bin/python3
# -*- coding: utf-8 -*-
"""
Created on Tue 8.9.22
@title: Optimization GUI components
@author: Parker Lamb
@description: Contains Qt6 widgets for optimizing
parameter sets compared to manual tracing.
"""

from pickletools import optimize
from PySide6.QtWidgets import (QWidget, QHBoxLayout, QGroupBox,
                            QPushButton, QVBoxLayout, QFileDialog,
                            QLabel, QScrollArea, QSizePolicy)
from PySide6.QtCore import Qt, QSize, QRunnable, QThreadPool, Slot
from helper.functions import erase_layout_widgets
from optimization.functions import (get_tracing_data, get_matches_avg_center, interpolate)
import numpy as np
import matplotlib.pyplot as plt
import os

# Constants
MAX_DISTANCE = 30.0
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

        # Create a threadpool
        self.threadpool = QThreadPool()

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

        # Create a scroll area for the autoBox
        autoScroll = QScrollArea()
        autoScroll.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOn)
        autoScroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        autoScroll.setWidgetResizable(True)
        autoScroll.setWidget(autoBox)
        autoLayout.addWidget(autoScroll)

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
        resultBox.setMinimumSize(QSize(150,150))
        resultBox.setSizePolicy(QSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding))
        self.resultLayout = QVBoxLayout()
        self.resultLayout.setAlignment(Qt.AlignTop)
        resultBox.setLayout(self.resultLayout)

        # Create a scroll area for the autoBox
        resultScroll = QScrollArea()
        resultScroll.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOn)
        resultScroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOn)
        resultScroll.setWidgetResizable(True)
        resultScroll.setWidget(resultBox)
        layout.addWidget(resultScroll)
    
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
        for manFile in self.manFiles.keys():
            n=0
            results = {}
            for autoFile in self.autoFiles.keys():
                n += 1
                self.manFiles[manFile], self.autoFiles[autoFile] = get_matches_avg_center(
                    self.manFiles[manFile], 
                    self.autoFiles[autoFile], 
                    30.0)
                if PLOT_MATCHES:
                    for mf in self.manFiles[manFile]:
                        if mf['matched']:
                            plt.plot(mf['x'], mf['y'], color='cyan', label="Matched manual")
                        else:
                            plt.plot(mf['x'], mf['y'], color='darkblue', label="Unmatched manual")
                    for af in self.autoFiles[autoFile]:
                        if af['matched']:
                            plt.plot(af['x'], af['y'], color='lime', label="Matched automatic")
                        else:
                            plt.plot(af['x'], af['y'], color='darkgreen', label="Unmatched automatic")
                    # Make sure labels are unique
                    handles, labels = plt.gca().get_legend_handles_labels()
                    dict_of_labels = dict(zip(labels, handles))
                    plt.legend(dict_of_labels.values(), dict_of_labels.keys())
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
            
                # Store the results to be sorted
                results[os.path.basename(autoFile)] = [mf_percentage, af_percentage]

            # Sort the results by manual for now
            result_temp = sorted(results.items(), key=lambda file : sum(file[1]), reverse=True)

            # Add the results to the resultBox
            for result in result_temp:
                self.resultLayout.addWidget(QLabel(
                            result[0]+' | M: {:.2f}% | A: {:.2f}%'.format(result[1][0], result[1][1])
                        ))

class OptimizeWorker(QRunnable):
    def __init__(self, manFile, autoFile, maxDist, afmf):
        """
        """
        super().__init__()

        self.manFile = manFile
        self.autoFile = autoFile
        self.maxDist = maxDist
        self.afmf = afmf

    @Slot()
    def run(self):
        """
        Optimize a single file.
        """
        manFile, autoFile = get_matches_avg_center(self.manFile, self.autoFile, self.maxDist)
        self.afmf.append([manFile, autoFile])