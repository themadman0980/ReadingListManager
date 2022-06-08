#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import readinglistmanager
from readinglistmanager.utilities import printResults
import os
from readinglistmanager.issue import Issue, ReadingListIssue
from readinglistmanager import config, datasource


class ReadingList:

    count = 0  # Number of lists with all series matched to CV
    numCompleteSeriesMatches = 0  # Number of lists with all series matched to CV
    numCompleteIssueMatches = 0  # Number of lists with all issues matched to CV

    @classmethod
    def printSummaryResults(self, readingLists):

        for readingList in readingLists:
            readingList.getSummary()

        printResults("Lists: %s" % (ReadingList.count), 2, True)
        printResults("All series matched: %s / %s" %
                     (ReadingList.numCompleteSeriesMatches, ReadingList.count), 3)
        printResults("All issues matched: %s / %s" %
                     (ReadingList.numCompleteIssueMatches, ReadingList.count), 3)

    def __init__(self, name, source, cvCache, issueList=None, id=None):
        ReadingList.count += 1
        try:
            self._name = name
            self.__nameFromPath()
            self._source = source
            self._issueList = issueList
            if self.issueList == None:
                self._issueList = []
            self._id = id
            self._cvCache = cvCache
        except Exception as e:
            printResults("Error: Problem initialising new list %s [%s]" % (
                name, source.name), 4)
            print(e)

    def getSummary(self):
        issuesMatched = 0
        seriesMatched = 0
        issueCount = len(self.issueList)
        seriesSet = set()

        for issue in self.issueList:
            if issue.hasValidID():
                issuesMatched += 1
            seriesSet.add(issue.series)

        seriesCount = len(seriesSet)

        for series in seriesSet:
            if series.hasValidID():
                seriesMatched += 1

        if issuesMatched == issueCount:
            ReadingList.numCompleteIssueMatches += 1

        if seriesMatched == seriesCount:
            ReadingList.numCompleteSeriesMatches += 1

        if config.verbose:
            printResults("ReadingList: %s [%s]" %
                         (self.name, self.source.type), 2)
        if config.verbose:
            printResults("Number of series matched: %s / %s" %
                         (seriesMatched, seriesCount), 3)
        if config.verbose:
            printResults("Number of issues matched: %s / %s" %
                         (issuesMatched, issueCount), 3)

    # Check for ID matches for series/issues in reading list

    #def validate(self, cvCacheConnection, cvSession):
    #    if config.verbose:
    #        printResults("Validating reading list : %s (%s) [%s]" % (
    #            self.name, self.source.type, self.id), 2)
    #    for series in self.seriesList:
    #        series.validate(cvCacheConnection, cvSession)

    def addIssue(self, issue, entryNumber):
        if isinstance(issue, Issue):
            readingListIssue = ReadingListIssue(issue, entryNumber)
            self._issueList.append(readingListIssue)

    # Function to import list of Issues as set of unique series
    #def processIssueList(self, issueList):
    #    printResults("Updating issue data for reading list : %s [%s]" % (
    #        self.name, self.source.type), 3)

    #    for issue in issueList:
    #        series = issue.series

    #    # Initialise seriesList set
    #    if self.seriesList is not None:
    #        seriesList = self.seriesList
    #    else:
    #        seriesList = set()

    #    # Ensure data is a list of Issues
    #    if isinstance(issueList, list):
    #        for issue in issueList:
    #            if isinstance(issue, Issue):
    #                seriesList.add(issue.series)
    #            else:
    #                print("Not valid issue: %s" % issue)
    #                return

    #    finalSeriesList = set()

    #    # Iterate through unique series
    #    for series in seriesList:
    #        curSeriesIssues = []
    #        # Check every issue in ReadingList for matches with current series
    #        for issue in issueList:
    #            if issue.series == series:
    #                # Book matches current series! Add issue to series issuelist
    #                curSeriesIssues.append(issue)
    #
    #        # Add all issues to series object
    #        series.issueList = curSeriesIssues

    #        finalSeriesList.add(series)

    #    self._seriesList = finalSeriesList

    # Internal function to add list numbers to each issue

    #def createFromIssueList(self, issueList):
    #    self.__setSeriesList(issueList)

    def __nameFromPath(self):
        filename, file_extension = os.path.splitext(self._name)
        self._name = str(filename)

    def id():
        doc = "The reading list id property as defined by the source db"

        def fget(self):
            return self._id

        def fset(self, value):
            self._id = value

        def fdel(self):
            del self._id
        return locals()
    id = property(**id())

    def name():
        doc = "The reading list name"

        def fget(self):
            return self._name

        def fset(self, value):
            self._name = value
            self.__nameFromPath()

        def fdel(self):
            del self._name
        return locals()
    name = property(**name())

    def source():
        doc = "The source of the reading list"

        def fget(self):
            return self._source

        def fset(self, value):
            if isinstance(value, datasource.Source):
                self._source = value

        def fdel(self):
            del self._source
        return locals()
    source = property(**source())

    def issueList():
        doc = "The list of series found in the readinglist"

        def fget(self):
            if self._issueList == None:
                self._issueList = []
            return self._issueList
        return locals()
    issueList = property(**issueList())
