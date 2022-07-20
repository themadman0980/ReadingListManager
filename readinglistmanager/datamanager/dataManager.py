#!/usr/bin/env python3
# -*- coding: utf-8 -*-

### Manages datasources, filters list[dict] lookup results into single dict and generates/manages Series objects

from readinglistmanager import filemanager,utilities,config
from readinglistmanager.utilities import printResults
from readinglistmanager.errorhandling.problemdata import ProblemData
from readinglistmanager.datamanager import cvManager,dbManager,datasource, save
from readinglistmanager.datamanager.datasource import ComicInformationSource, DataSourceType, ListSourceType
from readinglistmanager.model.readinglist import ReadingList
from readinglistmanager.model.series import Series
from readinglistmanager.model.issue import Issue

dataDB = dbManager.DataDB.get()
cv = cvManager.CV.get()

# NOTE : Order of sources in list affects lookup order!!
dataSources = [dataDB, cv]

_series = {}
_readingLists = {}
_seriesOverrideList = None
counters = {'matches' : {'override' : 0, 'cv' : 0, 'db' : 0}, 'noMatches':{'override' : 0, 'cv' : 0, 'db' : 0}, 'matchType' : {'one' : 0, 'multiple' : 0, 'blacklist' : 0}}
overrideMatchCounter = 0

lookupMatch = {'match' : None, 'problemData' : None }

def _getSeriesOverrideDetails() -> dict:
    seriesAltData = {}
    
    jsonData = filemanager.getJSONData(filemanager.overridesFile)

    for altSeries in jsonData:
        dictKey = Series.getSeriesKey(altSeries['altSeriesDynamicName'], altSeries['altSeriesStartYear'])
        seriesAltData[dictKey] = altSeries

    return seriesAltData

_seriesOverrideList = _getSeriesOverrideDetails()

#def getSeries(name : str, startYear : int, seriesID : str = None) -> Series:
#    # Check if series exists in dict
#    if seriesID is not None and id in _series:
#        return _series[id]
#    else:
#        dynamicName = utilities.getDynamicName(name)
#        startYear = utilities.getCleanYear(startYear)
#
#    if isinstance(series, Series):
#        # Check result is valid
#        if series.dynamicName != dynamicName or series.startYear != startYear:
#            printResults("Warning : Series ID match \"%s (%s) [%s]\" does not have exact match with ReadingList entry details \'%s (%s)\'" % (
#                series.id, series.name, series.startYear, name, startYear), 4)
#    else:
#        series = getSeriesFromDetails(name, startYear)

def getSeriesFromSeriesID(seriesID : str) -> Series:
    # Check if series exists in dict
    if seriesID in _series:
        return _series[seriesID]
    else:
        for source in dataSources:
            if isinstance(source, ComicInformationSource):
                seriesData = source.getSeriesFromSeriesID(seriesID)
                if seriesData is not None and isinstance(seriesData, list): 
                    seriesData = seriesData[0]
                    series = Series.fromDict(seriesData)

                    if isinstance(series, Series): 
                        return series

    return None

def getSeriesFromIssueID(issueID : str) -> Series:
    
    series = None

    for source in dataSources:
        if isinstance(source, ComicInformationSource) and config.CV.c:
            issueDetails = source.getIssueFromIssueID(issueID)
            if issueDetails is not None and isinstance(issueDetails, dict):
                seriesID = issueDetails['seriesID']
                if utilities.isValidID(seriesID):
                    series = getSeriesFromSeriesID(seriesID)

    return series

def getSeriesFromDetails(name : str, startYear : str) -> Series:
    series = None 
    seriesKey = Series.getSeriesKey(name, startYear)

    # Check if series exists in
    if seriesKey in _series:
        series = _series[seriesKey]
    else:
        if _seriesOverrideList is not None and seriesKey in _seriesOverrideList:
            # Series found in overrides list
            global overrideMatchCounter; overrideMatchCounter += 1
            try:
                seriesID = _seriesOverrideList[seriesKey]['volumeComicvineID']
                series = getSeriesFromSeriesID(seriesID)
            except Exception as e:
                printResults("Error : Unable to process series override for %s (%s) : %s" % (name, startYear, str(e)), 4)
            
        # If no result/error in override list
        if series is None:
            # Check all available data sources for an exact match
            series = createNewSeries(name, startYear)

    return series

def compareReadingListSources():
    readingListSet = getReadingListSet()
    for listData in readingListSet:
        for readingList in listData:
            #Get list of all alternate lists for same event
            otherLists = list(otherReadingList for otherReadingList in listData if isinstance(otherReadingList, ReadingList))
            otherLists.remove(readingList)

            if isinstance(readingList, ReadingList):
                # Do something
                for issueNum,issue in readingList.issueList.items():
                    for otherReadingList in otherLists:
                        if issue in otherReadingList.issueList.values():
                            pass
                            # otherIssueNum = otherReadingList.issueList.items().

def validateReadingLists(readingLists : list[ReadingList]) -> None:
    dataSourceType = ComicInformationSource.SourceType.Comicvine

    if isinstance(readingLists, list):
        for readingList in readingLists:
            if isinstance(readingList, ReadingList):
                readingList.setPublisherFromIssueDetails()

    numLists = len(readingLists)
    i = 0
    printResults("Checking %s reading lists" % (numLists), 2)

    readingListNames = list(set(readingList.name for readingList in readingLists))
    save.saveDataListToTXT('cvListLookup', readingListNames)
    
    if isinstance(readingLists, list):
        for readingList in readingLists:
            i += 1
            if isinstance(readingList, ReadingList):
                _updateReadingListFromDataSources(readingList,dataSourceType)
                printResults("%s / %s reading lists checked" % (i,numLists), 3, False, True)


def validateSeries() -> None:
    # Lookup series' details + collect all issue details based on series ID
    seriesSet = set(_series.values())
    checkCVSeriesSet = set()
    numSeries = len(seriesSet)

    # Check DB for all series 
    printResults("Checking DB for %s series" % (numSeries), 3)
    
    sourceType = ComicInformationSource.SourceType.Database
    i = 0
    for series in seriesSet:
        i += 1
        if isinstance(series, Series):
            if not series.checked[sourceType]:
                printResults("%s / %s series checked" % (i,numSeries),4,False,True)
                _updateSeriesFromDataSources(series,sourceType)

            if not series.hasCompleteSeriesDetails():
                checkCVSeriesSet.add(series)
    
    numSeriesLookupCV = len(checkCVSeriesSet)
    numSeriesFoundDB = numSeries - numSeriesLookupCV

    printResults("Validation : DB matches = %s / %s" % (numSeriesFoundDB,numSeries),3)
    printResults("Validation : CV Searches Required = %s" % (numSeriesLookupCV),3)


    # Iterate through set of incomplete series and check CV for each
    sourceType = ComicInformationSource.SourceType.Comicvine
    unmatchedCVSet = set()
    i = 0
    for series in checkCVSeriesSet:
        if isinstance(series, Series) and not series.checked[sourceType]:
            i += 1
            printResults("[%s / %s] : Checking CV for %s (%s) [%s]" % (i, numSeriesLookupCV, series.name, series.startYear, series.id), 4, False, True)
            _updateSeriesFromDataSources(series,sourceType)
            if not series.hasValidID(): 
                unmatchedCVSet.add(series)
    
    numSeriesUnmatchedCV = len(unmatchedCVSet)
    # Reprocess all series names for unmatched series
    printResults("Validation : Reprocessing Unmatched Series With Cleaned Name = %s" % (numSeriesUnmatchedCV),3)
    i = 0
    counter = {'processed':0,'cleaned':0, 'matches': 0}
    for series in unmatchedCVSet:
        i += 1
        if isinstance(series, Series):
            printResults("[%s / %s] : Reprocessing %s (%s) [%s]" % (i, numSeriesUnmatchedCV, series.name, series.startYear, series.id), 4, False, True)
            counter['processed'] += 1
            cleanedSeriesName = utilities._cleanSeriesName(series.name)
            if cleanedSeriesName != series.name:
                counter['cleaned'] += 1
                series.addProblem(ProblemData.ProblemType.NameCleaned,"Original: \'%s\', Cleaned: \'%s\'" % (series.name, cleanedSeriesName))
                series.name = cleanedSeriesName
                _updateSeriesFromDataSources(series)
                _addSeriesToList(series)

                if series.hasValidID():
                    counter['matches'] += 1

    printResults("%s / %s series names cleaned, with %s new matches found" % (counter['cleaned'],counter['processed'],counter['matches']), 3)
    # Save unmatched series to file

    cvSeriesNames = list(set(series.name for series in checkCVSeriesSet if isinstance(series, Series)))
    save.saveDataListToTXT('cvSeriesLookup', cvSeriesNames)

def _filterSeriesResults(results : list[dict], series : Series) -> dict[list[dict]]:
    preferredType = ComicInformationSource.ResultFilterType.Preferred 
    allowedType = ComicInformationSource.ResultFilterType.Allowed 
    blacklistType = ComicInformationSource.ResultFilterType.Blacklisted 
    resultsFiltered = {preferredType:[], allowedType:[], blacklistType:[]}
    nameOnlyMatches = list()

    # Check for exact name & year matches & categorise them

    for result in results:  
        if isinstance(result,dict):
            resultNameClean = utilities.getDynamicName(result['name'])
            resultYearClean = utilities.getCleanYear(result['startYear'])
            # If exact series name and year match
            if resultNameClean == series.dynamicName:
                if resultYearClean == series.startYear:
                    # Name and year is perfect match : add result to dict
                    curPublisher = result['publisher']

                    if curPublisher in config.CV.publisher_blacklist:
                        resultsFiltered[blacklistType].append(result)
                    elif curPublisher in config.CV.publisher_preferred:
                        resultsFiltered[preferredType].append(result)
                    else:
                        resultsFiltered[allowedType].append(result)
                else:
                    # Incorrect year
                    nameOnlyMatches.append(result)
            elif series.dynamicName in resultNameClean:
                # Series name is incorrect but similar
                nameOnlyMatches.append(result)


    # Identify & return matches

    acceptableMatches = resultsFiltered[preferredType] + resultsFiltered[allowedType]
    numAcceptableMatches = len(acceptableMatches)

    if numAcceptableMatches == 0:
        # No 'Preferred' or 'Allowed' publisher matches. Add ProblemData info
        if len(resultsFiltered[blacklistType]) > 0:
            series.addProblem(ProblemData.ProblemType.PublisherBlacklisted,resultsFiltered[blacklistType])
        elif len(nameOnlyMatches) > 0:
            matchCount = 0
            # If dynamicname matches were found, see if the series year was within 2 years of expected
            for result in nameOnlyMatches:
                matchYearClean = utilities.getCleanYear(result['startYear'])
                matchNameClean = utilities.getDynamicName(result['name'])
                if None not in (matchYearClean, series.startYear):
                    deviation = abs(int(matchYearClean) - int(series.startYear))
                    if deviation <= 2: 
                        if series.dynamicName == matchNameClean:
                            matchCount += 1
                            series.addProblem(ProblemData.ProblemType.CVIncorrectYear, result)
                        elif series.dynamicName in matchNameClean:
                            matchCount += 1
                            series.addProblem(ProblemData.ProblemType.CVSimilarMatch, result)
            if matchCount == 0:
                series.addProblem(ProblemData.ProblemType.CVNoNameYearMatch,result)
        else:
            series.addProblem(ProblemData.ProblemType.CVNoNameYearMatch,result)
        resultsFiltered = None
    elif numAcceptableMatches > 0:
        if numAcceptableMatches > 1:
            series.addProblem(ProblemData.ProblemType.MultipleMatch, acceptableMatches)

    return resultsFiltered


def _updateReadingListFromDataSources(readingList : ReadingList, checkDataSource : ComicInformationSource.SourceType = None) -> None:
    match = None

    if not isinstance(readingList, ReadingList):
        return

    _addReadingList(readingList)

    for dataSource in dataSources:
        if isinstance(dataSource, ComicInformationSource):
            if checkDataSource is not None and dataSource.type != checkDataSource:
                # Skip unwanted datasource if specific dataSource is specified in request
                continue

            # Check dataSource for match
            listResults = dataSource.getReadingListsFromName(readingList.name)

            readingList.checked[dataSource.type] = True
            
            if listResults is not None and len(listResults) > 0:
                # Results found - get exact match
                match = _getFinalListMatchFromResults(listResults,readingList)
            
            if match is not None:
                #try:
                # TODO : Add story arcs to data.db and account for matches in issue processing
                if match['issues'] is not None and isinstance(match['issues'], list):
                    issueList = dict()
                    for issue in match['issues']:
                        issueNum = match['issues'].index(issue) + 1
                        if issue is not None:
                            issueID = issue.id_
                            if issueID is not None and utilities.isValidID(issueID):
                                curIssue = getIssueFromIssueID(issueID)
                                #for dataSource in dataSources:
                                #    if isinstance(dataSource, ComicInformationSource):
                                #        curIssue = dataSource.getIssueFromIssueID(issueID)
                                if isinstance(curIssue,Issue): 
                                    issueList[issueNum] = curIssue
                                    continue
                match['issues'] = issueList
                newReadingList = ReadingList.fromDict(match, datasource.ListSourceType.CV)
                _addReadingList(newReadingList)
                readingList.id = match['listID']
                return
    
def _getFinalListMatchFromResults(results : list[dict], readingList : ReadingList) -> dict:
    # Takes list[dict] and filters it to return a single dict object
    exactMatches = list()
    finalMatch = None
    publisherMatches = list()

    if None not in (results, readingList) and isinstance(results, list) and isinstance(readingList, ReadingList):
        
        # Check name matches
        
        for result in results:
            resultDynamicName = utilities.getDynamicName(result['name'])
            if resultDynamicName == readingList.dynamicName:
                exactMatches.append(result)

        # Check publisher matches
        
        for match in exactMatches:
            if match['publisher'] == readingList.publisher:
                publisherMatches.append(match)

        # Process publisher matches
        
        if len(publisherMatches) == 1:
            finalMatch = publisherMatches[0]
        elif len(publisherMatches) > 1:
            finalMatch = publisherMatches[0]
            readingList.addProblem(ProblemData.ProblemType.MultipleMatch, publisherMatches)
            printResults("ReadingList Error : Multiple matches found for %s" % (readingList.name), 4)

        # Identify problems

        if finalMatch is None:
            if len(results) > 0:
                readingList.addProblem(ProblemData.ProblemType.CVNoNameYearMatch, results)
            else:
                readingList.addProblem(ProblemData.ProblemType.CVNoResults)
        else:
            finalMatch = cv.getReadingListFromID(finalMatch['listID'])
            finalMatch = finalMatch[0] if len(finalMatch) > 0 else None

    return finalMatch


def _updateSeriesFromDataSources(series : Series, checkDataSource : ComicInformationSource.SourceType = None) -> None:
    match = None

    if not isinstance(series, Series):
        return None

    for dataSource in dataSources:
        if isinstance(dataSource, ComicInformationSource):
            if checkDataSource is not None and dataSource.type != checkDataSource:
                # Skip unwanted datasource if specific dataSource is specified in request
                continue

            # Check dataSource for match
            if series.hasValidID():
                seriesResults = dataSource.getSeriesFromSeriesID(series.id)
            else:
                seriesResults = dataSource.getSeriesFromDetails(series.name, series.startYear)

            series.checked[dataSource.type] = True
            
            if seriesResults is not None and len(seriesResults) > 0:
                # Results found - get exact match
                match = _getFinalSeriesMatchFromResults(seriesResults,series)
            
            if match is not None:
                #try:
                series.dataSourceType = dataSource.type
                series.updateDetailsFromDict(match['seriesDetails'])
                series.updateIssuesFromDict(match['issueList'])
                _addSeriesToList(series)
                #except:
                #    printResults("Error : Unable to create series from dict : %s" % (seriesFinalMatch), 4)
                    
    # Add result to DB if legit match found on CV
    #if series is not None and isinstance(series, Series) and series.dataSourceType == ComicInformationSource.SourceType.Comicvine:


def _getFinalSeriesMatchFromResults(results : list[dict], series : Series) -> dict:
    # Takes list[dict] and filters it to return a single dict object
    match = None

    if results is not None and isinstance(results, list):
        filteredResultsList = _filterSeriesResults(results, series)

        issueNumList = series.getIssueNumsList()
        if issueNumList is not None and filteredResultsList is not None:
            match = _checkSeriesIssuesMatch(filteredResultsList, series)

            if match is None:
                series.addProblem(ProblemData.ProblemType.CVNoIssueMatch,filteredResultsList)
            
    return match
    

# Returns a (filtered) list of input series with exact match for all issue numbers/year
def _checkSeriesIssuesMatch(filteredSeriesMatchDict : dict[list[dict]], series : Series) -> list[dict]:
    seriesMatchList = [
        filteredSeriesMatchDict[ComicInformationSource.ResultFilterType.Preferred],
        filteredSeriesMatchDict[ComicInformationSource.ResultFilterType.Allowed]
        ]
    
    for seriesList in seriesMatchList:
        for seriesResult in seriesList:
            # Lookup issue list for each series match
            for dataSource in dataSources:
                seriesIssues = None

                if isinstance(dataSource, ComicInformationSource):
                    seriesIssues = dataSource.getIssuesFromSeriesID(seriesResult['seriesID'])

                # Check if issue results exist
                if seriesIssues is not None and len(seriesIssues) > 0:
                    exactSeriesMatch = True

                    seriesIssueNumbers = series.getIssueNumsList()

                    # TODO : Account for series start years at different times
                    # Quick test to check that numResults >= numSeriesIssues 
                    if len(seriesIssues) < len(seriesIssueNumbers):
                        exactSeriesMatch = False
                        break

                    # Check if all expected issues exist in CV volume match
                    for expectedIssueNum in seriesIssueNumbers:
                        # Check if expected issue number exists in series
                        if expectedIssueNum not in seriesIssues:
                            exactSeriesMatch = False
                            break
                        
                    # Exit loop immediately if exact match is found                    
                    if exactSeriesMatch: 
                        if dataSource.type == ComicInformationSource.SourceType.Comicvine:
                            dataDB.addVolume(seriesResult)
                            # Data obtained from CV
                            for issue in seriesIssues.values():
                                dataDB.addIssue(issue)
                        #Exact match found
                        return {'seriesDetails':seriesResult, 'issueList':seriesIssues}
    
    return None

def _addSeriesToList(series : Series) -> None:
    # Add series to master series dict 
    _series[series.key] = series
    _series[series.id] = series

def _addReadingList(readingList : ReadingList) -> None:
    # Add series to master series dict 
     if isinstance(readingList, ReadingList):

        if readingList.key in _readingLists:
            curList = _readingLists[readingList.key]
            if isinstance(curList, list):
                curList.append(readingList)
            else:
                curList = [readingList]
        else:
            _readingLists[readingList.key] = [readingList]

        if readingList.id in _readingLists:
            curList = _readingLists[readingList.id]
            if isinstance(curList, list):
                curList.append(readingList)
            else:
                curList = [readingList]
        else:
            _readingLists[readingList.id] = [readingList]

def createNewSeries(name : str, startYear : int, seriesID : str = None) -> Series :
    newSeries = Series(name, startYear)
    newSeries.id = seriesID

    for dataSource in dataSources:
        if isinstance(dataSource, ComicInformationSource):
            newSeries.checked[dataSource.type] = False

    _addSeriesToList(newSeries)

    return newSeries

def getIssueFromIssueID(issueID : str) -> Issue:
    issue = None

    for curDataSource in dataSources:
        if isinstance(curDataSource, ComicInformationSource):
            issueData = curDataSource.getIssueFromIssueID(issueID)

            if isinstance(issueData,list) and len(issueData) > 0:
                issueData = issueData[0]
                if isinstance(issueData, dict):
                    issue = Issue.fromDict(issueData)
                    seriesID = issueData['seriesID']
                    if utilities.isValidID(seriesID):
                        series = getSeriesFromSeriesID(seriesID)
                        if isinstance(series, Series):
                            series.addIssue(issue)

            if isinstance(issue, Issue):
                break

    return issue

def _getSeriesIssueDetails(seriesObject : Series) -> None:
    if isinstance(seriesObject,Series) and seriesObject.hasValidID():
        for dataSource in dataSources:
            if isinstance(dataSource,ComicInformationSource):
                issueDetailsList = dataSource.getIssuesFromSeriesID(seriesObject.id)
                if issueDetailsList is not None and len(issueDetailsList) > 0:
                    for issueDetails in issueDetailsList:
                        if issueDetails['issueNum'] in seriesObject.issueList:
                            curIssue = seriesObject.issueList[issueDetails['issueNum']]
                            if isinstance(curIssue, Issue):
                                curIssue.updateDetailsFromDict(issueDetails)
                                curIssue.sourceType = dataSource.type
                                if dataSource.type == ComicInformationSource.SourceType.Comicvine:
                                    dataDB.addIssue(curIssue.getDBDict())
            
            if seriesObject.hasCompleteIssueDetails():
                break
            else:
                # Not all details found
                pass

def getIssueFromDetails(seriesName : str, seriesStartYear : int, issueNum : str) -> Issue:
    issue = None

    if None not in (seriesName, seriesStartYear, issueNum):
        series = getSeriesFromDetails(seriesName,seriesStartYear)
        issue = series.getIssue(issueNum)

    return issue

def getIssueFromIDs(seriesID : str, issueID : str) -> Issue:
    issue = None

    if None not in (seriesID, issueID):
        series = getSeriesFromSeriesID(seriesID)
        issue = getIssueFromIssueID(issueID)
        if isinstance(series, Series) and isinstance(issue, Issue):
            series.addIssue(issue)

    return issue

def getIssueFromSeriesID(seriesID : str, issueNumber : str) -> Issue:
    issue = None

    if None not in (seriesID, issueNumber):
        series = getSeriesFromSeriesID(seriesID)
        issue = series.getIssue(issueNumber)
        if isinstance(series, Series) and isinstance(issue, Issue):
            series.addIssue(issue)
    
    return issue

def printSummaryResults():

    printResults("*** Comic Information Sources ***", 2)
    for dataSource in dataSources:
        if isinstance(dataSource,ComicInformationSource):
            if isinstance(dataSource.type, ComicInformationSource.SourceType):
                printResults("Data Source : %s" % (dataSource.type.value),3)
            
            for key, value in dataSource.counters.items():
                printResults("%s" % (key.value),4)
                printResults(', '.join('{} : {}'.format(k.value,v) for k,v in value.items()),5)



    printResults("*** Reading List Statistics ***", 2)
    readingListCompleteIssuesCount = 0
    readingListSet = getReadingListSet()
    for readingList in readingListSet:
        if isinstance(readingList, ReadingList):
            seriesDetailsFound = issueDetailsFound = 0
            seriesSet = set()
            issueListLength = len(readingList.issueList)

            # Check issue details found
            for issue in readingList.issueList.values():
                if isinstance(issue, Issue):
                    seriesSet.add(issue.series)
                    if issue.detailsFound:
                        issueDetailsFound += 1

            # Check series details found
            for series in seriesSet:
                if isinstance(series, Series):
                    if series.detailsFound:
                        seriesDetailsFound += 1

            if issueDetailsFound == issueListLength:
                readingListCompleteIssuesCount += 1
            #else:
            #    printResults("Reading List : %s" % (readingList.name), 3)
            #    printResults("Series Found : %s / %s" % (seriesDetailsFound,seriesListLength), 4)
            #    printResults("Issues Found : %s / %s" % (issueDetailsFound,issueListLength), 4)

    printResults("Reading List Summary", 3)
    printResults("Complete List Details Found : %s / %s" % (readingListCompleteIssuesCount,len(readingListSet)), 4)


    printResults("*** Series Statistics ***", 2)
    seriesSet = set(_series.values())
    seriesCount = len(seriesSet)
    seriesDetailsFound = seriesAllIssueDetailsFound = 0
    for series in seriesSet:
        if isinstance(series, Series):
            detailsFoundIssueCount = series.getNumCompleteIssues()
            numIssues = len(series.issueList)

            if series.detailsFound:
                seriesDetailsFound += 1
            #else:
            #    printResults("Series : %s (%s) [%s]" % (series.name,series.startYear,series.id),3)
            #    printResults("Match found : %s (%s)" % (series.detailsFound,series.dataSourceType.value),4)

            #printResults("Issues found : %s / %s" % (detailsFoundIssueCount,numIssues),4)
            if detailsFoundIssueCount == numIssues:
                seriesAllIssueDetailsFound += 1
#            elif series.detailsFound:
#                printResults("Series : %s (%s) [%s]" % (series.name,series.startYear,series.id),3)
#                printResults("Match found : %s (%s)" % (series.detailsFound,series.dataSourceType.value),4)
#                printResults("Issue Details found : %s / %s" % (detailsFoundIssueCount,numIssues),4)


    printResults("Series Found : %s / %s" % (seriesDetailsFound,seriesCount),3)
    printResults("Series Complete Issue Details Found : %s / %s" % (seriesAllIssueDetailsFound,seriesCount),3)

def processProblemData():
    seriesSet = set(series for series in _series.values() if isinstance(series, Series))
    
    for series in seriesSet:
        if isinstance(series, Series):
            curProblemData = series.problems
            for problemType, data in curProblemData.items():
                ProblemData.addSeriesEntry(series, problemType, data)

def saveReadingLists():
    # Get list of all readinglists
    readingLists = list(getReadingListSet())

    printResults("JSON", 2, True)
    save.saveReadingLists(readingLists,save.OutputFileType.JSON)

    printResults("CBL", 2, True)
    save.saveReadingLists(readingLists,save.OutputFileType.CBL)

def getReadingListSet():
    readingListSet = set()

    for k, v in _readingLists.items():
        if isinstance(v, list):
            for readingList in v:
                if isinstance(readingList, ReadingList):
                    readingListSet.add(readingList)

    return readingListSet
