#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import readinglistmanager
from readinglistmanager.utilities import printResults
from readinglistmanager import problemdata
from readinglistmanager import config


class Issue:

    count = 0
    dbMatches = 0
    dbNoMatch = 0
    dbMultipleMatches = 0
    idFound = 0

    def __init__(self, issueNumber, series, issueID=None, name=None, coverDate=None):
        if issueNumber is None:
            printResults("Warning: Invalid issue number for %s (%s) [%s] #%s" % (series.name,series.startYear,series.id,issueNumber),5)
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
        printResults("ID Match (Exact) = %s / %s    (%s)" %
                     (Issue.dbMatches, Issue.count,"{:.1%}".format(Issue.dbMatches/Issue.count)), 3)  # One match
        printResults("ID Match (Multiple) = %s / %s    (%s)" %
                     (Issue.dbMultipleMatches, Issue.count,"{:.1%}".format(Issue.dbMultipleMatches/Issue.count)), 3)  # One match
        printResults("ID Match (None) = %s / %s    (%s)" %
                     (Issue.dbNoMatch, Issue.count,"{:.1%}".format(Issue.dbNoMatch/Issue.count)), 3)  # One match

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
    def addToDB(self,database, issue, series):
        dbCursor = database.connection.cursor()

        checkIssueQuery = ''' SELECT * FROM cv_issues WHERE IssueID=%s ''' % (
            issue.id)
        checkResults = dbCursor.execute(checkIssueQuery).fetchall()

        if len(checkResults) > 0:
            # Match already exists!
            if config.verbose: print("Issue %s [%s] from series %s already exists in the DB!" % (issue.issueNumber, issue.id, series.id))
        elif issue.hasValidID() and issue.issueNumber is not None:
            #try:
            if issue.name or issue.coverDate:
                if issue.name and issue.coverDate:
                    # Both!
                    issueQuery = ''' INSERT INTO cv_issues (IssueID,VolumeID,IssueNumber,Name,CoverDate,DateAdded)
                                        VALUES (\"%s\",\"%s\",\"%s\",\"%s\",\"%s\",\"%s\")''' % (issue.id, series.id, issue.issueNumber, issue.name, issue.coverDate, issue.dateAdded)
                elif issue.name:
                    # name only
                    issueQuery = ''' INSERT INTO cv_issues (IssueID,VolumeID,IssueNumber,Name,DateAdded)
                                        VALUES (\"%s\",\"%s\",\"%s\",\"%s\",\"%s\")''' % (issue.id, series.id, issue.issueNumber, issue.name, issue.dateAdded)
                else:
                    # coverDate only
                    issueQuery = ''' INSERT INTO cv_issues (IssueID,VolumeID,IssueNumber,CoverDate,DateAdded)
                                        VALUES (\"%s\",\"%s\",\"%s\",\"%s\",\"%s\")''' % (issue.id, series.id, issue.issueNumber, issue.coverDate, issue.dateAdded)

            else:
                issueQuery = ''' INSERT INTO cv_issues (IssueID,VolumeID,IssueNumber,DateAdded)
                                    VALUES (\"%s\",\"%s\",\"%s\",\"%s\")''' % (issue.id, series.id, issue.issueNumber, issue.dateAdded)

            # Only add issues with CV match!
            dbCursor.execute(issueQuery)
            database.connection.commit()
            #except Exception as e:
            #    print("Unable to process issue for %s : %s [%s]" % (
            #        issue.series.id, issue.number, issue.id))
            #    print(e)

        dbCursor.close()

    def validate(self, database):
        if not self.hasValidID() and not self.checkedDB:
            # Check DB for issue ID match
            self.findDBIssueID(database)

    def findDBIssueID(self, database):

        lookupMatches = []
        if self.series.hasValidID() and self.issueNumber is not None:
            try:
                dbCursor = database.connection.cursor()
                lookupIssuesQuery = 'SELECT * FROM cv_issues WHERE VolumeID=? AND IssueNumber=?'
                # printResults("Looking up series: %s (%s)" % (nameClean, year), 3)
                lookupMatches = dbCursor.execute(lookupIssuesQuery,(self.series.id, self.issueNumber)).fetchall()
                dbCursor.close()
            except Exception as e:
                printResults("Error while retrieving issues for [%s] : %s" % (self.series.id,e),4)

            if lookupMatches is not None and len(lookupMatches) > 0:
                if len(lookupMatches) > 1:
                    printResults("Warning: More than one issue found for : %s (%s) #%s [%s]" % (
                        self.series.name, self.series.startYear, self.issueNumber, self.series.id), 4)
                    Issue.dbMultipleMatches += 1
                Issue.dbMatches += 1
                self.id = lookupMatches[0][0]
                self.name = lookupMatches[0][2]
                self.coverDate = readinglistmanager.utilities.getDateFromString(lookupMatches[0][3])
            else:
                Issue.dbNoMatch += 1
                if config.verbose: printResults("Info: No matches found for %s (%s) #%s [%s]" % (
                    self.series.name, self.series.startYear, self.issueNumber, self.series.id), 4)
                problemdata.ProblemData.addSeries(self.series,problemdata.ProblemData.ProblemType.IssueNotFound)
        else:
            pass
            #printResults("Info: Unable to find issue: %s (%s) [%s] #%s" % (self.series.name, self.series.startYear, self.series.id,self.issueNumber), 4)

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
    
    def year():
        doc = "The issue year"

        def fget(self):
            return self._coverDate

        return locals()
    year = property(**year())


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
