#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from readinglistmanager.utilities import printResults
from readinglistmanager import utilities
from enum import Enum

class Issue:

    def __init__(self, series, issueNumber : str, dataSourceType):
        if issueNumber is None:
            printResults("Warning: Invalid issue number for %s (%s) [%s] #%s" % (series.name,series.startYear,series.id,issueNumber),5)
        self.issueNumber = str(issueNumber)
        self.series = series
        self.id = None
        self.year = None
        self.name = None
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

    def updateDetailsFromDict(self, match : dict) -> None:
        # Populate attributes from _issueDetailsTemplate dict structure
        try:
            self.id = match['issueID']
            self.name = match['name']
            self.coverDate = match['coverDate']
            self.description = match['description']
            self.summary = match['summary']
            self.issueType = match['issueType']
            self.sourceType = match['dataSource']
            self.detailsFound = True
        except:
            if self.series is not None: 
                printResults("Error: Unable to update issue \'%s (%s) #%s [%s]\' from match data : %s" % (self.series.name, self.series.startYear, self.issueNumber, self.id, match),4)
            else:
                printResults("Error: Unable to update issue #%s [%s] from match data : %s" % (self.issueNumber, self.id, match),4)


    def coverDateString():
        doc = "The issue's coverdate in String format"

        def fget(self):

            return utilities.getStringFromDate(self.coverDate)
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
            'CoverDate': self.coverDateString,
            'Database': {
                'Name':'Comicvine',
                'SeriesID': self.series.id, 
                'IssueID': self.id
                }
            }
        return data