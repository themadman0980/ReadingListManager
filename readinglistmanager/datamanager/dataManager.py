#!/usr/bin/env python3
# -*- coding: utf-8 -*-

### Manages datasources, filters list[dict] lookup results into single dict and generates/manages Series objects

from numpy import DataSource
from readinglistmanager import filemanager,utilities,config
from readinglistmanager.errorhandling import problemdata
from readinglistmanager.utilities import printResults
from readinglistmanager.errorhandling.problemdata import ProblemData
from readinglistmanager.datamanager import cvManager,dbManager,datasource
from readinglistmanager.datamanager.datasource import ComicInformationSource
from readinglistmanager.model.readinglist import ReadingList
from readinglistmanager.model.series import Series
from readinglistmanager.model.issue import Issue

dataDB = dbManager.DataDB.get()
cv = cvManager.CV.get()

# NOTE : Order of sources in list affects lookup order!!
dataSources = [dataDB, cv]

_series = {}
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

def getSeries(name : str, startYear : int, seriesID : str = None) -> Series:
    # Check if series exists in dict
    if seriesID is not None and id in _series:
        return _series[id]
    else:
        dynamicName = utilities.getDynamicName(name)
        startYear = utilities.getCleanYear(startYear)

    if isinstance(series, Series):
        # Check result is valid
        if series.nameClean != dynamicName or series.startYear != startYear:
            printResults("Warning : Series ID match \"%s (%s) [%s]\" does not have exact match with ReadingList entry details \'%s (%s)\'" % (
                series.id, series.name, series.startYear, name, startYear), 4)
    else:
        series = getSeriesFromDetails(name, startYear)

def getSeriesFromID(id : str) -> Series:
    # Check if series exists in dict
    if id in _series:
        return _series[id]

    return None

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
                series = getSeriesFromID(seriesID)
            except Exception as e:
                printResults("Error : Unable to process series override for %s (%s) : %s" % (name, startYear, str(e)), 4)
            
        # If no result/error in override list
        if series is None:
            # Check all available data sources for an exact match
            series = createNewSeries(name, startYear)

    return series

def validateSeries():
    # Identify series' with incomplete details + collect all issue details based on series ID
    seriesSet = set()
    checkCVSeriesSet = set()

    # Check _series list for incomplete series and add to set
    for key, series in _series.items():
        if isinstance(series, Series):
            seriesSet.add(series)

    # Check DB for all series 
    sourceType = ComicInformationSource.SourceType.Database
    for series in seriesSet:
        if isinstance(series, Series):
            if not series.checked[sourceType]:
                _updateSeriesFromDataSources(series,sourceType)

            if not series.hasCompleteSeriesDetails():
                checkCVSeriesSet.add(series)

    
    numSeries = len(seriesSet)
    numSeriesLookupCV = len(checkCVSeriesSet)
    numSeriesFoundDB = numSeries - numSeriesLookupCV
    i = 0

    printResults("Validation : DB matches = %s / %s" % (numSeriesFoundDB,numSeries),3)
    printResults("Validation : CV Searches Required = %s" % (numSeriesLookupCV),3)

    # Iterate through set of incomplete series and check CV for each
    sourceType = ComicInformationSource.SourceType.Comicvine
    for series in checkCVSeriesSet:
        if isinstance(series, Series) and not series.checked[sourceType]:
            i += 1
            printResults("[%s / %s] : Checking CV for %s (%s) [%s]" % (i, numSeriesLookupCV, series.name, series.startYear, series.id), 4, False, True)
            _updateSeriesFromDataSources(series,sourceType)
            

def _filterSeriesResults(results : list[dict], series : Series) -> dict[list[dict]]:
    preferredType = ComicInformationSource.ResultFilterType.Preferred 
    allowedType = ComicInformationSource.ResultFilterType.Allowed 
    blacklistType = ComicInformationSource.ResultFilterType.Blacklisted 
    resultsFiltered = {preferredType:[], allowedType:[], blacklistType:[]}
    problemTypes = list()
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
            # If dynamicname matches were found, see if the series year was within 2 years of expected
            for result in nameOnlyMatches:
                matchYearClean = utilities.getCleanYear(result['startYear'])
                matchNameClean = utilities.getDynamicName(result['name'])
                if None not in (matchYearClean, series.startYear):
                    deviation = abs(int(matchYearClean) - int(series.startYear))
                    if deviation <= 2: 
                        if series.dynamicName == matchNameClean:
                            series.addProblem(ProblemData.ProblemType.CVIncorrectYear, result)
                        elif series.dynamicName in matchNameClean:
                            series.addProblem(ProblemData.ProblemType.CVSimilarMatch, result)
        else:
            series.addProblem(ProblemData.ProblemType.CVNoMatch,None)
    elif numAcceptableMatches > 0:
        if numAcceptableMatches > 1:
            series.addProblem(ProblemData.ProblemType.MultipleMatch, acceptableMatches)

    return resultsFiltered

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
                match = _getFinalMatchFromResultsList(seriesResults,series)
            
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


def _getFinalMatchFromResultsList(results : list[dict], series : Series = None) -> dict:
    # Takes list[dict] and filters it to return a single dict object
    match = None

    if results is not None and isinstance(results, list):
        filteredResultsList = _filterSeriesResults(results, series)

        issueNumList = series.getIssueNumsList()
        if issueNumList is not None:
            match = _checkSeriesIssuesMatch(filteredResultsList, series)
    
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
    _series[series.key] = _series[series.id] = series

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

            if isinstance(issueData,list):
                issueData = issueData[0]
                issue = Issue(None,issueData['issueNum'],curDataSource.type)
                issue.updateDetailsFromDict(issueData)

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
                                curIssue.dataSourceType = dataSource.type
                                if dataSource.type == ComicInformationSource.SourceType.Comicvine:
                                    dataDB.addIssue(curIssue.getDict())
            
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
        series = getSeriesFromID(seriesID)
        issue = getIssueFromIssueID(issueID)
        if isinstance(series, Series) and isinstance(issue, Issue):
            series.addIssue(issue)

    return issue

def getIssueFromSeriesID(seriesID : str, issueNumber : str) -> Issue:
    issue = None

    if None not in (seriesID, issueNumber):
        series = getSeriesFromID(seriesID)
        issue = series.getIssue(issueNumber)
        if isinstance(series, Series) and isinstance(issue, Issue):
            series.addIssue(issue)
    
    return issue

def printSummaryResults(readingLists : list[ReadingList]):

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
    
    for readingList in readingLists:
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
    printResults("Complete List Details Found : %s / %s" % (readingListCompleteIssuesCount,len(readingLists)), 4)


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
    seriesSet = set(_series.values())
    
    for series in seriesSet:
        if isinstance(series, Series):
            curProblemData = series.problems
            for problemType, data in curProblemData.items():
                ProblemData.addSeriesEntry(series, problemType, data)