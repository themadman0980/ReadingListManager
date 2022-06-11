#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
from datetime import datetime

timeString = datetime.today().strftime("%y%m%d%H%M%S")

scriptDirectory = os.getcwd()
#rootDirectory = os.path.dirname(scriptDirectory)
dataDirectory = os.path.join(scriptDirectory, "Data")
readingListDirectory = os.path.join(scriptDirectory, "ReadingLists")
resultsDirectory = os.path.join(scriptDirectory, "Results")

dataFile = os.path.join(dataDirectory, "data.db")
cvCacheFile = os.path.join(dataDirectory, "cv.db")
configFile = os.path.join(scriptDirectory, 'config.ini')
resultsFile = os.path.join(resultsDirectory, "results-%s.txt" % (timeString))
problemsFile = os.path.join(resultsDirectory, "problems-%s.txt" % (timeString))

def checkDirectories():

    directories = {dataDirectory,readingListDirectory,resultsDirectory}

    for directory in directories:
        if not os.path.exists(directory):
            os.makedirs(directory)

    pass

class FileManager():
    def __init__(self):
        self._cvCacheFile = cvCacheFile
        self._dataDirectory = dataDirectory
        self._readingListDirectory = readingListDirectory
        self._resultsDirectory = resultsDirectory
        self._resultsFile = resultsFile
        self._problemsFile = problemsFile
        self._dataFile = dataFile
        checkDirectories()

    def cvCacheFile():
        doc = "The cvCache property."

        def fget(self):
            return self._cvCacheFile

        return locals()
    cvCacheFile = property(**cvCacheFile())

    def dataFile():
        doc = "The main database file"

        def fget(self):
            return self._dataFile

        return locals()
    dataFile = property(**dataFile())

    def dataDirectory():
        doc = "The dataDirectory property."

        def fget(self):
            return self._dataDirectory

        return locals()
    dataDirectory = property(**dataDirectory())

    def readingListDirectory():
        doc = "The readingListDirectory property."

        def fget(self):
            return self._readingListDirectory

        return locals()
    readingListDirectory = property(**readingListDirectory())

    def resultsDirectory():
        doc = "The resultsDirectory property."

        def fget(self):
            return self._resultsDirectory

        return locals()
    resultsDirectory = property(**resultsDirectory())
    
    def resultsFile():
        doc = "The output file for console data"

        def fget(self):
            return self._resultsFile

        return locals()
    resultsFile = property(**resultsFile())

    def problemsFile():
        doc = "The output file for problem data"

        def fget(self):
            return self._problemsFile

        return locals()
    problemsFile = property(**problemsFile())


files = FileManager()
