#!/usr/bin/python3
# -*- coding: utf-8 -*-
"""
Created on Mon 6.27.22
@title: Feature Tracing
@author: Parker Lamb
@description: Multifunction scientific feature tracing application
@usage: todo
"""

from PySide6.QtWidgets import (QApplication, QLabel, QMainWindow, QTabWidget)
from tracing.widgets import TracingWidget
from helper.widgets import HelperWidget
from analysis.widgets import AnalysisWidget

class FeatureTracing(QApplication):
    def __init__(self):
        """
        FeatureTracing application.
        """
        super().__init__()
        
    class Window(QMainWindow):
        def __init__(self):
            """
            Main window, holding all application elements.
            """
            super().__init__()

            # Application setup and backend
            self.version = 0.1
            self.title = "Feature Tracing v{}".format(self.version)
            self.resize(850,600)
            self.setWindowTitle(self.title)
        
            # Set up all the tabs
            tabs = QTabWidget()
            tabs.setDocumentMode(True)

            # Instantiate widgets
            analysis = AnalysisWidget()
            tracing = TracingWidget()
            helper = HelperWidget()

            # Set the analysis and tab widgets
            tracing.autoTab.occult.set_at(analysis, tabs)

            # Add new widgets for each page
            # tabs.addTab(label,"Preprocessing")
            tabs.addTab(tracing,"Tracing")
            tabs.addTab(analysis,"Analysis")
            # tabs.addTab(label1,"Time Series")
            tabs.addTab(helper,"Helper functions")

            self.setCentralWidget(tabs)


    def run(self):
        """
        Run the FeatureTracing application.
        """
        win = self.Window()

        win.show()
        self.exec()


if __name__ == "__main__":
    gui = FeatureTracing()
    gui.run()