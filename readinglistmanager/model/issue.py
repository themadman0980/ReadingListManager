#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from readinglistmanager.utilities import printResults
from readinglistmanager import utilities
from enum import Enum
from readinglistmanager.model.date import PublicationDate


class Issue:

    def __init__(self, series, issueNumber : str, dataSourceType):
        if issueNumber is None:
            printResults("Warning: Invalid issue number for %s (%s) [%s] #%s" % (series.name,series.startYear,series.id,issueNumber),5)
        self.issueNumber = str(issueNumber)
        self.series = series
        self.listReferences = set()
        self.id = None
        self.year = None
        self.name = None
        self.sourceDate = None
        self.coverDate = None
        self.description = None
        self.summary = None
        self.issueType = None
        self.sourceType = dataSourceType
        self.detailsFound = False

    #@classmethod
    #def printSummaryResults(self):
    #    printResults("Issues: %s" % (Issue.count), 2, True)
    #    #TODO: Correctly process new cv matches
    #    printResults("ID Match (DB - Exact) = %s / %s    (%s)" %
    #                 (Issue.dbMatches, Issue.count,"{:.1%}".format(Issue.dbMatches/Issue.count)), 3)  # One match
    #    printResults("ID Match (DB - Multiple) = %s / %s    (%s)" %
    #                 (Issue.dbMultipleMatches, Issue.count,"{:.1%}".format(Issue.dbMultipleMatches/Issue.count)), 3)  # One match
    #    printResults("ID Match (None) = %s / %s    (%s)" %
    #                 (Issue.dbNoMatch, Issue.count,"{:.1%}".format(Issue.dbNoMatch/Issue.count)), 3)  # One match

    def __eq__(self, other):
        if (isinstance(other, Issue)):
            if self.id and other.id:
                return self.id == other.id
            else:
                return self.series == other.series and self.issueNumber == other.issueNumber
        return False

    def __hash__(self):
        return hash((self.series.dynamicName, self.series.startYear, self.issueNumber, self.id))

    # Check that issueID and seriesID exist
    def hasValidID(self):
        return utilities.isValidID(self.id)

    @classmethod
    def fromDict(self, match : dict):
        newIssue = Issue(None,match['issueNum'],match['dataSource'])
        newIssue.updateDetailsFromDict(match)
        return newIssue

    def addReadingListRef(self,readingList):
        self.listReferences.add(readingList)

    def getReadingListRefs(self):
        return self.listReferences

    def updateDetailsFromDict(self, match : dict) -> None:
        # Populate attributes from _issueDetailsTemplate dict structure
        try:
            self.id = match['issueID']
            self.name = match['name']
            self.setCoverDate(match['coverDate'])
            self.description = match['description']
            self.summary = match['summary']
            self.issueType = match['issueType']
            self.sourceType = match['dataSource']
            self.detailsFound = True
        except Exception as e:
            if self.series is not None: 
                printResults("Error: Unable to update issue \'%s (%s) #%s [%s]\' from match data : %s" % (self.series.name, self.series.startYear, self.issueNumber, self.id, match),4)
                printResults("Exception: %s" % (e),4)
            else:
                printResults("Error: Unable to update issue #%s [%s] from match data : %s" % (self.issueNumber, self.id, match),4)
                printResults("Exception: %s" % (e),4)

    def setSourceDate(self, issueDate : PublicationDate):
        if isinstance(issueDate, PublicationDate):
            self.sourceDate = issueDate
        elif issueDate is not None:
            try:
                self.sourceDate = PublicationDate(issueDate)
            except Exception as e:
                pass

    def setCoverDate(self, coverDate : PublicationDate):
        if isinstance(coverDate, PublicationDate):
            self.coverDate = coverDate
        elif coverDate is not None:
            try:
                self.coverDate = PublicationDate(coverDate)
            except Exception as e:
                pass

        if isinstance(self.coverDate, PublicationDate):
            self.year = self.coverDate.year

    def getYear(self):
        if self.coverDate is not None and isinstance(self.coverDate, PublicationDate):
            return self.coverDate.year
        if self.sourceDate is not None and isinstance(self.sourceDate, PublicationDate):
            return self.sourceDate.year

        return None

    def coverDateString():
        doc = "The issue's coverdate in String format"

        def fget(self):
            if self.coverDate is not None and isinstance(self.coverDate, PublicationDate):
                return self.coverDate.getString()

            return ""
        return locals()
    coverDateString = property(**coverDateString())

    def getDBDict(self) -> dict:
        data = {
            'issueID': self.id, 
            'seriesID': self.series.id, 
            'name': self.name, 
            'coverDate': self.coverDateString, 
            'issueNum': self.issueNumber, 
            'description': self.description, 
            'summary': self.summary}
        return data
    
    def getJSONDict(self) -> dict:
        data = {
            'SeriesName': self.series.name,
            'SeriesStartYear': self.series.startYear,
            'IssueNum': self.issueNumber,
            'IssueType': None,
            'CoverDate': self.coverDateString,
            'Database': {
                'Name':'Comicvine',
                'SeriesID': self.series.id, 
                'IssueID': self.id
                }
            }

        if self.issueType is not None:
            data.update({'IssueType': self.issueType.value})

        return data