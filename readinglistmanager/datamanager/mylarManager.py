#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from readinglistmanager.datamanager.datasource import Library 
from readinglistmanager.utilities import printResults, isValidID
from readinglistmanager import config

class Mylar(Library):
    instance = None
    libraryType = Library.LibraryType.Mylar
    apiKey = config.Mylar().api_key
    endpointURL = config.Mylar().endpoint

    @classmethod
    def get(self):    
        if Mylar.instance is None: 
            Mylar.instance = Mylar()

        return Mylar.instance

    def addSeriesToLibrary(self, seriesID : str) -> bool:
        params = {'id': seriesID}
        printResults("Adding series %s to Mylar" % (seriesID),2)
        apiResults = Library.queryAPI(self, 'addComic', params)

        if isinstance(apiResults, dict) and 'success' in apiResults:
            return apiResults['success']
        else:
            return False

    def getSeriesDetails(self, seriesID : str) -> dict:
        params = {'id': seriesID}
        apiResults = Library.queryAPI(self, 'getComic', params)

        return apiResults

    def getSeriesList(self) -> dict:
        apiResults = Library.queryAPI(self, 'getIndex', None)

        return apiResults

    def getSeriesIDList(self) -> set:
        apiResults = self.getSeriesList()

        seriesList = set()

        if 'data' in apiResults:
            for series in apiResults['data']:
                if 'id' in series and isValidID(series['id']):
                    try:
                        seriesList.add(int(series['id']))
                    except:
                        printResults("Unable to process series id: %s" % (series['id']),2)

        return seriesList


    
mylar = Mylar.get()

def addSeriesToMylar(seriesIDList : list):

    existingSeriesList = mylar.getSeriesIDList()

    if config.Mylar.add_missing_series:
        for seriesID in seriesIDList:
            if (seriesID is not None) and (seriesID not in existingSeriesList):
                mylar.addSeriesToLibrary(seriesID)
