#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import readinglistmanager
from readinglistmanager.utilities import printResults
from readinglistmanager import utilities


class Issue:

    count = 0
    dbMatches = 0
    dbMultipleMatches = 0
    idFound = 0

    def __init__(self, issueNumber, series, issueID=None, name=None, coverDate=None):
        self._issueNumber = issueNumber
        self._series = series
        self._id = issueID
        self._name = name
        self._coverDate = coverDate
        self.checkedDB = False
        Issue.count += 1

    @classmethod
    def printSummaryResults(self):
        printResults("Issues: %s" % (Issue.count), 2, True)
        printResults("ID Match (Exact) = %s / %s" %
                     (Issue.dbMatches, Issue.count), 3)  # One match
        printResults("ID Match (Multiple) = %s / %s" %
                     (Issue.dbMultipleMatches, Issue.count), 3)  # One match
        printResults("ID Match (None) = %s / %s" %
                     (Issue.count-Issue.dbMatches, Issue.count), 3)  # One match

    def __eq__(self, other):
        if (isinstance(other, Issue)):
            if self.id and other.id:
                return self.id == other.id
            else:
                return self.series == other.series and self.issueNumber == other.issueNumber
        return False

    def __hash__(self):
        return hash((self.series.nameClean, self.series.startYearClean, self.issueNumber, self.id))

    @classmethod
    def addToDB(self,cvCache, issue, series):
        dbCursor = cvCache.connection.cursor()

        dateAdded = utilities.getTodaysDate()
        coverDate = utilities.parseDate(issue.cover_date)
        checkIssueQuery = ''' SELECT * FROM cv_issues WHERE IssueID=%s ''' % (
            issue.id_)
        checkResults = dbCursor.execute(checkIssueQuery).fetchall()

        if len(checkResults) > 0:
            # Match already exists!
            print("Issue %s [%s] from series %s already exists in the DB!" % (
                issue.number, issue.id_, series.id))
        elif issue.number is not None and str(issue.id_).isdigit():
            #try:
            if issue.name or issue.coverDate:
                if issue.name and issue.coverDate:
                    # Both!
                    issueQuery = ''' INSERT INTO cv_issues (IssueID,VolumeID,IssueNumber,Name,CoverDate,DateAdded)
                                        VALUES (\"%s\",\"%s\",\"%s\",\"%s\",\"%s\",\"%s\")''' % (issue.id_, series.id, issue.number, issue.name, coverDate, dateAdded)
                elif issue.name:
                    # name only
                    issueQuery = ''' INSERT INTO cv_issues (IssueID,VolumeID,IssueNumber,Name,DateAdded)
                                        VALUES (\"%s\",\"%s\",\"%s\",\"%s\",\"%s\")''' % (issue.id_, series.id, issue.number, issue.name, dateAdded)
                else:
                    # coverDate only
                    issueQuery = ''' INSERT INTO cv_issues (IssueID,VolumeID,IssueNumber,CoverDate,DateAdded)
                                        VALUES (\"%s\",\"%s\",\"%s\",\"%s\",\"%s\")''' % (issue.id_, series.id, issue.number, coverDate, dateAdded)

            else:
                issueQuery = ''' INSERT INTO cv_issues (IssueID,VolumeID,IssueNumber,DateAdded)
                                    VALUES (\"%s\",\"%s\",\"%s\",\"%s\")''' % (issue.id_, series.id, issue.number, dateAdded)

            # Only add issues with CV match!
            dbCursor.execute(issueQuery)
            connection.commit()
            #except Exception as e:
            #    print("Unable to process issue for %s : %s [%s]" % (
            #        issue.series.id, issue.number, issue.id))
            #    print(e)

        dbCursor.close()

    def validate(self, cvCache):
        if not self.hasValidID() and not self.checkedDB:
            # Check DB for issue ID match
            self.findDBIssueID(cvCache)

    def findDBIssueID(self, cvCache):

        lookupMatches = []
        if self.series.hasValidID():
            try:
                dbCursor = cvCache.connection.cursor()
                lookupIssuesQuery = ''' SELECT * FROM cv_issues WHERE VolumeID=\"%s\" AND IssueNumber=\"%s\" ''' % (
                    self.series.id, self.issueNumber)
                # printResults("Looking up series: %s (%s)" % (nameClean, year), 3)
                lookupMatches = dbCursor.execute(lookupIssuesQuery).fetchall()
                dbCursor.close()
            except Exception as e:
                print("Error while retrieving issues for [%s]" % (
                    self.series.id))
                print(repr(e))

            if lookupMatches is not None and len(lookupMatches) > 0:
                if len(lookupMatches) > 1:
                    printResults("Warning: More than one issue found for : %s (%s) #%s [%s]" % (
                        self.series.name, self.series.startYear, self.issueNumber, self.series.id), 4)
                    Issue.dbMultipleMatches += 1
                Issue.dbMatches += 1
                self.id = lookupMatches[0][0]
                self.name = lookupMatches[0][2]
                self.coverDate = lookupMatches[0][3]
            else:
                printResults("Warning: No matches found for %s (%s) #%s [%s]" % (
                    self.series.name, self.series.startYear, self.issueNumber, self.series.id), 4)

    # Check that issueID and seriesID exist
    def hasValidID(self):
        if self.id is not None and str(self.id).isdigit() and self.series.hasValidID():
            return True
        return False

    def issueNumber():
        doc = "The issue number"

        def fget(self):
            return self._issueNumber

        def fset(self, value):
            if isinstance(value, (int, str)):
                self._issueNumber = value

        def fdel(self):
            del self._issueNumber
        return locals()
    issueNumber = property(**issueNumber())

    def id():
        doc = "The issue's ComicVine ID"

        def fget(self):
            return self._id

        def fset(self, value):
            if isinstance(value, int):
                if self.id is None:
                    Issue.idFound += 1
                self._id = value

        def fdel(self):
            del self._id
        return locals()
    id = property(**id())

    def name():
        doc = "The issue name"

        def fget(self):
            return self._name

        def fset(self, value):
            if isinstance(value, str):
                self._name = value

        def fdel(self):
            del self._name
        return locals()
    name = property(**name())

    def series():
        doc = "The series object"

        def fget(self):
            return self._series

        def fset(self, value):
            self._series = value

        def fdel(self):
            del self._series
        return locals()
    series = property(**series())

    def coverDate():
        doc = "The issue cover date"

        def fget(self):
            return self._coverDate

        def fset(self, value):
            self._coverDate = value

        def fdel(self):
            del self._coverDate
        return locals()
    coverDate = property(**coverDate())


class ReadingListIssue(Issue):

    def __init__(self, issue, readingListNumber):
        self._issue = issue
        self._listNumber = readingListNumber

    def __getattr__(self, attr):
        return getattr(self._issue, attr)

    def listNumber():
        doc = "The reading list entry number"

        def fget(self):
            return self._listNumber

        def fset(self, value):
            self._listNumber = value

        def fdel(self):
            del self._listNumber
        return locals()
    listNumber = property(**listNumber())
