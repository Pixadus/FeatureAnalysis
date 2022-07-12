#!/usr/bin/python3
# -*- coding: utf-8 -*-
"""
Created on Wed 6.29.22
@title: Helper function GUI components
@author: Parker Lamb
@description: Contains Qt6 widgets to act as helper
functions for the feature tracing program. 
"""

from PySide6.QtGui import QPalette
from PySide6.QtWidgets import (QCheckBox, QFileDialog, QFormLayout, QLabel, QLineEdit, QGroupBox, QHBoxLayout, QPushButton, QVBoxLayout, QWidget)
from scipy.io import readsav
from skimage.transform import rotate
from skimage.util import img_as_float64
from astropy.io import fits
from matplotlib import pyplot, colors
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg
import numpy as np

class HelperWidget(QWidget):
    def __init__(self):
        """
        Container widget used when the "Helper
        functions" tab is selected.
        """
        super().__init__()

        # Grand layout
        layout = QHBoxLayout(self)

        # Helper functions box
        hfBox = QGroupBox()
        hfBox.setTitle("Helper functions")
        hfLayout = QVBoxLayout()
        hfBox.setLayout(hfLayout)
        layout.addWidget(hfBox)

        # Function buttons
        sfButton = QPushButton("Convert .sav to .fits")
        sfButton.clicked.connect(lambda: self.toggle_widget(self.sfw))
        hfLayout.addWidget(sfButton)

        efButton = QPushButton("Edit .FITS file")
        efButton.clicked.connect(lambda: self.toggle_widget(self.efw))
        hfLayout.addWidget(efButton)

        # Add the helper widgets
        self.sfw = SFWidget()
        self.efw = EditFITSWidget()
        layout.addWidget(self.sfw)
        layout.addWidget(self.efw)

        # Hide helper widgets initially
        self.efw.setVisible(False)
        self.sfw.setVisible(False)

    def toggle_widget(self, widget):
        """
        Function to toggle widget to be visble.
        """
        if widget.isVisible():
            widget.setVisible(False)
        else:
            widget.setVisible(True)

class SFWidget(QWidget):
    def __init__(self):
        """
        IDL .sav to .fits parameters widget. 
        """
        super().__init__()

        # Initiate variables
        self.sav = None

        # Set layout
        layout = QVBoxLayout(self)

        # Button to select the sav file containing images
        selectSav = QPushButton("Select .sav file")
        selectSav.clicked.connect(self.open_sav)
        layout.addWidget(selectSav)

        # List of entries within the .sav
        sBox = QGroupBox()
        sBox.setTitle(".sav contents to convert")
        self.sLayout = QVBoxLayout()
        sBox.setLayout(self.sLayout)
        layout.addWidget(sBox)

        # Add a "Convert" button
        self.convButton = QPushButton("Convert selections to .FITS")
        self.convButton.clicked.connect(self.conv_to_fits)
        layout.addWidget(self.convButton)

        # Disable convButton by default
        self.convButton.setEnabled(False)

    def open_sav(self):
        """
        Open a file browser and select a sav file.
        """
        dialog = QFileDialog()
        # Only allow single, existing files
        dialog.setFileMode(QFileDialog.ExistingFile)
        # Image is a tuple of (path, file_type)
        sav_path = dialog.getOpenFileName(
            self, 
            "Open IDL sav", 
            filter="IDL SAV file (*.sav)"
            )[0]

        if len(sav_path) == 0:
            return

        # Overwrite previous .sav entries (if any)
        for i in reversed(range(self.sLayout.count())):
            self.sLayout.itemAt(i).widget().setParent(None)

        # Get sav data in dictionary format
        self.sav = readsav(sav_path)
        
        # Iterate over .sav keys, add checkboxes
        for entry in self.sav.keys():
            eCheckbox = QCheckBox(entry)
            eCheckbox.stateChanged.connect(self.set_convert_button)
            self.sLayout.addWidget(eCheckbox)

        # Disable convertButton
        self.convButton.setEnabled(False)
    
    def set_convert_button(self):
        """
        Enables the convert button if any checkbox is checked
        """
        enabled = False

        # Iterate over all checkboxes, and check their state.
        for i in range(self.sLayout.count()):
            if self.sLayout.itemAt(i).widget().checkState():
                enabled = True
        
        # Set the "Convert" button state
        self.convButton.setEnabled(enabled)
    
    def conv_to_fits(self):
        """
        Open a file dialog to determine save location.

        Then, iterate over all checkboxes. If checked, convert
        corresponding IDL save entity to a .fits file.
        """
        dialog = QFileDialog()
        # We're saving a file, not opening here
        dialog.setAcceptMode(QFileDialog.AcceptSave)
        # Only allow directories to be selected
        dialog.setFileMode(QFileDialog.Directory)
        # Returned path is a tuple of (path, file_type)
        save_path = dialog.getExistingDirectory(self, "Select directory to save .fits in")

        # Do nothing if the folder was not selected
        if len(save_path) == 0:
            return

        # Iterate over entities, convert to .fits and save in save_path
        for i in range(self.sLayout.count()):
            if self.sLayout.itemAt(i).widget().checkState():
                selectedText = self.sLayout.itemAt(i).widget().text()
                data = self.sav[selectedText]
                hdu = fits.PrimaryHDU(data)
                path = save_path+"/"+selectedText+".fits"
                hdu.writeto(path)

class EditFITSWidget(QWidget):
    def __init__(self):
        """
        Container widget for editing .fits files.
        """
        super().__init__()

        # Layout for the widget
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

        # Add a vertical bar to the right
        sideLayout = QVBoxLayout()
        layout.addLayout(sideLayout)

        # Open image button 
        imageButton = QPushButton("Open image")
        imageButton.clicked.connect(self.open_image)
        sideLayout.addWidget(imageButton)

        # Group of image edit buttons
        editGroup = QGroupBox("Edit functions")
        editLayout = QFormLayout()
        editGroup.setLayout(editLayout)
        sideLayout.addWidget(editGroup)
        
        # Add editing functions
        self.rotateEdit = QLineEdit()
        self.cropTop = QLineEdit()
        self.cropRight = QLineEdit()
        self.cropBottom = QLineEdit()
        self.cropLeft = QLineEdit()

        # Set width of bar
        self.rotateEdit.setMinimumWidth(65)

        # Set placeholder text
        self.rotateEdit.setPlaceholderText("0.0 deg")
        self.cropTop.setPlaceholderText("0 px")
        self.cropRight.setPlaceholderText("0 px")
        self.cropBottom.setPlaceholderText("0 px")
        self.cropLeft.setPlaceholderText("0 px")

        # Add the widgets to the layout
        editLayout.addRow("Rotate:",self.rotateEdit)
        editLayout.addRow("Crop top:",self.cropTop)
        editLayout.addRow("Crop right:",self.cropRight)
        editLayout.addRow("Crop bottom:",self.cropBottom)
        editLayout.addRow("Crop left:",self.cropLeft)

        # Add a edit summary section
        summGroup = QGroupBox("Edit totals")
        self.summLayout = QFormLayout()
        summGroup.setLayout(self.summLayout)
        sideLayout.addWidget(summGroup)

        # Add edit summary totals
        self.rotateTotal = 0.0
        self.cropTopTotal = 0
        self.cropRightTotal = 0
        self.cropBottomTotal = 0
        self.cropLeftTotal = 0

        # Add totals to summary
        self.summLayout.insertRow(0,"Rotation:", QLabel(str(self.rotateTotal)))
        self.summLayout.insertRow(1,"Crop top:", QLabel(str(self.cropTopTotal)))
        self.summLayout.insertRow(2,"Crop right:", QLabel(str(self.cropRightTotal)))
        self.summLayout.insertRow(3,"Crop bottom:", QLabel(str(self.cropBottomTotal)))
        self.summLayout.insertRow(4,"Crop left:", QLabel(str(self.cropLeftTotal)))

        # Add a horizontal layout to the buttons
        buttonLayout = QHBoxLayout()
        sideLayout.addLayout(buttonLayout)

        # Add an apply changes button
        applyButton = QPushButton("Apply")
        applyButton.clicked.connect(self.apply_changes)
        buttonLayout.addWidget(applyButton)

        # Add an image reset button
        resetButton = QPushButton("Reset")
        resetButton.clicked.connect(self.reset_changes)
        buttonLayout.addWidget(resetButton)

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
        except:
            print("Error opening image.")
            return
        
        self.reset_changes()
    
    def set_image(self):
        """
        Set the axes image and refresh.
        """
        self.ax.cla()
        self.ax.imshow(self.img_alt, origin="lower")
        # Refresh the canvas
        self.ax.draw_artist(self.ax.patch)
        self.canvas.update()
        self.canvas.flush_events()
        self.canvas.draw()

    def reset_changes(self):
        """
        Reset the image back to the original.
        """
        self.ax.cla()
        self.ax.imshow(self.img_orig, origin="lower")
        # Refresh the canvas
        self.ax.draw_artist(self.ax.patch)
        self.canvas.update()
        self.canvas.flush_events()
        self.canvas.draw()
        self.img_alt = self.img_orig

        # Reset summary text
        self.rotateTotal = 0
        self.summLayout.removeRow(0)
        self.summLayout.insertRow(0, "Rotate:", QLabel(str(self.rotateTotal)))
        self.cropTopTotal = 0
        self.summLayout.removeRow(1)
        self.summLayout.insertRow(1, "Crop top:", QLabel(str(self.cropTopTotal)))
        self.cropRightTotal = 0
        self.summLayout.removeRow(2)
        self.summLayout.insertRow(2, "Crop right:", QLabel(str(self.cropRightTotal)))
        self.cropBottomTotal = 0
        self.summLayout.removeRow(3)
        self.summLayout.insertRow(3, "Crop bottom:", QLabel(str(self.cropBottomTotal)))
        self.cropLeftTotal = 0
        self.summLayout.removeRow(4)
        self.summLayout.insertRow(4, "Crop left:", QLabel(str(self.cropLeftTotal)))
    
    def apply_changes(self):
        """
        Apply supplied changes to the image.
        """
        # Get all the parameters from the params box
        if self.rotateEdit.text() != '':
            self.img_alt = rotate(
                img_as_float64(self.img_alt), 
                float(self.rotateEdit.text()),
                resize=False
                )

            self.img_alt = self.img_alt[~np.all(self.img_alt == 0, axis=1)]
            bad_cols = np.argwhere(np.all(self.img_alt[..., :] == 0, axis=0))
            self.img_alt = np.delete(self.img_alt, bad_cols, axis=1)

            # Set the image
            self.set_image()

            # Increment the counter
            self.rotateTotal += int(self.rotateEdit.text())
            
            # Reset row
            self.summLayout.removeRow(0)
            self.summLayout.insertRow(0, "Rotate:", QLabel(str(self.rotateTotal)))

        if self.cropTop.text() != '':
            n = int(self.cropTop.text())
            # Size is of format (rows,cols)
            img_size = self.img_alt.shape

            # Remove the first n rows
            self.img_alt = np.delete(
                self.img_alt,
                np.s_[img_size[0]-n:img_size[0]],
                axis=0
            )

            # Set the image
            self.set_image()

            # Increment the counter
            self.cropTopTotal += int(self.cropTop.text())
            
            # Reset row
            self.summLayout.removeRow(1)
            self.summLayout.insertRow(1, "Crop top:", QLabel(str(self.cropTopTotal)))
        
        if self.cropRight.text() != '':
            n = int(self.cropRight.text())
            # Size is of format (rows, cols)
            img_size = self.img_alt.shape

            # Remove last n cols
            self.img_alt = np.delete(
                self.img_alt,
                np.s_[img_size[1]-n:img_size[1]],
                axis=1
            )

            # Set the image
            self.set_image()

            # Increment the counter
            self.cropRightTotal += int(self.cropRight.text())
            
            # Reset row
            self.summLayout.removeRow(2)
            self.summLayout.insertRow(2, "Crop right:", QLabel(str(self.cropRightTotal)))

        
        if self.cropBottom.text() != '':
            n = int(self.cropBottom.text())

            # Remove the last n rows
            self.img_alt = np.delete(
                self.img_alt,
                np.s_[0:n],
                axis=0
            )

            # Set the image
            self.set_image()

            # Increment the counter
            self.cropBottomTotal += int(self.cropBottom.text())
            
            # Reset row
            self.summLayout.removeRow(3)
            self.summLayout.insertRow(3, "Crop bottom:", QLabel(str(self.cropBottomTotal)))

        if self.cropLeft.text() != '':
            n = int(self.cropLeft.text())
            # Size is of format (rows, cols)
            img_size = self.img_alt.shape

            # Remove first n cols
            self.img_alt = np.delete(
                self.img_alt,
                np.s_[0:n],
                axis=1
            )

            # Set the image
            self.set_image()

            # Increment the counter
            self.cropLeftTotal += int(self.cropLeft.text())
            
            # Reset row
            self.summLayout.removeRow(4)
            self.summLayout.insertRow(4, "Crop left:", QLabel(str(self.cropLeftTotal)))

    def save_results(self):
        """
        Save the new data.
        """
        dialog = QFileDialog()
        # We're saving a file, not opening here
        dialog.setAcceptMode(QFileDialog.AcceptSave)
        dialog.setFileMode(QFileDialog.AnyFile)
        # Returned path is a tuple of (path, file_type)
        save_path = dialog.getSaveFileName(self, "Save results", filter="CSV file (*.fits)")[0]
        
        hdu = fits.PrimaryHDU(self.img_alt)
        hdu.writeto(save_path)