#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from readinglistmanager.utilities import printResults
import os, datetime
from readinglistmanager.model.issue import Issue
from readinglistmanager.model.series import Series
from readinglistmanager.datamanager import datasource
from readinglistmanager import config, filemanager, utilities


class ReadingList:

#    @classmethod
#    def printSummaryResults(self, readingLists):
#
#        for readingList in readingLists:
#            readingList.getSummary()
#
#        printResults("Lists: %s" % (ReadingList.count), 2, True)
#        printResults("All series matched: %s / %s" %
#                     (ReadingList.numCompleteSeriesMatches, ReadingList.count), 3)
#        printResults("All issues matched: %s / %s" %
#                     (ReadingList.numCompleteIssueMatches, ReadingList.count), 3)
    
    @classmethod
    def generateCBLs(self, readingLists : list):
        if readingLists is not None and isinstance(readingLists, list):
            for readingList in readingLists:
                if isinstance(readingList, ReadingList):
                    readingList.writeToCBL()

    def writeToCBL(self):
        #sourcePath = self.source.file
        if isinstance(self.source, datasource.Source):
            sourceFolder = os.path.dirname(self.source.file)
            # Set output to subdirectory of output folder
            destFolder = ""
            #Set top level of cbl output destination
            if self.source.type == datasource.ListSourceType.CBL:
                destFolderTop = os.path.join(filemanager.outputDirectory,"CBL")
                destFolder = str(sourceFolder).replace(filemanager.readingListDirectory,destFolderTop)
            if self.source.type == datasource.ListSourceType.Website:
                destFolder = os.path.join(filemanager.outputDirectory,"WEB",utilities.sanitisePathString(self.source.name))

            # Set full path to CBL, keeping relative location
        else:
            # Set output file to output folder
            destFolder = filemanager.outputDirectory

        fileName = "%s.cbl" % (utilities.sanitisePathString(self.name))

        file = os.path.join(destFolder,fileName)
        utilities.checkPath(file)

        with open(file, 'w') as outputFile:

            lines = []

            lines.append("<?xml version=\"1.0\" encoding=\"utf-8\"?>")
            lines.append("<ReadingList xmlns:xsd=\"http://www.w3.org/2001/XMLSchema\" xmlns:xsi=\"http://www.w3.org/2001/XMLSchema-instance\">")
            lines.append("<Name>%s</Name>" % (self.name))
            lines.append("<Books>")

            #For each issue in arc
            for key,issue in sorted(self.issueList.items()):
                if isinstance(issue,Issue):
                    # Check if issue cover date exists
                    if issue.coverDate is not None and isinstance(issue.coverDate,datetime.datetime):
                        issueYear = issue.coverDate.year
                    else:
                        issueYear = issue.year

                    seriesName = utilities.escapeString(issue.series.name)
                    issueNum = utilities.escapeString(issue.issueNumber)

                    if issue.hasValidID() or (isinstance(issue.series, Series) and issue.series.hasValidID()):
                        lines.append("<Book Series=\"%s\" Number=\"%s\" Volume=\"%s\" Year=\"%s\">" % (seriesName,issueNum,issue.series.startYear,issueYear))
                        lines.append("<Database Name=\"cv\" Series=\"%s\" Issue=\"%s\" />" % (issue.series.id,issue.id))
                        lines.append("</Book>")
                    else:
                        lines.append("<Book Series=\"%s\" Number=\"%s\" Volume=\"%s\" Year=\"%s\" />" % (seriesName,issueNum,issue.series.startYear,issueYear))

            lines.append("</Books>")
            lines.append("<Matchers />")
            lines.append("</ReadingList>")

            outputFile.writelines(lines)

            outputFile.close()


    def __init__(self, listName, source, listID = None):
        try:
            self._name = None
            self.name = listName
            self.source = source
            self.id = listID
            self.issueList = {}
        except Exception as e:
            printResults("Error: Problem initialising new list %s [%s] : %s" % (listName, source, str(e)), 4)

    def getSummary(self) -> dict:
        issuesMatched = seriesMatched = 0
        seriesSet = set()

        for issue in self.issueList:
            if issue.hasValidID():
                issuesMatched += 1
            if isinstance(issue.series, Series):
                seriesSet.add(issue.series)

        for series in seriesSet:
            if series.hasValidID():
                seriesMatched += 1

        issueCount = len(self.issueList)
        seriesCount = len(seriesSet)

        if config.verbose:
            printResults("ReadingList: %s [%s]" %
                         (self.name, self.source.type), 2)
        if config.verbose:
            printResults("Number of series matched: %s / %s" %
                         (seriesMatched, seriesCount), 3)
        if config.verbose:
            printResults("Number of issues matched: %s / %s" %
                         (issuesMatched, issueCount), 3)
        
        return {'issueCount':issueCount, 'issuesMatched':issuesMatched,'seriesCount':seriesCount,'seriesMatched':seriesMatched}


    def addIssue(self, entryNumber, issue):
        if isinstance(issue, Issue):
            self.issueList[entryNumber] = issue


    def __nameFromPath(self, file):
        filename, file_extension = os.path.splitext(file)
        self._name = str(filename)

    def name():
        doc = "The reading list name"

        def fget(self):
            return self._name

        def fset(self, value):
            self.__nameFromPath(value)

        def fdel(self):
            del self._name
        return locals()
    name = property(**name())


