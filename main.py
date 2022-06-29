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
            self.resize(800,600)
            self.setWindowTitle(self.title)
        
            # Set up all the tabs
            tabs = QTabWidget()
            tabs.setDocumentMode(True)

            # Demo label - REMOVE
            label = QLabel("Demo for preprocessing")

            # Add new widgets for each page
            tabs.addTab(label,"Preprocessing")
            tabs.addTab(TracingWidget(),"Tracing")
            # tabs.addTab(label1,"Analysis")
            # tabs.addTab(label1,"Time Series")
            # tabs.addTab(label1,"Miscellaneous")

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