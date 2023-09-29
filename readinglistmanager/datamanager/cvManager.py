#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from html import unescape
from readinglistmanager import config,filemanager,utilities
#from readinglistmanager.datamanager import dataManager
from readinglistmanager.utilities import printResults
from readinglistmanager.model.date import PublicationDate
from readinglistmanager.datamanager.datasource import ComicInformationSource
import simyan.schemas.volume, simyan.schemas.issue, simyan.schemas.story_arc, simyan.comicvine
from simyan.sqlite_cache import SQLiteCache

CACHE_RETENTION_TIME = 60 #days
MAX_RESULTS = 100

if config.CV.cache_searches:
    _cvSession = simyan.comicvine.Comicvine(api_key=config.CV.api_key, cache=SQLiteCache(filemanager.cvCacheFile,CACHE_RETENTION_TIME))
else:
    _cvSession = simyan.comicvine.Comicvine(api_key=config.CV.api_key)

class CV(ComicInformationSource):
    instance = None
    type = ComicInformationSource.SourceType.Comicvine

    @classmethod
    def get(self):    
        if CV.instance is None: 
            CV.instance = CV()

        return CV.instance

    def convertIssueResultsToDict(self, issueResults : list[simyan.schemas.issue.IssueEntry], resultsType : ComicInformationSource.ResultType) -> list[dict]:
        results = []
        self.updateCounter(ComicInformationSource.SearchStatusType.SearchCount,resultsType)

        if isinstance(issueResults, simyan.schemas.issue.IssueEntry):
            # Single result found
            result = issueResults
            issueDetails = ComicInformationSource._issueDetailsTemplate.copy()
            issueType = ComicInformationSource._getIssueType(result.name, result.description,result.summary)
            issueDetails.update({
                'issueID' : result.issue_id, 
                'name' : result.name, 
                'coverDate' : PublicationDate.fromDateTimeObj(result.cover_date), 
                'issueNum': str(result.number), 
                'issueType' : issueType, 
                'description' : result.description, 
                'summary' : result.summary,
                'dataSource' : self.type
                })
            results.append(issueDetails)
        elif isinstance(issueResults, list):
            for result in issueResults:
                if isinstance(result, simyan.schemas.issue.IssueEntry):
                    issueDetails = ComicInformationSource._issueDetailsTemplate.copy()
                    issueType = ComicInformationSource._getIssueType(result.name,result.description,result.summary)
                    seriesID = None
                    if result.volume is not None: seriesID = result.volume.id_
                    issueDetails.update({
                        'issueID' : result.issue_id, 
                        'seriesID':seriesID,
                        'name' : result.name, 
                        'coverDate' : PublicationDate.fromDateTimeObj(result.cover_date), 
                        'issueNum': str(result.number), 
                        'issueType' : issueType, 
                        'description' : result.description, 
                        'summary' : result.summary,
                        'dataSource' : self.type
                        })
                    results.append(issueDetails)
        
        if results is None or len(results) == 0:
            self.updateCounter(ComicInformationSource.SearchStatusType.NoResultsCount,resultsType)
        else:
            self.updateCounter(ComicInformationSource.SearchStatusType.ResultsCount,resultsType)

        if not config.CV.check_issues: results = None

        return results


    def convertSeriesResultsToDict(self, volumeResults : list[simyan.schemas.volume.VolumeEntry], resultsType : ComicInformationSource.ResultType) -> list[dict]:
        results = []
        self.updateCounter(ComicInformationSource.SearchStatusType.SearchCount,resultsType)

        if isinstance(volumeResults, simyan.schemas.volume.VolumeEntry):
            # Single result found
            result = volumeResults
            seriesDetails = ComicInformationSource._seriesDetailsTemplate.copy()
            publisher = result.publisher.name if result.publisher is not None else None
            issueList = self.convertIssueResultsToDict(volumeResults, ComicInformationSource.ResultType.IssueList) if hasattr(volumeResults, 'issues') else None
            seriesDetails.update({
                'seriesID': result.volume_id, 
                'name' : result.name, 
                'startYear' : result.start_year, 
                'publisher' : publisher, 
                'numIssues' : result.issue_count, 
                'description' : result.description, 
                'summary' : result.summary,
                'issueList' : issueList,
                'dataSource' : self.type
                })
            results.append(seriesDetails)
        elif isinstance(volumeResults, list):
            for result in volumeResults:
                if isinstance(result, simyan.schemas.volume.VolumeEntry):
                    seriesDetails = ComicInformationSource._seriesDetailsTemplate.copy()
                    publisher = result.publisher.name if result.publisher is not None else None
                    issueList = self.convertIssueResultsToDict(result.issues, ComicInformationSource.ResultType.IssueList) if hasattr(result, 'issues') else None
                    seriesDetails.update({
                        'seriesID': result.volume_id, 
                        'name' : result.name, 
                        'startYear' : result.start_year, 
                        'publisher' : publisher, 
                        'numIssues' : result.issue_count, 
                        'description' : result.description, 
                        'summary' : result.summary,
                        'issueList' : issueList,
                        'dataSource' : self.type
                        })
                    results.append(seriesDetails)
        
        if results is None or len(results) == 0:
            self.updateCounter(ComicInformationSource.SearchStatusType.NoResultsCount,resultsType)
        else:
            self.updateCounter(ComicInformationSource.SearchStatusType.ResultsCount,resultsType)

        return results


    def convertReadingListResultsToDict(self, searchResults : list[simyan.schemas.story_arc.StoryArc], resultsType : ComicInformationSource.ResultType) -> list[dict]:
        dictResults = []
        self.updateCounter(ComicInformationSource.SearchStatusType.SearchCount,resultsType)

        if isinstance(searchResults, simyan.schemas.story_arc.StoryArc):
            # Single result found
            result = searchResults
            listDetails = ComicInformationSource._listDetailsTemplate.copy()
            issueList = None
            if result.issues is not None and isinstance(result.issues, list):
                issueList = result.issues
                # issueList = self.convertIssueResultsToDict(result.issues, ComicInformationSource.ResultType.Issue)
            publisher = result.publisher.name if result.publisher is not None else None
            listDetails.update({
                'listID': result.id_, 
                'name' : result.name, 
                'publisher' : publisher, 
                'issues': issueList, 
                'numIssues' : result.issue_count, 
                'description' : result.description, 
                'summary' : result.summary,
                'dataSource' : self.type
                })
            dictResults.append(listDetails)
        elif isinstance(searchResults, list):
            for result in searchResults:
                if isinstance(result, simyan.schemas.story_arc.StoryArc):
                    listDetails = ComicInformationSource._listDetailsTemplate.copy()
                    issueList = None
                    if result.issues is not None and isinstance(result.issues, list):
                        issueList = result.issues
                        # issueList = self.convertIssueResultsToDict(result.issues,ComicInformationSource.ResultType.Issue)
                    publisher = result.publisher.name if result.publisher is not None else None
                    listDetails.update({
                        'listID': result.id_, 
                        'name' : result.name, 
                        'publisher' : publisher, 
                        'issues': issueList, 
                        'numIssues' : result.issue_count, 
                        'description' : result.description, 
                        'summary' : result.summary,
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

        if config.CV.check_series and None not in (name, startYear):
            #printResults("Info: Searching CV for series : %s (%s)" % (name, startYear), 4) 
            dynamicName = utilities.getDynamicName(name)

            # Try a search filter (exact text match only)     
            results = self.getSeriesFromNameFilter(name)

            # Find matches if results exist
            if results is not None and len(results) > 0:
                for match in results:
                    if isinstance(match, dict):
                        resultDynamicName = utilities.getDynamicName(match['name'])
                        resultStartYear = utilities.getCleanYear(match['startYear'])
                        if resultDynamicName == dynamicName and resultStartYear == startYear:
                            matches.append(match)

            # No matches from CV FILTER lookup
            if len(matches) == 0:
                # Try resource search instead of filter
                results = self.getSeriesFromNameSearch(name)

        # Return *all* results for processing/filtering by dataManager
        return results

    def getSeriesFromNameFilter(self,name : str) -> list[dict]:
        # Use FILTER to identify CV matches from series name
        results = None
        resultsType = ComicInformationSource.ResultType.SeriesList

        if not config.CV.check_series: return None

        #try:
        results = _cvSession.volume_list(params={"filter": "name:%s" % (name)},max_results=MAX_RESULTS)
        results = self.convertSeriesResultsToDict(results, resultsType)
        #except Exception as e:
        #    printResults("CV Error: Unable to search for series \"%s\" : %s" % (name,str(e)), 4)

        return results


    def getSeriesFromNameSearch(self, name : str) -> list[dict]:
        # Use SEARCH to identify CV matches from series name
        results = None
        resultsType = ComicInformationSource.ResultType.SeriesList

        if not config.CV.check_series: return None

        #try:
        results = _cvSession.search(resource=simyan.comicvine.ComicvineResource.VOLUME,query=name,max_results=MAX_RESULTS)
        results = self.convertSeriesResultsToDict(results, resultsType)
        #except Exception as e:
        #    printResults("CV Error: Unable to search for series \"%s\" : %s" % (name,str(e)), 4)

        return results


    def getSeriesFromSeriesID(self, seriesID : str) -> list[dict]:
        results = None
        resultsType = ComicInformationSource.ResultType.Series

        if not config.CV.check_series: return None

        #try:
        results = _cvSession.volume(seriesID)
        results = self.convertSeriesResultsToDict(results, resultsType)
        #except Exception as e:
        #    printResults("CV Error: Unable to search for series [%s] : %s" % (seriesID, str(e)), 4)

        return results


    def getIssuesFromSeriesID(self, seriesID : str) -> list[dict]:
        resultsDict = dict()
        resultsType = ComicInformationSource.ResultType.IssueList

        ### Issue results required for series validation ###
        # if not config.CV.check_issues: return None

        try:
            if seriesID is not None:
                results = _cvSession.issue_list(params={"filter": "volume:%s" % (seriesID)})
                resultsList = self.convertIssueResultsToDict(results, resultsType)
                if resultsList is not None:
                    for result in resultsList:
                        resultsDict[result['issueNum']] = result

        except Exception as e:
            printResults("CV Error: Unable to search for series issues using series ID [%s] : %s" % (seriesID,str(e)), 4)
        

        return resultsDict


    def getIssueFromID(self, issueID : str) -> list[dict]:
        results = None
        resultsType = ComicInformationSource.ResultType.Issue

        if not config.CV.check_issues: return None

        try:
            results = _cvSession.issue(issueID)
            results = self.convertIssueResultsToDict(results, resultsType)
        except Exception as e:
            printResults("CV Error: Unable to search for issue ID [%s] : %s" % (issueID, str(e)), 4)

        return results

    def getReadingListsFromName(self, name : str) -> list[dict]:
        results = None
        resultsType = ComicInformationSource.ResultType.ReadingLists

        if not config.CV.check_arcs: return None

        try:
            results = _cvSession.story_arc_list(params={"filter": "name:%s" % (name)},max_results=MAX_RESULTS)
            results = self.convertReadingListResultsToDict(results, resultsType)
        except Exception as e:
            printResults("CV Error: Unable to search for story arc \"%s\" : %s" % (name, str(e)), 4)

        return results

    def getReadingListFromID(self, listID : str) -> dict[dict]:
        results = None
        resultsType = ComicInformationSource.ResultType.ReadingList

        if not config.CV.check_arcs: return None

        #try:
        if listID is not None:
            results = _cvSession.story_arc(listID)
            results = self.convertReadingListResultsToDict(results, resultsType)
        #except Exception as e:
        #    printResults("CV Error: Unable to search for issue ID [%s] : %s" % (name, str(e)), 4)

        return results

            