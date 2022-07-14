#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from abc import abstractmethod
from readinglistmanager.utilities import printResults
import os
from enum import Enum

class DataSourceType(Enum):
    pass

class ListSourceType(DataSourceType):
    Website = "WEB"
    CBL = "CBL"
    CV = "CV"

class Source:
    def __init__(self, name : str, file : str, sourceType : DataSourceType = None, tableDict : dict = None):
        self.file = file
        self.name = name
        self.type = sourceType
        if self.type == ListSourceType.Website:
            #try:
            self.tableReadingListTitles = tableDict['ReadingLists']
            self.tableReadingListDetails = tableDict['ReadingListDetails']
            self.tableIssueDetails = tableDict['IssueDetails']
            #except Exception as e:
            #    printResults("Warning : Unable to find DB table details for %s: %s" % (self.name, e), 5)

    def isValidFile(self):
        if self.file is not None and os.path.exists(self.file):
            return True
        
        printResults("Warning: Source file not found - %s [%s]" % (
            self.file, self.name), 2)
        return False

class ListSource(Source):
    def __init__(self, name : str, file : str, sourceType : ListSourceType, tableDict : dict = None):
        super.init(name, file, sourceType, tableDict)

class ComicInformationSource():

    # Responsible for looking up data from source and returning a list[dict] object of the relevant type (Series / Issue)

    _issueDetailsTemplate = {'issueID' : None, 'seriesID' : None, 'name' : None, 'coverDate' : None, 'issueNum': None, 'issueType' : None, 'description' : None, 'summary' : None, 'dateAdded' : None, 'dataSource' : None}
    _seriesDetailsTemplate = {'seriesID': None, 'name' : None, 'startYear' : None, 'publisher' : None, 'numIssues' : None, 'description' : None, 'summary' : None, 'dateAdded' : None, 'dataSource' : None}
    _listDetailsTemplate = {'listID': None, 'name' : None, 'publisher' : None, 'issues': None, 'numIssues' : None, 'description' : None, 'summary' : None, 'dateAdded' : None, 'dataSource' : None}

    class IssueType(Enum):
        Issue = "Issue"
        Trade = "Trade"

    class ReadingListType(Enum):
        Event = "Event"
        Character = "Character"
        Team = "Team"

    @property
    @abstractmethod
    def type(self):
        # Property that identifies the type of each ComicInformationSource child using ComicSourceType
        pass

    @property
    @abstractmethod
    def instance(self):
        # Property that identifies the single instance of each ComicInformationSource child
        pass

    @property
    @abstractmethod
    def get(self):
        # Property that instantiates and returns the single instance of each ComicInformationSource child
        pass

    class SourceType(DataSourceType):
        # Identifies the source of truth this information was obtained from
        Manual = "Manual"
        Comicvine = "Comicvine"
        Database = "Database"

    class ResultType(Enum):
        # Identifies the different types of results returned by ComicInformationSource
        Series = "Volume"
        SeriesList = "VolumeList"
        Issue = 'Issue'
        IssueList = 'IssueList'
        ReadingList = 'Reading List'
        ReadingLists = 'Reading Lists'

    class SearchStatusType(Enum):
        SearchCount = 'Search Count'
        ResultsCount = 'Results Found Count'
        NoResultsCount = 'No Results Count'

    class ResultFilterType(Enum):
        Preferred = 'Preferred'
        Allowed = 'Allowed'
        Blacklisted = 'Blacklisted'

    def __init__(self):
        # Create a dict of ResultType objects with initial value set to 0
        results = dict((result,0) for result in ComicInformationSource.ResultType)
        
        # Create a 2d dict of counters using ResultType and SearchStatusType
        self.counters = dict((status,results.copy()) for status in ComicInformationSource.SearchStatusType)

    def updateCounter(self, searchStatusType : SearchStatusType, resultType : ResultType):
        self.counters[searchStatusType][resultType] += 1

    @abstractmethod
    def getIssueFromIssueID(self, issueID : str) -> list[dict]:
        pass

    # Now covered by dataManager
    #@abstractmethod
    #def getIssueFromDetails(self, seriesID : str, issueNumber : str) -> list[dict]:
    #    pass

    @abstractmethod
    def getSeriesFromSeriesID(self, seriesID : str) -> list[dict]:
        pass

    @abstractmethod
    def getSeriesFromDetails(self, name : str, startYear : int) -> list[dict]:
        pass

    @abstractmethod
    def getIssuesFromSeriesID(self, seriesID : str) -> dict[dict]:
        pass

    @abstractmethod
    def getReadingListsFromName(self, name : str) -> list[dict]:
        pass

    @abstractmethod
    def getReadingListFromID(self, listID : str) -> dict[dict]:
        pass

    @abstractmethod
    def convertIssueResultsToDict(self, searchResults : list, resultsType : ResultType) -> list[dict]:
        pass

    @abstractmethod
    def convertSeriesResultsToDict(self, searchResults : list, resultsType : ResultType) -> list[dict]:
        pass

    @abstractmethod
    def convertReadingListResultsToDict(self, searchResults : list, resultsType : ResultType) -> list[dict]:
        pass
