#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from readinglistmanager.utilities import printResults
import os
from readinglistmanager.issue import Issue, ReadingListIssue
from readinglistmanager import config,datasource, utilities
from readinglistmanager.filemanager import files


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
    
    @classmethod
    def generateCBLs(self,readingLists):
        if readingLists is not None:
            for list in readingLists:
                if isinstance(list,ReadingList):
                    list.writeToCBL()

    def writeToCBL(self):
        #sourcePath = self.source.file
        if isinstance(self.source,datasource.Source):
            sourceFolder = os.path.dirname(self.source.file)
            # Set output to subdirectory of output folder
            if isinstance(self.source,datasource.CBLSource):
                destFolder = str(sourceFolder).replace(files.readingListDirectory,os.path.join(files.outputDirectory,"CBL"))
            if isinstance(self.source,datasource.OnlineSource):
                destFolder = str(sourceFolder).replace(files.dataDirectory,os.path.join(files.outputDirectory,"WEB"))
        else:
            # Set output file to output folder
            destFolder = files.outputDirectory

        fileName = self.name + ".cbl"

        file = os.path.join(destFolder,fileName)
        utilities.checkPath(file)

        with open(file, 'w') as outputFile:

            lines = []

            lines.append("<?xml version=\"1.0\" encoding=\"utf-8\"?>")
            lines.append("<ReadingList xmlns:xsd=\"http://www.w3.org/2001/XMLSchema\" xmlns:xsi=\"http://www.w3.org/2001/XMLSchema-instance\">")
            lines.append("<Name>%s</Name>" % (self.name))
            lines.append("<Books>")

            #For each issue in arc
            for issue in self.issueList:
                if issue.coverDate is not None:
                    issueYear = issue.coverDate.year
                else:
                    issueYear = None

                if isinstance(issue,ReadingListIssue):
                    if issue.hasValidID() or issue.series.hasValidID():
                        lines.append("<Book Series=\"%s\" Number=\"%s\" Volume=\"%s\" Year=\"%s\">" % (issue.series.name,issue.issueNumber,issue.series.startYear,issueYear))
                        if issue.hasValidID(): lines.append("<IssueID>%s</IssueID>" % (issue.id))
                        if issue.series.hasValidID(): lines.append("<SeriesID>%s</SeriesID>" % (issue.series.id))
                        lines.append("</Book>")
                    else:
                        lines.append("<Book Series=\"%s\" Number=\"%s\" Volume=\"%s\" Year=\"%s\" />" % (issue.series.name,issue.issueNumber,issue.series.startYear,issueYear))

            lines.append("</Books>")
            lines.append("<Matchers />")
            lines.append("</ReadingList>")

            outputFile.writelines(lines)

            outputFile.close()


    def __init__(self, name, source, database, issueList=None, id=None):
        ReadingList.count += 1
        try:
            self._name = name
            self.__nameFromPath()
            self._source = source
            self._issueList = issueList
            if self.issueList == None: 
                self._issueList = []
            self._id = id
            self._database = database
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


    def addIssue(self, issue, entryNumber):
        if isinstance(issue, Issue):
            readingListIssue = ReadingListIssue(issue, entryNumber)
            self._issueList.append(readingListIssue)


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
