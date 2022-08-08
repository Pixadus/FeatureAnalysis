#!/usr/bin/python3
# -*- coding: utf-8 -*-
"""
Created on Tue 7.12.22
@title: Preprocessing GUI components
@author: Parker Lamb
@description: Contains Qt6 widgets for preprocessing
scientific images.
"""

from PySide6.QtGui import QPalette
from PySide6.QtWidgets import (QComboBox, QFileDialog, QFormLayout, QGroupBox, QHBoxLayout, QLabel, QLineEdit, QPushButton, QVBoxLayout, QWidget)
from matplotlib import (colors, pyplot)
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg
from astropy.io import fits
from preprocessing import processing

class PreprocessWidget(QWidget):
    def __init__(self):
        """
        Container widget for the preprocessing
        tab.
        """
        super().__init__()

        # Global layout
        layout = QVBoxLayout(self)

        # Image layout
        imgLayout = QHBoxLayout()
        layout.addLayout(imgLayout)

        # Create the images
        self.baseimg = self.MPLImage("Base image")
        self.procimg = self.MPLImage("Processed image")
        imgLayout.addWidget(self.baseimg)
        imgLayout.addWidget(QLabel("→"))
        imgLayout.addWidget(self.procimg)

        # Add a controls area
        controlsBox = QGroupBox("Controls")
        controlsLayout = QHBoxLayout()
        controlsBox.setLayout(controlsLayout)
        layout.addWidget(controlsBox)

        # Add an 'open image' button
        openButton = QPushButton("Open image")
        openButton.clicked.connect(self.open_image)
        controlsLayout.addWidget(openButton)

        # Add an algorithm box
        algBox = QGroupBox("Processing algorithm")
        algLayout = QVBoxLayout()
        algBox.setLayout(algLayout)
        controlsLayout.addWidget(algBox)

        # Processing options
        self.options = {
            "Gaussian smoothing" : self.GSParams(),
            "Sharpening" : self.SharpParams(),
            "Rolling hough transform" : self.RHTParams()
            }

        # Add a processing algorithm selector
        self.procAlg = QComboBox()
        self.procAlg.addItems([o for o in self.options.keys()])
        self.currentOpt = self.procAlg.currentText()
        algLayout.addWidget(self.procAlg)

        # Add a processing alg settings box
        procOpts = QGroupBox("Algorithm options")
        self.procLayout = QVBoxLayout()
        procOpts.setLayout(self.procLayout)
        controlsLayout.addWidget(procOpts)

        # Add widgets and hide them
        for opt in self.options.keys():
            self.procLayout.addWidget(self.options[opt])
            self.options[opt].setVisible(False)
        
        # Show the current selection
        self.alg_index_changed()

        # Add an event manager for when the combobox changes
        self.procAlg.currentIndexChanged.connect(self.alg_index_changed)

        # Add control buttons
        procButton = QPushButton("Process")
        saveButton = QPushButton("Save")
        btnLayout = QVBoxLayout()
        controlsLayout.addLayout(btnLayout)
        btnLayout.addWidget(procButton)
        btnLayout.addWidget(saveButton)

        # Add event listeners to the buttons
        procButton.clicked.connect(self.process)
        saveButton.clicked.connect(self.save_results)

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
            self.img_orig = f[0].data
            self.baseimg.set_image(self.img_orig)
            self.procimg.set_image(self.img_orig)
        except:
            print("Error opening image.")
            return
        
        self.reset_changes()
    
    def save_results(self):
        """
        Save the new data.
        """
        dialog = QFileDialog()
        # We're saving a file, not opening here
        dialog.setAcceptMode(QFileDialog.AcceptSave)
        dialog.setFileMode(QFileDialog.AnyFile)
        # Returned path is a tuple of (path, file_type)
        save_path = dialog.getSaveFileName(self, "Save results", filter="FITS file (*.fits)")[0]
        # Save the data as a .FITS file
        hdu = fits.PrimaryHDU(self.img_alt)
        hdu.writeto(save_path)
    
    def reset_changes(self):
        """
        Reset the image back to the original.
        """
        self.procimg.ax.cla()
        self.procimg.ax.imshow(self.img_orig, origin="lower")
        # Refresh the canvas
        self.procimg.ax.draw_artist(self.procimg.ax.patch)
        self.procimg.canvas.update()
        self.procimg.canvas.flush_events()
        self.procimg.canvas.draw()
        self.img_alt = self.img_orig

    def alg_index_changed(self):
        """
        Functions when the selected algorithm is changed.
        """
        self.options[self.currentOpt].setVisible(False)
        self.currentOpt = self.procAlg.currentText()
        self.options[self.currentOpt].setVisible(True)

    def process(self):
        """
        Process the image using the selected algorithm.
        """
        # Create a dictionary of functions
        opt_fn = {
            "Gaussian smoothing" : processing.gaussian_smoothing,
            "Sharpening" : processing.sharpen,
            "Rolling hough transform" : processing.rolling_hough_transform
        }
        params = self.options[self.currentOpt].get_params()

        # Run the associated processing function
        self.img_alt = opt_fn[self.currentOpt](self.img_alt, params)

        # set the image
        self.procimg.set_image(self.img_alt)

    class MPLImage(QWidget):
        def __init__(self, title=''):
            """
            Custom class for the base image.
            """
            super().__init__()

            # Create the layout for the image
            layout = QVBoxLayout(self)

            # Add a title widget
            self.title = QLabel(title)
            layout.addWidget(self.title)

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
        
        def set_title(self, title):
            """
            Sets the title of the MPLImage.

            Parameters
            ----------
            title : str
            """
            self.title.setText(str(title))

        def set_image(self, img):
            """
            Set the axes to the image and refresh canvas.

            Parameters
            ----------
            img : ndarray
            """
            self.ax.cla()
            self.ax.imshow(img, origin="lower")
            # Refresh the canvas
            self.ax.draw_artist(self.ax.patch)
            self.canvas.update()
            self.canvas.flush_events()
            self.canvas.draw()
    
    class GSParams(QWidget):
        def __init__(self):
            """
            Gaussian smoothing params.
            """
            super().__init__()

            # Set layout
            layout = QFormLayout(self)

            # Create params
            self.sigmaEdit = QLineEdit()
            self.sigmaEdit.setPlaceholderText("5")
            modes = ['reflect','constant','nearest','mirror','wrap']
            self.modesEdit = QComboBox()
            self.modesEdit.addItems(modes)
            
            # Add params to layout
            layout.insertRow(0, "Sigma:", self.sigmaEdit)
            layout.insertRow(1, "Modes:", self.modesEdit)

        def get_params(self):
            """
            Return the parameters of the box.

            Returns
            -------
            params : list
            """
            # Set the placeholder text to the actual text if run without an entry
            for param in [self.sigmaEdit]:
                if len(param.text()) == 0:
                    param.setText(param.placeholderText())

            sigma = self.sigmaEdit.text()
            mode = self.modesEdit.currentText()

            return([
                sigma,
                mode
                ])

    class SharpParams(QWidget):
        def __init__(self):
            """
            Sharpening params.
            """
            super().__init__()

            # Set layout
            layout = QFormLayout(self)

            # Create params
            self.kernelEdit = QLineEdit()
            self.kernelEdit.setPlaceholderText("5,5")
            self.sigmaEdit = QLineEdit()
            self.sigmaEdit.setPlaceholderText("1.0")
            self.amountEdit = QLineEdit()
            self.amountEdit.setPlaceholderText("1.0")
            self.threshEdit = QLineEdit()
            self.threshEdit.setPlaceholderText("0")
            
            # Add params to layout
            layout.insertRow(0, "Kernel size:", self.kernelEdit)
            layout.insertRow(1, "Sigma:", self.sigmaEdit)
            layout.insertRow(2, "Amount:", self.amountEdit)
            layout.insertRow(3, "Threshold:", self.threshEdit)

        def get_params(self):
            """
            Return the parameters of the box.

            Returns
            -------
            params : list
            """
            # Set the placeholder text to the actual text if run without an entry
            for param in [self.kernelEdit, self.sigmaEdit, self.amountEdit, self.threshEdit]:
                if len(param.text()) == 0:
                    param.setText(param.placeholderText())

            kern = self.kernelEdit.text()
            kern = tuple([int(k) for k in kern.split(",")])
            sigma = self.sigmaEdit.text()
            amount = self.amountEdit.text()
            thresh = self.threshEdit.text()

            return([
                kern,
                sigma,
                amount,
                thresh
                ])

    class RHTParams(QWidget):
        def __init__(self):
            """
            Rolling Hough Transform parameters.
            """
            super().__init__()

            # Set layout
            layout = QFormLayout(self)

            # Create params
            self.wlenEdit = QLineEdit()
            self.wlenEdit.setPlaceholderText("55")
            self.wlenEdit.setToolTip("Must be an odd number.")
            self.smrEdit = QLineEdit()
            self.smrEdit.setPlaceholderText("4")
            self.fracEdit = QLineEdit()
            self.fracEdit.setPlaceholderText("0.7")
            
            # Add params to layout
            layout.insertRow(0, "Min. length:", self.wlenEdit)
            layout.insertRow(1, "Smoothing radius:", self.smrEdit)
            layout.insertRow(2, "Int. threshold:", self.fracEdit)

        def get_params(self):
            """
            Return the parameters of the box.

            Returns
            -------
            params : list
            """
            # Set the placeholder text to the actual text if run without an entry
            for param in [self.wlenEdit, self.smrEdit, self.fracEdit]:
                if len(param.text()) == 0:
                    param.setText(param.placeholderText())

            wlen = int(self.wlenEdit.text())
            smr = int(self.smrEdit.text())
            frac = float(self.fracEdit.text())

            return([
                wlen,
                smr,
                frac
                ])