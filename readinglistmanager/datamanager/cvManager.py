#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from html import unescape
from readinglistmanager import config,filemanager,utilities
#from readinglistmanager.datamanager import dataManager
from readinglistmanager.errorhandling.problemdata import ProblemData
from readinglistmanager.utilities import printResults
from readinglistmanager.datamanager.datasource import ComicInformationSource
import simyan.schemas.volume, simyan.schemas.issue, simyan.comicvine
from simyan.sqlite_cache import SQLiteCache

cacheRetentionLenth = 60 #days

_cvSession = simyan.comicvine.Comicvine(api_key=config.CV.api_key, cache=SQLiteCache(filemanager.cvCacheFile,cacheRetentionLenth))

class CV(ComicInformationSource):
    instance = None
    type = ComicInformationSource.SourceType.Comicvine

    @classmethod
    def get(self):    
        if CV.instance is None: 
            CV.instance = CV()

        return CV.instance

    def convertIssueResultsToDict(self, issueResults : list[simyan.schemas.issue.Issue], resultsType : ComicInformationSource.ResultType) -> list[dict]:
        results = []
        self.updateCounter(ComicInformationSource.SearchStatusType.SearchCount,resultsType)

        if isinstance(issueResults, simyan.schemas.issue.Issue):
            # Single result found
            result = issueResults
            issueDetails = ComicInformationSource._issueDetailsTemplate.copy()
            issueType = _getIssueType(result.description,result.summary)
            issueDetails.update({'issueID' : result.id_, 'name' : result.name, 'coverDate' : result.cover_date, 'issueNum': result.number, 'type' : issueType, 'description' : result.description, 'summary' : result.summary})
            results.append(issueDetails)
        elif isinstance(issueResults, list):
            for result in issueResults:
                if isinstance(result, simyan.schemas.issue.Issue):
                    issueDetails = ComicInformationSource._issueDetailsTemplate.copy()
                    issueType = _getIssueType(result.description,result.summary)
                    seriesID = None
                    if result.volume is not None: seriesID = result.volume.id_
                    issueDetails.update({'issueID' : result.issue_id, 'seriesID':seriesID,'name' : result.name, 'coverDate' : result.cover_date, 'issueNum': result.number, 'type' : issueType, 'description' : result.description, 'summary' : result.summary})
                    results.append(issueDetails)
        
        if results is None or len(results) == 0:
            self.updateCounter(ComicInformationSource.SearchStatusType.NoResultsCount,resultsType)
        else:
            self.updateCounter(ComicInformationSource.SearchStatusType.ResultsCount,resultsType)

        return results


    def convertSeriesResultsToDict(self, volumeResults : list[simyan.schemas.volume.Volume], resultsType : ComicInformationSource.ResultType) -> list[dict]:
        results = []
        self.updateCounter(ComicInformationSource.SearchStatusType.SearchCount,resultsType)

        if isinstance(volumeResults, simyan.schemas.volume.Volume):
            # Single result found
            result = volumeResults
            seriesDetails = ComicInformationSource._seriesDetailsTemplate.copy()
            if result.publisher is not None: publisher = result.publisher.name
            seriesDetails.update({'seriesID': result.id_, 'name' : result.name, 'startYear' : result.start_year, 'publisher' : publisher, 'numIssues' : result.issue_count, 'description' : result.description, 'summary' : result.summary})
            results.append(seriesDetails)
        elif isinstance(volumeResults, list):
            for result in volumeResults:
                if isinstance(result, simyan.schemas.volume.Volume):
                    seriesDetails = ComicInformationSource._seriesDetailsTemplate.copy()
                    if result.publisher is not None: publisher = result.publisher.name
                    seriesDetails.update({'seriesID': result.id_, 'name' : result.name, 'startYear' : result.start_year, 'publisher' : publisher, 'numIssues' : result.issue_count, 'description' : result.description, 'summary' : result.summary})
                    results.append(seriesDetails)
        
        if results is None or len(results) == 0:
            self.updateCounter(ComicInformationSource.SearchStatusType.NoResultsCount,resultsType)
        else:
            self.updateCounter(ComicInformationSource.SearchStatusType.ResultsCount,resultsType)

        return results

    def getSeriesFromDetails(self, name : str, startYear : int) -> list[dict]:
        
        matches = []

        if config.CV.check_volumes and None not in (name, startYear):
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
            #if len(matches) == 0:
            #    # Try resource search instead of filter
            #    results = self.getSeriesFromNameSearch(name)

        # Return *all* results for processing/filtering by dataManager
        return results

    def getSeriesFromNameFilter(self,name : str) -> list[dict]:
        # Use FILTER to identify CV matches from series name
        results = None
        resultsType = ComicInformationSource.ResultType.SeriesList

        try:
            results = _cvSession.volume_list(params={"filter": "name:%s" % (name)})
            results = self.convertSeriesResultsToDict(results, resultsType)
        except Exception as e:
            printResults("CV Error: Unable to search for series \"%s\" : %s" % (name,str(e)), 4)

        return results


    def getSeriesFromNameSearch(self, name : str) -> list[dict]:
        # Use SEARCH to identify CV matches from series name
        results = None
        resultsType = ComicInformationSource.ResultType.SeriesList

        try:
            results = _cvSession.search(resource=simyan.comicvine.ComicvineResource.VOLUME,query=name)
            results = self.convertSeriesResultsToDict(results, resultsType)
        except Exception as e:
            printResults("CV Error: Unable to search for series \"%s\" : %s" % (name,str(e)), 4)

        return results


    def getSeriesDetails(self, seriesID : str) -> list[dict]:
        results = None
        resultsType = ComicInformationSource.ResultType.Series

        try:
            results = _cvSession.volume(seriesID)
            results = self.convertSeriesResultsToDict(results, resultsType)
        except Exception as e:
            printResults("CV Error: Unable to search for series [%s] : %s" % (seriesID, str(e)), 4)

        return results


    def getIssuesFromSeriesID(self, seriesID : str) -> list[dict]:
        resultsDict = dict()
        resultsType = ComicInformationSource.ResultType.IssueList
        
        #try:
        if seriesID is not None:
            results = _cvSession.issue_list(params={"filter": "volume:%s" % (seriesID)})
            resultsList = self.convertIssueResultsToDict(results, resultsType)
            for result in resultsList:
                resultsDict[result['issueNum']] = result

        #except Exception as e:
        #    printResults("CV Error: Unable to search for series issues using series ID [%s] : %s" % (seriesID,str(e)), 4)
        

        return resultsDict


    def getIssueFromID(self, issueID : str) -> list[dict]:
        results = None
        resultsType = ComicInformationSource.ResultType.Issue
        
        try:
            results = _cvSession.issue(issueID)
            results = self.convertIssueResultsToDict(results, resultsType)
        except Exception as e:
            printResults("CV Error: Unable to search for issue ID [%s] : %s" % (issueID, str(e)), 4)

        return results


# Returns the issue print format as an IssueType 
def _getIssueType(description : str, summary : str) -> ComicInformationSource.IssueType:
    desc = description
    story = summary

    if desc is None or not isinstance(desc,str):
        desc = ''
    if story is None or not isinstance(story,str):
        story = ''
    
    story = unescape(story.lower())
    desc = unescape(desc.lower())
    
    namestarts = ['hc', 'volume ', 'book ']
    for tn in namestarts:
        if story.startswith(tn):
            return ComicInformationSource.IssueType.Trade

    descphrases = ['collecting issues', 'collects issues']
    for tn in descphrases:
        if tn in desc:
            return ComicInformationSource.IssueType.Trade
        
    return ComicInformationSource.IssueType.Issue
            