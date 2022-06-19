#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from readinglistmanager import filemanager,datasource,db
from readinglistmanager.utilities import printResults
import os
from readinglistmanager.readinglist import ReadingList
from readinglistmanager.series import Series
from readinglistmanager.issue import Issue
import xml.etree.ElementTree as ET

readingListDB = [
    {'SourceName': 'cmro', 'DBTables': {
        'ReadingLists': 'ReadingListsView', 'ReadingListDetails': 'ReadingListDetailsView', 'IssueDetails': 'ComicsView'
        }},
    #{'SourceName': 'dcro', 'DBTables': {
    #    'ReadingLists': 'olists', 'ReadingListDetails': 'olistcom', 'IssueDetails': 'comics'
    #    }}
    ]


def parseCBLfiles(database):
    readingLists = []

    printResults("Checking CBL files in %s" %
                 (filemanager.files.readingListDirectory), 2)
    for root, dirs, files in os.walk(filemanager.files.readingListDirectory):
        for file in files:
            if file.endswith(".cbl") and not file.startswith('._'):
                try:
                    filename = os.path.join(root, file)
                    # print("Parsing %s" % (filename))
                    tree = ET.parse(filename)
                    fileroot = tree.getroot()

                    cblinput = fileroot.findall("./Books/Book")

                    readingList = ReadingList(
                        file, datasource.CBLSource(file, filename), database)

                    i = 0
                    count = len(cblinput)
                    printResults("Updating issue data for reading list : %s [%s]" % (
                        readingList.name, readingList.source.type), 3)

                    for entry in cblinput:
                        i += 1
                        printResults("Processing %s / %s" % (i,count),4,False,True)

                        curSeries = None
                        # ,'issueYear':entry.attrib['Year']}
                        seriesName = entry.attrib['Series']
                        seriesStartYear = entry.attrib['Volume']
                        issueNumber = entry.attrib['Number']
                        curSeries = Series.getSeries(seriesName, seriesStartYear)
                        curIssue = curSeries.getIssue(issueNumber)
                        #for series in Series.seriesList:
                        #    print("%s (%s) [%s]" % (series.name,
                        #          series.startYear, series.id))
                        #    for issue in series.issueList:
                        #        print("#%s [%s]" % (issue.issueNumber, issue.id))
                        readingList.addIssue(curIssue, i)
                    if len(readingList.issueList) == 0:
                        printResults(
                            "Warning: No issues found for list : %s" % (file), 4)

                    readingLists.append(readingList)
                except Exception as e:
                    printResults("Unable to process file at %s" %
                                 (os.path.join(str(root), str(file))), 3)
                    printResults(repr(e), 3)

    return readingLists


def getOnlineLists(database):

    onlineLists = []

    for listSourceObject in readingListDB:
        # Create Source object
        sourceName = listSourceObject['SourceName']
        sourceFile = os.path.join(
            filemanager.files.dataDirectory, sourceName + ".db")
        sourceTable = listSourceObject['DBTables']

        curSource = datasource.OnlineSource(
            sourceName, sourceFile, sourceTable)

        # Create DB connection
        curDB = db.OnlineDB(curSource)

        curListNames = curDB.getListNames()

        for readingList in curListNames:
            listID = readingList[0]
            listName = readingList[1]

            curReadingList = ReadingList(
                listName, curSource, database, None, listID)

            # Get all reading list entries from readinglist DB table
            printResults("Getting issue details for %s" % (curReadingList.name), 3)
            curListDetails = curDB.getListDetails(curReadingList.id)

            count = len(curListDetails)
            i = 0

            # Get details for each list entry from issue DB table
            for listEntry in curListDetails:
                i += 1
                printResults("Processing %s / %s" % (i,count),4,False,True)
                listEntryNum = listEntry[1]
                listEntryID = listEntry[2]

                entryMatches = curDB.getIssueDetails(listEntryID)
                #printResults("%s entries found for hrnum='%s'" % (len(entryMatches), listEntryID), 5)

                numMatches = len(entryMatches)

                if numMatches > 0:
                    if numMatches > 1:
                        printResults("Warning: Multiple db entries found for issue with hrnum='%s' in %s" % (
                            listEntryID, readingList.name), 4)
                    for issueEntry in entryMatches:
                        _, _, _, seriesName, seriesStartYear, seriesIssueNum, _ = issueEntry

                    if seriesName is None or seriesStartYear is None:
                        printResults("Error: Invalid series data found for name='%s' startYear='%s')" % (seriesName,seriesStartYear),4)
                    else:
                        curSeries = Series.getSeries(seriesName, seriesStartYear)
                        curIssue = curSeries.getIssue(seriesIssueNum)
                        curReadingList.addIssue(curIssue, listEntryNum)
                    #curIssue = Issue(
                    #    seriesIssueNum, curSeries, listEntryNum)
                    #issueList.append(curIssue)

            #curReadingList.processIssueList(issueList)

            onlineLists.append(curReadingList)

    return onlineLists
