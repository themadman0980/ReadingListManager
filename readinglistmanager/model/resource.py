#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from readinglistmanager.datamanager.datasource import WebSourceList

# Class designed to enable id checking for resources such as issues, series, reading lists etc

class Resource():

    def __init__(self):
        self.sourceList = WebSourceList()

    def setSourceID(self, source : "ComicInformationSource.SourceType", sourceID : str):
        self.sourceList.setSourceID(source,sourceID)

    def hasValidID(self, source : "ComicInformationSource.SourceType" = None):
        return self.sourceList.hasValidID(source)

    def getSourceID(self, source: "ComicInformationSource.SourceType"):
        return self.sourceList.getSourceID(source)

    def allSourcesChecked(self) -> bool:
        return self.sourceList.allSourcesChecked()

    def allSourcesMatched(self) -> bool:
        return self.sourceList.allSourcesMatched()
    
