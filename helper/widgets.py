#!/usr/bin/python3
# -*- coding: utf-8 -*-
"""
Created on Wed 6.29.22
@title: Helper function GUI components
@author: Parker Lamb
@description: Contains Qt6 widgets to act as helper
functions for the feature tracing program. 
"""

from PySide6.QtWidgets import (QCheckBox, QFileDialog, QGroupBox, QHBoxLayout, QPushButton, QVBoxLayout, QWidget)
from scipy.io import readsav
from astropy.io import fits

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
        sfButton.clicked.connect(self.toggle_sav_fits)
        hfLayout.addWidget(sfButton)

        # Save -> FITS Widget
        self.sfw = SFWidget()
        layout.addWidget(self.sfw)

    def toggle_sav_fits(self):
        """
        Function to toggle the IDL .sav -> .fits
        format widget.
        """
        if self.sfw.isVisible():
            self.sfw.setVisible(False)
        else:
            self.sfw.setVisible(True)

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