#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from readinglistmanager import utilities
from readinglistmanager.utilities import printResults
import os


class Source:
    def __init__(self, name, file, type):
        self._file = file
        self._name = name
        self._type = type

    def isValidFile(self):
        printResults("Checking if source file exists: %s [%s]" % (
            self.file, self.name), 2)
        if self.file is not None and os.path.exists(self.file):
            return True
        return False

    def type():
        doc = "The type property."

        def fget(self):
            return self._type

        def fset(self, value):
            self._type = value

        def fdel(self):
            del self._type
        return locals()
    type = property(**type())

    def file():
        doc = "The name and path of the source file"

        def fget(self):
            return self._file

        def fset(self, value):
            self._file = value

        def fdel(self):
            del self._file
        return locals()
    file = property(**file())

    def name():
        doc = "The name of the source"

        def fget(self):
            return self._name

        def fset(self, value):
            self._name = value

        def fdel(self):
            del self._name
        return locals()
    name = property(**name())


class CBLSource(Source):
    def __init__(self, name, file):
        super().__init__(name, file, "CBL")


class CVSource(Source):
    def __init__(self, name, file):
        super().__init__(name, file, "CV")
        self._tableIssueDetails = 'cv_issues'
        self._tableSearchIssues = 'cv_searches_issues'
        self._tableVolumeDetails = 'cv_volumes'
        self._tableSearchVolume = 'cv_searches_volumes'

    def tableVolumeDetails():
        doc = "The Volume Details table name"

        def fget(self):
            return self._tableVolumeDetails

        def fset(self, value):
            self._tableVolumeDetails = value

        def fdel(self):
            del self._tableVolumeDetails
        return locals()
    tableVolumeDetails = property(**tableVolumeDetails())

    def tableIssueDetails():
        doc = "The Issue Details table name"

        def fget(self):
            return self._tableIssueDetails

        def fdel(self):
            del self._tableIssueDetails
        return locals()
    tableIssueDetails = property(**tableIssueDetails())


class OnlineSource(Source):
    def __init__(self, name, file, tableDict):
        super().__init__(name, file, "WEB-DL")
        try:
            self._tableReadingListTitles = tableDict['ReadingLists']
            self._tableReadingListDetails = tableDict['ReadingListDetails']
            self._tableIssueDetails = tableDict['IssueDetails']
        except Exception as e:
            printResults(
                "Warning : Unable to find DB table details for %s" % (self.name), 5)

    def tableReadingListTitles():
        doc = "The Reading List Title table name."

        def fget(self):
            return self._tableReadingListTitles
        return locals()
    tableReadingListTitles = property(**tableReadingListTitles())

    def tableReadingListDetails():
        doc = "The Reading List Details table name."

        def fget(self):
            return self._tableReadingListDetails
        return locals()
    tableReadingListDetails = property(**tableReadingListDetails())

    def tableIssueDetails():
        doc = "The Issue Details table name"

        def fget(self):
            return self._tableIssueDetails
        return locals()
    tableIssueDetails = property(**tableIssueDetails())
