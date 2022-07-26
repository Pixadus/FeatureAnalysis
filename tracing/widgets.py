#!/usr/bin/python3
# -*- coding: utf-8 -*-
"""
Created on Tue 6.28.22
@title: Tracing GUI Components
@author: Parker Lamb
@description: Contains Qt6 widgets for automatically and manually tracing
curvilinear features.
"""

from PySide6.QtGui import QPalette
from PySide6.QtWidgets import (QColorDialog, QComboBox, QFileDialog, 
                            QFormLayout, QGroupBox, QHBoxLayout, 
                            QLabel, QLineEdit, QPushButton,
                            QTabWidget, QVBoxLayout, QWidget)
from astropy.io import fits
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg
from matplotlib import (pyplot, colors)
from tracing.tracing import (AutoTracingOCCULT)
import csv

class TracingWidget(QWidget):
    def __init__(self):
        """
        Container widget used when the "Tracing" tab
        is selected.
        """
        super().__init__()

        # Layout for the whole tab window
        layout = QHBoxLayout(self)
        
        # Add matplotlib canvas to layout
        self.figure = pyplot.figure()
        self.ax = self.figure.add_axes([0,0,1,1])
        self.canvas = FigureCanvasQTAgg(self.figure)
        layout.addWidget(self.canvas)

        # Set the background color of the canvas
        win_color = self.palette().color(QPalette.Window).getRgbF()
        plot_color = colors.rgb2hex(win_color)
        self.figure.set_facecolor(plot_color)

        # Hide the axes
        self.ax.get_xaxis().set_visible(False)
        self.ax.get_yaxis().set_visible(False)

        # Layout for the vertical bar on the right
        controlLayout = QVBoxLayout()

        # Button to open an image
        openButton = QPushButton("Open image")
        openButton.clicked.connect(self.open_image)
        controlLayout.addWidget(openButton)

        # Add plot configuration box
        plotConfig = QGroupBox()
        plotConfigLayout = QFormLayout()
        plotConfig.setLayout(plotConfigLayout)
        plotConfig.setTitle("Plot Config")

        # Add color map configuration
        cmaps = ['viridis', 'gray', 'inferno']
        self.cmapBox = QComboBox()
        self.cmapBox.addItems(cmaps)
        plotConfigLayout.addRow(QLabel("Color map:"), self.cmapBox)

        # Whenever a new cmap is selected, update it in the plot
        self.cmapBox.currentIndexChanged.connect(self.set_cmap)

        # Disable cmapBox until enabled after trace
        self.cmapBox.setEnabled(False)

        # Add plot color configuration
        self.colorPicker = QColorDialog()
        self.colorButton = QPushButton("Select")
        self.colorButton.clicked.connect(self.set_color)
        plotConfigLayout.addRow(QLabel("Line color:"), self.colorButton)

        # Add plot config box to OCCULT box
        controlLayout.addWidget(plotConfig)

        # Add "Automatic" and "Manual" tabs
        tabs = QTabWidget()
        self.autoTab = AutoTab()
        for pset in self.autoTab.options.keys():
            self.autoTab.options[pset].set_mpl(self.canvas, self.ax)
        tabs.setDocumentMode(True)
        tabs.addTab(self.autoTab, "Automatic")
        controlLayout.addWidget(tabs)

        layout.addLayout(controlLayout)
    
    def open_image(self):
        """
        Open a file browser and select an image.
        """
        dialog = QFileDialog()
        # Only allow single, existing files
        dialog.setFileMode(QFileDialog.ExistingFile)
        # Image is a tuple of (path, file_type)
        image_path = dialog.getOpenFileName(self, "Open image", filter="FITS file (*.fits)")[0]
        # Test if file is a FITS file
        if ".fits" in image_path:
            f = fits.open(image_path, ignore_missing_end=True)
            self.image_data = f[0].data
            self.ax.cla()
            self.ax.imshow(self.image_data, origin="lower")
            for opt in self.autoTab.options.keys():
                self.autoTab.options[opt].update_buttons(image_path, self.image_data)
            self.canvas.draw()

        # Try to enable color map
        if image_path == '':
            self.cmapBox.setEnabled(False)
        else:
            self.cmapBox.setEnabled(True)
    
    def set_cmap(self):
        """
        Set the colormap for the figure
        """
        self.ax.imshow(self.image_data, origin="lower", cmap=self.cmapBox.currentText())

        # Redraw everything
        self.ax.draw_artist(self.ax.patch)
        self.canvas.update()
        self.canvas.flush_events()
        self.canvas.draw()
    
    def set_color(self):
        """
        Sets the color of the current plot.
        """
        color = self.colorPicker.getColor(options=QColorDialog.ShowAlphaChannel)

        try:
            self.pcolor = tuple(c/255 for c in color.toTuple())
        except:
            return

        for line in self.ax.get_lines():
            line.set_color(self.pcolor)

        # Redraw everything
        self.ax.draw_artist(self.ax.patch)
        self.canvas.update()
        self.canvas.flush_events()
        self.canvas.draw()

class AutoTab(QWidget):
    def __init__(self):
        """
        Widget which contains the automatic tracing group.
        """
        super().__init__()

        layout = QVBoxLayout(self)

        self.options = {
            "OCCULT-2" : OCCULTParams()
            }

        # Menu to select tracing type
        self.menu = QComboBox()
        self.menu.addItems([o for o in self.options.keys()])
        layout.addWidget(self.menu)

        # Since our default is for OCCULT-2, add the OCCULTParams box
        for opt in self.options.keys():
            layout.addWidget(self.options[opt])
            self.options[opt].setVisible(False)
        
        # Create the onchange event for the params dropdown
        self.menu.currentIndexChanged.connect(self.set_param_visibility)

        # Set the current params box
        self.set_param_visibility()
    
    def set_param_visibility(self):
        """
        Show the parameters of the currently selected tracer.
        """
        # Hide all other parameter sets
        for opt in self.options.keys():
            self.options[opt].setVisible(False)
        
        # Set the seleted parameter set to visible
        self.options[self.menu.currentText()].setVisible(True)

class OCCULTParams(QWidget):
    def __init__(self):
        """
        Parameters & buttons used when OCCULT-2 is selected.
        """
        super().__init__()

        # Initial variable values
        self.image_path = None
        self.canvas = None
        self.ax = None
        self.results = None
        self.pcolor = (0,0,1,1)

        # Layout for the section
        layout = QVBoxLayout(self)

        # Parameters setup
        params = QGroupBox()
        paramsLayout = QFormLayout()
        paramsLayout.setFieldGrowthPolicy(QFormLayout.ExpandingFieldsGrow)
        params.setTitle("Parameters")
        params.setLayout(paramsLayout)

        # Parameters
        self.nsm1 = QLineEdit()
        self.nsm1.setMinimumWidth(40)
        self.nsm1.setPlaceholderText("4")
        self.rmin = QLineEdit()
        self.rmin.setPlaceholderText("45")
        self.lmin = QLineEdit()
        self.lmin.setPlaceholderText("35")
        self.nstruc = QLineEdit()
        self.nstruc.setPlaceholderText("2000")
        self.ngap = QLineEdit()
        self.ngap.setPlaceholderText("1")
        self.qthresh1 = QLineEdit()
        self.qthresh1.setPlaceholderText("0.0")
        self.qthresh2 = QLineEdit()
        self.qthresh2.setPlaceholderText("3.0")

        # Set rows for parameter box
        paramsLayout.addRow(QLabel("NSM1:"), self.nsm1)
        paramsLayout.addRow(QLabel("RMIN:"), self.rmin)
        paramsLayout.addRow(QLabel("LMIN:"), self.lmin)
        paramsLayout.addRow(QLabel("NSTRUC:"), self.nstruc)
        paramsLayout.addRow(QLabel("NGAP:"), self.ngap)
        paramsLayout.addRow(QLabel("QTHRESH1:"), self.qthresh1)
        paramsLayout.addRow(QLabel("QTHRESH2:"), self.qthresh2)

        # Add parameters box to global box
        layout.addWidget(params)

        # Add horizontal button group
        buttonLayout = QHBoxLayout()

        # Add button to save, trace and analyze the data
        self.traceButton = QPushButton("Trace")
        self.saveButton = QPushButton("Save")
        self.analyzeButton = QPushButton("Analyze")

        # Disable buttons until enabled by functions
        self.traceButton.setEnabled(False)
        self.saveButton.setEnabled(False)
        self.analyzeButton.setEnabled(False)

        # Button configuration
        self.traceButton.clicked.connect(self.run_occult)
        self.saveButton.clicked.connect(self.save_results)
        self.analyzeButton.clicked.connect(self.analyze_results)
        
        # Add buttons to layout
        layout.addWidget(self.traceButton)
        buttonLayout.addWidget(self.analyzeButton)
        buttonLayout.addWidget(self.saveButton)

        # Add sub-layout to params layout
        layout.addLayout(buttonLayout)

    def update_buttons(self, image_path, image_data):
        """
        Enable some elements if the image path becomes valid.
        """
        if image_path == None:
            self.traceButton.setEnabled(False)
        else:
            self.traceButton.setEnabled(True)

        self.image_path = image_path
        self.image_data = image_data

    def set_mpl(self, canvas, ax):
        """
        Update the local canvas & axes

        Parameters
        ----------
        canvas : FigureCanvasQTAgg
            This function is only meant to be run internally
        ax : Figure.Axes
            This function is only meant to be run internally
        """
        self.canvas = canvas
        self.ax = ax
    
    def set_at(self, analysis, tabs):
        """
        Set the analysis and tab widgets from main.py.

        Parameters
        ----------
        analysis : AnalysisWidget
            Necessary to set plot data on the analysis tab.
        tabs : QTabWidget
            Necessary to swap tabs.
        """
        self.analysis = analysis
        self.tabs = tabs

    def run_occult(self):
        """
        Run OCCULT-2 using paramers attached to self.
        """
        params = [self.nsm1, self.rmin, self.lmin, self.nstruc, self.ngap, self.qthresh1, self.qthresh2]

        # Set the placeholder text to the actual text if run without an entry
        for param in params:
            if len(param.text()) == 0:
                param.setText(param.placeholderText())

        # Create an AutoTracingOCCULT instance
        at = AutoTracingOCCULT(self.image_path)

        # Run OCCULT-2
        self.results = at.run(
            int(self.nsm1.displayText()),
            int(self.rmin.text()),
            int(self.lmin.text()),
            int(self.nstruc.text()),
            int(self.ngap.text()),
            float(self.qthresh1.text()),
            float(self.qthresh2.text())
        )

        # Clear the current axes from previous results
        self.ax.cla()

        # Reset the image, since it's cleared with cla()
        self.ax.imshow(self.image_data, origin="lower")

        # Plot the results
        for result in self.results:
            x = []
            y = []
            for coord in result:
                x.append(coord[0])
                y.append(coord[1])
            self.ax.plot(x,y, color=self.pcolor, linewidth=0.5)

        # Refresh the canvas
        self.ax.draw_artist(self.ax.patch)
        self.canvas.update()
        self.canvas.flush_events()
        self.canvas.draw()

        # Enable the save & color buttons
        self.saveButton.setEnabled(True)
        self.analyzeButton.setEnabled(True)

    def save_results(self):
        """
        Save the feature trace results.
        """
        dialog = QFileDialog()
        # We're saving a file, not opening here
        dialog.setAcceptMode(QFileDialog.AcceptSave)
        dialog.setFileMode(QFileDialog.AnyFile)
        # Returned path is a tuple of (path, file_type)
        save_path = dialog.getSaveFileName(self, "Save results", filter="CSV file (*.csv)")[0]
        
        # Save format will be { feature_id, x, y }
        f_count = 0
        with open(save_path, 'w') as outfile:
            resultwriter = csv.writer(outfile)
            for result in self.results:
                f_count+=1
                for coord in result:
                        # TODO verify this is x,y and not y,x
                        resultwriter.writerow([f_count, coord[0], coord[1]])

    def analyze_results(self):
        """
        Send the features over to analysis and switch tabs.
        """
        # Switch to the analysis tab
        self.tabs.setCurrentWidget(self.analysis)

        # Set the image
        self.analysis.open_image([self.image_data])

        # Open the data in analysis
        self.analysis.open_data(self.results)