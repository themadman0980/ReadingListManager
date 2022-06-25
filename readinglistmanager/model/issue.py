#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from readinglistmanager.utilities import printResults
from readinglistmanager import utilities
from enum import Enum

class Issue:

    def __init__(self, series, issueNumber, dataSourceType):
        if issueNumber is None:
            printResults("Warning: Invalid issue number for %s (%s) [%s] #%s" % (series.name,series.startYear,series.id,issueNumber),5)
        self.issueNumber = issueNumber
        self.series = series
        self.id = None
        self.year = None
        self.name = None
        self.coverDate = None
        self.description = None
        self.summary = None
        self.issueType = None
        self.dataSourceType = dataSourceType
        self.checkedDB = False
        self.checkedType = False
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
        return hash((self.series.nameClean, self.series.startYearClean, self.issueNumber, self.id))

    def validate(self):
        if not self.hasValidID() and not self.checkedDB:
            # Check DB for issue ID match
            #self.findDBIssueID(database)
            pass

    # Check that issueID and seriesID exist
    def hasValidID(self):
        if self.id is not None and str(self.id).isdigit():
            return True
        return False

    def updateDetailsFromDict(self, match : dict) -> None:
        # Populate attributes from _issueDetailsTemplate dict structure
        try:
            self.id = match['issueID']
            self.name = match['name']
            self.coverDate = match['coverDate']
            self.description = match['description']
            self.summary = match['summary']
            self.issueType = match['issueType']
            self.dataSourceType = match['dataSourceType']
            self.detailsFound = True
        except:
            printResults("Error: Unable to update issue \'%s (%s) #%s\' from match data : %s" % (self.series.name, self.series.startYear, self.issueNumber, match),4)

    def coverDateString():
        doc = "The issue's coverdate in String format"

        def fget(self):

            return utilities.getStringFromDate(self.coverDate)
        return locals()
    coverDateString = property(**coverDateString())

    def getDict(self) -> dict:
        data = {
            'issueID': self.id, 
            'seriesID': self.series.id, 
            'name': self.name, 
            'coverDate': self.coverDateString, 
            'issueNum': self.issueNumber, 
            'description': self.description, 
            'summary': self.summary, 
            'dateAdded': self.dateAdded}
        return data