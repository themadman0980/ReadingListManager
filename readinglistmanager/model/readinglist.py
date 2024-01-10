#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from readinglistmanager.utilities import printResults
import os
from datetime import datetime
import re
from readinglistmanager.model.issue import Issue
from readinglistmanager.model.issueRange import IssueRange, IssueRangeCollection
from readinglistmanager.model.series import Series
from readinglistmanager.model.date import PublicationDate
from readinglistmanager.datamanager.datasource import Source, ListSourceType, ComicInformationSource
from readinglistmanager import config, filemanager, utilities
from readinglistmanager.model.resource import Resource

class ReadingList(Resource):

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
        lines.append(
            "<ReadingList xmlns:xsd=\"http://www.w3.org/2001/XMLSchema\" xmlns:xsi=\"http://www.w3.org/2001/XMLSchema-instance\">")
        lines.append("<Name>%s</Name>" % (self.name))
        if self.getNumIssues() is not None:
            lines.append("<NumIssues>%s</NumIssues>" % (self.getNumIssues()))
        lines.append("<Source>%s</Source>" % (self.getSourceName()))
        lines.append("<StartYear>%s</StartYear>" % (self.startYear))
        if self.id is not None and utilities.isValidID(self.id):
            lines.append("<Database Name=\"cv\" ID=\"%s\" />" % (self.id))
        lines.append("<Books>")

        # For each issue in arc
        for key, issue in sorted(self.issueList.items()):
            if isinstance(issue, Issue):
                # Check if issue cover date exists
                seriesName = utilities.escapeString(issue.series.name)
                issueNum = utilities.escapeString(issue.issueNumber)

                if issue.hasValidID() or (isinstance(issue.series, Series) and issue.series.hasValidID()):
                    lines.append("<Book Series=\"%s\" Number=\"%s\" Volume=\"%s\" Year=\"%s\">" % (
                        seriesName, issueNum, issue.series.startYear, issue.getYear()))
                    for source in issue.sourceList.getSourcesList():
                        if source.id is not None and source.type is not ComicInformationSource.SourceType.Database:
                            lines.append("<Database Name=\"%s\" Series=\"%s\" Issue=\"%s\" />" % (source.name, issue.series.getSourceID(source.type), source.id))
                    lines.append("</Book>")
                else:
                    lines.append("<Book Series=\"%s\" Number=\"%s\" Volume=\"%s\" Year=\"%s\" />" %
                                 (seriesName, issueNum, issue.series.startYear, issue.getYear()))

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
        listData['StartYear'] = self.startYear
        listData['IssueCount'] = self.getNumIssues()
        #listData['Type'] = None
        listData['Source'] = self.getSourceName()

        if utilities.isValidID(self.id):
            listData['Database'] = list()
            database = {'Name': 'Comicvine', 'ID': self.id}
            listData['Database'].append(database)

        issueData = list()

        for issue in self.issueList.values():
            if isinstance(issue, Issue):
                issueData.append(issue.getJSONDict())

        #listData['Issues'] = dict()
        #for number, issue in self.issueList.items():
        #    if isinstance(issue, Issue):
        #        listData['Issues'][str(number)] = issue.getJSONDict()

        return listData

    def setStartYearFromIssueDetails(self):
        yearCounts = dict()
        issueCount = len(self.issueList)

        if self.issueList is not None and issueCount > 0:
            for number, issue in self.issueList.items():
                if isinstance(issue, Issue) and issue.getYear() is not None:
                    try:
                        curIssueYear = int(issue.getYear())
                    except:
                        continue

                    if curIssueYear < 1900 or curIssueYear > 2030:
                        continue

                    if curIssueYear not in yearCounts:
                        yearCounts[curIssueYear] = 0

                    yearCounts[curIssueYear] += 1

        if len(yearCounts) > 0:
            # Get a sorted list of the years
            listYears = sorted(yearCounts)

            curStartYear = listYears[0]
            curCount = yearCounts[curStartYear]

            n = 1

            #TODO: Improve logic
            if len(listYears) > 1 :
                while(n < len(listYears)):
                    # The prev year is detached from current one!
                    if (listYears[n] - listYears[n-1] >= 2 and 
                        yearCounts[listYears[n-1]] <= 2 and 
                        yearCounts[listYears[n-1]] / issueCount * 100 < 20):
                        # If prev year:
                        #   1. Was 2+ years before next issue
                        #   2. Had only 1 issue 
                        #   3. Composes less than 20% off total issue count
                        # set curStartYear to next year in list
                        curStartYear = listYears[n]
                        curCount = yearCounts[curStartYear]
                    else:
                        # Exit with initial year
                        break
                    
                    n += 1

            #for year, count in sorted(yearCounts.items()):
            #    if curCount == 0:
            #        # First iteration : set starting values
            #        curStartYear = year
            #        curCount = count
            #        continue
            #    elif year - curStartYear >= 2 :
            #        if curCount <= 2 
            #            if count > 1:
            #                curStartYear = year
            #                curCount = count
            #            else:
            #                continue
            #
            self.startYear = curStartYear

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

    def __init__(self, source: Source, listName=None, listID=None):
        super().__init__()
        #try:
        self.source = source
        self._name = None
        self._sourceNameOverride = None
        self.problems = dict()
        self.dynamicName = None
        self.startYear = None
        self.publisher = None
        self.sourceIssueList = None
        self.id = listID
        self.part = None
        self.key = None

        self.dataSourceType = None
        self.checked = dict()
        self.issueList = dict()
        
        if listName is not None:
            self.name = listName
        # elif filePath is not None:
        #    self.name = filePath
        elif isinstance(source, Source) and self.source.type in [ListSourceType.CBL,ListSourceType.TXT]:
            self._getNameFromFile(self.source.file)

        if self.source is not None and isinstance(self.source, Source):
            self.key = ReadingList.getKey(
                self.dynamicName, self.source.type, self.source.name)

        #except Exception as e:
        #    printResults("Error: Problem initialising new list %s [%s] : %s" % (
        #        listName, source, str(e)), 4)

    def __hash__(self):
        return hash((self.dynamicName, self.source))

    @classmethod
    def getKey(self, dynamicListName: str, listSourceType: ListSourceType, listSourceName: str = None):
        keyList = list()
        if dynamicListName is not None and isinstance(dynamicListName, str):
            keyList.append(dynamicListName)
        if listSourceType is not None and isinstance(dynamicListName, ListSourceType):
            keyList.append(listSourceType.value)
        if listSourceName is not None and isinstance(listSourceName, str):
            keyList.append(listSourceName.replace(' ', ''))
        return "-".join(keyList)

    def getSourceName(self):
        if self._sourceNameOverride is not None:
            return self._sourceNameOverride
        elif isinstance(self.source, Source):                
            return self.source.name
        else:
            return "Unknown"

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

        return {'issueCount': issueCount, 'issuesMatched': issuesMatched, 'seriesCount': seriesCount, 'seriesMatched': seriesMatched}

    def isAnnual(self) -> bool:
        return 'annual' in str(self.name).lower()

    def addIssue(self, entryNumber, issue):
        if isinstance(issue, Issue):
            self.issueList[entryNumber] = issue

    def addProblem(self, problemType, extraData=None):
        self.problems[problemType] = extraData

    @classmethod
    def sortListsByReleaseDate(self,readingLists : list):
        if isinstance(readingLists, list):
            for readingList in readingLists:
                readingList.sortListByReleaseDate()

    def sortListByReleaseDate(self):
        if self.source is not None and self.source.type is ListSourceType.TXT:
            # Sort issue list by datestamp
            originalIssueList = list(self.issueList.values())
            sortedIssueList = sorted(originalIssueList,key=lambda x: x.getIssueReleaseDateString())

            # Create numbered dict
            sortedIssueDict = dict()
            i=0

            for issueEntry in sortedIssueList:
                i+=1
                sortedIssueDict[i] = issueEntry

            # Update readinglist issue list
            self.issueList = sortedIssueDict



    @classmethod
    def fromDict(self, matchData: dict, listType: ListSourceType) -> 'ReadingList':
        listSource = Source(matchData['name'], None, listType)
        curList = ReadingList(
            listName=matchData['name'], source=listSource, listID=matchData['listID'])
        curList.issueList = matchData['issues']
        curList.updateDetailsFromDict(matchData)

        return curList

    def updateDetailsFromDict(self, match: dict) -> None:
        # Populate attributes from _seriesDetailsTemplate dict structure
        try:
            self.id = match['listID']
            #self.name = match['name']
            #self.startYear = match['startYear']
            self.publisher = match['publisher']
            self.dateAdded = match['dateAdded']
            self.startYear = match['startYear']
            self.dataSourceType = match['dataSource']
            # self.numIssues = match['numIssues'] Calculated dynamically from self.issueList
            self.sourceIssueList = match['issues']
            self.description = match['description']
            self.summary = match['summary']
            self.detailsFound = True
        except Exception as e:
            printResults("Unable to update list \'%s [%s]\' from match data : %s" % (
                self.name, self.id, match), 4)

    def getNumIssues(self) -> int:
        return len(self.issueList) if self.issueList is not None else None

    def _getNameFromFile(self, fileName):
        file = os.path.basename(fileName)
        fileName, file_extension = os.path.splitext(file)
        self.name = fileName

    def getFileName(self) -> str:
        fileName = list()

        if self.publisher is not None:
            fileName.append("[%s]" % self.publisher)

        #if self.startYear is not None:
        #    fileName.append("(%s)" % self.startYear)

        fileName.append("%s" % (str(self.name)))

        if self.part is not None:
            fileName.append("Part #%s" % str(self.part))

        #sourceName = self.getSourceName()
        #if self._sourceNameOverride is not None:
        #    # String override in effect for WEB source
        #    sourceString = "WEB-%s" % (sourceName)
        #    fileName.append("(%s)" % sourceString)
        #elif isinstance(self.source, Source) and isinstance(self.source.type, ListSourceType):
        #    sourceString = self.source.type.value
        #    if self.source.type == ListSourceType.Website:
        #        sourceString += '-%s' % self.source.name
        #    fileName.append("(%s)" % sourceString)

        return " ".join(fileName)

    def name():
        doc = "The reading list name"

        def fget(self):
            return self._name

        def fset(self, value):
            listWithParts = utilities._getReadingListPart(value)

            if listWithParts:
                self.part = listWithParts['partNumber']
                cleanName = utilities._cleanReadingListName(
                    listWithParts['listName'])
            else:
                cleanName = utilities._cleanReadingListName(value)
                if 'partNumber' in cleanName:
                    self.part = cleanName['partNumber']

            self._name = str(cleanName['listName']).strip()

            #Update source type from CBL to WEB if filename indicates WEB source
            if self.source.type == ListSourceType.CBL and 'source' in cleanName and isinstance(cleanName['source'],str) and utilities._isWebSource(cleanName['source']):
                newSourceName = utilities._getWebSourceName(cleanName['source'])
                self._sourceNameOverride = newSourceName

            self.dynamicName = utilities.getDynamicName(self._name)

        def fdel(self):
            del self._name
        return locals()
    name = property(**name())

    def title():
        doc = "The reading list title (including start year)"

        def fget(self):
            return "%s (%s)" % (self.name,self.startYear)

        return locals()

    title = property(**title())


    def getEventSeriesSummary(readingLists : list) -> list:
        
        textLines = ["Summary of Reading List Series"]

        for curReadingList in readingLists:
            if isinstance(curReadingList, ReadingList):
                textLines.append("\n%s\n-" % curReadingList.title)
                seriesList = dict()

                for listIssueNum, issue in curReadingList.issueList.items():
                    if isinstance(issue, Issue):
                        seriesTitle = issue.series.title
                        if seriesTitle not in seriesList:
                            seriesList[seriesTitle] = []

                        seriesList[seriesTitle].append(issue)
                
                for series, issues in seriesList.items():
                    if isinstance(issues, list):
                        issueNumList = []
                        seriesLength = None

                        for issue in issues:
                            if isinstance(issue, Issue):                     
                                if issue.issueNumber is None or issue.issueNumber in ["", " "]:
                                    pass

                                issueNumList.append(issue.issueNumber)
                                if seriesLength is None and isinstance(issue.series, Series):
                                    seriesLength = issue.series.numIssues

                        # Try to group
                        if "." in issueNumList:
                            pass
                        
                        curIssueList = IssueRangeCollection.fromListOfNumbers(issueNumList)


                        if seriesLength is None:
                            completeStatus = "Unknown"
                        elif len(issues) == seriesLength:
                            completeStatus = "Complete"
                        else:
                            completeStatus = "Incomplete"

                        textLines.append("%s : %s [%s]" % (series, curIssueList.issueRangeString, completeStatus))
        
        return textLines


