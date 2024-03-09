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
    
    def doesIDMatch(self, id : str, source : "ComicInformationSource.SourceType" = None):
        if source is not None and isinstance(source, ComicInformationSource.SourceType):
            #Check ID from specified source
            if self.getSourceID(source) == id:
                return True
        else:
            #check ID's from ALL sources
            for source in self.sourceList:
                if source.id == id:
                    return True
        
        # No matches found
        return False

    def getSourceID(self, source: "ComicInformationSource.SourceType"):
        return self.sourceList.getSourceID(source)

    def allSourcesChecked(self) -> bool:
        return self.sourceList.allSourcesChecked()

    def allSourcesMatched(self) -> bool:
        return self.sourceList.allSourcesMatched()
    
