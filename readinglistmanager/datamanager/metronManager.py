#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from html import unescape
from readinglistmanager import config,filemanager,utilities
#from readinglistmanager.datamanager import dataManager
from readinglistmanager.utilities import printResults, stripYearFromName
from readinglistmanager.model.date import PublicationDate
from readinglistmanager.datamanager.datasource import ComicInformationSource, ListSourceType
import mokkari.series, mokkari.issue, mokkari.arc
from mokkari.sqlite_cache import SqliteCache

import mokkari

CACHE_RETENTION_TIME = 60 #days
MAX_RESULTS = 100

if config.Metron.cache_searches:
    _metronSession = mokkari.api(config.Metron.username, config.Metron.password, cache=SqliteCache(filemanager.metronCacheFile,CACHE_RETENTION_TIME))
else:
    _metronSession = mokkari.api(config.Metron.username, config.Metron.password)

class Metron(ComicInformationSource):
    instance = None
    type = ComicInformationSource.SourceType.Metron

    @classmethod
    def get(self):    
        if Metron.instance is None: 
            Metron.instance = Metron()

        return Metron.instance

    def convertIssueResultsToDict(self, issueResults : list[mokkari.issue.Issue], resultsType : ComicInformationSource.ResultType) -> list[dict]:
        results = []
        self.updateCounter(ComicInformationSource.SearchStatusType.SearchCount,resultsType)

        if isinstance(issueResults, mokkari.issue.Issue):
            # Single result found
            result = issueResults
            issueDetails = ComicInformationSource._issueDetailsTemplate.copy()
            issueType = ComicInformationSource._getIssueType(result.name, result.description,"")
            
            if hasattr(result,'desc'): 
                description = result.desc
            else:
                description = none

            issueDetails.update({
                'issueID' : str(result.id), 
                'name' : result.issue_name, 
                'coverDate' : PublicationDate.fromDateTimeObj(result.cover_date), 
                'issueNum': str(result.number), 
                'issueType' : issueType, 
                'description' : description, 
                'summary' : "",
                'dataSource' : self.type
                })
            results.append(issueDetails)
        elif isinstance(issueResults, mokkari.issue.IssuesList):
            for result in issueResults:
                if isinstance(result, mokkari.issue.Issue):
                    issueDetails = ComicInformationSource._issueDetailsTemplate.copy()

                    if hasattr(result, 'desc'): 
                        description = result.desc
                    else:
                        description = None

                    issueType = ComicInformationSource._getIssueType(result.issue_name,description,"")
                    issueDetails.update({
                        'issueID' : str(result.id), 
                        'name' : result.issue_name, 
                        'coverDate' : PublicationDate.fromDateTimeObj(result.cover_date), 
                        'issueNum': str(result.number), 
                        'issueType' : issueType, 
                        'description' : description, 
                        'summary' : "",
                        'dataSource' : self.type
                        })
                    results.append(issueDetails)
        
        if results is None or len(results) == 0:
            self.updateCounter(ComicInformationSource.SearchStatusType.NoResultsCount,resultsType)
        else:
            self.updateCounter(ComicInformationSource.SearchStatusType.ResultsCount,resultsType)

        if not config.Metron.check_issues: results = None

        return results


    def convertSeriesResultsToDict(self, volumeResults : list[mokkari.series.Series], resultsType : ComicInformationSource.ResultType) -> list[dict]:
        results = []
        self.updateCounter(ComicInformationSource.SearchStatusType.SearchCount,resultsType)

        if isinstance(volumeResults, mokkari.series.Series):
            # Single result found
            result = volumeResults
            seriesDetails = ComicInformationSource._seriesDetailsTemplate.copy()
            publisher = result.publisher.name if result.publisher is not None else None
            issueList = self.getIssuesFromSeriesID(result.id, self.type) if hasattr(result, 'id') else None
            issueList = self.convertIssueResultsToDict(issueList, ComicInformationSource.ResultType.IssueList) if issueList is not None else None
            name = stripYearFromName(result.display_name)
            #issueList = self.convertIssueResultsToDict(volumeResults, ComicInformationSource.ResultType.IssueList) if hasattr(volumeResults, 'issues') else None
            seriesDetails.update({
                'seriesID': str(result.id), 
                'name' : name, 
                'startYear' : result.year_began, 
                'publisher' : publisher, 
                'numIssues' : result.issue_count, 
                'description' : result.desc, 
                'summary' : "",
                'issueList' : issueList,
                'dataSource' : self.type
                })
            results.append(seriesDetails)
        elif isinstance(volumeResults, mokkari.series.SeriesList):
            for result in volumeResults.series:
                if isinstance(result, mokkari.series.Series):
                    seriesDetails = ComicInformationSource._seriesDetailsTemplate.copy()
                    issueList = self.getIssuesFromSeriesID(result.id, self.type) if hasattr(result, 'id') else None
                    #issueList = self.convertIssueResultsToDict(issueList, ComicInformationSource.ResultType.IssueList) if issueList is not None else None
                    #issueList = self.convertIssueResultsToDict(volumeResults, ComicInformationSource.ResultType.IssueList) if hasattr(volumeResults, 'issues') else None
                    name = stripYearFromName(result.display_name)
                    seriesDetails.update({
                        'seriesID': str(result.id), 
                        'name' : name, 
                        'startYear' : result.year_began, 
                        'numIssues' : result.issue_count, 
                        'issueList' : issueList,
                        'dataSource' : self.type
                        })
                    results.append(seriesDetails)        
        if results is None or len(results) == 0:
            self.updateCounter(ComicInformationSource.SearchStatusType.NoResultsCount,resultsType)
        else:
            self.updateCounter(ComicInformationSource.SearchStatusType.ResultsCount,resultsType)

        return results


    def convertReadingListResultsToDict(self, searchResults : list[mokkari.arc.Arc], resultsType : ComicInformationSource.ResultType) -> list[dict]:
        dictResults = []
        self.updateCounter(ComicInformationSource.SearchStatusType.SearchCount,resultsType)

        if isinstance(searchResults, mokkari.arc.Arc):
            # Single result found
            result = searchResults
            listDetails = ComicInformationSource._listDetailsTemplate.copy()
            issueList = None
            if result.id is not None:
                issueList = self.arc_issues_list(result.id)
                issueList = self.convertIssueResultsToDict(issueList, ComicInformationSource.ResultType.Issue)
                # issueList = self.convertIssueResultsToDict(result.issues, ComicInformationSource.ResultType.Issue)
            #publisher = result.publisher.name if result.publisher is not None else None
            listDetails.update({
                'listID': str(result.id), 
                'name' : result.name, 
                'publisher' : "", 
                'issues': issueList, 
                'numIssues' : len(issueList), 
                'description' : result.desc, 
                'summary' : "",
                'dataSource' : self.type
                })
            dictResults.append(listDetails)
        elif isinstance(searchResults, list):
            for result in searchResults:
                if isinstance(result, mokkari.arc.Arc):
                    listDetails = ComicInformationSource._listDetailsTemplate.copy()
                    issueList = None
                    if result.id is not None:
                        issueList = self.arc_issues_list(result.id)
                        issueList = self.convertIssueResultsToDict(issueList, ComicInformationSource.ResultType.Issue)
                        # issueList = self.convertIssueResultsToDict(result.issues, ComicInformationSource.ResultType.Issue)
                    #publisher = result.publisher.name if result.publisher is not None else None
                    listDetails.update({
                        'listID': str(result.id), 
                        'name' : result.name, 
                        'publisher' : "", 
                        'issues': issueList, 
                        'numIssues' : len(issueList), 
                        'description' : result.desc, 
                        'summary' : "",
                        'dataSource' : self.type
                        })
                    dictResults.append(listDetails)
        
        if dictResults is None or len(dictResults) == 0:
            self.updateCounter(ComicInformationSource.SearchStatusType.NoResultsCount,resultsType)
        else:
            self.updateCounter(ComicInformationSource.SearchStatusType.ResultsCount,resultsType)

        return dictResults


    def getSeriesFromDetails(self, name : str, startYear : int) -> list[dict]:
        results = None
        matches = []

        if config.Metron.check_series and None not in (name, startYear):
            #printResults("Info: Searching CV for series : %s (%s)" % (name, startYear), 4) 
            dynamicName = utilities.getDynamicName(name)

            # Try a search filter (exact text match only)     
            results = self.getSeriesFromNameFilter(name, startYear)

            # Find matches if results exist
            if results is not None and len(results) > 0:
                for match in results:
                    if isinstance(match, dict):
                        resultDynamicName = utilities.getDynamicName(match['name'])
                        resultStartYear = utilities.getCleanYear(match['startYear'])
                        if resultDynamicName == dynamicName and resultStartYear == startYear:
                            matches.append(match)

            # No matches from CV FILTER lookup
            #if len(matches) == 0:
                # Try resource search instead of filter
                #results = self.getSeriesFromNameSearch(name)

        # Return *all* results for processing/filtering by dataManager
        return results

    def getSeriesFromNameFilter(self,name : str, startYear : int = None) -> list[dict]:
        results = None
        resultsType = ComicInformationSource.ResultType.SeriesList

        if not config.Metron.check_series: return None

        #try:
        if startYear is None:
            results = _metronSession.series_list({"name": name})
        else:
            results = _metronSession.series_list({"name": name, "year_began": int(startYear)})

        results = self.convertSeriesResultsToDict(results, resultsType)
        #except Exception as e:
        #    printResults("CV Error: Unable to search for series \"%s\" : %s" % (name,str(e)), 4)

        return results


    def getSeriesFromNameSearch(self, name : str) -> list[dict]:
        # Use SEARCH to identify CV matches from series name
        results = None
        resultsType = ComicInformationSource.ResultType.SeriesList

        if not config.Metron.check_series: return None

        #try:
        results = _metronSession.search(resource=simyan.comicvine.ComicvineResource.VOLUME,query=name)
        results = self.convertSeriesResultsToDict(results, resultsType)
        #except Exception as e:
        #    printResults("CV Error: Unable to search for series \"%s\" : %s" % (name,str(e)), 4)

        return results


    def getSeriesFromSeriesID(self, dataSourceType : ComicInformationSource.SourceType, seriesID : str) -> list[dict]:
        results = None
        resultsType = ComicInformationSource.ResultType.Series

        if not config.Metron.check_series: return None
        if dataSourceType is not self.type: return None

        #try:
        results = _metronSession.series(seriesID)
        results = self.convertSeriesResultsToDict(results, resultsType)
        #except Exception as e:
        #    printResults("CV Error: Unable to search for series [%s] : %s" % (seriesID, str(e)), 4)

        return results


    def getIssuesFromSeriesID(self, seriesID : str, dataSourceType : ComicInformationSource.SourceType = None) -> dict[dict]:
        resultsDict = dict()
        resultsType = ComicInformationSource.ResultType.IssueList

        ### Issue results required for series validation ###
        # if not config.CV.check_issues: return None

        #try:
        if seriesID is not None and dataSourceType == self.type:
            results = _metronSession.issues_list(params={"series_id" : seriesID})
            resultsList = self.convertIssueResultsToDict(results, resultsType)
            if resultsList is not None:
                for result in resultsList:
                    result['seriesID'] = seriesID
                    resultsDict[result['issueNum']] = result

        #except Exception as e:
        #    printResults("Metron Error: Unable to search for series issues using series ID [%s] : %s" % (seriesID,str(e)), 4)        

        return resultsDict


    def getIssueFromID(self, issueID : str) -> list[dict]:
        results = None
        resultsType = ComicInformationSource.ResultType.Issue

        if not config.Metron.check_issues: return None

        try:
            results = _metronSession.issue(issueID)
            results = self.convertIssueResultsToDict(results, resultsType)
        except Exception as e:
            printResults("CV Error: Unable to search for issue ID [%s] : %s" % (issueID, str(e)), 4)

        return results

    def getReadingListsFromName(self, name : str) -> list[dict]:
        results = None
        resultsType = ComicInformationSource.ResultType.ReadingLists

        if not config.Metron.check_arcs: return None

        try:
            results = _metronSession.arcs_list(params={"name" : name})
            results = self.convertReadingListResultsToDict(results, resultsType)
        except Exception as e:
            printResults("CV Error: Unable to search for story arc \"%s\" : %s" % (name, str(e)), 4)

        return results

    def getReadingListFromID(self, listID : str) -> dict[dict]:
        results = None
        resultsType = ComicInformationSource.ResultType.ReadingList

        if not config.Metron.check_arcs: return None

        #try:
        if listID is not None:
            results = _metronSession.story_arc(listID)
            results = self.convertReadingListResultsToDict(results, resultsType)
        #except Exception as e:
        #    printResults("CV Error: Unable to search for issue ID [%s] : %s" % (name, str(e)), 4)

        return results