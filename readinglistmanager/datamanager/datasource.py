#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from abc import abstractmethod
from readinglistmanager.utilities import printResults, isValidID
import os
import requests
from html import unescape
from enum import Enum
from copy import deepcopy

class DataSourceType(Enum):
    pass

class Library():
    class LibraryType(Enum):
        Mylar = "Mylar"

    def __init__(self, libraryType : LibraryType = None):
        self.libraryType = libraryType

    @property
    @abstractmethod
    def libraryType(self):
        # Property that identifies the type of each Library child using LibraryType
        pass

    @property
    @abstractmethod
    def endpointURL(self):
        # Property that identifies the URL location of each Library child
        pass

    @property
    @abstractmethod
    def apiKey(self):
        # Property that identifies the type of each Library child using LibraryType
        pass

    @property
    @abstractmethod
    def instance(self):
        # Property that identifies the single instance of each Library child
        pass

    @property
    @abstractmethod
    def get(self):
        # Property that instantiates and returns the single instance of each Library child
        pass

    def queryAPI(library, cmd : str, params : dict) -> dict:

        baseUrl = '%s/api?' % (library.endpointURL)

        allParams = {            
            'apikey':library.apiKey,
            'cmd':cmd
        }

        if params is not None and isinstance(params, dict):
            allParams.update(params)

        resp = requests.get(url=baseUrl, params=allParams)
        data = resp.json() # Check the JSON Response Content documentation below

        return data

    @abstractmethod
    def addSeriesToLibrary(self, seriesID : str) -> bool:
        pass
 
    @abstractmethod
    def getSeriesDetails(self, seriesID : str) -> dict:
        pass


class ListSourceType(DataSourceType):
    Website = "WEB"
    CBL = "CBL"
    CV = "CV"
    Metron = "Metron"
    TXT = "TXT"

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
    _seriesDetailsTemplate = {'seriesID': None, 'name' : None, 'startYear' : None, 'publisher' : None, 'numIssues' : None, 'description' : None, 'summary' : None, 'dateAdded' : None, 'issueList' : None, 'dataSource' : None}
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
        Comicvine = "comicvine"
        Metron = "metron"
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
    def getSeriesFromSeriesID(self, dataSourceType : "ComicInformationSource.SourceType", seriesID : str) -> list[dict]:
        pass

    @abstractmethod
    def getSeriesFromDetails(self, name : str, startYear : int) -> list[dict]:
        pass

    @abstractmethod
    def getIssuesFromSeriesID(self, seriesID : str, source : "ComicInformationSource.SourceType") -> dict[dict]:
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

    # Returns the issue print format as an IssueType 
    @classmethod
    def _getIssueType(self, name : str, description : str, summary : str) -> IssueType:
        curDescription = description
        curSummary = summary
        curName = name

        if curDescription is None or not isinstance(curDescription,str):
            curDescription = ''
        if curSummary is None or not isinstance(curSummary,str):
            curSummary = ''
        if curName is None or not isinstance(curName,str):
            curName = ''
        
        curSummary = unescape(curSummary.lower())
        curDescription = unescape(curDescription.lower())
        
        namestarts = [
            'hc', 
            #'volume ', 
            'tpb',
            #'book '
            ]
        for tn in namestarts:
            if curName.startswith(tn):
                return ComicInformationSource.IssueType.Trade

        descphrases = ['collecting', 'collects']
        for tn in descphrases:
            if tn in curDescription:
                return ComicInformationSource.IssueType.Trade
            
        return ComicInformationSource.IssueType.Issue

class WebSource():
    #Used for keeping track of checks against comic information sources for a specific resource (issue, series, list etc)

    def __init__(self, source : ComicInformationSource.SourceType):
        self._name = source.value
        self.type = source
        self.checked = False
        self.id = None

    @property
    def name(self):
        return self._type.value

    @property
    def type(self):
        return self._type

    @type.setter
    def type(self, value):
        if isinstance(value, ComicInformationSource.SourceType):
            self._type = value

    @property
    def id(self):
        return self._id

    @id.setter
    def id(self, value):
        validID = isValidID(value)
        if value is None or validID:
            self._id = value

    @property
    def checked(self):
        return self._checked

    @checked.setter
    def checked(self, value):
        if isinstance(value, bool):
            self._checked = value


class WebSourceList():
    def __init__(self):
        webSourcesManager = WebSourceManager.get()
        if isinstance(webSourcesManager, WebSourceManager):
            self._sourceList = webSourcesManager.getBlankSourceList()

    def getSourcesList(self):
        return list(self._sourceList.values())

    def getSourcesJSON(self):
        sourceIDs = list()

        for source in self.getSourcesList():

            if source.id is not None:
                curSource = dict()
                curSource['Name'] = source.name
                curSource['ID'] = source.id

                sourceIDs.append(curSource)

        return sourceIDs

    def hasSource(self, source: ComicInformationSource.SourceType):
        if isinstance(source, ComicInformationSource.SourceType) and source in self._sourceList:
            return True
        else:
            return False

    def setSourceChecked(self,source: ComicInformationSource.SourceType):
        if source in self._sourceList:
            self._sourceList[source].checked = True

    def isSourceChecked(self, source: ComicInformationSource.SourceType):
        if source in self._sourceList:
            return self._sourceList[source].checked
        else:
            return False

    def getSourceID(self, source : ComicInformationSource.SourceType):
        if source in self._sourceList:
            return self._sourceList[source].id
        else:
            return None

    def setSourceID(self, source : ComicInformationSource.SourceType, sourceID : str):
        if source in self._sourceList:
            self._sourceList[source].id = sourceID
        
        if sourceID is None:
            pass

    def allSourcesChecked(self) -> bool:
        allSourcesChecked = True

        for source in self._sourceList:
            if isinstance(source, WebSource):
                if not source.checked: 
                    allSourcesChecked = False

        return allSourcesChecked

    def allSourcesMatched(self) -> bool:
        if not self.allSourcesChecked(): 
            return False

        allSourcesMatched = True

        for source in self.getSourcesList():
            if isinstance(source, WebSource):
                if source.id is None and source.name != "Database": 
                    allSourcesMatched = False

        return allSourcesMatched

    def hasValidID(self, source : ComicInformationSource.SourceType = None):
        if source is None:
            for webSource in self._sourceList.values():
                if webSource.id is not None:
                    return True
            
            return False

        elif source in self._sourceList and self._sourceList[source].id is not None:
            return True
        else:
            return False
            
    def getSourceID(self, source: ComicInformationSource.SourceType):
        if source in self._sourceList and source in WebSourceManager.WebSourceTypes:
            return self._sourceList[source].id
        else:
            return None

class WebSourceManager():
    # Generates dict of WebSources for easy access and re-use by resources

    instance = None
    _sourceList = dict()

    @classmethod
    def get(self):    
        if WebSourceManager.instance is None: 
            WebSourceManager.instance = WebSourceManager()

        return WebSourceManager.instance

    # Needs to be updated for any new web data source
    WebSourceTypes = [
        ComicInformationSource.SourceType.Comicvine,
        ComicInformationSource.SourceType.Metron    
    ]

    def __init__(self):
        databaseSource = ComicInformationSource.SourceType.Database
        self._sourceList[databaseSource] = WebSource(databaseSource)

        for source in WebSourceManager.WebSourceTypes:
            self._sourceList[source] = WebSource(source)

    def getBlankSourceList(self):
        return deepcopy(self._sourceList)
