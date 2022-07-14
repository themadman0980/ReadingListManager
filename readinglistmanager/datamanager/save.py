#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os, json
from readinglistmanager.model.readinglist import ReadingList
from readinglistmanager.model.issue import Issue
from readinglistmanager.datamanager.datasource import Source, ListSourceType
from readinglistmanager.utilities import printResults
from readinglistmanager import filemanager, utilities

def getOutputFile(readingList : ReadingList) -> str:
    if isinstance(readingList, ReadingList):
        fileName = readingList.getFileName()
        fileName += ".json"
        #fileName = "%s (%s) [%s].json" % (listName, listPublisher, sourceName)
        fileDir = filemanager.jsonOutputDirectory

        file = os.path.join(fileDir, fileName)
        
        return file
    
    return None

def saveList(readingList : ReadingList):
    if isinstance(readingList, ReadingList):
        listData = dict()
        listData['ListName'] = readingList.name        
        listData['Publisher'] = readingList.publisher
        listData['IssueCount'] = readingList.getNumIssues()
        #listData['Type'] = None
        if isinstance(readingList.source, Source):
            listData['Source'] = readingList.source.name

        if utilities.isValidID(readingList.id):
            listData['Database'] = list()
            database = {'Name' : 'Comicvine', 'ID':readingList.id}
            listData['Database'].append(database)

        listData['Issues'] = dict()
        for number,issue in readingList.issueList.items():
            if isinstance(issue, Issue):
                listData['Issues'][str(number)] = issue.getJSONDict()

        file = getOutputFile(readingList)
        
        with open(file, 'w') as outputFile:
            json.dump(listData, outputFile, indent=4)


def saveLists(readingLists : list[ReadingList]):
    if isinstance(readingLists, list):
        for readingList in readingLists:
            if isinstance(readingList, ReadingList):
                saveList(readingList)        

def saveListData(file : str, listData : list):
    if not isinstance(listData, list):
        if isinstance(listData, set) or isinstance(listData, tuple):
            listData = list(listData)
        elif isinstance(listData, dict):
            listData = list(listData.values())
    
    if isinstance(listData, list) and isinstance(file, str):
        with open(file, mode='w') as outputFile:
            for line in listData:
                outputFile.write(f"{line}\n")