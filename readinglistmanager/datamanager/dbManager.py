#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from readinglistmanager import utilities, config,filemanager,utilities
from readinglistmanager.errorhandling import problemdata
from readinglistmanager.utilities import printResults
from readinglistmanager.datamanager.datasource import ComicInformationSource, Source, ListSourceType
import sqlite3, datetime

dbConnectionList = []

def connectToSource(source) -> sqlite3.Connection:
    global dbConnectionList

    if isinstance(source, Source) and (source.type == ListSourceType.Website or source.name == 'Database'):
        for db in dbConnectionList:
            if db['source'].file == source.file:
                # return existing connection
                return db['connection']
        # No match found, so return new connection
        try:
            newConnection = sqlite3.connect(source.file)
            newDB = {'source': source, 'connection': newConnection}
            dbConnectionList.append(newDB)
            return newConnection
        except Exception as e:
            print(e)
        return None

class DB:
    def __init__(self, source):
        self.source = source
        self.connection = None
        self.setDBConnection()

    def setDBConnection(self):
        self.connection = connectToSource(self.source)
        if self.connection == None:
            printResults("Error: Connection to db failed for %s" %
                         (self.source.file), 2)

class DataDB(DB,ComicInformationSource):

    instance = None
    type = ComicInformationSource.SourceType.Database
    
    @classmethod
    def get(self):    
        if DataDB.instance is None: 
            DataDB.instance = DataDB()

        return DataDB.instance


    def __init__(self):
        databaseSource = Source("Database", filemanager.dataFile)
        DB.__init__(self,databaseSource)
        ComicInformationSource.__init__(self)
        self.createTables()
        #if config.Troubleshooting.update_clean_names:
        #    self.recreateCleanNames()

    def convertIssueResultsToDict(self, issueResults : list, resultsType : ComicInformationSource.ResultType) -> list[dict]:
        results = []
        self.updateCounter(ComicInformationSource.SearchStatusType.SearchCount,resultsType)

        if issueResults is not None and len(issueResults) > 0:
            for result in issueResults:
                curResult = ComicInformationSource._issueDetailsTemplate.copy()
                issueID,seriesID,name,coverDate,issueNum,description,summary = result
                issueType = ComicInformationSource._getIssueType(name, description, summary)
                try: 
                    coverDate = utilities.getDateFromString(coverDate)
                except: 
                    printResults("Error: Unable to process cover date \"%s\"" % (coverDate,), 4)
                curResult.update({
                    'issueID':issueID, 
                    'seriesID':seriesID, 
                    'name':name, 
                    'coverDate':coverDate,
                    'issueNum':str(issueNum),
                    'issueType':issueType,
                    'description':description,
                    'summary':summary,
                    'dataSource':self.type
                    })
                results.append(curResult)
        
        if len(results) == 0:
            self.updateCounter(ComicInformationSource.SearchStatusType.NoResultsCount,resultsType)
        else:
            self.updateCounter(ComicInformationSource.SearchStatusType.ResultsCount,resultsType)

        return results

    def convertSeriesResultsToDict(self, seriesResults : list, resultsType : ComicInformationSource.ResultType) -> list[dict]:
        # Check for multiple results and return dict of first match and any problems identified
        results = []
        self.updateCounter(ComicInformationSource.SearchStatusType.SearchCount,resultsType)

        if seriesResults is not None and len(seriesResults) > 0:
            # Check for problem data
            for result in seriesResults:
                curResult = ComicInformationSource._seriesDetailsTemplate.copy()
                seriesID, name, startYear, numIssues, publisher = result
                curResult.update({
                    'seriesID':seriesID,
                    'name':name,
                    'startYear':startYear,
                    'publisher':publisher,
                    'numIssues':numIssues,
                    'dataSource':self.type
                    })
                results.append(curResult)
        
        if len(results) == 0:
            self.updateCounter(ComicInformationSource.SearchStatusType.NoResultsCount,resultsType)
        else:
            self.updateCounter(ComicInformationSource.SearchStatusType.ResultsCount,resultsType)

        return results

    def getSeriesFromSeriesID(self, seriesID : str) -> list[dict]:
        results = None
        resultsType = ComicInformationSource.ResultType.Series

        try:
            dbCursor = self.connection.cursor()
            lookupVolumeQuery = 'SELECT VolumeID,Name,StartYear,NumIssues,Publisher FROM cv_volumes WHERE VolumeID=?'
            results = dbCursor.execute(lookupVolumeQuery,(seriesID,)).fetchall()
            dbCursor.close()
            results = self.convertSeriesResultsToDict(results, resultsType)
        except Exception as e:
            printResults("DB Error : Series Lookup [%s] : %s" % (seriesID,str(e)),4)


        return results

    def getSeriesFromDetails(self, name : str, startYear : int) -> list[dict]:
        results = None
        resultsType = ComicInformationSource.ResultType.Series

        dynamicName = utilities.getDynamicName(name)

        try:
            dbCursor = self.connection.cursor()
            lookupVolumeQuery = 'SELECT VolumeID,Name,StartYear,NumIssues,Publisher FROM cv_volumes WHERE NameClean=? AND StartYear=?'
            results = dbCursor.execute(lookupVolumeQuery,(dynamicName, startYear)).fetchall()            
            dbCursor.close()
            results = self.convertSeriesResultsToDict(results, resultsType)
        except Exception as e:
            printResults("DB Error : Series Lookup \"%s (%s)\" : %s" % (name, startYear, str(e)),4)
        
        return results


    def getIssueFromIssueID(self, issueID : str) -> dict:
        results = None
        resultsType = ComicInformationSource.ResultType.Issue

        try:
            dbCursor = self.connection.cursor()
            lookupIssuesQuery = 'SELECT IssueID,VolumeID,Name,CoverDate,IssueNumber,Description,Summary FROM cv_issues WHERE IssueID=?'
            results = dbCursor.execute(lookupIssuesQuery,(issueID,)).fetchall()
            dbCursor.close()
            results = self.convertIssueResultsToDict(results, resultsType)
        except Exception as e:
            printResults("DB Error : Issue from ID [%s] : %s" % (issueID, str(e)),4)


        return results

    def getIssueFromDetails(self, seriesID : str, issueNumber : str) -> dict:
        results = None
        resultsType = ComicInformationSource.ResultType.Issue

        try:
            dbCursor = self.connection.cursor()
            lookupIssuesQuery = 'SELECT IssueID,VolumeID,Name,CoverDate,IssueNumber,Description,Summary FROM cv_issues WHERE VolumeID=? AND IssueNumber=?'
            results = dbCursor.execute(lookupIssuesQuery,(seriesID, issueNumber)).fetchall()
            dbCursor.close()
            results = self.convertIssueResultsToDict(results, resultsType)
        except Exception as e:
            printResults("DB Error : Issue from Series ID [%s] and #%s : %s" % (seriesID,issueNumber,str(e)),4)

        return results

    def getIssuesFromSeriesID(self, seriesID : str) -> dict[dict]:
        resultsDict = dict()
        resultsType = ComicInformationSource.ResultType.IssueList

        try:
            dbCursor = self.connection.cursor()
            lookupIssuesQuery = 'SELECT IssueID,VolumeID,Name,CoverDate,IssueNumber,Description,Summary FROM cv_issues WHERE VolumeID=?'
            results = dbCursor.execute(lookupIssuesQuery,(seriesID,)).fetchall()
            dbCursor.close()
            resultsList = self.convertIssueResultsToDict(results, resultsType)
            for result in resultsList:
                resultsDict[result['issueNum']] = result
        except Exception as e:
            printResults("DB Error : IssueList from Series ID [%s] : %s" % (seriesID,e),4)

        return resultsDict


    def createTables(self):
        cursor = self.connection.cursor()
        cursor.execute('''CREATE TABLE IF NOT EXISTS cv_volumes
                       (VolumeID INT NOT NULL, Name TEXT, StartYear INT, NumIssues INT, Publisher TEXT, NameClean TEXT, DateAdded DATE, DateLastChecked DATE, PRIMARY KEY (VolumeID))''')
        cursor.execute('''CREATE TABLE IF NOT EXISTS cv_volume_overrides
                       (VolumeID INT NOT NULL, AltSeriesName TEXT, AltSeriesStartYear INT, PRIMARY KEY (AltSeriesName, AltSeriesStartYear))''')
        cursor.execute('''CREATE TABLE IF NOT EXISTS cv_issues
                       (IssueID INT NOT NULL, VolumeID INT NOT NULL, Name TEXT, CoverDate DATE, IssueNumber TEXT, Description TEXT, Summary TEXT, DateAdded DATE, DateLastChecked DATE, PRIMARY KEY (IssueID))''')
        self.connection.commit()
        cursor.close()

    def recreateCleanNames(self):
        printResults("Cleaning DB volume names", 2)
        cursor = self.connection.cursor()

        seriesList = cursor.execute('SELECT VolumeID,Name FROM cv_volumes').fetchall()

        for series in seriesList:
            seriesID,seriesName = series
            dynamicName = utilities.getDynamicName(seriesName)
            printResults("Updating CleanName for %s : %s" % (seriesID, dynamicName), 3)
            cursor.execute('UPDATE cv_volumes SET NameClean=? WHERE VolumeID=?',(dynamicName, seriesID))
            self.connection.commit()

        cursor.close()

    # Add a series to the DB
    def addVolume(self, seriesDetails : dict) -> None:
        if utilities.isValidID(seriesDetails['seriesID']):
            dateAdded = utilities.getTodaysDate()
            printResults("Adding %s (%s) [%s] to the DB" % (
                seriesDetails['name'], seriesDetails['startYear'], seriesDetails['seriesID']), 5)
            dbCursor = self.connection.cursor()

            checkResults = dbCursor.execute('SELECT * FROM cv_volumes WHERE VolumeID=?',(seriesDetails['seriesID'],)).fetchall()

            if len(checkResults) > 0:
                # Match already exists in DB!
                printResults("Series %s (%s) [%s] already exists in the DB!" % (
                    seriesDetails['name'], seriesDetails['startYear'], seriesDetails['seriesID']))
            else:
                #try:
                dynamicName = utilities.getDynamicName(seriesDetails['name'])
                curSeries = (seriesDetails['seriesID'], seriesDetails['name'], dynamicName, seriesDetails['startYear'], seriesDetails['numIssues'], seriesDetails['publisher'], dateAdded)
                dbCursor.execute('INSERT OR IGNORE INTO cv_volumes (VolumeID,Name,NameClean,StartYear,NumIssues,Publisher,DateAdded) VALUES (?,?,?,?,?,?,?)',curSeries)
                self.connection.commit()
                dbCursor.close()
                #except Exception as e:
                #    printResults("Unable to process series : %s (%s) [%s] - %s" % (
                #        seriesDetails['name'], seriesDetails['startYear'], seriesDetails['seriesID'], str(e)),4)

    # Add an issue to the DB
    def addIssue(self, issueDetails : dict) -> None:
        dbCursor = self.connection.cursor()

        checkIssueQuery = 'SELECT * FROM cv_issues WHERE IssueID=?'
        checkResults = dbCursor.execute(checkIssueQuery, (issueDetails['issueID'],)).fetchall()

        if len(checkResults) > 0:
            # Match already exists!
            if config.verbose: print("Issue #%s [%s] from series [%s] already exists in the DB!" % (issueDetails['issueNum'], issueDetails['issueID'], issueDetails['seriesID']))
        elif utilities.isValidID(issueDetails['issueID']) and issueDetails['issueNum'] is not None:
            if isinstance(issueDetails['coverDate'],datetime.date):
                coverDate = utilities.getStringFromDate(issueDetails['coverDate'])
            else:
                coverDate = issueDetails['coverDate']

            issueDetailsTuple = (issueDetails['issueID'],issueDetails['seriesID'],issueDetails['name'],coverDate,issueDetails['issueNum'],issueDetails['description'],issueDetails['summary'],issueDetails['dateAdded'])
            try:            
                issueQuery = 'INSERT INTO cv_issues (IssueID,VolumeID,Name,CoverDate,IssueNumber,Description,Summary,DateAdded) VALUES (?,?,?,?,?,?,?,?)'
                # Only add issues with CV match!
                dbCursor.execute(issueQuery,issueDetailsTuple)
                self.connection.commit()
            except Exception as e:
                printResults("Unable to process issue for %s : %s [%s] - %s" % (
                    issueDetails['seriesID'], issueDetails['issueNum'], issueDetails['issueID'], str(e)),4)
        dbCursor.close()

class ListDB(DB):
    def __init__(self, source):
        super().__init__(source)

    # Retrieve list of readinglists from index table
    def getListNames(self):
        printResults("Getting list names for source: %s" %
                     (self.source.name), 3)
        if self.source.type == ListSourceType.Website:
            readingListTitles = []
            cursor = self.connection.cursor()

            try:
                listQuery = ''' SELECT olistnum, name FROM %s ''' % (
                    self.source.tableReadingListTitles)
                readingListTitles = cursor.execute(listQuery).fetchall()
            except Exception as e:
                print("Caught error:", e)
                printResults("Warning : Unable to find DB table details for %s: %s" % (
                    self.source.name, e), 5)

            cursor.close()

            return readingListTitles

    # Retrieve issues for each list from DB table

    def getIssueDetails(self, issueID):
        cursor = self.connection.cursor()
        entryQuery = ''' SELECT hrnum, series, start_year, issue, story FROM %s WHERE hrnum=?; ''' % (
            self.source.tableIssueDetails, )
        entryParam = (issueID, )
        entryMatches = cursor.execute(entryQuery, entryParam).fetchall()

        return entryMatches

    # Get DB matches
    def getListDetails(self, listEntryID):
        # Retrieve list of readinglists from index table
        cursor = self.connection.cursor()
        try:
            # Get all entries in readingList
            listQuery = ''' SELECT olistnum, hrnum, read_order FROM %s WHERE olistnum=?; ''' % (
                self.source.tableReadingListDetails, )
            listParams = (listEntryID, )
            listResults = cursor.execute(listQuery, listParams).fetchall()

        except Exception as e:
            printResults("Warning : Unable to find list details for %s : %s" % (
                self.source.name, listEntryID), 5)
            print(e)

        cursor.close()

        return listResults