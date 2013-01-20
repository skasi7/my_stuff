#!/usr/bin/python2.7
#-*- coding: utf-8 -*-

# Pychecher options
__pychecker__ = 'no-callinit no-classattr'

# External imports
import sys
from PyQt4 import QtCore, QtGui

# Internal imports (if any)


def __addCallbacks(main):
  """
  Examples of what can be here (Callbacks not provided):

  QtCore.QObject.connect(main.actionOpen
      , QtCore.SIGNAL("activated()")
      , openCallback)
  QtCore.QObject.connect(main.actionSave_as
      , QtCore.SIGNAL("activated()")
      , saveAsCallback)
  QtCore.QObject.connect(main.treeWidget
      , QtCore.SIGNAL("itemChanged(QTreeWidgetItem*, int)")
      , itemChangedCallback)
  QtCore.QObject.connect(main.treeWidget
      , QtCore.SIGNAL("itemDoubleClicked(QTreeWidgetItem*, int)")
      , itemDoubleClickedCallback)
  """


if __name__ == "__main__":
  app = QtGui.QApplication(sys.argv)
  MainWindow = QtGui.QMainWindow()
  ui = Ui_MainWindow()
  ui.setupUi(MainWindow)
  __addCallbacks(ui)
  MainWindow.show()
  """
  Automatically opens a file (openFile not provided)
  if len(sys.argv) > 1:
    openFile(sys.argv[1])
  """
  sys.exit(app.exec_())

