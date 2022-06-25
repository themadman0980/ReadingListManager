#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
from readinglistmanager import filemanager,utilities
from readinglistmanager.datamanager import datasource, dataManager, dbManager
from readinglistmanager.utilities import printResults
from readinglistmanager.model.readinglist import ReadingList
from readinglistmanager.model.series import Series
from readinglistmanager.model.issue import Issue
import xml.etree.ElementTree as ET

dbTables = {'ReadingLists': 'ReadingListsView', 'ReadingListDetails': 'ReadingListDetailsView', 'IssueDetails': 'ComicsView'}

def parseCBLfiles():

    readingLists = []

    printResults("Checking CBL files in %s" % (filemanager.readingListDirectory), 2)
    for root, dirs, files in os.walk(filemanager.readingListDirectory):
        for file in files:
            if file.endswith(".cbl") and not file.startswith('._'):
                #try:
                filename = file
                filePath = os.path.join(root, file)
                # print("Parsing %s" % (filename))
                tree = ET.parse(filePath)
                fileroot = tree.getroot()
                cblBooks = fileroot.findall("./Books/Book")

                #cblBooks = fileroot.findall("./Books/Book")

                cblSource = datasource.Source(filename, filePath, datasource.ListSourceType.CBL)

                readingList = ReadingList(file, cblSource)

                i = 0
                bookCount = len(cblBooks)
                printResults("Updating issue data for reading list : %s [%s]" % (
                    readingList.name, readingList.source.type.value), 3)

                for entry in cblBooks:
                    i += 1
                    printResults("Processing %s / %s" % (i,bookCount),4,False,True)
                                        

                    seriesName = entry.attrib['Series']
                    seriesStartYear = utilities.getCleanYear(entry.attrib['Volume'])
                    issueNumber = entry.attrib['Number']
                    issueYear = None
                    if 'Year' in entry.attrib:
                        issueYear = entry.attrib['Year']
                    
                    seriesID = issueID = None

                    # Check for ID details in CBL entry
                    databaseEntries = entry.findall('Database')
                    if databaseEntries is not None or len(databaseEntries) == 0:
                        for databaseElement in databaseEntries:
                            if 'Name' in databaseElement.attrib:
                                if databaseElement.attrib['Name'] == 'cv':
                                    seriesID = databaseElement.attrib['Series']
                                    issueID = databaseElement.attrib['Issue']
                    
                    curIssue = dataManager.getIssueFromDetails(seriesName, seriesStartYear, issueNumber)

                    # Get issue using series
                    if isinstance(curIssue,Issue):
                        curIssue.year = issueYear
                        # Update seriesID if found
                        if seriesID is not None and utilities.isValidID(seriesID) and isinstance(curIssue.series,Series) and curIssue.series.id is None:
                            curIssue.series.id = seriesID
                                        
                        # Update issueID if found
                        if issueID is not None and utilities.isValidID(issueID) and isinstance(curIssue,Issue):
                            curIssue.id = issueID

                    readingList.addIssue(i, curIssue)

                if len(readingList.issueList) == 0:
                    printResults(
                        "Warning: No issues found for list : %s" % (file), 4)

                readingLists.append(readingList)
                #except Exception as e:
                #    printResults("Unable to process file at %s : %s" %
                #                 (os.path.join(str(root), str(file)), str(e)), 3)

    return readingLists


def getOnlineLists():

    onlineLists = []

    # Get list of DB's from /Data directory
    for root,dir,files in os.walk(filemanager.dataDirectory + '/'):
        for file in files:
            if file.endswith(".db"):
                # TODO : Re-enable cbro.db
                if not (file == "cv.db" or file == "data.db" or file == "cbro.db"):
                    #try:
                    # Create Source object
                    filePath = os.path.join(root, file)
                    fileName = str(file).replace(".db","").upper()

                    curSource = datasource.Source(fileName,filePath,datasource.ListSourceType.Website,dbTables)

                    # Create DB connection
                    curDB = dbManager.ListDB(curSource)

                    curListNames = curDB.getListNames()

                    for readingList in curListNames:
                        listID = readingList[0]
                        listName = readingList[1]

                        curReadingList = ReadingList(listName, curSource, listID)

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
                                
                                #for issueEntry in entryMatches:
                                _, seriesName, seriesStartYear, issueNum, _ = entryMatches[0]

                                if seriesName is None or seriesStartYear is None:
                                    printResults("ReadingList Error: Invalid DB entry : %s" % (str(entryMatches[0])),4)
                                else:
                                    curIssue = dataManager.getIssueFromDetails(seriesName, seriesStartYear,issueNum)
                                    curReadingList.addIssue(listEntryNum, curIssue)

                        onlineLists.append(curReadingList)
                    #except Exception as e:
                    #    printResults("Error: Unable to process db file %s : %s" % (file,e),2)

    return onlineLists
