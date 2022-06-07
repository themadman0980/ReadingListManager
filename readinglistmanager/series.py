#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from readinglistmanager import utilities
from readinglistmanager.utilities import printResults
from readinglistmanager import config
from readinglistmanager.db import CVDB
from readinglistmanager.issue import Issue

_seriesList = []

class Series:

    count = 0
    dbCounters = {'SearchCount': 0, 'Found': 0, 'NotFound': 0}
    cvCounters = {'SearchCount': 0, 'Found': 0, 'NotFound': 0}
    cvMatchTypes = {'NoMatch': 0, 'OneMatch': 0,
                    'MultipleMatch': 0, 'BlacklistOnlyMatch': 0}
    cvCache = None


    @classmethod
    def getSeries(self,name=None, startYear=None, id=None):
        # Look for series by ID
        if id is not None and str(id).isdigit():
            # Check if there is an existing match for this id
            for series in _seriesList:
                if series.id == id:
                    return series

            # No match! Create series from ID
            newSeries = Series(None, None, id)
            _seriesList.append(newSeries)

            return newSeries
        # Look for series by name + startYear
        elif name is not None and name != "" and startYear is not None:
            # Check if there is an existing match for this id
            for series in _seriesList:
                if series.nameClean == Series.getCleanName(name) and series.startYearClean == Series.getCleanStartYear(startYear):
                    return series

            # No match! Create series from ID
            newSeries = Series(name, startYear)
            _seriesList.append(newSeries)

            return newSeries

    @classmethod
    def addToDB(self,series):

        dbCursor = Series.cvCache.connection.cursor()
        checkVolumeQuery = ''' SELECT * FROM cv_volumes WHERE VolumeID=%s ''' % (series.id)
        checkResults = dbCursor.execute(checkVolumeQuery).fetchall()

        if len(checkResults) > 0:
            # Match already exists!
            printResults("Series %s (%s) [%s] already exists in the DB!" % (name, startYear, seriesID))
        elif isinstance(series,Series) and series.hasValidID():
            dateAdded = utilities.getTodaysDate()
            #try:
            if series.numIssues or series.publisher:
                if series.numIssues and series.publisher:
                    # Both!
                    volumeQuery = ''' INSERT OR IGNORE INTO cv_volumes (VolumeID,Name,NameClean,StartYear,NumIssues,Publisher,DateAdded)
                                        VALUES (\"%s\",\"%s\",\"%s\",\"%s\",\"%s\",\"%s\",\"%s\")''' % (series.id, series.name, series.nameClean, series.startYear, series.numIssues, series.publisher, dateAdded)
                elif series.numIssues:
                    # NumIssues only
                    volumeQuery = ''' INSERT OR IGNORE INTO cv_volumes (VolumeID,Name,NameClean,StartYear,NumIssues,DateAdded)
                                        VALUES (\"%s\",\"%s\",\"%s\",\"%s\",\"%s\",\"%s\")''' % (series.id, series.name, series.nameClean, series.startYear, series.numIssues, dateAdded)
                else:
                    # Publisher only
                    volumeQuery = ''' INSERT OR IGNORE INTO cv_volumes (VolumeID,Name,NameClean,StartYear,Publisher,DateAdded)
                                        VALUES (\"%s\",\"%s\",\"%s\",\"%s\",\"%s\",\"%s\")''' % (series.id, series.name, series.nameClean, series.startYear, series.publisher, dateAdded)
            else:
                volumeQuery = ''' INSERT OR IGNORE INTO cv_volumes (VolumeID,Name,NameClean,StartYear,DateAdded)
                                        VALUES (\"%s\",\"%s\",\"%s\",\"%s\",\"%s\")''' % (series.id, series.name, series.nameClean, series.startYear, dateAdded)

            # Only add issues with CV match!
            dbCursor.execute(volumeQuery)
            Series.cvCache.connection.commit()

            #except Exception as e:
            #    print("Unable to process series : %s (%s) [%s]" % (name, startYear, seriesID))
            #    print(e)

        dbCursor.close()



    @classmethod
    def validateAll(self):
        for series in _seriesList:
            series.validate()

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
        seriesCount = len(_seriesList)

        for series in _seriesList:
            if series.hasValidID():
                seriesMatched += 1
            if series.hasCompleteIssueList():
                seriesComplete += 1

        # Summary of results:
        printResults("Series: %s" % (Series.count), 2, True)
        printResults("DB Searches: %s, CV Searches = %s" %
                (Series.dbCounters['SearchCount'], Series.cvCounters['SearchCount']), 3)
        printResults("Number of series matched: %s / %s" %
                     (seriesMatched, seriesCount), 3)
        printResults("Number of series complete: %s / %s" %
                     (seriesComplete, seriesCount), 3)
        printResults("Match (DB) = %s / %s" %
                     (Series.dbCounters['Found'], Series.count), 3)  # One match
        printResults("No Match (DB) = %s / %s" %
                     (Series.dbCounters['NotFound'], Series.count), 3)  # One match
        printResults("Match (CV-Single) = %s / %s" %
                     (Series.cvMatchTypes['OneMatch'], Series.count), 3)  # One match
        printResults("Match (CV-Multiple) = %s / %s" %
                     (Series.cvMatchTypes['MultipleMatch'], Series.count), 3)  # Multiple series matches
        # Blacklist publisher matches only
        printResults("No Match (CV-Blacklist) = %s / %s" %
                     (Series.cvMatchTypes['BlacklistOnlyMatch'], Series.count), 3)
        printResults("No Match (Unfound) = %s / %s" %
                     (Series.cvMatchTypes['NoMatch'], Series.count), 3)  # No cv matches

    def __init__(self, curName, curStartYear, curID=None, curPublisher=None, curNumIssues=None, curDateAdded=None, curIssueList=None):
        self._name = curName
        self._startYear = curStartYear
        self._publisher = curPublisher
        self._id = curID
        self._numIssues = curNumIssues
        self._dateAdded = curDateAdded
        self._issueList = curIssueList
        if self._issueList is None:
            self._issueList = []
        self._nameClean = Series.getCleanName(curName)
        self._startYearClean = Series.getCleanStartYear(curStartYear)
        self.checkedCVVolumes = False
        self.checkedCVIssues = False
        self.checkedDB = False

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
                    return issue

        # No match found. Create issue
        newIssue = Issue(issueNumber, self, id)
        self._issueList.append(newIssue)

        return newIssue

    def validate(self):
        if not self.hasValidID() and not self.checkedDB:
            if config.verbose:
                printResults("Validating series : %s (%s) [%s]" % (
                    self.name, self.startYear, self.id), 3)
            # ID missing and DB hasn't been checked yet
            self.findDBSeriesID()

            #if self.hasValidID():
            #self.findDBIssueIDs(cvCacheConnection)

        if config.verbose:
            printResults("DB match : %s" % (self.id), 4)

        if not self.hasValidID():
            # No match found in DB - check CV
            self.findCVSeriesID()

            # If a new series id match was found in CV, check for volume issue details on CV
            if self.hasValidID():
                self.findCVIssueID()

        for issue in self.issueList:                
            # Check if issues exist in DB
            issue.validate(Series.cvCache)

            # If no matching issue was found in the DB
            if issue.id is None:
                self.findCVIssueID()
                issue.validate(Series.cvCache)

    def findDBSeriesID(self):
        lookupMatches = []
        Series.dbCounters['SearchCount'] += 1
        try:
            dbCursor = Series.cvCache.connection.cursor()
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

    def findCVIssueID(self):
        if self.hasValidID() and not self.checkedCVIssues and config.CV.check_issues:
            Series.cvCounters['SearchCount'] += 1

            if CVDB.searchCount < config.Troubleshooting.api_query_limit:
                printResults("Info: Searching CV for issues : %s (%s) [%s]" % (self.name,self.startYear,self.id),4)

            results = Series.cvCache.findIssueMatches(self.id)

            for issue in results:
                curIssue = self.getIssue()
                if issue.id_ is not None and str(issue.id_).isdigit() and issue.number is not None:
                    Issue.addToDB(Series.cvCache,issue,self)

            self.checkedCVIssues = True

    def findCVSeriesID(self):
        numVolumeResults = 0
        numVolumeMatches = 0

        # TODO: FIX
        if config.CV.check_volumes and self.name is not None:
            Series.cvCounters['SearchCount'] += 1

            results = []
            series_matches = []
            blacklist_matches = []
            allowed_matches = []
            preferred_matches = []

            #try:
            if config.verbose:
                printResults("Searching for Volume : %s (%s) on CV" %
                                (self.name, self.startYear), 4)
            
            if CVDB.searchCount < config.Troubleshooting.api_query_limit:
                printResults("Info: Searching CV for series : %s (%s)" % (self.name,self.startYear),4)
            cvResults = Series.cvCache.findVolumeMatches(self.name)

            if cvResults is None or len(cvResults) == 0:
                printResults("No matches found for %s (%s)" %
                                (self.name, self.startYear), 4)
                Series.cvMatchTypes['NoMatch'] += 1
            else:  # Results were found
                for result in cvResults:  # Iterate through CV results
                    resultNameClean = utilities.cleanNameString(
                        result.name)
                    resultYearClean = utilities.cleanYearString(
                        result.start_year)
                    # If exact series name and year match
                    if config.verbose: printResults("Comparing CV \"%s (%s)\" with DB \"%s (%s)\"" % (
                        resultNameClean, resultYearClean, self.nameClean, self.startYearClean), 5)
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
                    Series.cvMatchTypes['NoMatch'] += 1
                    if config.verbose:
                        printResults("No exact matches found for %s (%s)" %
                                        (self.name, self.startYear), 4)
                elif len(series_matches) == 1:
                    # One match
                    if len(blacklist_matches) > 0:
                        Series.cvMatchTypes['BlacklistOnlyMatch'] += 1
                        printResults("No valid results found for %s (%s). %s blacklisted results found with the following publishers: %s" % (
                            self.name, self.startYear, len(blacklist_matches), ",".join(blacklist_matches)), 5)
                    else:
                        Series.cvMatchTypes['OneMatch'] += 1
                        results = series_matches
                else:
                    # Multiple matches
                    Series.cvMatchTypes['MultipleMatch'] += 1
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
                            self.name, self.startYear, len(blacklist_matches)), 5)

                printResults("CV : Results = %s; Matches = %s" %
                                (numVolumeResults, numVolumeMatches), 4)

                self.processCVResults(results)

            #except Exception as e:
            #    printResults("There was an error processing Volume search for %s (%s)" % (
            #        self.name, self.startYear), 4)
            #    printResults(e, 4)

        self.checkedCVVolumes = True

    def processCVResults(self, results):
        issueCounter = 0
        publisher = seriesID = numIssues = None

        if len(results) > 0:
            for result in results:
                curNumIssues = result.issue_count
                curPublisher = result.publisher.name
                curID = result.id_
                curName = result.name
                curYear = result.start_year

                curSeries = Series.getSeries(curName, curYear)
                curSeries.id = curID
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
            if self._issueList == None: self._issueList=[]
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
