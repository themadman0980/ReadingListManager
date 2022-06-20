#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import readinglistmanager
import os,json
from readinglistmanager import utilities, filemanager
from readinglistmanager.problemdata import ProblemData
from readinglistmanager.utilities import printResults
from readinglistmanager import config
from readinglistmanager.db import DataDB
from readinglistmanager.issue import Issue

_seriesList = {}  # Set of all series

class Series:

    count = 0
    dbCounters = {'SearchCount': 0, 'Found': 0, 'NotFound': 0}
    overrideCounters = {'SearchCount': 0, 'Found': 0, 'NotFound': 0, 'Invalid': 0}
    cvCounters = {'SearchCount': 0, 'Found': 0, 'NotFound': 0}
    cvMatchTypes = {'NoMatch': 0, 'OneMatch': 0,
                    'MultipleMatch': 0, 'BlacklistOnlyMatch': 0}
    database = None

    @classmethod
    def getSeries(self, name, startYear):
        if None not in (name, startYear):
            seriesKey = Series.getKey(name, startYear)

            if seriesKey in _seriesList:
                # Match for key found in ist
                return _seriesList.get(seriesKey)
            else:
                # No match! Create series from ID
                newSeries = Series(name, startYear)
                _seriesList[seriesKey] = newSeries
                return newSeries
        else:
            printResults("Warning: Invalid series details for %s (%s)" % (
                name, startYear), 5)
            return None

    def addToDB(self):
        Series.addToDB(self)

    @classmethod
    def addToDB(self, series):

        dbCursor = Series.database.connection.cursor()
        checkVolumeQuery = 'SELECT * FROM cv_volumes WHERE VolumeID=?'
        checkResults = dbCursor.execute(checkVolumeQuery,(series.id,)).fetchall()

        if len(checkResults) > 0:
            # Match already exists!
            printResults("Series %s (%s) [%s] already exists in the DB!" % (
                series.name, series.startYear, series.id),4)
        elif isinstance(series, Series) and series.hasValidID():
            volumeQuery = 'INSERT OR IGNORE INTO cv_volumes (VolumeID,Name,NameClean,StartYear,NumIssues,Publisher,DateAdded) VALUES (?,?,?,?,?,?,?)'
            #if series.numIssues or series.publisher:
            #    if series.numIssues and series.publisher:
            #        # Both!
            #        volumeQuery = ''' INSERT OR IGNORE INTO cv_volumes (VolumeID,Name,NameClean,StartYear,NumIssues,Publisher,DateAdded)
            #                            VALUES (\"%s\",\"%s\",\"%s\",\"%s\",\"%s\",\"%s\",\"%s\")''' % (series.id, series.name, series.nameClean, series.startYear, series.numIssues, series.publisher, dateAdded)
            #    elif series.numIssues:
            #        # NumIssues only
            #        volumeQuery = ''' INSERT OR IGNORE INTO cv_volumes (VolumeID,Name,NameClean,StartYear,NumIssues,DateAdded)
            #                            VALUES (\"%s\",\"%s\",\"%s\",\"%s\",\"%s\",\"%s\")''' % (series.id, series.name, series.nameClean, series.startYear, series.numIssues, dateAdded)
            #    else:
            #        # Publisher only
            #        volumeQuery = ''' INSERT OR IGNORE INTO cv_volumes (VolumeID,Name,NameClean,StartYear,Publisher,DateAdded)
            #                            VALUES (\"%s\",\"%s\",\"%s\",\"%s\",\"%s\",\"%s\")''' % (series.id, series.name, series.nameClean, series.startYear, series.publisher, dateAdded)
            #else:
            #    volumeQuery = ''' INSERT OR IGNORE INTO cv_volumes (VolumeID,Name,NameClean,StartYear,DateAdded)
            #                            VALUES (\"%s\",\"%s\",\"%s\",\"%s\",\"%s\")''' % (series.id, series.name, series.nameClean, series.startYear, dateAdded)
            try:
                # Only add issues with CV match!
                dbCursor.execute(volumeQuery,series.dbEntry)
                Series.database.connection.commit()
            except Exception as e:
                ProblemData.addSeries(series,ProblemData.ProblemType.DBError)
                print("Unable to process series : %s (%s) [%s]" % (
                    series.name, series.startYear, series.id))
                print(str(e))

        dbCursor.close()

    @classmethod
    def validateAll(self):
        for key, series in _seriesList.items():
            series.validate()

    @classmethod
    def getCleanName(self, name):
        if name is not None and isinstance(name, str):
            return utilities.getDynamicName(name)

    @classmethod
    def getCleanStartYear(self, startYear):
        if startYear is not None:
            return utilities.getCleanYear(startYear)

    @classmethod
    def printSummaryResults(self):

        seriesMatched = 0
        seriesComplete = 0
        seriesCount = len(_seriesList)

        for key, series in _seriesList.items():
            if series.hasValidID():
                seriesMatched += 1
            if series.hasCompleteIssueList():
                seriesComplete += 1

        overrideCount = Series.dbCounters['NotFound']
        CVCount = overrideCount - Series.overrideCounters['Found']
        unfoundCount = CVCount - Series.cvCounters['Found']

        # Summary of results:
        printResults("Series: %s" % (Series.count), 2, True)
        printResults("DB Searches: %s, CV Searches = %s" %
                     (Series.dbCounters['SearchCount'], Series.cvCounters['SearchCount']), 3)
        printResults("Number of series matched: %s / %s    (%s)" %
                     (seriesMatched, seriesCount,"{:.0%}".format(seriesMatched/seriesCount)), 3)
        printResults("Number of series complete: %s / %s    (%s)" %
                     (seriesComplete, seriesCount,"{:.0%}".format(seriesComplete/seriesCount)), 3)
        printResults("*** DB ***",3)
        printResults("Match = %s / %s" %
                     (Series.dbCounters['Found'], Series.count), 4)  # One match
        printResults("No Match = %s / %s" %
                     (Series.dbCounters['NotFound'], Series.count), 4)  # One match
        printResults("*** OVERRIDE ***",3)
        printResults("Match = %s / %s" %
                     (Series.overrideCounters['Found'], overrideCount), 4)  # Series ID match found in overrides file
        printResults("Invalid ID = %s / %s" %
                     (Series.overrideCounters['Invalid'], overrideCount), 4)  # Series ID in overrides file not found on CV
        printResults("*** CV ***",3)
        printResults("Match (Single) = %s / %s" %
                     (Series.cvMatchTypes['OneMatch'], CVCount), 4)  # One match
        printResults("Match (Multiple) = %s / %s" %
                     (Series.cvMatchTypes['MultipleMatch'], CVCount), 4)  # Multiple series matches
        printResults("*** NOT FOUND ***",3)
        # Blacklist publisher matches only
        printResults("No Match (Blacklist) = %s / %s" %
                     (Series.cvMatchTypes['BlacklistOnlyMatch'], unfoundCount), 4)
        printResults("No Match (Unfound) = %s / %s" %
                     (Series.cvMatchTypes['NoMatch'], unfoundCount), 4)  # No cv matches

    def __init__(self, curName, curStartYear, curID=None, curPublisher=None, curNumIssues=None, curDateAdded=None, curIssueList=None):
        self._name = ""
        self.name = curName
        self._startYear = curStartYear
        self._publisher = curPublisher
        self._id = curID
        self._numIssues = curNumIssues
        self._dateAdded = curDateAdded
        self._issueList = curIssueList
        self._cvResultsSeries = None
        self._cvResultsIssues = None
        self.key = Series.getKey(self.name, self.startYear)
        if self._issueList is None:
            self._issueList = []
        #self._nameClean = Series.getCleanName(curName)
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

    @classmethod
    def getKey(self, seriesName, seriesStartYear):
        if None not in (seriesName, seriesStartYear):
            return "%s-%s" % (utilities.getDynamicName(seriesName), utilities.getCleanYear(seriesStartYear))
        else:
            return None

    def getIssue(self, issueNumber=None, id=None):
        if issueNumber is None and id is None:
            printResults("Warning: Invalid issue details for %s (%s) #%s [%s]" % (
                self.name,self.startYear,issueNumber, id), 4)
            ProblemData.addSeries(self,ProblemData.ProblemType.IssueError)
            return
        else:
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
                # Check if series exists in overrides file
                self.findOverrideSeriesID()

                # No match found in DB or AltSeriesDetails file - check CV
                if not self.hasValidID():
                    self.findCVSeriesID()

                    # If a new series id match was found in CV, check for volume issue details on CV
                    if self.hasValidID():
                        self.findCVIssueID()

            if self.hasValidID():
                for issue in self.issueList:
                    # Check if issues exist in DB
                    issue.validate(Series.database)

                    # If no matching issue was found in the DB
                    if issue.id is None:
                        self.findCVIssueID()
                        issue.validate(Series.database)

    def findDBSeriesID(self):
        lookupMatches = []
        Series.dbCounters['SearchCount'] += 1
        try:
            dbCursor = Series.database.connection.cursor()
            lookupVolumeQuery = 'SELECT VolumeID,Name,StartYear,NumIssues,Publisher FROM cv_volumes WHERE NameClean=? AND StartYear=?'
            if config.verbose:
                printResults("Searching CV cache for %s (%s)" %
                             (self.nameClean, self.startYearClean), 4)
            # printResults("Looking up series: %s (%s)" % (nameClean, year), 3)
            lookupMatches = dbCursor.execute(lookupVolumeQuery,(self.nameClean, self.startYearClean)).fetchall()
            if config.verbose:
                printResults("%s series matches found in CV Cache for %s (%s)" % (
                    len(lookupMatches), self.name, self.startYear), 4)
            
            dbCursor.close()
        except Exception as e:
            ProblemData.addSeries(self,ProblemData.ProblemType.DBError)
            print("Error while checking series %s (%s)" %
                  (self.name, self.startYear))
            print(e)

        if lookupMatches is not None and len(lookupMatches) > 0:
            if len(lookupMatches) > 1:
                ProblemData.addSeries(self,ProblemData.ProblemType.MultipleMatch)
                printResults("Warning: Multiple DB matches found for %s (%s)" % (
                    self.nameClean, self.startYearClean), 4)
            # There was an exact match. Check publisher preferences
            self.id, self.name, self.startYear, self.numIssues, self.publisher = lookupMatches[0]
            Series.dbCounters['Found'] += 1
        else:
            Series.dbCounters['NotFound'] += 1

        self.checkedDB = True

    def findSeriesData(self):
        found = self.findDBSeriesData()

        if not found:
            # CV search for series ID
            self.findCVSeriesData()


    def findDBSeriesData(self):
        if self.hasValidID():
            lookupMatches = []
            Series.overrideCounters['SearchCount'] += 1
            try:
                dbCursor = Series.database.connection.cursor()
                lookupVolumeQuery = 'SELECT Name,StartYear,NumIssues,Publisher FROM cv_volumes WHERE VolumeID=?'
                if config.verbose:
                    printResults("Searching CV cache for %s" %
                                (self.id), 4)
                lookupMatches = dbCursor.execute(lookupVolumeQuery,(self.id,)).fetchall()
                if config.verbose:
                    printResults("%s series matches found in CV Cache for %s" % (
                        len(lookupMatches), self.id), 4)
                dbCursor.close()
            except Exception as e:
                ProblemData.addSeries(self,ProblemData.ProblemType.DBError)
                printResults("Error while lookup up series [%s] : %s" % (self.id,e),4)

            if lookupMatches is not None and len(lookupMatches) > 0:
                if len(lookupMatches) > 1:
                    ProblemData.addSeries(self,ProblemData.ProblemType.MultipleMatch)
                    printResults("Warning: Multiple DB matches found for [%s]" % (self.id,), 4)
                
                # There was an exact match. Check publisher preferences
                self.id, self.startYear, self.numIssues, self.publisher = lookupMatches[0]
                
                #self.id = lookupMatches[0][0]
                #self.publisher = lookupMatches[0][4]
                #self.numIssues = lookupMatches[0][3]
                
                Series.overrideCounters['Found'] += 1

            self.checkedDB = True
            return len(lookupMatches) > 0

    def findCVSeriesData(self):
        results = []

        if self.hasValidID():
            result = Series.database.findVolumeDetails(self.id)
            
            self.cvResultsSeries = result

            if result is not None:
                Series.overrideCounters['Found'] += 1

                # Exact match found for ID!
                self.name = result.name
                self.startYear = result.start_year
                self.publisher = result.publisher.name
                self.numIssues = result.issue_count
                Series.addToDB(self)
            else:
                Series.overrideCounters['Error'] += 1
                ProblemData.addSeries(self,ProblemData.ProblemType.OverrideError)

        return len(results) > 0

    def findOverrideSeriesID(self):
        if self.key:
            try:
                altDetails = overrideSeriesData[self.key]

                seriesID = altDetails['volumeComicvineID']
                if Series.isValidID(seriesID):
                    self.id = seriesID
                    self.findSeriesData()
                else:
                    ProblemData.addSeries(self,ProblemData.ProblemType.OverrideError)
            except KeyError:
                pass


    def findCVIssueID(self):
        if self.hasValidID() and not self.checkedCVIssues and config.CV.check_issues:
            Series.cvCounters['SearchCount'] += 1

            printResults("Info: Searching CV for issues : %s (%s) [%s]" % (
                self.name, self.startYear, self.id), 4)

            results = Series.database.findIssueMatches(self.id)

            if results is not None:
                printResults("CV : Results = %s" % (len(results)), 5)

                for issue in results:
                    curIssue = self.getIssue(issue.number, issue.id_)
                    curIssue.dateAdded = utilities.getTodaysDate()
                    curIssue.coverDate = utilities.getDateFromString(issue.cover_date)
                    curIssue.name = utilities.stripSymbols(issue.name)
                    if curIssue.id is None:
                        curIssue.id = issue.id_

                    if curIssue.hasValidID() and curIssue.issueNumber is not None:
                        Issue.addToDB(Series.database, curIssue, self)

            self.checkedCVIssues = True

    def findCVSeriesID(self):
        numVolumeResults = 0
        numVolumeMatches = 0

        # TODO: FIX
        if config.CV.check_volumes and self.name is not None:
            Series.cvCounters['SearchCount'] += 1

            matches = {'Preferred':[],'Allowed':[],'Blacklist':[],'NameOnly':[]}
            matchCounter = 0
            results = []
            blacklistPublishers = set()

            #try:
            if config.verbose:
                printResults("Searching for Volume : %s (%s) on CV" %
                            (self.name, self.startYear), 4)

            printResults("Info: Searching CV for series : %s (%s)" %
                        (self.name, self.startYear), 4)
            self.cvResultsSeries = Series.database.findVolumeMatches(self.name)

            if self.cvResultsSeries is not None and len(self.cvResultsSeries) == 0 and ':' in self.name:
                modifiedName = self.name.replace(':','')
                printResults("Info: Searching CV for series : %s (%s)" %
                            (modifiedName, self.startYear), 4)
                self.cvResultsSeries = Series.database.findVolumeMatches(modifiedName)


            if self.cvResultsSeries is None or len(self.cvResultsSeries) == 0:
                printResults("No matches found for %s (%s)" %
                            (self.name, self.startYear), 4)
                Series.cvMatchTypes['NoMatch'] += 1
                ProblemData.addSeries(self,ProblemData.ProblemType.CVNoResults)
            else:  # Results were found
                for result in self.cvResultsSeries:  # Iterate through CV results
                    resultNameClean = utilities.getDynamicName(
                        result.name)
                    resultYearClean = utilities.getCleanYear(
                        result.start_year)
                    # If exact series name and year match
                    #if config.verbose:
                    printResults("Comparing CV \"%s (%s)\" with DB \"%s (%s)\"" % (
                        resultNameClean, resultYearClean, self.nameClean, self.startYearClean), 5)
                    if resultNameClean == self.nameClean:
                        if resultYearClean == self.startYearClean:
                            # Add result to lists
                            curPublisher = result.publisher.name
                            matchCounter += 1

                            if curPublisher in config.CV.publisher_blacklist:
                                matches['Blacklist'].append(result)
                                blacklistPublishers.add(curPublisher)
                            elif curPublisher in config.CV.publisher_preferred:
                                matches['Preferred'].append(result)
                            else:
                                matches['Allowed'].append(result)
                        else:
                            # Incorrect year
                            matches['NameOnly'].append(result)
                    elif self.nameClean in resultNameClean:
                            # Series name is incorrect but similar
                            matches['NameOnly'].append(result)
                                

                numResults = len(self.cvResultsSeries)
                matchesFinal = matches['Preferred'] + matches['Allowed']
                numAllowedMatches = len(matchesFinal)

                if numAllowedMatches < 0:
                    numAllowedMatches = 0

                if matchCounter == 0:
                    Series.cvMatchTypes['NoMatch'] += 1
                    if config.verbose: printResults("No exact matches found for %s (%s)" % (self.name, self.startYear), 4)
                    if len(matches['NameOnly']) > 0:
                        # If dynamicname matches were found, see if the series year was within 2 years of expected
                        deviation = 100
                        for match in matches['NameOnly']:
                            matchYearClean = utilities.getCleanYear(match.start_year)
                            matchNameClean = utilities.getDynamicName(match.name)
                            
                            if self.nameClean == matchNameClean:
                                if None not in (match.start_year, self.startYearClean):
                                    newDeviation = abs(int(matchYearClean) - int(self.startYearClean))
                                    deviation = min(deviation,newDeviation)    

                                    if deviation <= 2:
                                        ProblemData.addSeries(self,ProblemData.ProblemType.CVSimilarMatch)
                            elif self.nameClean in matchNameClean:
                                if None not in (match.start_year, self.startYearClean):
                                    newDeviation = abs(int(matchYearClean) - int(self.startYearClean))
                                    deviation = min(deviation,newDeviation)
                        
                                    if deviation <= 2:
                                        ProblemData.addSeries(self,ProblemData.ProblemType.CVIncorrectYear)
                        
                        ProblemData.addSeries(self,ProblemData.ProblemType.CVNoMatch)

                elif matchCounter == 1:
                    # One match
                    if len(matches['Blacklist']) > 0:
                        Series.cvMatchTypes['BlacklistOnlyMatch'] += 1
                        printResults("No valid results found for %s (%s). %s blacklisted results found with the following publishers: %s" % (
                            self.name, self.startYear, len(matches['Blacklist']), ",".join(blacklistPublishers)), 5)
                    else:
                        Series.cvMatchTypes['OneMatch'] += 1
                        results = matchesFinal
                else:
                    # Multiple matches
                    Series.cvMatchTypes['MultipleMatch'] += 1
                    publishers = set(
                        [vol.publisher.name for vol in matchesFinal])
                    printResults("Warning: Multiple CV matches found! Publishers: %s" % (
                        ", ".join(publishers)), 5)
                    if len(matches['Preferred']) > 0:
                        results = matches['Preferred']
                    elif len(matches['Allowed']) > 0:
                        results = matches['Allowed']
                    else:
                        ProblemData.addSeries(self,ProblemData.ProblemType.CVNoMatch)
                        printResults("No valid results found for %s (%s). %s blacklisted results found." % (
                            self.name, self.startYear, len(matches['Blacklist'])), 5)
                    
                if numAllowedMatches > 1 : ProblemData.addSeries(self,ProblemData.ProblemType.MultipleMatch)

                printResults("CV : Results = %s; Matches = %s" %
                            (numResults, numAllowedMatches), 5)

                # Process results
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
                else:
                    # Add to db search history
                    pass

        #except Exception as e:
        #    printResults("There was an error processing Volume search for %s (%s)" % (
        #        self.name, self.startYear), 4)
        #    print(str(e))

        self.checkedCVVolumes = True

    # Check series name has correct encoding
#    def checkHasValidName(self):
#        #if len(self.name) == len(self.name.encode())
#        if not utilities.hasValidEncoding(self.name):
#            self._name = utilities.fixEncoding(self.name)
#            if not utilities.hasValidEncoding(self.name):
#                ProblemData.addSeries(self,ProblemData.ProblemType.InvalidSeriesNameEncoding)

    @classmethod
    def isValidID(self,ID):
        if ID is not None:
            isDigit = str(ID).isdigit()
            return isDigit
        return False

    def hasValidID(self):
        return Series.isValidID(self.id)

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
            self._name = utilities.fixEncoding(value)
            self._nameClean = Series.getCleanName(value)

        def fdel(self):
            del self._name
        return locals()
    name = property(**name())

    def dbEntry():
        doc = "A tuple of all the DB fields found in data.db"

        def fget(self):
            dateAdded = utilities.getTodaysDate()
            data = (self.id, self.name, self.nameClean, self.startYear, self.numIssues, self.publisher, dateAdded)
            return data

        return locals()
    dbEntry = property(**dbEntry())


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
            if Series.isValidID(value):
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
                return utilities.getCleanYear(self.startYear)

        def fdel(self):
            del self._startYearClean
        return locals()
    startYearClean = property(**startYearClean())

    def issueList():
        doc = "The issueList property."

        def fget(self):
            if self._issueList == None:
                self._issueList = []
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


    def cvResultsIssues():
        doc = "The CV issue results"

        def fget(self):
            return self._cvResultsIssues

        def fset(self, value):
            self._cvResultsIssues = value

        def fdel(self):
            del self._cvResultsIssues
        return locals()
    cvResultsIssues = property(**cvResultsIssues())

    def cvResultsSeries():
        doc = "The CV series results"

        def fget(self):
            return self._cvResultsSeries

        def fset(self, value):
            self._cvResultsSeries = value

        def fdel(self):
            del self._cvResultsSeries
        return locals()
    cvResultsSeries = property(**cvResultsSeries())

def getSeriesOverrideDetails():
    seriesAltData = {}

    altSeriesDataFile = open(os.path.join(filemanager.files.dataDirectory,'SeriesOverrides.json'),'r')
    jsonData = json.load(altSeriesDataFile)
    for altSeries in jsonData:
        dictKey = Series.getKey(altSeries['altSeriesDynamicName'],altSeries['altSeriesStartYear'])
        seriesAltData[dictKey] = altSeries

    return seriesAltData

overrideSeriesData = getSeriesOverrideDetails()
