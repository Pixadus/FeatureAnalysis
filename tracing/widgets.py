#!/usr/bin/python3
# -*- coding: utf-8 -*-
"""
Created on Tue 6.28.22
@title: Tracing GUI Components
@author: Parker Lamb
@description: Contains Qt6 widgets for automatically and manually tracing
curvilinear features.
"""

from PySide6.QtCore import Qt
from PySide6.QtGui import QPalette
from PySide6.QtWidgets import (QColorDialog, QComboBox, QFileDialog, 
                            QFormLayout, QGroupBox, QHBoxLayout, 
                            QLabel, QLineEdit, QPushButton,
                            QSizePolicy, QTabWidget, QVBoxLayout, 
                            QWidget)
from astropy.io import fits
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg
from matplotlib import (pyplot, colors)
from tracing.tracing import (AutoTracingOCCULT)
from helper.functions import ZoomPan
from collections import OrderedDict
import numpy as np
import csv

# Global variables
LINEWIDTH = 0.5
LINECOLOR = (0,0,1,0.7) # RGBA
SEL_LINEWIDTH = 0.5
SEL_LINECOLOR = (1,0,0,0.7)

class TracingWidget(QWidget):
    def __init__(self):
        """
        Container widget used when the "Tracing" tab
        is selected.
        """
        super().__init__()

        # Layout for the whole tab window
        layout = QHBoxLayout(self)

        # Set the focus policy
        self.setFocusPolicy(Qt.ClickFocus)
        
        # Add matplotlib canvas to layout
        self.figure = pyplot.figure()
        self.ax = self.figure.add_axes([0,0,1,1])
        self.canvas = FigureCanvasQTAgg(self.figure)
        self.canvas.setSizePolicy(QSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding))
        layout.addWidget(self.canvas)

        # Set the background color of the canvas
        win_color = self.palette().color(QPalette.Window).getRgbF()
        plot_color = colors.rgb2hex(win_color)
        self.figure.set_facecolor(plot_color)

        # Hide the axes
        self.ax.get_xaxis().set_visible(False)
        self.ax.get_yaxis().set_visible(False)

        # Add pan and zoom functionality
        self.zp = ZoomPan(self.ax)

        # Add container widget for layout on right
        controlWidget = QWidget()
        controlWidget.setMaximumWidth(300)

        # Layout for the vertical bar on the right
        controlLayout = QVBoxLayout()
        controlWidget.setLayout(controlLayout)

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
        self.colorButton.setEnabled(False)
        plotConfigLayout.addRow(QLabel("Line color:"), self.colorButton)

        # Add line width configuration
        widthWidget = QWidget()
        self.widthTextBox = QLineEdit()
        self.widthTextBox.setPlaceholderText("1.0")
        self.widthButton = QPushButton("Set")
        self.widthButton.clicked.connect(self.set_linewidth)
        self.widthButton.setEnabled(False)
        widthLayout = QHBoxLayout()
        widthLayout.addWidget(self.widthTextBox)
        widthLayout.addWidget(self.widthButton)
        widthWidget.setLayout(widthLayout)
        plotConfigLayout.addRow(QLabel("Line width:"), widthWidget)

        # Add plot config box to OCCULT box
        controlLayout.addWidget(plotConfig)

        # Add "Automatic" and "Manual" tabs
        tabs = QTabWidget()
        self.autoTab = AutoTab()
        self.manTab = ManualTab()
        self.manTab.zp = self.zp
        self.canvas.mpl_connect('button_press_event', self.manTab.process_click)
        self.manTab.set_mpl(self.canvas, self.ax)
        for pset in self.autoTab.options.keys():
            self.autoTab.options[pset].set_mpl(self.canvas, self.ax)
        tabs.setDocumentMode(True)
        tabs.addTab(self.autoTab, "Automatic")
        tabs.addTab(self.manTab, "Manual")
        controlLayout.addWidget(tabs)
        layout.addWidget(controlWidget)
    
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

        # Try to enable buttons
        if image_path == '':
            self.cmapBox.setEnabled(False)
        else:
            self.cmapBox.setEnabled(True)
            self.widthButton.setEnabled(True)
            self.colorButton.setEnabled(True)
            self.manTab.openButton.setEnabled(True)
            self.manTab.lineButton.setEnabled(True)
    
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

        # Set colors for new lines in each class
        self.autoTab.linecolor = self.pcolor
        for opt in self.autoTab.options.keys():
            self.autoTab.options[opt].linecolor = self.pcolor
        self.manTab.linecolor = self.pcolor

        # Redraw everything
        self.redraw_canvas()

    def set_linewidth(self):
        """
        Sets the line width of all current lines.
        """
        try:
            width = float(self.widthTextBox.text())
        except:
            print("Unable to interpret text width.")
            return

        for line in self.ax.get_lines():
            line.set_linewidth(width)

        # Set widths for new lines in each class
        self.autoTab.linewidth = width
        self.autoTab.sel_linewidth = width
        for opt in self.autoTab.options.keys():
            self.autoTab.options[opt].linewidth = width
            self.autoTab.options[opt].sel_linewidth = width
        self.manTab.linewidth = width
        self.manTab.sel_linewidth = width

        # Redraw everything
        self.redraw_canvas()

    def keyPressEvent(self, event):
        """
        Redefine the keyPressEvent for the tracing widget.
        """
        if event.key() == Qt.Key_Escape or event.key() == Qt.Key_Enter or event.key() == Qt.Key_Return:
            self.manTab.deselect_line()
            self.manTab.empty_drawcache()
            self.manTab.redraw_canvas(full=False)
        if event.key() == Qt.Key_Delete or event.key() == Qt.Key_Backspace:
            self.manTab.delete_line()
            self.manTab.deselect_line()
            self.manTab.redraw_canvas(full=False)
        return

    def redraw_canvas(self, full=False):
        """
        Refresh the canvas
        """
        if full:
            self.ax.draw_artist(self.ax.patch)
            self.canvas.update()
            self.canvas.flush_events()
            self.canvas.draw()
        else:
            self.canvas.draw()

class AutoTab(QWidget):
    def __init__(self):
        """
        Widget which contains the automatic tracing group.
        """
        super().__init__()

        layout = QVBoxLayout(self)

        # Variable setup
        self.linecolor = LINECOLOR
        self.linewidth = LINEWIDTH
        self.sel_linecolor = SEL_LINECOLOR
        self.sel_linewidth = SEL_LINEWIDTH

        # Tracing options
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

class ManualTab(QWidget):
    def __init__(self):
        """
        Widget which contains manual tracing functions
        """
        super().__init__()

        # Global layout
        layout = QVBoxLayout(self)

        # Variable initiation
        self.selected_line = None
        self.zp = None
        self.drawcache = []
        self.linecolor = LINECOLOR
        self.linewidth = LINEWIDTH
        self.sel_linecolor = SEL_LINECOLOR
        self.sel_linewidth = SEL_LINEWIDTH
        self.f_data = OrderedDict()

        # Button to open previous or automatic data
        self.openButton = QPushButton("Open data (optional)")
        self.openButton.clicked.connect(self.open_data)
        self.openButton.setEnabled(False)
        layout.addWidget(self.openButton)
        
        # Image controls box
        controlBox = QGroupBox("Controls")
        controlLayout = QVBoxLayout()
        controlLayout.setAlignment(Qt.AlignTop)
        controlBox.setLayout(controlLayout)
        layout.addWidget(controlBox)

        # Add buttons to controls box
        self.lineButton = QPushButton("Line")
        self.lineButton.setCheckable(True)
        self.lineButton.setEnabled(False)
        self.lineButton.clicked.connect(self.toggle_pan)
        controlLayout.addWidget(self.lineButton)

        # Controls hints box
        selBox = QGroupBox("Shortcuts")
        selLayout = QVBoxLayout()
        selLayout.setAlignment(Qt.AlignTop)
        selBox.setLayout(selLayout)
        selLayout.addWidget(QLabel("<Click> to select line/place point"))
        selLayout.addWidget(QLabel("<Esc> or <Enter> to deselect line"))
        selLayout.addWidget(QLabel("<Del> or <Bckspc> to delete line"))
        selLayout.addWidget(QLabel("<Scroll> to zoom"))
        selLayout.addWidget(QLabel("<Click-Hold> to pan"))
        layout.addWidget(selBox)

        # Add save button to layout
        self.saveButton = QPushButton("Save data")
        self.saveButton.clicked.connect(self.save_data)
        layout.addWidget(self.saveButton)
    
    def toggle_pan(self):
        """
        Toggle the pan functionality of the graph. 
        """
        if self.lineButton.isChecked():
            self.zp.pan = False
        else:
            self.zp.pan = True
    
    def process_click(self, event):
        """
        Process a click on the matplotlib canvas.

        If none of the control buttons are selected, assume
        click is used to select a feature line. Enter/esc
        key deselects feature.

        If Line is selected, trace line until
        enter/esc key is pressed. Highlight active line in different
        color.
        """
        ix, iy = event.xdata, event.ydata
        if self.lineButton.isChecked():
            # Draw a multi-point line
            if self.selected_line:
                # Add point to line if Some
                self.drawcache.append((ix,iy))
                x = np.array([coord[0] for coord in self.drawcache])
                y = np.array([coord[1] for coord in self.drawcache])
                self.selected_line.set_data(x,y)
                self.redraw_canvas(full=False)
            else:
                # Initialize the line if None
                self.selected_line, = self.ax.plot(
                    ix,iy, 
                    color=self.sel_linecolor, 
                    linewidth=self.sel_linewidth
                    )
                self.drawcache.append((ix,iy))
                self.redraw_canvas(full=False)
        else:
            # Select line
            closest_distance = 10000
            closest_line = None
            # Reset previously selected line, if any
            self.deselect_line()
            if self.selected_line:
                self.selected_line.set_color(self.linecolor)
                self.selected_line.set_linewidth(self.linewidth)
            for line in self.ax.get_lines():
                xdata = line.get_xdata()
                ydata = line.get_ydata()
                d = np.sqrt(
                    (xdata - ix)**2 + (ydata - iy)**2)
                if len(d[d <= closest_distance]):
                    closest_distance = np.sort(d[d<=closest_distance])[0]
                    closest_line = line
            if closest_line:
                closest_line.set_color(self.sel_linecolor)
                closest_line.set_linewidth(self.sel_linewidth)
                self.selected_line = closest_line
            self.redraw_canvas(full=False)
            
    def deselect_line(self):
        """
        Unselect a selected line, if any.
        """
        if self.selected_line:
            self.selected_line.set_color(self.linecolor)
            self.selected_line.set_linewidth(self.linewidth)
            self.selected_line = None
    
    def delete_line(self):
        """
        Delete a selected line, if any. 
        """
        if self.selected_line:
            self.selected_line.remove()
    
    def empty_drawcache(self):
        """
        Empty the point cache.
        """
        self.drawcache = []

    def redraw_canvas(self, full=True):
        """
        Refresh the canvas
        """
        if full:
            self.ax.draw_artist(self.ax.patch)
            self.canvas.update()
            self.canvas.flush_events()
            self.canvas.draw()
        else:
            self.canvas.draw()

    def open_data(self):
        """
        Load in automatic or previous manual data into the graph.
        """
        dialog = QFileDialog()
        # Only allow single, existing files
        dialog.setFileMode(QFileDialog.ExistingFile)
        # Image is a tuple of (path, file_type)
        data_path = dialog.getOpenFileName(self, "Open CSV", filter="CSV file (*.csv)")[0]
        if len(data_path) == 0:
            return

        # Try to open data and set graph data
        with open(data_path, newline='') as datafile:
            data = csv.reader(datafile)
            f_num = 0
            self.f_data[f_num] = []
            for row in data:
                print(row)
                # If a coordinate in the same feature
                if int(float(row[0])) == f_num:
                    coord = {"coord" : (float(row[1]), float(row[2]))}
                    self.f_data[f_num].append(coord)
                # If a new feature
                else:
                    x = [c["coord"][0] for c in self.f_data[f_num]]
                    y = [c["coord"][1] for c in self.f_data[f_num]]
                    self.ax.plot(x,y, color=self.linecolor, linewidth=self.linewidth)
                    # Set the new feature number
                    f_num = int(float(row[0]))
                    coord = {"coord" : (float(row[1]), float(row[2]))}
                    # Initialize the coordinate list, add current coord
                    self.f_data[f_num] = [coord]
        
        # Redraw everything
        self.redraw_canvas()
        self.saveButton.setEnabled(True)
    
    def save_data(self):
        """
        Save the manual data.
        """
        dialog = QFileDialog()
        # We're saving a file, not opening here
        dialog.setAcceptMode(QFileDialog.AcceptSave)
        dialog.setFileMode(QFileDialog.AnyFile)
        # Returned path is a tuple of (path, file_type)
        save_path = dialog.getSaveFileName(self, "Save results", filter="CSV file (*.csv)")[0]
        if len(save_path) == 0:
            return
        f_num = 0
        with open(save_path, 'w', newline='') as csvfile:
            cw = csv.writer(csvfile)
            for line in self.ax.get_lines():
                f_num += 1
                for x,y in zip(line.get_data()[0], line.get_data()[1]):
                    cw.writerow([f_num, x, y])

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
        self.linecolor = LINECOLOR
        self.linewidth = LINEWIDTH
        self.sel_linecolor = SEL_LINECOLOR
        self.sel_linewidth = SEL_LINEWIDTH


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

        # Check if there is a range of parameters
        self.multiparams = {}
        for param in params:
            if param.text().count(",") == 1 and param != self.qthresh1 and param != self.qthresh2:
                start = param.text().split(",")[0]
                end = param.text().split(",")[1]
                self.multiparams[param] = [int(start), int(end)]
            elif param.text().count(",") == 1 and param == self.qthresh1 and param == self.qthresh2:
                start = param.text().split(",")[0]
                end = param.text().split(",")[1]
                self.multiparams[param] = [float(start), float(end)]            
            elif param.text().count(",") > 1:
                print("Error: Too many commas in ", param.text())
                return

        # Run OCCULT-2
        if len(self.multiparams) == 0:
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
                self.ax.plot(x,y, color=self.linecolor, linewidth=self.linewidth)

            # Refresh the canvas
            self.ax.draw_artist(self.ax.patch)
            self.canvas.update()
            self.canvas.flush_events()
            self.canvas.draw()

            # Enable the save & color buttons
            try:
                self.saveButton.clicked.disconnect()
                self.saveButton.clicked.connect(self.save_results)
            except:
                pass
            self.saveButton.setEnabled(True)
            self.analyzeButton.setEnabled(True)
        
        # If we have multiple parameters selected
        else:
            self.results = OrderedDict()
            for param in params:
                if param not in self.multiparams:
                    if param == self.qthresh1 or param == self.qthresh2:
                        self.multiparams[param] = [float(param.text()), float(param.text())+0.25]
                    else:
                        self.multiparams[param] = [int(param.text()), int(param.text())+1]
            
            # Run OCCULT-2 over all ranges
            for nsm1 in range(self.multiparams[self.nsm1][0], self.multiparams[self.nsm1][1]):
                for rmin in range(self.multiparams[self.rmin][0], self.multiparams[self.rmin][1]):
                    for lmin in range(self.multiparams[self.lmin][0], self.multiparams[self.lmin][1]):
                        for nstruc in range(self.multiparams[self.nstruc][0], self.multiparams[self.nstruc][1],100):
                            for ngap in range(self.multiparams[self.ngap][0], self.multiparams[self.ngap][1]):
                                for qthresh1 in np.arange(self.multiparams[self.qthresh1][0], self.multiparams[self.qthresh1][1], 0.25):
                                    for qthresh2 in np.arange(self.multiparams[self.qthresh2][0], self.multiparams[self.qthresh2][1], 0.25):
                                        # Dictionary keys will be parameter set
                                        key_name = "N{}-R{}-L{}-NS{}-NG{}-Q1{}-Q2{}".format(nsm1, rmin, lmin, nstruc, ngap, qthresh1, qthresh2)
                                        print("Running OCCULT-2 for", key_name)
                                        result = at.run(
                                            nsm1,
                                            rmin,
                                            lmin,
                                            nstruc,
                                            ngap,
                                            qthresh1,
                                            qthresh2
                                        )
                                        self.results[key_name] = result

            # Clear the current axes from previous results
            self.ax.cla()

            # Reset the image, since it's cleared with cla()
            self.ax.imshow(self.image_data, origin="lower")

            # Plot the results
            for feature in self.results[key_name]:
                x = []
                y = []
                for coord in feature:
                    x.append(coord[0])
                    y.append(coord[1])
                self.ax.plot(x,y, color=self.linecolor, linewidth=self.linewidth)

            # Refresh the canvas
            self.ax.draw_artist(self.ax.patch)
            self.canvas.update()
            self.canvas.flush_events()
            self.canvas.draw()

            # Enable the save & color buttons
            try:
                self.saveButton.clicked.disconnect()
                self.saveButton.clicked.connect(self.save_multiple)
            except:
                pass
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
        with open(save_path, 'w', newline='') as outfile:
            resultwriter = csv.writer(outfile)
            for result in self.results:
                f_count+=1
                for coord in result:
                        resultwriter.writerow([f_count, coord[0], coord[1]])
    
    def save_multiple(self):
        """
        Save multiple results, if multiple parameters specified
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
        for paramset in self.results.keys():
            # Save format will be { feature_id, x, y }
            f_count = 0
            with open(save_path+"/"+paramset+".csv", 'w', newline='') as outfile:
                resultwriter = csv.writer(outfile)
                for feature in self.results[paramset]:
                    f_count+=1
                    for coord in feature:
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