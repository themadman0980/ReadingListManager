#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
from readinglistmanager import filemanager,utilities, config
from readinglistmanager.datamanager import datasource, dataManager, dbManager
from readinglistmanager.utilities import printResults
from readinglistmanager.model.readinglist import ReadingList
from readinglistmanager.model.series import Series
from readinglistmanager.model.issue import Issue
from readinglistmanager.model.date import PublicationDate
import xml.etree.ElementTree as ET

dbTables = {'ReadingLists': 'ReadingListsView', 'ReadingListDetails': 'ReadingListDetailsView', 'IssueDetails': 'ComicsView'}
totalProblemEntries = 0
totalProblemReadingLists = 0

def parseCBLfiles():

    readingLists = []
    fileCount = 0
    for root, dirs, files in os.walk(filemanager.cblReadingListImportDirectory):
        for file in files:
            if file.endswith(".cbl") and not file.startswith('._'):
                fileCount += 1

    processedFileCount = 0
    printResults("Processing %s CBL files in %s" % (fileCount,filemanager.cblReadingListImportDirectory), 2)
    for root, dirs, files in os.walk(filemanager.cblReadingListImportDirectory):
        for file in files:
            if file.endswith(".cbl") and not file.startswith('._'):
                #try:
                curFilename = file
                curFilePath = os.path.join(root, file)
                # print("Parsing %s" % (filename))
                tree = ET.parse(curFilePath)
                fileroot = tree.getroot()
                cblBooks = fileroot.findall("./Books/Book")
                processedFileCount += 1

                #cblBooks = fileroot.findall("./Books/Book")

                cblSource = datasource.Source(curFilename, curFilePath, datasource.ListSourceType.CBL)

                readingList = ReadingList(source = cblSource)

                i = 0
                bookCount = len(cblBooks)
                if config.Troubleshooting.verbose:
                    printResults("Updating issue data for reading list : %s [%s]" % (
                        readingList.name, readingList.source.type.value), 3)

                for entry in cblBooks:
                    i += 1
                    printResults("[%s / %s] Processing %s / %s" % (processedFileCount, fileCount, i,bookCount),4,False,True)
                                        

                    seriesName = entry.attrib['Series']
                    seriesStartYear = utilities.getCleanYear(entry.attrib['Volume'])
                    issueNumber = entry.attrib['Number']
                    issueYear = None
                    if 'Year' in entry.attrib:
                        issueYear = PublicationDate(entry.attrib['Year'])
                    
                    essentialFields = (seriesName, seriesStartYear, issueNumber)
                    discardValues = [None, "", " "]
                    problem = False

                    for field in essentialFields:
                        if field in discardValues:
                            problem = True

                    if problem:
                        continue

                    seriesID = issueID = None
                    
                    curIssue = dataManager.getIssueFromDetails(seriesName, seriesStartYear, issueNumber)

                    # Get issue using series
                    if isinstance(curIssue,Issue):
                        curIssue.setSourceDate(issueYear)

                        # Check for ID details in CBL entry
                        databaseEntries = entry.findall('Database')

                        # Add ID for any database sources found
                        if databaseEntries is not None or len(databaseEntries) == 0:
                            for databaseElement in databaseEntries:
                                if 'Name' in databaseElement.attrib:
                                    for webSource in dataManager.activeWebSources:
                                        sourceNames = [webSource.type.value.lower()]
                                        if webSource.type.value.lower() == 'comicvine':
                                            sourceNames.append('cv')
                                        if databaseElement.attrib['Name'].lower() in sourceNames:
                                            # Update issue ID
                                            curIssue.setSourceID(webSource.type,databaseElement.attrib['Issue'])

                                            # Update series ID
                                            if curIssue.series is not None:
                                                if curIssue.series.hasValidID(webSource.type):
                                                    if curIssue.series.getSourceID(webSource.type) != databaseElement.attrib['Series']:
                                                        printResults("Warning: Series '%s (%s)' existing ID [%s] does not match proposed ID [%s]!" % (curIssue.series.name, curIssue.series.startYear, curIssue.series.getSourceID(webSource.type),databaseElement.attrib['Series']))
                                                        #TODO: Handle digital releases of one-shots (eg. CVID 28134 vs 34404)
                                                else:
                                                    curIssue.series.setSourceID(webSource.type,databaseElement.attrib['Series'])

                                            break

                    readingList.addIssue(i, curIssue)
                    curIssue.addReadingListRef(readingList)

                if len(readingList.issueList) == 0:
                    printResults(
                        "Warning: No issues found for list : %s" % (file), 4)

                readingLists.append(readingList)
                #except Exception as e:
                #    printResults("Unable to process file at %s : %s" %
                #                 (os.path.join(str(root), str(file)), str(e)), 3)

    return readingLists

def parseTXTfiles():

    readingLists = []
    fileCount = 0
    for root, dirs, files in os.walk(filemanager.textReadingListImportDirectory):
        for file in files:
            if file.endswith(".txt") and not file.startswith('._'):
                fileCount += 1

    processedFileCount = 0
    printResults("Processing %s CBL files in %s" % (fileCount,filemanager.textReadingListImportDirectory), 2)
    for root, dirs, files in os.walk(filemanager.textReadingListImportDirectory):
        for file in files:
            if file.endswith(".txt") and not file.startswith('._'):
                #try:
                curFilename = file
                curFilePath = os.path.join(root, file)
                # print("Parsing %s" % (filename))
                string = open(curFilePath,"r").read()
                splitString = string.split('\n')
                processedFileCount += 1

                listSource = datasource.Source(curFilename, curFilePath, datasource.ListSourceType.TXT)

                readingList = ReadingList(source = listSource)

                i = 1
                if config.Troubleshooting.verbose:
                    printResults("Updating issue data for reading list : %s [%s]" % (
                        readingList.name, readingList.source.type.value), 3)

                for entry in splitString:
                    curSeries = None
                    match = utilities.parseStringIssueList(entry)
                    if match is not None:
                        printResults("[%s / %s] Processing %s" % (processedFileCount, fileCount, i),4,False,True)
                                            
                        seriesName = match['Series']
                        seriesStartYear = utilities.getCleanYear(match['Year'])
                        issueNumList = list()

                        # Force ID's from Comicvine
                        curSourceType = datasource.ComicInformationSource.SourceType.Comicvine

                        # Retrieve series match using details provided
                        curSeries = dataManager.getSeriesFromDetails(seriesName,seriesStartYear)
                        
                        if 'SeriesID' in match and match['SeriesID'] is not None:
                            # There is a specified seriesID

                            if curSeries is not None and isinstance(curSeries, Series):
                                # We are working with a valid series object

                                if curSeries.hasValidID(curSourceType): 
                                    if not curSeries.doesIDMatch(match['SeriesID'],curSourceType):
                                    # SeriesID field doesn't match ID of curSeries object
                                        #Force create new series and assign seriesID
                                        curSeries = dataManager.createNewSeries(seriesName,seriesStartYear)
                                
                                if not curSeries.hasValidID(curSourceType):
                                    # series has no ID
                                    curSeries.setSourceID(curSourceType,match['SeriesID'])

                        dataManager._updateSeriesFromDataSources(curSeries)

                        if 'FirstIssueNum' not in match or match['FirstIssueNum'] is None:
                            # No issue numbers specified

                            # Get issue list
                            issueNumList = curSeries.getIssueNumsList()
                            issueNumList.sort(key=lambda x: int(x))

                        else:
                            # Issue numbers specified
                            firstIssueNumber = int(match['FirstIssueNum'])
                            issueNumList.append(firstIssueNumber)

                            if match['LastIssueNum'] is not None:
                                lastIssueNumber = int(match['LastIssueNum'])

                                # Create list of numbers (assumes no gaps)
                                for curIssueNum in range(firstIssueNumber+1,lastIssueNumber+1):
                                    issueNumList.append(curIssueNum)

                        essentialFields = (seriesName, seriesStartYear)
                        discardValues = [None, "", " "]
                        problem = False

                        for field in essentialFields:
                            if field in discardValues:
                                problem = True

                        if problem:
                            continue


                        for issueNumber in issueNumList:
                            if curSeries is not None and isinstance(curSeries, Series) and curSeries.hasValidID:
                                curIssue = curSeries.getIssue(issueNumber)
                            else:
                                curIssue = dataManager.getIssueFromDetails(seriesName, seriesStartYear, issueNumber)
                                
                            curIssue.addReadingListRef(readingList)

                            i += 1
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
    global totalProblemEntries, totalProblemReadingLists

    onlineLists = []

    # Get list of DB's from /Data directory
    for root,dir,files in os.walk(filemanager.dataDirectory + '/'):
        for file in files:
            if file.endswith(".db"):
                # TODO : Re-enable cbro.db
                if file not in ("cv.db", "data.db", "overrides.db", "metron.db"):
                    #try:
                    # Create Source object
                    filePath = os.path.join(root, file)
                    fileName = str(file).replace(".db","").upper()

                    curDBSource = datasource.Source(name = fileName, file = filePath, sourceType = datasource.ListSourceType.Website, tableDict = dbTables)

                    # Create DB connection
                    curDB = dbManager.ListDB(curDBSource)

                    curListNames = curDB.getListNames()

                    for readingList in curListNames:
                        curDBListID = readingList[0]
                        curListName = readingList[1]

                        curReadingList = ReadingList(source = curDBSource, listName = curListName)

                        # Get all reading list entries from readinglist DB table
                        if config.Troubleshooting.verbose:
                            printResults("Getting issue details for %s" % (curReadingList.name), 3)
                        curListDetails = curDB.getListDetails(curDBListID)

                        count = len(curListDetails)
                        i = 0
                        curProblemEntries = 0

                        # Get details for each list entry from issue DB table

                        for listEntry in curListDetails:
                            i += 1
                            printResults("Processing %s / %s" % (i,count),4,False,True)
                            listEntryNum = listEntry[2]
                            listEntryID = listEntry[1]

                            entryMatches = curDB.getIssueDetails(listEntryID)
                            #printResults("%s entries found for hrnum='%s'" % (len(entryMatches), listEntryID), 5)

                            numMatches = len(entryMatches)

                            if numMatches > 0:
                                if numMatches > 1:
                                    printResults("Reading-List Warning: Multiple db entries found for issue with entry ID='%s' in %s" % (
                                        listEntryID, readingList.name), 4)
                                
                                #for issueEntry in entryMatches:
                                _, seriesName, seriesStartYear, issueNum, _, sourceIssueDate = entryMatches[0]

                                essentialFields = (seriesName, seriesStartYear, issueNum)
                                discardValues = [None, "", " "]
                                problem = False

                                for field in essentialFields:
                                    if field in discardValues:
                                        curProblemEntries += 1
                                        problem = True

                                if problem:
                                    continue

                                curIssue = dataManager.getIssueFromDetails(seriesName, seriesStartYear,issueNum)

                                if curIssue is not None and isinstance(curIssue, Issue):
                                    if sourceIssueDate is not None: 
                                        curIssue.setSourceDate(PublicationDate(sourceIssueDate))

                                curReadingList.addIssue(listEntryNum, curIssue)
                                curIssue.addReadingListRef(curReadingList)
                        
                        totalProblemEntries += curProblemEntries
                        if curProblemEntries > 0: 
                            totalProblemReadingLists += 1
                            printResults("Reading-List Warning: %s invalid entries in list %s [%s]" % (curProblemEntries, curListName,curDBSource.name),4)

                        onlineLists.append(curReadingList)
                    #except Exception as e:
                    #    printResults("Error: Unable to process db file %s : %s" % (file,e),2)

    return onlineLists

