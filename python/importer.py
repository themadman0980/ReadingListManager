#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from filemanager import files as fileManager
from utilities import printResults
import os
import datasource
import db
import config
from readinglist import ReadingList
from series import Series
from issue import Issue
import xml.etree.ElementTree as ET

readingListDB = [
    {'SourceName': 'CMRO', 'DBTables': {
        'ReadingLists': 'olists', 'ReadingListDetails': 'olistcom', 'IssueDetails': 'comics'
        }},
    {'SourceName': 'DCRO', 'DBTables': {
        'ReadingLists': 'olists', 'ReadingListDetails': 'olistcom', 'IssueDetails': 'comics'
        }}]


def parseCBLfiles(cvCache):
    readingLists = []

    printResults("Checking CBL files in %s" %
                 (fileManager.readingListDirectory), 2)
    for root, dirs, files in os.walk(fileManager.readingListDirectory):
        for file in files:
            if file.endswith(".cbl"):
                #try:
                filename = os.path.join(root, file)
                # print("Parsing %s" % (filename))
                tree = ET.parse(filename)
                fileroot = tree.getroot()

                cblinput = fileroot.findall("./Books/Book")

                readingList = ReadingList(
                    file, datasource.CBLSource(file, filename), cvCache)

                i = 0
                printResults("Updating issue data for reading list : %s [%s]" % (
                    readingList.name, readingList.source.type), 3)

                for entry in cblinput:
                    i += 1
                    # ,'issueYear':entry.attrib['Year']}
                    seriesName = entry.attrib['Series']
                    seriesStartYear = entry.attrib['Volume']
                    curSeries = Series.getSeries(seriesName, seriesStartYear)
                    curIssue = curSeries.getIssue(entry.attrib['Number'])
                    for series in Series.seriesList:
                        print("%s (%s) [%s]" % (series.name,
                              series.startYear, series.id))
                        for issue in series.issueList:
                            print("#%s [%s]" % (issue.issueNumber, issue.id))
                    readingList.addIssue(curIssue, i)
                if len(readingList.issueList) == 0:
                    printResults(
                        "Warning: No issues found for list : %s" % (file), 4)

                readingLists.append(readingList)
                #except Exception as e:
                #    printResults("Unable to process file at %s" %
                #                 (os.path.join(str(root), str(file))), 3)
                #    printResults(repr(e), 3)

    return readingLists


def getOnlineLists(cvCache):

    onlineLists = []

    for listSourceObject in readingListDB:
        # Create Source object
        sourceName = listSourceObject['SourceName']
        sourceFile = os.path.join(
            fileManager.dataDirectory, sourceName + ".db")
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
                listName, curSource, cvCache, None, listID)

            # Get all reading list entries from readinglist DB table
            curListDetails = curDB.getListDetails(curReadingList.id)

            issueList = []

            # Get details for each list entry from issue DB table
            for listEntry in curListDetails:
                listEntryNum = listEntry[1]
                listEntryID = listEntry[2]

                entryMatches = curDB.getIssueDetails(listEntryID)
                #printResults("%s entries found for hrnum='%s'" % (len(entryMatches), listEntryID), 5)

                numMatches = len(entryMatches)

                if numMatches > 0:
                    if numMatches > 1:
                        printResults("Warning: Multiple db entries found for issue with hrnum='%s' in %s" % (
                            listEntryID, readingList.name), 4)
                    seriesName = entryMatches[0][3]
                    seriesStartYear = entryMatches[0][4]
                    seriesIssueNum = entryMatches[0][5]
                    curSeries = Series.getSeries(seriesName, seriesStartYear)
                    curIssue = curSeries.getIssue(seriesIssueNum)
                    curReadingList.addIssue(curIssue, listEntryNum)
                    #curIssue = Issue(
                    #    seriesIssueNum, curSeries, listEntryNum)
                    #issueList.append(curIssue)

            #curReadingList.processIssueList(issueList)

            onlineLists.append(curReadingList)

    return onlineLists
