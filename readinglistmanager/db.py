#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from readinglistmanager import utilities,config
from readinglistmanager.utilities import printResults
from readinglistmanager.datasource import Source, OnlineSource, CVSource
from readinglistmanager.series import Series
import sqlite3

dbConnectionList = []


def connectToSource(source):

    global dbConnectionList

    if isinstance(source, Source) and source.isValidFile():
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


class CVDB(DB):
    def __init__(self, source):
        super().__init__(source)
        if not isinstance(source, CVSource):
            printResults("Error: Invalid source type for CV data!")
        self.createTables()
        if config.Troubleshooting.update_clean_names:
            self.recreateCleanNames()

    def createTables(self):
        cursor = self.connection.cursor()
        cursor.execute('''CREATE TABLE IF NOT EXISTS cv_volumes
                       (VolumeID INT NOT NULL, Name TEXT, StartYear INT, NumIssues INT, Publisher TEXT, NameClean TEXT, DateAdded DATE, DateLastChecked DATE, PRIMARY KEY (VolumeID))''')
        cursor.execute('''CREATE TABLE IF NOT EXISTS cv_issues
                       (IssueID INT NOT NULL, VolumeID INT NOT NULL, Name TEXT, CoverDate DATE, IssueNumber TEXT, DateAdded DATE, DateLastChecked DATE, PRIMARY KEY (IssueID))''')
        cursor.execute('''CREATE TABLE IF NOT EXISTS cv_searches_volumes
                       (Name TEXT, NameClean TEXT, StartYear INT, DateChecked DATE) ''')
        cursor.execute('''CREATE TABLE IF NOT EXISTS cv_searches_issues
                       (SeriesID int NOT NULL, DateChecked DATE) ''')
        self.connection.commit()
        cursor.close()

    def recreateCleanNames(self):
        printResults("Cleaning Volume Names", 2)
        cursor = self.connection.cursor()

        seriesListQuery = ''' SELECT * FROM cv_volumes '''
        seriesList = cursor.execute(seriesListQuery).fetchall()

        for series in seriesList:
            seriesID = series[0]
            seriesName = series[1]
            seriesStartYear = series[2]

            nameClean = utilities.cleanNameString(seriesName)

            updateCleanNameQuery = ''' UPDATE cv_volumes SET NameClean=\"%s\" WHERE VolumeID=\"%s\" ''' % (
                nameClean, seriesID)
            printResults("Updating CleanName for %s : %s" %
                         (seriesID, nameClean), 3)
            cursor.execute(updateCleanNameQuery)
            self.connection.commit()

        cursor.close()

    def addSeries(self, series):
        if series.hasValidID() and config.DB.cache_results:
            dateAdded = utilities.getTodaysDate()
            printResults("Adding %s (%s) [%s] to the DB" % (
                series.name, series.startYear, series.id), 5)
            dbCursor = self.connection.cursor()

            checkVolumeQuery = ''' SELECT * FROM cv_volumes WHERE VolumeID=%s ''' % (
                series.id)
            checkResults = dbCursor.execute(checkVolumeQuery).fetchall()

            if len(checkResults) > 0:
                # Match already exists!
                printResults("Series %s (%s) [%s] already exists in the DB!" % (
                    series.name, series.startYear, series.id))
            else:
                try:
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

                    dbCursor.execute(volumeQuery)
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
                     (self.source.name), 4)
        if isinstance(self.source, OnlineSource):
            cursor = self.connection.cursor()

            try:
                listQuery = ''' SELECT * FROM %s ''' % (
                    self.source.tableReadingListTitles)
                readingListTitles = cursor.execute(listQuery).fetchall()
            except Exception as e:
                printResults("Warning : Unable to find DB table details for %s" % (
                    self.source.name), 5)
                print(e)

            cursor.close()

            return readingListTitles

    # Retrieve issues for each list from DB table

    def getIssueDetails(self, issueID):
        cursor = self.connection.cursor()
        entryQuery = ''' SELECT * FROM %s WHERE hrnum=\"%s\" ''' % (
            self.source.tableIssueDetails, issueID)
        entryMatches = cursor.execute(entryQuery).fetchall()

        return entryMatches

    # Get DB matches
    def getListDetails(self, listEntryID):
        # printResults("Getting issue details for %s" % (list.name), 5)
        # Retrieve list of readinglists from index table
        cursor = self.connection.cursor()
        try:
            # Get all entries in readingList
            listQuery = ''' SELECT * FROM %s WHERE olistnum=\"%s\" ''' % (
                self.source.tableReadingListDetails, listEntryID)
            listResults = cursor.execute(listQuery).fetchall()

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
