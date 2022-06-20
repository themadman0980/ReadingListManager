#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from readinglistmanager import utilities, config
from readinglistmanager.filemanager import files
from readinglistmanager.utilities import printResults
from readinglistmanager.datasource import Source, OnlineSource, DataSource
#from readinglistmanager.series import Series
import sqlite3
import time
from simyan.comicvine import Comicvine
from simyan.sqlite_cache import SQLiteCache

dbConnectionList = []


def connectToSource(source):

    global dbConnectionList

    if isinstance(source, Source):
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
        self._source = source
        self._connection = None
        self.setDBConnection()

    def setDBConnection(self):
        self._connection = connectToSource(self._source)
        if self._connection == None:
            printResults("Error: Connection to db failed for %s" %
                         (self.source.file), 2)

    def connection():
        doc = "The db connection"

        def fget(self):
            return self._connection

        def fdel(self):
            self._connection.close()
            del self._connection
        return locals()
    connection = property(**connection())

    def source():
        doc = "The db source details"

        def fget(self):
            return self._source

        def fset(self, value):
            if isinstance(value, Source):
                self._source = value
                self.setDBConnection()

        def fdel(self):
            del self._source
        return locals()
    source = property(**source())


class DataDB(DB):

    searchCount = 0

    def __init__(self, source):
        super().__init__(source)
        self.lastSearchedTimestamp = 0
        self.cvSession = Comicvine(api_key=config.CV.api_key, cache=SQLiteCache(files.cvCacheFile,60))

        if not isinstance(source, DataSource):
            printResults("Error: Invalid source type for CV data!")
        self.createTables()
        if config.Troubleshooting.update_clean_names:
            self.recreateCleanNames()

#    def getCVSleepTimeRemaining(self):
#        #get time since last CV API call
#        timeDif = (utilities.getCurrentTimeStamp()
#                   - self._lastSearchedTimestamp) / 1000
#        return max(0, config.CV.api_rate - timeDif)

    def findVolumeMatches(self, name):
        results = None
        try:
            #time.sleep(self.getCVSleepTimeRemaining())
            self._lastSearchedTimestamp = utilities.getCurrentTimeStamp()
            results = self.cvSession.volume_list(
                params={"filter": "name:%s" % (name)})
        except Exception as e:
            printResults("There was an error processing CV search for %s" % (name), 4)
            printResults(str(e), 4)

        return results

    def findIssueMatches(self, seriesID):
        results = None
        
        try:
            #time.sleep(self.getCVSleepTimeRemaining())
            self._lastSearchedTimestamp = utilities.getCurrentTimeStamp()
            results = self.cvSession.issue_list(
                params={"filter": "volume:%s" % (seriesID)})
            DataDB.searchCount += 1
            if len(results) == 0:
                printResults("Warning: No issues found for series [%s]" % (seriesID), 4)
        except Exception as e:
            printResults("Error: Unable to search for CV issues for [%s]" % (seriesID), 4)
            printResults(str(e), 4)

        return results
    
    def findVolumeDetails(self,seriesID):
        results = None
        try:
            results = self.cvSession.volume(seriesID)
            DataDB.searchCount += 1
            if results is None:
                printResults("Warning: No volume found for [%s]" % (seriesID), 4)
        except Exception as e:
            printResults("Error: Unable to search for CV volume [%s]" % (seriesID), 4)
            printResults(str(e), 4)

        return results


    def createTables(self):
        cursor = self.connection.cursor()
        cursor.execute('''CREATE TABLE IF NOT EXISTS cv_volumes
                       (VolumeID INT NOT NULL, Name TEXT, StartYear INT, NumIssues INT, Publisher TEXT, NameClean TEXT, DateAdded DATE, DateLastChecked DATE, PRIMARY KEY (VolumeID))''')
        cursor.execute('''CREATE TABLE IF NOT EXISTS cv_volume_overrides
                       (VolumeID INT NOT NULL, AltSeriesName TEXT, AltSeriesStartYear INT, PRIMARY KEY (AltSeriesName, AltSeriesStartYear))''')
        cursor.execute('''CREATE TABLE IF NOT EXISTS cv_issues
                       (IssueID INT NOT NULL, VolumeID INT NOT NULL, Name TEXT, CoverDate DATE, IssueNumber TEXT, DateAdded DATE, DateLastChecked DATE, PRIMARY KEY (IssueID))''')
        #cursor.execute('''CREATE TABLE IF NOT EXISTS cv_searches_volumes
        #               (Name TEXT, NameClean TEXT, StartYear INT, DateChecked DATE) ''')
        #cursor.execute('''CREATE TABLE IF NOT EXISTS cv_searches_issues
        #               (SeriesID int NOT NULL, DateChecked DATE) ''')
        self.connection.commit()
        cursor.close()

    def recreateCleanNames(self):
        printResults("Cleaning Volume Names", 2)
        cursor = self.connection.cursor()

        seriesList = cursor.execute('SELECT * FROM cv_volumes').fetchall()

        for series in seriesList:
            seriesID = series[0]
            seriesName = series[1]
            seriesStartYear = series[2]

            nameClean = utilities.cleanNameString(seriesName)

            printResults("Updating CleanName for %s : %s" %
                         (seriesID, nameClean), 3)
            cursor.execute('UPDATE cv_volumes SET NameClean=? WHERE VolumeID=?',(nameClean, seriesID))
            self.connection.commit()

        cursor.close()

    def addSeries(self, series):
        if series.hasValidID():
            dateAdded = utilities.getTodaysDate()
            printResults("Adding %s (%s) [%s] to the DB" % (
                series.name, series.startYear, series.id), 5)
            dbCursor = self.connection.cursor()

            checkResults = dbCursor.execute('SELECT * FROM cv_volumes WHERE VolumeID=?',(series.id,)).fetchall()

            if len(checkResults) > 0:
                # Match already exists in DB!
                printResults("Series %s (%s) [%s] already exists in the DB!" % (
                    series.name, series.startYear, series.id))
            else:
                try:
                    curSeries = (series.id, series.name, series.nameClean, series.startYear, series.numIssues, series.publisher, dateAdded)
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

                    dbCursor.execute('INSERT OR IGNORE INTO cv_volumes (VolumeID,Name,NameClean,StartYear,NumIssues,Publisher,DateAdded) VALUES (?,?,?,?,?,?,?)',curSeries)
                    self.connection.commit()
                    dbCursor.close()
                except Exception as e:
                    print("Unable to process series : %s (%s) [%s]" % (
                        series.name, series.startYear, series.id))
                    print(e)


class OnlineDB(DB):
    def __init__(self, source):
        super().__init__(source)

    # Retrieve list of readinglists from index table
    def getListNames(self):
        printResults("Getting list names for source: %s" %
                     (self.source.name), 3)
        if isinstance(self.source, OnlineSource):
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
        entryQuery = ''' SELECT hrnum, pubdate, title, series, start_year, issue, story FROM %s WHERE hrnum=?; ''' % (
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

    def readingListNames():
        doc = "A list of the reading lists associated with this source."

        def fget(self):
            return self._readingListNames

        def fset(self, value):
            self._readingListNames = value

        def fdel(self):
            del self._readingListNames
        return locals()
    readingListNames = property(**readingListNames())
