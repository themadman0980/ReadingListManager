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

cvCacheFile = os.path.join(dataDirectory, "cv.db")
configFile = os.path.join(scriptDirectory, 'config.ini')
resultsFile = os.path.join(resultsDirectory, "results-%s.txt" % (timeString))

class FileManager():
    def __init__(self):
        self._cvCache = cvCacheFile
        self._dataDirectory = dataDirectory
        self._readingListDirectory = readingListDirectory
        self._resultsDirectory = resultsDirectory
        self._resultsFile = resultsFile

    def cvCache():
        doc = "The cvCache property."

        def fget(self):
            return self._cvCache

        return locals()
    cvCache = property(**cvCache())

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
        doc = "The resultsFile property."

        def fget(self):
            return self._resultsFile

        return locals()
    resultsFile = property(**resultsFile())

files = FileManager()
