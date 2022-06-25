#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os,json
from re import L
from readinglistmanager import utilities
from readinglistmanager.utilities import printResults
from readinglistmanager.model.issue import Issue
from readinglistmanager.datamanager.datasource import ComicInformationSource

class Series:

    @classmethod
    def getSeriesKey(self, seriesName, seriesStartYear):
        if None not in (seriesName, seriesStartYear):
            return "%s-%s" % (utilities.getDynamicName(seriesName), utilities.getCleanYear(seriesStartYear))
        else:
            return None

    def updateDetailsFromDict(self, match : dict) -> None:
        # Populate attributes from _seriesDetailsTemplate dict structure
        try:
            self.id = match['seriesID']
            #self.name = match['name']
            #self.startYear = match['startYear']
            self.publisher = match['publisher']
            self.dateAdded = match['dateAdded']
            self.numIssues = match['numIssues']
            self.description = match['description']
            self.summary = match['summary']
            self.detailsFound = True
        except:
            printResults("Unable to update series \'%s (%s)\' from match data : %s" % (self.name, self.startYear, match),4)

    @classmethod
    def getCleanName(self, name):
        if name is not None and isinstance(name, str):
            return utilities.getDynamicName(name)

    @classmethod
    def getCleanStartYear(self, startYear):
        if startYear is not None:
            return utilities.getCleanYear(startYear)

    def __init__(self, seriesName, seriesStartYear):
        self._name = None
        self.dynamicName = None
        self.name = seriesName
        self.startYear = Series.getCleanStartYear(seriesStartYear)
        self.publisher = None
        self.id = None
        self.numIssues = None
        self.dateAdded = None
        self.issueList = dict()
        self.problems = dict()
        self._issueNums = set()
        self.dataSourceType = ComicInformationSource.SourceType.Manual
        self.key = Series.getSeriesKey(self.name, self.startYear)
        self.checked = dict()
        self.detailsFound = False

    def __eq__(self, other):
        if (isinstance(other, Series)):
            if self.id and other.id:
                return self.id == other.id
            else:
                return self.dynamicName == other.dynamicName and self.startYear == other.startYear
        return False

    def __hash__(self):
        return hash((self.dynamicName, self.startYear))
    
    def getKey(self):
        if None not in (self.name,self.startYear):
            return Series.getKey(self.name,self.startYear)

    def addIssue(self, issueObject : Issue) -> None:
        if isinstance(issueObject, Issue):
            issueObject.series = self
            self.issueList[issueObject.issueNumber] = issueObject

    def getIssue(self, issueNum : str) -> Issue:
        issue = None

        # Get existing issue from series issue list
        if issueNum in self.issueList:
            issue = self.issueList[issueNum]
        else: 
            issue = Issue(self,issueNum,ComicInformationSource.SourceType.Manual)
            self.issueList[issueNum] = issue
            self._issueNums.add(issueNum)        
        return issue

    # Check series name has correct encoding
#    def checkHasValidName(self):
#        #if len(self.name) == len(self.name.encode())
#        if not utilities.hasValidEncoding(self.name):
#            self._name = utilities.fixEncoding(self.name)
#            if not utilities.hasValidEncoding(self.name):
#                ProblemData.addSeries(self,ProblemData.ProblemType.InvalidSeriesNameEncoding)

    def addProblem(self, problemType, extraData = None):
        self.problems[problemType] = extraData

    def updateIssuesFromDict(self, issueDetailsDict : dict[dict]) -> None:
        if isinstance(issueDetailsDict,dict):
            for issue in self.issueList.values():
                if isinstance(issue, Issue) and issue.issueNumber in issueDetailsDict:
                    issue.updateDetailsFromDict(issueDetailsDict[issue.issueNumber])

    def getIssueNumsList(self):
        return sorted(self._issueNums)

    def hasValidID(self):
        return utilities.isValidID(self.id)

    def hasCompleteSeriesDetails(self):
        if self.hasValidID() and None not in (self.name, self.startYear, self.publisher, self.numIssues):
            return True
        return False

    def hasCompleteIssueDetails(self):
        #Check if any issues in list haven't been ID'ed
        for key,issue in self.issueList.items():
            if isinstance(issue, Issue):
                if not issue.detailsFound:
                    return False

        return True

    def getNumCompleteIssues(self):
        count = 0
        
        for key,issue in self.issueList.items():
            if isinstance(issue, Issue):
                if issue.detailsFound:
                    count += 1
        
        return count


    def hasCompleteIssueList(self):
        if self.issueList is not None and self.numIssues is not None:
            return len(self.issueList) == self.numIssues

    def name():
        doc = "The series' name"

        def fget(self):
            return self._name

        def fset(self, value):
            self._name = utilities.fixEncoding(value)
            self.dynamicName = Series.getCleanName(value)

        def fdel(self):
            del self._name
        return locals()
    name = property(**name())

    def getDict(self):
        data = {
            'seriesID': self.id, 
            'name': self.name, 
            'dynamicName': self.dynamicName, 
            'startYear': self.startYear, 
            'numIssues': self.numIssues, 
            'publisher': self.publisher, 
            'dateAdded': self.dateAdded
            }
        return data
