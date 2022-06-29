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
from tracing.tracing import AutoTracingOCCULT
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

        # Add "Automatic" and "Manual" tabs
        tabs = QTabWidget()
        self.autoTab = AutoTab()
        self.autoTab.occult.set_mpl(self.canvas, self.ax)
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
            self.ax.cla()
            self.ax.imshow(f[0].data, origin="lower")
            self.autoTab.occult.update_buttons(image_path, f[0].data)
            self.canvas.draw()

class AutoTab(QWidget):
    def __init__(self):
        """
        Widget which contains the automatic tracing group.
        """
        super().__init__()

        layout = QVBoxLayout(self)

        options = ["OCCULT-2"]

        # Menu to select tracing type
        menu = QComboBox()
        menu.addItems(options)
        layout.addWidget(menu)

        # Since our default is for OCCULT-2, add the OCCULTParams box
        self.occult = OCCULTParams()
        layout.addWidget(self.occult)

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
        self.lmin.setPlaceholderText("45")
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
        layout.addWidget(plotConfig)

        # Add horizontal button group
        buttonLayout = QHBoxLayout()

        # Add button to run the trace and to save the data
        self.traceButton = QPushButton("Trace")
        self.saveButton = QPushButton("Save")

        # Disable buttons until enabled by functions
        self.traceButton.setEnabled(False)
        self.saveButton.setEnabled(False)

        # Button configuration
        self.traceButton.clicked.connect(self.run_occult)
        self.saveButton.clicked.connect(self.save_results)
        
        # Add buttons to layout
        buttonLayout.addWidget(self.traceButton)
        buttonLayout.addWidget(self.saveButton)

        # Add sub-layout to params layout
        layout.addLayout(buttonLayout)

    def update_buttons(self, image_path, image_data):
        """
        Enable some elements if the image path becomes valid.
        """
        if image_path == None:
            self.traceButton.setEnabled(False)
            self.cmapBox.setEnabled(False)
        else:
            self.traceButton.setEnabled(True)
            self.cmapBox.setEnabled(True)

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
        color = self.colorPicker.getColor()

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
            self.ax.plot(x,y, color=self.pcolor)

        # Refresh the canvas
        self.ax.draw_artist(self.ax.patch)
        self.canvas.update()
        self.canvas.flush_events()
        self.canvas.draw()

        # Enable the save & color buttons
        self.saveButton.setEnabled(True)

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