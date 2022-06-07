#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from readinglistmanager import utilities
from readinglistmanager.utilities import printResults
from readinglistmanager import config
import time
from readinglistmanager.issue import Issue


class Series:

    count = 0
    dbCounters = {'SearchCount': 0, 'Found': 0, 'NotFound': 0}
    cvCounters = {'SearchCount': 0, 'Found': 0, 'NotFound': 0}
    cvMatchTypes = {'NoMatch': 0, 'OneMatch': 0,
                    'MultipleMatch': 0, 'BlacklistOnlyMatch': 0}
    cvCache = None

    seriesList = []

    @classmethod
    def getSeries(self, name=None, startYear=None, id=None):
        # Look for series by ID
        if id is not None and str(id).isdigit():
            # Check if there is an existing match for this id
            for series in Series.seriesList:
                if series.id == id:
                    return series

            # No match! Create series from ID
            printResults(
                "No existing series instance found for [%s]" % (id), 4)
            newSeries = Series(None, None, id)
            Series.seriesList.append(newSeries)

            return newSeries
        # Look for series by name + startYear
        elif name is not None and name != "" and startYear is not None:
            # Check if there is an existing match for this id
            for series in Series.seriesList:
                if series.nameClean == Series.getCleanName(name) and series.startYearClean == Series.getCleanStartYear(startYear):
                    return series

            # No match! Create series from ID
            printResults("No existing series instance found for %s (%s)" %
                         (name, startYear), 4)
            newSeries = Series(name, startYear)
            Series.seriesList.append(newSeries)

            return newSeries

    @classmethod
    def validateAll(self, cvCacheConnection, cvSession):
        for series in Series.seriesList:
            series.validate(cvCacheConnection, cvSession)

    @classmethod
    def getCleanName(self, name):
        if name is not None and isinstance(name, str):
            return utilities.cleanNameString(name)

    @classmethod
    def getCleanStartYear(self, startYear):
        if startYear is not None:
            return utilities.cleanYearString(startYear)

    @classmethod
    def printSummaryResults(self):

        seriesMatched = 0
        seriesComplete = 0
        seriesCount = len(Series.seriesList)

        for series in Series.seriesList:
            printResults("Series : %s (%s) [%s]" % (
                series.name, series.startYear, series.id), 4)
            for issue in series.issueList:
                printResults("Issue: #%s [%s]" %
                             (issue.issueNumber, issue.id), 5)
            if series.hasValidID():
                seriesMatched += 1
            if series.hasCompleteIssueList():
                seriesComplete += 1

        # Summary of results:
        printResults("Series: %s" % (Series.count), 2, True)
        printResults("Number of series matched: %s / %s" %
                     (seriesMatched, seriesCount), 3)
        printResults("Number of series complete: %s / %s" %
                     (seriesComplete, seriesCount), 3)
#        printResults("Match (DB) = %s / %s" %
#                     (Series.dbCounters['Found'], Series.count), 3)  # One match
#        printResults("Match (CV-Single) = %s" %
#                     (Series.cvMatchTypes['OneMatch']), 3)  # One match
#        printResults("Match (CV-Multiple) = %s" %
#                     (Series.cvMatchTypes['MultipleMatch']), 3)  # Multiple series matches
#        # Blacklist publisher matches only
#        printResults("No Match (CV-Blacklist) = %s" %
#                     (Series.cvMatchTypes['BlacklistOnlyMatch']), 3)
#        printResults("No Match (Unfound) = %s / %s" %
#                     (Series.cvMatchTypes['NoMatch'], Series.count), 3)  # No cv matches

    def __init__(self, name, startYear, id=None, publisher=None, numIssues=None, dateAdded=None, issueList=[]):
        self._name = name
        self._startYear = startYear
        self._publisher = publisher
        # self._id = id if str(id).isdigit() else None
        self._id = id
        self._numIssues = numIssues
        self._dateAdded = dateAdded
        self._issueList = issueList
        self._nameClean = Series.getCleanName(name)
        self._startYearClean = self.getCleanStartYear(startYear)
        self.checkedCVVolumes = False
        self.checkedCVIssues = False
        self.checkedDB = False
        self.cvResults = None

        Series.count += 1

    def __eq__(self, other):
        if (isinstance(other, Series)):
            if self.id and other.id:
                return self.id == other.id
            else:
                return self.nameClean == other.nameClean and self.startYearClean == other.startYearClean
        return False

    def __hash__(self):
        return hash((self.nameClean, self.startYearClean))

    def getIssue(self, issueNumber=None, id=None):
        # Match issue from ID
        if id is not None and str(id).isdigit():
            for issue in self.issueList:
                if issue.id == id:
                    return issue

        # Match issue from number
        if issueNumber is not None:
            for issue in self.issueList:
                if issue.issueNumber == issueNumber:
                    print("Issue match found: '%s' == '%s'" %
                          (issue.issueNumber, issueNumber))
                    return issue

        # No match found. Create issue
        printResults("No existing issue instance found for %s (%s) #%s [%s]" % (
            self.name, self.startYear, issueNumber, id), 5)
        newIssue = Issue(issueNumber, self, id)
        self._issueList.append(newIssue)

        return newIssue

    def validate(self, cvCacheConnection, cvSession):
        if not self.hasValidID() and not self.checkedDB:
            if config.verbose:
                printResults("Validating series : %s (%s) [%s]" % (
                    self.name, self.startYear, self.id), 3)
            # ID missing and DB hasn't been checked yet
            self.findDBSeriesID(cvCacheConnection)

            #if self.hasValidID():
            #self.findDBIssueIDs(cvCacheConnection)

        if config.verbose:
            printResults("DB match : %s" % (self.id), 4)

        if not self.hasValidID():
            # No match found in DB - check CV
            self.findCVSeriesID(cvCacheConnection, cvSession)

            # If a new id match was found, check for issues on CV
            if self.hasValidID():
                self.findCVIssueID(cvCacheConnection, cvSession)

        # Check if issues exist in DB
        for issue in self.issueList:
            issue.validate(cvCacheConnection)

    def findDBSeriesID(self, cvCacheConnection):
        lookupMatches = []
        Series.dbCounters['SearchCount'] += 1
        try:
            dbCursor = cvCacheConnection.cursor()
            lookupVolumeQuery = ''' SELECT * FROM cv_volumes WHERE NameClean=\"%s\" AND StartYear=\"%s\" ''' % (
                self.nameClean, self.startYearClean)
            if config.verbose:
                printResults("Searching CV cache for %s (%s)" %
                             (self.nameClean, self.startYearClean), 4)
            # printResults("Looking up series: %s (%s)" % (nameClean, year), 3)
            lookupMatches = dbCursor.execute(lookupVolumeQuery).fetchall()
            if config.verbose:
                printResults("%s series matches found in CV Cache for %s (%s)" % (
                    len(lookupMatches), self.name, self.startYear), 4)
            dbCursor.close()
        except Exception as e:
            print("Error while checking series %s (%s)" %
                  (self.name, self.startYear))
            print(e)

        if lookupMatches is not None and len(lookupMatches) > 0:
            if len(lookupMatches) > 1:
                printResults("Warning: Multiple DB matches found for %s (%s)" % (
                    self.nameClean, self.startYearClean), 4)
            # There was an exact match. Check publisher preferences
            self.id = lookupMatches[0][0]
            self.publisher = lookupMatches[0][4]
            self.numIssues = lookupMatches[0][3]
            Series.dbCounters['Found'] += 1
        else:
            Series.dbCounters['NotFound'] += 1

        self.checkedDB = True

    def findCVIssueID(self, cvCacheConnection, CVSession):
        if self.hasValidID() and not self.checkedCVIssues and config.CV.check_issues:
            try:
                time.sleep(utilities.getCVSleepTimeRemaining())
                results = CVSession.issue_list(
                    params={"filter": "volume:%s" % (self.id)})
            except Exception as e:
                printResults(
                    "There was an error processing CV search for issues for [%s]" % (self.id), 4)
                printResults(e, 4)

            for issue in results:
                # CV API format for results
                number = issue.number
                issueID = issue.id
                name = issue.name
                coverDate = issue.cover_date

                if issueID is not None and str(issueID).isdigit() and number is not None:
                    Issue.addToDB(number, issueID, self.ID, name, coverDate)

            self.checkedCVIssues = True

    def findCVSeriesID(self, dbConnection, cvSession):
        numVolumeResults = 0
        numVolumeMatches = 0
        numCVMatchOne = 0
        numCVMatchMultiple = 0
        numCVNoMatchBlacklist = 0
        numCVNoMatch = 0

        # TODO: FIX
        if config.CV.check_volumes:
            Series.cvCounters['SearchCount'] += 1

            results = []
            series_matches = []
            blacklist_matches = []
            allowed_matches = []
            preferred_matches = []

            try:
                if config.verbose:
                    printResults("Searching for Volume : %s (%s) on CV" %
                                 (self.name, self.startYear), 4)
                if self.name is not None:
                    time.sleep(utilities.getCVSleepTimeRemaining())
                    self.cvResults = cvSession.volume_list(
                        params={"filter": "name:%s" % (self.name)})

                numVolumeResults = len(self.cvResults)

                if self.cvResults is None or numVolumeResults == 0:
                    printResults("No matches found for %s (%s)" %
                                 (self.name, self.startYear), 4)
                    numCVNoMatch += 1
                else:  # Results were found
                    for result in self.cvResults:  # Iterate through CV results
                        resultNameClean = utilities.cleanNameString(
                            result.name)
                        resultYearClean = utilities.cleanYearString(
                            result.start_year)
                        # If exact series name and year match
                        printResults("Comparing CV \"%s (%s)\" with DB \"%s (%s)\"" % (
                            resultNameClean, resultYearClean, self.nameClean, self.startYearClean), 4)
                        if resultNameClean == self.nameClean and resultYearClean == self.startYearClean:
                            # Add result to lists
                            series_matches.append(result)
                            curPublisher = result.publisher.name

                            if curPublisher in config.CV.publisher_blacklist:
                                blacklist_matches.append(result)
                            elif curPublisher in config.CV.publisher_preferred:
                                preferred_matches.append(result)
                            else:
                                allowed_matches.append(result)

                    numVolumeMatches = len(
                        series_matches) - len(blacklist_matches)
                    if numVolumeMatches < 0:
                        numVolumeMatches = 0

                    if len(series_matches) == 0:
                        numCVNoMatch += 1
                        if config.verbose:
                            printResults("No exact matches found for %s (%s)" %
                                         (self.name, self.year), 4)
                    elif len(series_matches) == 1:
                        # One match
                        if len(blacklist_matches) > 0:
                            numCVNoMatchBlacklist += 1
                            printResults("No valid results found for %s (%s). %s blacklisted results found with the following publishers: %s" % (
                                self.name, self.year, len(blacklist_matches), ",".join(blacklist_matches)), 5)
                        else:
                            numCVMatchOne += 1
                            results = series_matches
                    else:
                        # Multiple matches
                        numCVMatchMultiple += 1
                        publishers = set(
                            [vol.publisher.name for vol in series_matches])
                        printResults("Warning: Multiple CV matches found! Publishers: %s" % (
                            ", ".join(publishers)), 5)
                        if len(preferred_matches) > 0:
                            results = preferred_matches
                        elif len(allowed_matches) > 0:
                            results = allowed_matches
                        else:
                            printResults("No valid results found for %s (%s). %s blacklisted results found." % (
                                self.name, self.year, len(blacklist_matches)), 5)

                    printResults("CV : Results = %s; Matches = %s" %
                                 (numVolumeResults, numVolumeMatches), 4)

                    self.processCVResults(results)

            except Exception as e:
                printResults("There was an error processing Volume search for %s (%s)" % (
                    self.name, self.year), 4)
                printResults(e, 4)

        self.checkedCVVolumes = True

    def processCVResults(self, results):
        issueCounter = 0
        publisher = seriesID = numIssues = None

        if len(results) > 0:
            for result in results:
                curNumIssues = result.issue_count
                curPublisher = result.publisher.name
                curID = result.id
                curName = result.name
                curYear = result.start_year

                curSeries = Series.getSeries(curName, curYear, curID)
                curSeries.publisher = curPublisher
                curSeries.numIssues = curNumIssues

                # Add result to DB
                Series.addToDB(curSeries)

                # Check if current series has more issues than any other preferred results!
                if curNumIssues > issueCounter:
                    publisher = curPublisher
                    seriesID = curID
                    numIssues = curNumIssues
                    issueCounter = curNumIssues

            self.id = seriesID
            self.publisher = publisher
            self.numIssues = numIssues

    def hasValidID(self):
        if self.id is not None:
            return str(self.id).isdigit()
        return False

    def hasCompleteDetails(self):
        if self.hasValidID() and self.hasCompleteIssueList() and None not in (self.name, self.startYear, self.publisher, self.numIssues):
            return True
        return False

    def hasCompleteIssueList(self):
        print("'%s' == '%s'" % (len(self.issueList), self.numIssues))
        if self.issueList is not None and self.numIssues is not None:
            return len(self.issueList) == self.numIssues

    def name():
        doc = "The series' name"

        def fget(self):
            return self._name

        def fset(self, value):
            if value != "":
                self._name = value
                self._nameClean = Series.getCleanName(self.name)

        def fdel(self):
            del self._name
        return locals()
    name = property(**name())

    def startYear():
        doc = "The series' start year"

        def fget(self):
            return self._startYear

        def fset(self, value):
            if value != "":
                self._startYear = value
                self._startYearClean = Series.getCleanStartYear(self.startYear)

        def fdel(self):
            del self._startYear
        return locals()
    startYear = property(**startYear())

    def publisher():
        doc = "The series' publisher"

        def fget(self):
            return self._publisher

        def fset(self, value):
            self._publisher = value

        def fdel(self):
            del self._publisher
        return locals()
    publisher = property(**publisher())

    def id():
        doc = "The series' ComicVine ID"

        def fget(self):
            return self._id

        def fset(self, value):
            if str(value).isdigit():
                self._id = value

        def fdel(self):
            del self._id
        return locals()
    id = property(**id())

    def nameClean():
        doc = "The cleaned version of the 'name' field"

        def fget(self):
            return self._nameClean
        return locals()
    nameClean = property(**nameClean())

    def startYearClean():
        doc = "The cleaned version of the 'startYear' field"

        def fget(self):
            if self.startYear is not None:
                return utilities.cleanYearString(self.startYear)

        def fdel(self):
            del self._startYearClean
        return locals()
    startYearClean = property(**startYearClean())

    def issueList():
        doc = "The issueList property."

        def fget(self):
            return self._issueList

        def fdel(self):
            del self._issueList
        return locals()
    issueList = property(**issueList())

    def numIssues():
        doc = "The number of issues in this series according to CV"

        def fget(self):
            return self._numIssues

        def fset(self, value):
            self._numIssues = value

        def fdel(self):
            del self._numIssues
        return locals()
    numIssues = property(**numIssues())
