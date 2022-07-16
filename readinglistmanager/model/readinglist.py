#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from readinglistmanager.utilities import printResults
import os, datetime, re
from readinglistmanager.model.issue import Issue
from readinglistmanager.model.series import Series
from readinglistmanager.datamanager.datasource import Source, ListSourceType
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
    def getCBLData(self):
        lines = []

        lines.append("<?xml version=\"1.0\" encoding=\"utf-8\"?>")
        lines.append("<ReadingList xmlns:xsd=\"http://www.w3.org/2001/XMLSchema\" xmlns:xsi=\"http://www.w3.org/2001/XMLSchema-instance\">")
        lines.append("<Name>%s</Name>" % (self.name))
        if self.getNumIssues() is not None: 
            lines.append("<NumIssues>%s</NumIssues>" % (self.getNumIssues()))
        lines.append("<Source>%s</Source>" % (self.source.name))
        if self.id is not None and utilities.isValidID(self.id):
            lines.append("<Database Name=\"cv\" ID=\"%s\" />" % (self.id))
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

        return lines

    def getTXTData(self):
        return "%s : %s issues" % (self.getFileName(), self.getNumIssues())

    def getJSONData(self):

        listData = dict()

        listData['ListName'] = self.name        
        listData['Publisher'] = self.publisher
        listData['IssueCount'] = self.getNumIssues()
        #listData['Type'] = None
        if isinstance(self.source, Source):
            listData['Source'] = self.source.name

        if utilities.isValidID(self.id):
            listData['Database'] = list()
            database = {'Name' : 'Comicvine', 'ID':self.id}
            listData['Database'].append(database)

        listData['Issues'] = dict()
        for number,issue in self.issueList.items():
            if isinstance(issue, Issue):
                listData['Issues'][str(number)] = issue.getJSONDict()
        
        return listData

    def setPublisherFromIssueDetails(self):
        publisherCounts = dict()
        if self.issueList is not None and len(self.issueList) > 0:
            for number, issue in self.issueList.items():
                if isinstance(issue, Issue) and issue.series is not None and isinstance(issue.series, Series):
                    if issue.series.publisher not in publisherCounts: 
                        publisherCounts[issue.series.publisher] = 0
                    
                    publisherCounts[issue.series.publisher] += 1
        
        curPublisher = None
        curPubCount = 0
        for publisher, count in publisherCounts.items():
            if count > curPubCount:
                curPublisher = publisher
                curPubCount = count
        
        self.publisher = curPublisher

    def __init__(self, source : Source, listName = None, listID = None):
        try:
            self.source = source
            self._name = None
            self.problems = dict()
            self.dynamicName = None
            self.publisher = None
            self.sourceIssueList = None
            self.id = listID
            self.part = None
            self.key = None

            if listName is not None:
                self.name = listName
            #elif filePath is not None:
            #    self.name = filePath
            elif isinstance(source, Source) and self.source.type == ListSourceType.CBL:
                self._getNameFromFile(self.source.file)

            if self.source is not None and isinstance(self.source, Source):
                self.key = ReadingList.getKey(self.dynamicName,self.source.type,self.source.name)

            self.dataSourceType = None
            self.checked = dict()
            self.issueList = dict()
        except Exception as e:
            printResults("Error: Problem initialising new list %s [%s] : %s" % (listName, source, str(e)), 4)

    def __hash__(self):
        return hash((self.dynamicName, self.source))

    @classmethod
    def getKey(self, dynamicListName : str, listSourceType : ListSourceType, listSourceName : str = None):
        keyList = list()
        if dynamicListName is not None and isinstance(dynamicListName, str):
            keyList.append(dynamicListName)
        if listSourceType is not None and isinstance(dynamicListName, ListSourceType):
            keyList.append(listSourceType.value)
        if listSourceName is not None and isinstance(listSourceName, str):
            keyList.append(listSourceName.replace(' ',''))
        return "-".join(keyList)

    def getSummary(self) -> dict:
        issuesMatched = seriesMatched = 0
        seriesSet = set()

        for issue in self.issueList:
            if isinstance(issue, Issue) and issue.hasValidID():
                issuesMatched += 1
            if isinstance(issue.series, Series):
                seriesSet.add(issue.series)

        for series in seriesSet:
            if isinstance(series, Series):
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

    def isAnnual(self) -> bool:
        return 'annual' in str(self.name).lower()

    def addIssue(self, entryNumber, issue):
        if isinstance(issue, Issue):
            self.issueList[entryNumber] = issue

    def addProblem(self, problemType, extraData = None):
        self.problems[problemType] = extraData

    @classmethod
    def fromDict(self, matchData : dict, listType : ListSourceType) -> 'ReadingList':
        listSource = Source(matchData['name'], None, listType)
        curList = ReadingList(listName = matchData['name'], source = listSource, listID = matchData['listID'])
        curList.issueList = matchData['issues']
        curList.updateDetailsFromDict(matchData)

        return curList

    def updateDetailsFromDict(self, match : dict) -> None:
        # Populate attributes from _seriesDetailsTemplate dict structure
        try:
            self.id = match['listID']
            #self.name = match['name']
            #self.startYear = match['startYear']
            self.publisher = match['publisher']
            self.dateAdded = match['dateAdded']
            self.dataSourceType = match['dataSource']
            #self.numIssues = match['numIssues'] Calculated dynamically from self.issueList
            self.sourceIssueList = match['issues']
            self.description = match['description']
            self.summary = match['summary']
            self.detailsFound = True
        except Exception as e:
            printResults("Unable to update list \'%s [%s]\' from match data : %s" % (self.name, self.id, match),4)

    def getNumIssues(self) -> int:
        return len(self.issueList) if self.issueList is not None else None

    def _getNameFromFile(self, fileName):
        file = os.path.basename(fileName)
        fileName, file_extension = os.path.splitext(file)
        self.name = fileName

    def getFileName(self) -> str:
        fileName = list()
        
        if self.publisher is not None: fileName.append("[%s]" % self.publisher)

        fileName.append(str(self.name))

        if self.part is not None:
            fileName.append("Part #%s" % str(self.part))

        if isinstance(self.source, Source) and isinstance(self.source.type, ListSourceType):
            sourceString = self.source.type.value
            if self.source.type == ListSourceType.Website:
                sourceString += '-%s' % self.source.name
            fileName.append("(%s)" % sourceString)
        
        return " ".join(fileName)


    def name():
        doc = "The reading list name"

        def fget(self):
            return self._name

        def fset(self, value):
            cleanName = utilities._cleanReadingListName(value)

            self._name = cleanName['listName']
            if 'part' in cleanName:
                self.part = cleanName['partNumber']

            self.dynamicName = utilities.getDynamicName(self._name)

        def fdel(self):
            del self._name
        return locals()
    name = property(**name())


