#!/usr/bin/env python3
# -*- coding: utf-8 -*-

### Manages datasources, filters list[dict] lookup results into single dict and generates/manages Series objects

from readinglistmanager import filemanager,utilities,config
from readinglistmanager.utilities import printResults
from readinglistmanager.errorhandling.problemdata import ProblemData, ProblemSeries
from readinglistmanager.datamanager import cvManager,metronManager,dbManager,datasource, save
from readinglistmanager.datamanager.datasource import ComicInformationSource, DataSourceType, ListSourceType
from readinglistmanager.model.readinglist import ReadingList
from readinglistmanager.model.series import Series, CoreSeries, CoreSeriesCollection
from readinglistmanager.model.issue import Issue
from readinglistmanager.model.issueRange import IssueRangeCollection

dataDB = dbManager.DataDB.get()
cv = cvManager.CV.get()
metron = metronManager.Metron.get()

# NOTE : Order of sources in list affects lookup order!!
#dataSources = [dataDB, metron]
activeDataSources = [dataDB]
activeWebSources = []

if config.CV.active: 
    activeDataSources.append(cv)
    activeWebSources.append(cv)
if config.Metron.active: 
    activeDataSources.append(metron)
    activeWebSources.append(metron)

_series = dict()
_series["Keys"] = dict()

_readingLists = dict()
_readingLists["Keys"] = dict()

for webSource in activeWebSources:
    _series[webSource.type] = dict()
    _readingLists[webSource.type] = dict()


_seriesOverrideList = None
counters = {
    'matches' : {'override' : 0, 'cv' : 0, 'db' : 0}, 
    'noMatches': {'override' : 0, 'cv' : 0, 'db' : 0}, 
    'matchType' : {'one' : 0, 'multiple' : 0, 'blacklist' : 0}
    }
overrideMatchCounter = 0

lookupMatch = {'match' : None, 'problemData' : None }

CORE_SERIES = ["Superman", "Batman", "Aquaman", "The Flash", "Justice League", "Wonder Woman", "Supergirl", \
    "Star Wars", "Star Wars: Darth Vader", "Star Wars: Bounty Hunters", "Star Wars: Doctor Aphra"]

_coreSeriesCollection = CoreSeriesCollection()


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

def getSeriesFromSeriesID(dataSourceType: ComicInformationSource.SourceType, seriesID : str) -> Series:
    # Check if series exists in dict
    if source in _series and seriesID in _series[source]:
        return _series[seriesID]
    else:
        for source in activeDataSources:
            if isinstance(source, ComicInformationSource):
                seriesData = source.getSeriesFromSeriesID(dataSourceType, seriesID)
                if seriesData is not None and isinstance(seriesData, list) and len(seriesData) > 0: 
                    seriesData = seriesData[0]
                    series = Series.fromDict(seriesData)

                    if isinstance(series, Series): 
                        return series

    return None

def getSeriesFromIssueID(dataSourceType : ComicInformationSource.SourceType, issueID : str) -> Series:
    
    series = None

    for source in activeDataSources:
        if isinstance(source, ComicInformationSource):
            issueDetails = source.getIssueFromIssueID(dataSourceType, issueID)
            if issueDetails is not None and isinstance(issueDetails, dict):
                seriesID = issueDetails['seriesID']
                if utilities.isValidID(seriesID):
                    series = getSeriesFromSeriesID(dataSourceType, seriesID)

    return series

def getSeriesFromDetails(name : str, startYear : str, seriesID : str = None) -> Series:
    series = None 
    seriesKey = Series.getSeriesKey(name, startYear)

    # Check if series exists in
    if seriesKey in _series["Keys"] and seriesID is not None and _series["Keys"][seriesKey].doesIDMatch(seriesID):
        series = _series["Keys"][seriesKey]
    else:
        if _seriesOverrideList is not None and seriesKey in _seriesOverrideList:
            # Series found in overrides list
            global overrideMatchCounter; overrideMatchCounter += 1
            #try:
            for webSource in activeWebSources:
                if webSource.type.value in _seriesOverrideList[seriesKey]:
                    if seriesID is None: 
                        seriesID = _seriesOverrideList[seriesKey][webSource.type.value]

                    series = getSeriesFromSeriesID(webSource.type, seriesID)
                    if isinstance(series, Series):
                        series.altSeriesKeys.append(seriesKey)
                        _addSeriesToList(series)
            #except Exception as e:
            #    printResults("Error : Unable to process series override for %s (%s) : %s" % (name, startYear, str(e)), 4)
            
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
    for webSource in activeWebSources:
        dataSourceType = webSource.type
        if isinstance(readingLists, list):
            for readingList in readingLists:
                if isinstance(readingList, ReadingList):
                    readingList.setStartYearFromIssueDetails()
                    readingList.setPublisherFromIssueDetails()

        numLists = len(readingLists)
        i = 0
        printResults("Checking %s reading lists" % (numLists), 2)

        readingListNames = list(set(readingList.name for readingList in readingLists))
        save.saveDataList('%sListLookup' % (webSource.type.value), readingListNames)
        
        if isinstance(readingLists, list):
            for readingList in readingLists:
                i += 1
                if isinstance(readingList, ReadingList):
                    _updateReadingListFromDataSources(readingList,dataSourceType)
                    printResults("%s / %s reading lists checked" % (i,numLists), 3, False, True)

def getSeriesSet():
    seriesSet = set()
    for seriesList in _series.values():
        seriesSet.update(seriesList.values())
    
    return seriesSet

def validateSeries() -> None:
    # Lookup series' details + collect all issue details based on series ID
    seriesSet = getSeriesSet()
    checkWebSeriesSet = set()
    numSeries = len(seriesSet)

    # Check DB for all series 
    printResults("Checking DB for %s series" % (numSeries), 3)
    
    sourceType = ComicInformationSource.SourceType.Database
    i = 0
    for series in seriesSet:
        i += 1
        if isinstance(series, Series):
            if series.sourceList.hasSource(sourceType) and not series.sourceList.isSourceChecked(sourceType):
                printResults("%s / %s series checked" % (i,numSeries),4,False,True)
                _updateSeriesFromDataSources(series,sourceType)

            if not series.allSourcesMatched():
                checkWebSeriesSet.add(series)
    
    numSeriesLookupWeb = len(checkWebSeriesSet)
    numSeriesFoundDB = numSeries - numSeriesLookupWeb

    printResults("Validation : DB matches = %s / %s" % (numSeriesFoundDB,numSeries),3)
    printResults("Validation : Web Searches Required = %s" % (numSeriesLookupWeb),3)


    # Iterate through set of incomplete series and check web for each
    unmatchedWebSet = set()
    i = 0
    for series in checkWebSeriesSet:
        i += 1
        for source in activeWebSources:
            if isinstance(series, Series) and not series.sourceList.isSourceChecked(source.type):
                printResults("[%s / %s] : Checking %s for %s (%s) [%s]" % (i, numSeriesLookupWeb, source.type.value, series.name, series.startYear, series.sourceList.getSourceID(source.type)), 4, False, True)
                _updateSeriesFromDataSources(series,source.type)
                if not series.hasValidID(source.type): 
                    unmatchedWebSet.add(series)
    
    numSeriesUnmatchedWeb = len(unmatchedWebSet)
    # Reprocess all series names for unmatched series
    printResults("Validation : Reprocessing Unmatched Series With Cleaned Name = %s" % (numSeriesUnmatchedWeb),3)
    i = 0
    counter = {'processed':0,'cleaned':0, 'matches': 0}
    for series in unmatchedWebSet:
        i += 1
        if isinstance(series, Series):
            printResults("[%s / %s] : Reprocessing %s (%s)" % (i, numSeriesUnmatchedWeb, series.name, series.startYear), 4, False, True)
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

    webSeriesNames = list(set(series.name for series in checkWebSeriesSet if isinstance(series, Series)))
    save.saveDataList('webSeriesLookup', webSeriesNames)

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

    for dataSource in activeDataSources:
        if isinstance(dataSource, ComicInformationSource):
            if checkDataSource is not None and dataSource.type not in (ComicInformationSource.SourceType.Database,checkDataSource):
                # Skip unwanted datasource if specific dataSource is specified in request
                continue

            # Check dataSource for match
            listResults = dataSource.getReadingListsFromName(readingList.name)

            readingList.sourceList.setSourceChecked(dataSource.type)
            
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
                newReadingList = ReadingList.fromDict(match, datasource.type)
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
            for webSource in activeWebSources:
                finalMatch = cv.getReadingListFromID(finalMatch['listID'])
                finalMatch = finalMatch[0] if len(finalMatch) > 0 else None

                if finalMatch is not None: return finalMatch
    
    return None


def _updateSeriesFromDataSources(series : Series, checkDataSource : ComicInformationSource.SourceType = None) -> None:

    if not isinstance(series, Series):
        return None

    for dataSource in activeDataSources:
        if (checkDataSource is not None 
            and isinstance(checkDataSource, ComicInformationSource.SourceType) 
            and dataSource.type is not checkDataSource):
                continue

        if isinstance(dataSource.type, ComicInformationSource.SourceType):
            if dataSource.type == ComicInformationSource.SourceType.Database:
                #Different process for database lookups (need one lookup for each webSource type)
                for webDataSource in activeWebSources:
                    #Check database for match against each web data source
                    _updateSeriesFromDataSource(series, dataSource, webDataSource.type)
            else:                
                #Check web data source if desired
                _updateSeriesFromDataSource(series, dataSource)

    # If a match was found, update internal series dictionary with IDs
    if series.hasValidID():
        _addSeriesToList(series)
         
    # Add result to DB if legit match found on CV
    #if series is not None and isinstance(series, Series) and series.dataSourceType == ComicInformationSource.SourceType.Comicvine:

def _updateSeriesFromDataSource(series : Series, dataSource, dataSourceLookupType : ComicInformationSource.SourceType = None) -> None:
    # Check dataSource for match
    if isinstance(series, Series):
        if series.name == 'Avengers Assemble':
            pass

        if dataSourceLookupType is not None and series.hasValidID(dataSourceLookupType):
            seriesResults = dataSource.getSeriesFromSeriesID(dataSourceLookupType, series.getSourceID(dataSourceLookupType))
        elif series.hasValidID(dataSource.type):
            seriesResults = dataSource.getSeriesFromSeriesID(dataSource.type, series.getSourceID(dataSource.type))
        else:
            if dataSource.type == ComicInformationSource.SourceType.Database:
                #Need to pass lookup type if using database
                seriesResults = dataSource.getSeriesFromDetails(series.name, series.startYear, dataSourceLookupType)
            else:
                seriesResults = dataSource.getSeriesFromDetails(series.name, series.startYear)

    series.sourceList.setSourceChecked(dataSource.type)
    
    match = None

    if seriesResults is not None and len(seriesResults) > 0:
        # Results found - get exact match
        match = _getFinalSeriesMatchFromResults(seriesResults,series)
    
    if match is not None:
        #try:
        series.mainDataSourceType = dataSource.type
        series.updateDetailsFromDict(match['seriesDetails'])
        series.updateIssuesFromDict(match['issueList'])
        #except:
        #    printResults("Error : Unable to create series from dict : %s" % (seriesFinalMatch), 4)


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
            for dataSource in activeDataSources:
                databaseSeriesIssues = None

                if isinstance(dataSource, ComicInformationSource):
                    databaseSeriesIssues = dataSource.getIssuesFromSeriesID(seriesResult['seriesID'], seriesResult['dataSource'])
                    #series.sourceList.setSourceChecked(dataSource.type)

                # Check if issue results exist
                if databaseSeriesIssues is not None and len(databaseSeriesIssues) > 0:
                    exactSeriesMatch = True

                    seriesIssueNumbers = series.getIssueNumsList()

                    # TODO : Account for series start years at different times
                    # Quick test to check that numResults >= numSeriesIssues 
                    if len(databaseSeriesIssues) < len(seriesIssueNumbers):
                        exactSeriesMatch = False
                        break
                    else:
                        # Check if all expected issues exist in CV volume match
                        for expectedIssueNum in seriesIssueNumbers:
                            doesCurrentIssueMatch = doesSeriesIssueMatchDatabaseResult(expectedIssueNum,seriesIssueNumbers,databaseSeriesIssues)
                            if not doesCurrentIssueMatch:
                                exactSeriesMatch = False
                                break
                        
                    # Exit loop immediately if exact match is found                    
                    if exactSeriesMatch: 
                        if dataSource.type in [ComicInformationSource.SourceType.Comicvine,ComicInformationSource.SourceType.Metron]:
                            dataDB.addVolume(dataSource.type, seriesResult)
                            # Data obtained from CV
                            for issue in databaseSeriesIssues.values():
                                dataDB.addIssue(dataSource.type, issue)
                        #Exact match found
                        return {'seriesDetails':seriesResult, 'issueList':databaseSeriesIssues}
    
    return None

def doesSeriesIssueMatchDatabaseResult(curIssueNum : str, seriesIssueNums : list, databaseIssueNums : list):
    # This function checks a selected issueNumber from seriesIssueList matches database search results

    if curIssueNum in databaseIssueNums:
        return True
    else:
        if not utilities.isNumber(curIssueNum):
            # Current issue number is not an integer! Need to check for match after stripping additional characters from curIssueNum
            strippedIssueNum = utilities.stripIssueNumber(curIssueNum)
            if strippedIssueNum in databaseIssueNums and strippedIssueNum not in seriesIssueNums:
                # Match found with stripped issueNumber, so safe to continue
                return True
        else: 
            # Current issue number is an integer! Need to check for match after stripping additional characters from partial matches in databaseIssueNums

            # Get all partial issue number matches in databaseIssueNums (as a list of strings)
            partialIssueNumMatches = utilities.findPartialStringMatches(curIssueNum, databaseIssueNums)

            if len(partialIssueNumMatches) > 0:
                # Similar issue numbers found. Time to clean and compare them!
                for issueNum in partialIssueNumMatches:
                    if utilities.stripIssueNumber(issueNum) == curIssueNum:
                        # Match found with stripped issueNumber, so safe to continue
                        return True
        
        return False


def _addSeriesToList(series : Series) -> None:
    # Add series to master series dict 
    _series["Keys"][series.key] = series
    if len(series.altSeriesKeys) > 0:
        for seriesKey in series.altSeriesKeys:
            _series["Keys"][seriesKey] = series

    for source in series.sourceList.getSourcesList():
        if source.id is not None:
            _series[source.type][source.id] = series

    # Add core series to special set
    if series.name in CORE_SERIES:
        newCoreSeries = CoreSeries(series)
        _coreSeriesCollection.addCoreSeries(newCoreSeries)


def _addReadingList(readingList : ReadingList) -> None:
    # Add series to master series dict 
     if isinstance(readingList, ReadingList):

        if readingList.key in _readingLists["Keys"]:
            curList = _readingLists["Keys"][readingList.key]
            if isinstance(curList, list):
                curList.append(readingList)
            else:
                curList = [readingList]
        else:
            _readingLists[readingList.key] = [readingList]

        for source in readingList.sourceList.getSourcesList():
            if utilities.isValidID(source.id):
                if source.id in _readingLists[source.type]:
                    curList = _readingLists[source.type][source.id]
                    if isinstance(curList, list):
                        curList.append(readingList)
                    else:
                        curList = [readingList]
                else :
                    _readingLists[source.type][source.id] = [readingList]

def createNewSeries(name : str, startYear : int) -> Series :

    newSeries = Series(name, startYear)
    _addSeriesToList(newSeries)

    return newSeries

def getIssueFromIssueID(dataSourceType : ComicInformationSource.SourceType, issueID : str) -> Issue:
    issue = None

    for curDataSource in activeDataSources:
        if isinstance(curDataSource, ComicInformationSource):
            issueData = curDataSource.getIssueFromIssueID(dataSourceType, issueID)


            if isinstance(issueData,list) and len(issueData) > 0:
                issueData = issueData[0]
                if isinstance(issueData, dict):
                    issue = Issue.fromDict(issueData)
                    issue.sourceList.setSourceChecked(dataSourceType)
                    seriesID = issueData['seriesID']
                    if utilities.isValidID(seriesID):
                        series = getSeriesFromSeriesID(dataSourceType, seriesID)
                        if isinstance(series, Series):
                            series.addIssue(issue)

            if isinstance(issue, Issue):
                break
                issue.sourceList.setSourceChecked(dataSourceType)

    return issue

def _getSeriesIssueDetails(seriesObject : Series) -> None:
    if isinstance(seriesObject,Series) and seriesObject.hasValidID():
        for webSource in seriesObject.sourceList.getSourcesList():
            if seriesObject.hasValidID(webSource.type):
                #TODO: Allow prioritisation of data sources when multiple matches found
                for dataSource in activeDataSources:
                    if isinstance(dataSource,ComicInformationSource):
                        issueDetailsList = dataSource.getIssuesFromSeriesID(seriesObject.id, webSource.type)
                        if issueDetailsList is not None and len(issueDetailsList) > 0:
                            for issueDetails in issueDetailsList:
                                #if issueDetails['issueNum'] in seriesObject.issueList:
                                # We want all series issues, not just the ones that are used!
                                curIssue = seriesObject.issueList[issueDetails['issueNum']]
                                if isinstance(curIssue, Issue):
                                    curIssue.updateDetailsFromDict(issueDetails)
                                    curIssue.sourceType = dataSource.type
                                    issue.sourceList.setSourceChecked(dataSource.type)
                                    if dataSource.type in [ComicInformationSource.SourceType.Comicvine,ComicInformationSource.SourceType.Metron]:
                                        dataDB.addIssue(curIssue.getDBDict())
                
                if seriesObject.hasCompleteIssueDetails():
                    break
                else:
                    # Not all details found
                    pass

#def getSeriesIssueDetails(series : Series) -> None:
#    try:
#        getSeriesIssueDetails(series)

def getIssueFromDetails(seriesName : str, seriesStartYear : int, issueNum : str) -> Issue:
    issue = None

    if None not in (seriesName, seriesStartYear, issueNum):
        series = getSeriesFromDetails(seriesName,seriesStartYear)
        issue = series.getIssue(issueNum)

    return issue

def getIssueFromIDs(dataSourceType: ComicInformationSource.SourceType, seriesID : str, issueID : str) -> Issue:
    issue = None

    if None not in (seriesID, issueID):
        series = getSeriesFromSeriesID(dataSourceType, seriesID)
        issue = getIssueFromIssueID(dataSourceType, issueID)
        if isinstance(series, Series) and isinstance(issue, Issue):
            series.addIssue(issue)

    return issue

def getIssueFromSeriesID(dataSourceType: ComicInformationSource.SourceType, seriesID : str, issueNumber : str) -> Issue:

    if None not in (dataSourceType,seriesID, issueNumber):
        series = getSeriesFromSeriesID(dataSourceType, seriesID)
        issue = series.getIssue(issueNumber)
        
        if isinstance(series, Series) and isinstance(issue, Issue):
            series.addIssue(issue)
    
        return issue
    else:
        return None

def printSummaryResults():

    printResults("*** Comic Information Sources ***", 2)
    for dataSource in activeDataSources:
        if isinstance(dataSource,ComicInformationSource):
            if isinstance(dataSource.type, ComicInformationSource.SourceType):
                printResults("Data Source : %s" % (dataSource.type.value),3)
            
            for key, value in dataSource.counters.items():
                printResults("%s" % (key.value),4)
                printResults(', '.join('{} : {}'.format(k.value,v) for k,v in value.items()),5)



    printResults("*** Reading List Statistics ***", 2)
    readingListCompleteIssuesCount = 0
    readingListSet = getReadingListSet()

    issuesCheckedSet = set()
    issueIDsFound = dict()
    for source in activeWebSources:
        issueIDsFound[source.type] = 0

    for readingList in readingListSet:
        if isinstance(readingList, ReadingList):
            seriesDetailsFound = issueDetailsFound = 0
            seriesSet = set()
            issueListLength = len(readingList.issueList)

            # Check issue details found
            for issue in readingList.issueList.values():
                if isinstance(issue, Issue):
                    seriesSet.add(issue.series)
                    if issue not in issuesCheckedSet:
                        for source in issueIDsFound.keys():
                            if issue.hasValidID(source):
                                issueIDsFound[source] += 1
                        issuesCheckedSet.add(issue)
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
    for source in issueIDsFound.keys():
        printResults("%s issues matched : %s / %s" % (str(source.value).capitalize(),issueIDsFound[source],len(issuesCheckedSet)),4)


    printResults("*** Series Statistics ***", 2)
    seriesSet = getSeriesSet()
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
    seriesSet = getSeriesSet()
    
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

def getSeriesIDList() -> list:
    seriesIDList = set(series.getSourceID(ComicInformationSource.SourceType.Comicvine) for series in getSeriesSet())
    return seriesIDList

def getIssueNumsList(seriesID : str, sourceType : ComicInformationSource.SourceType) -> list:
    issueNums = list()
    for source in activeDataSources:
        
        # Get all issue details from source
        issueDetails = source.getIssuesFromSeriesID(seriesID, sourceType)
        
        if issueDetails is not None:

            #Add issue numbers to list
            for issue in issueDetails.values():
                issueNums.append(issue['issueNum'])
            
            #don't bother checking other sources
            return issueNums

    # If no matches found in either source
    return None

def getSeriesEvents() -> str:
        
    stringData = ["Summary of Series Events\n"]

    for seriesName, seriesDict in _coreSeriesCollection.getCoreSeriesDict().items():
        for seriesStartYear, seriesSet in seriesDict.items():
            for curSeries in seriesSet:
                if isinstance(curSeries, CoreSeries):
                    # Get all reading list references in each Issue
                    for issue in curSeries.issueList.values():
                        try:
                            readingListRefs = issue.getReadingListRefs()
                            for readingList in readingListRefs:
                                curSeries.addReadingListReference(readingList, issue.issueNumber)
                        except:
                            pass
                    
                    #tempDict = dict()
                    #for readingList, issueNumList in curSeries.readingListReferences.items():
                    #    tempDict[readingList.name] = IssueRangeCollection.fromListOfNumbers(issueNumList)


                    #Simplify issue numbers
                    #TODO: Remove hardcoded ID check
                    seriesIssueNums = getIssueNumsList(curSeries.getSourceID(ComicInformationSource.SourceType.Comicvine), ComicInformationSource.SourceType.Comicvine)
                    curSeries.organiseIssueNums(seriesIssueNums)
                    #curSeries.getEventRelationshipString()
                    
                    #Export series event list to file
                    stringData.extend(curSeries.getEventsSummary())
    
    return stringData

def getPUMLString() -> str:
        
    return _coreSeriesCollection.getPUMLString()

def getVizGraphString() -> str:
        
    return _coreSeriesCollection.getVizGraphString()


def processNoIssueMatches():

    #Process series where there are more issues in list than are found on CV
    # ie. Series is split between 2 vols
     
    data = ProblemData.getData(ProblemData.ProblemType.CVNoIssueMatch)
    seriesMatches = dict()

    for problemSeries in data:
        if isinstance(problemSeries, ProblemSeries):
            seriesIssueNumbers = problemSeries.getIssueNumsList()
            seriesIssuesMatched = dict()
            seriesIssuesMatched['unknown'] = seriesIssueNumbers

            for webSource in activeWebSources:
                # Get list of series name matches
                seriesList = webSource.getSeriesFromNameFilter(problemSeries.series.name)
                seriesYearList = dict()

                for series in seriesList:
                    if series['startYear'] not in seriesYearList: seriesYearList[series['startYear']] = list()
                    seriesYearList[series['startYear']].append(series['seriesID'])
                        
                seriesYearList = dict(sorted(seriesYearList.items(), key=lambda item: item[1]))


                # Iterate through series matches starting with year given
                #TODO: Set year match priority
                for curSeries in seriesList:
                    seriesIssuesMatched = _getSeriesIssuesMatch(seriesIssuesMatched, curSeries)
                    if len(seriesIssuesMatched['unknown']) == 0:
                        # All issues matched!
                        break
                
                if len(seriesIssuesMatched['unknown']) == 0:
                        # All issues matched!
                        break

            #if isinstance(problemSeries.data,dict) and ComicInformationSource.ResultFilterType.Allowed in problemSeries.data:
            #    if len(problemSeries.data[ComicInformationSource.ResultFilterType.Allowed]) == 1:
            #        #Exactly one series match - proceed!
            #        seriesResult = problemSeries.data[ComicInformationSource.ResultFilterType.Allowed][0]
            #        for dataSource in dataSources:
            #            seriesIssues = None
            #            if isinstance(dataSource, ComicInformationSource):
            #                seriesIssues = dataSource.getIssuesFromSeriesID(seriesResult['seriesID'])
            #            # Check if issue results exist
            #            if seriesIssues is not None and len(seriesIssues) > 0:
            #                exactSeriesMatch = True
            #                while(len(seriesIssuesMatched['unknown']) > 0):
            #                # Quick test to check that numResults >= numSeriesIssues 
            #                if len(seriesIssues) < len(seriesIssueNumbers):
            #                    # TODO : Check for split series here
            #                    for curIssueNum in seriesIssueNumbers:
            #                        if curIssueNum in seriesIssues.keys():
            #                            #Transfer issue number from unmatched to matched list
            #                            seriesIssuesMatched['seriesID'].append(seriesIssuesMatched['unknown'].pop(curIssueNum))
            #                    #if len(seriesIssuesMatched) > 0:
            #                    #    seriesMatches[seriesResult['seriesID']] = seriesIssuesMatched
            #                    if len(seriesIssuesMatched['unknown']) > 0:
            #                        issueStrings = utilities.simplifyListOfNumbers(seriesIssuesMatched['unknown'])
            #                        
            #                    exactSeriesMatch = False
            #                    break
            #                if isinstance(dataSource, ComicInformationSource):
            #                    seriesIssues = dataSource.getIssuesFromSeriesID(seriesResult['seriesID'])

# Given a dict of series : issueNums and series details dict, check for issue matches and return updated issueNum dict
def _getSeriesIssuesMatch(seriesIssueMatches : dict, seriesDict : dict):
    updatedSeriesIssueMatches = seriesIssueMatches

    if isinstance(seriesDict, dict) and isinstance(updatedSeriesIssueMatches, dict) and 'seriesID' in seriesDict:
        for dataSource in activeDataSources:
            seriesIssues = None

            if isinstance(dataSource, ComicInformationSource):
                # Grab issue details
                seriesIssues = dataSource.getIssuesFromSeriesID(seriesDict['seriesID'], dataSource.type)

                for issueNum in updatedSeriesIssueMatches['unknown']:
                    if isinstance(seriesIssues, dict) and issueNum in seriesIssues.keys():
                        if 'issueType' in seriesIssues[issueNum] and seriesIssues[issueNum]['issueType'] == ComicInformationSource.IssueType.Trade:
                            return seriesIssueMatches

                        # Initialise list if needed
                        if seriesDict['seriesID'] not in updatedSeriesIssueMatches: 
                            updatedSeriesIssueMatches[seriesDict['seriesID']] = list()

                        # Update lists
                        updatedSeriesIssueMatches[seriesDict['seriesID']].append(issueNum)
                        updatedSeriesIssueMatches['unknown'].remove(issueNum)


                if seriesIssues is not None:
                    #Exit loop if match found
                    return updatedSeriesIssueMatches

    
    return updatedSeriesIssueMatches
