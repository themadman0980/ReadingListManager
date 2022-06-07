#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os

scriptDirectory = os.getcwd()
rootDirectory = os.path.dirname(scriptDirectory)
dataDirectory = os.path.join(rootDirectory, "Data")
readingListDirectory = os.path.join(rootDirectory, "ReadingLists")

cvCacheFile = os.path.join(dataDirectory, "cv.db")
configFile = os.path.join(rootDirectory, 'config.ini')

# Read config info


class FileManager():
    def __init__(self):
        self._cvCache = cvCacheFile
        self._dataDirectory = dataDirectory
        self._readingListDirectory = readingListDirectory

    def cvCache():
        doc = "The cvCache property."

        def fget(self):
            return self._cvCache

        def fdel(self):
            del self._cvCache
        return locals()
    cvCache = property(**cvCache())

    def dataDirectory():
        doc = "The dataDirectory property."

        def fget(self):
            return self._dataDirectory

        def fdel(self):
            del self._dataDirectory
        return locals()
    dataDirectory = property(**dataDirectory())

    def readingListDirectory():
        doc = "The readingListDirectory property."

        def fget(self):
            return self._readingListDirectory

        def fset(self, value):
            self._readingListDirectory = value

        def fdel(self):
            del self._readingListDirectory
        return locals()
    readingListDirectory = property(**readingListDirectory())


global files
files = FileManager()
