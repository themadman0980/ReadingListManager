#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from readinglistmanager import utilities
from readinglistmanager.utilities import printResults
from readinglistmanager.model.issue import Issue
from readinglistmanager.model.resource import Resource
from readinglistmanager.model.issueRange import IssueRange, IssueRangeCollection
from readinglistmanager.datamanager.datasource import ComicInformationSource
from readinglistmanager.model.relationshipList import RelationshipList
from readinglistmanager.model.event import Event

readingListCounter = readingListVizCounter = 1
readingListPUMLTracker = readingListVizTracker = dict()
graphVizColourList = ["red",'blue','black','cyan', 'green','purple','orange']
curColourIndex = 0

class Series(Resource):

    @classmethod
    def getSeriesKey(self, seriesName, seriesStartYear):
        if None not in (seriesName, seriesStartYear):
            return "%s-%s" % (utilities.getDynamicName(seriesName), utilities.getCleanYear(seriesStartYear))
        else:
            return None

    def updateDetailsFromDict(self, match : dict) -> None:
        # Populate attributes from _seriesDetailsTemplate dict structure
        try:
            #self.name = match['name']
            #self.startYear = match['startYear']
            self.publisher = match['publisher']
            self.dateAdded = match['dateAdded']
            self.numIssues = match['numIssues']
            self.updateIssuesFromDict(match['issueList'])
            self.description = match['description']
            self.summary = match['summary']
            self.detailsFound = True
            self.mainDataSourceType = match['dataSource']
            self.setSourceID(match['dataSource'],str(match['seriesID']))
        except Exception as e:
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
        super().__init__()
        self._name = None
        self.dynamicName = None
        self.startYear = Series.getCleanStartYear(seriesStartYear)
        self.name = seriesName
        self.publisher = None
        self.numIssues = None
        self.dateAdded = None
        self.issueList = dict()
        self.problems = dict()
        self._issueNums = set()
        self.mainDataSourceType = ComicInformationSource.SourceType.Manual
        self.detailsFound = False
        self.altSeriesKeys = list()

    def __eq__(self, other):
        if isinstance(other, Series):
            if self.hasValidID() and other.hasValidID():
                for dataSource in self.sourceList.getSourcesList():
                    if dataSource.id is not None and other.sourceList.getSourceID(dataSource.type) is not None:
                        return dataSource.id == other.sourceList.getSourceID(dataSource.type)

            #If not matches found among database ID's, match based on name/year combo
            return self.dynamicName == other.dynamicName and self.startYear == other.startYear
        
        return False

    def __hash__(self):
        return hash((self.dynamicName, self.startYear))
    
    def getKey(self):
        if None not in (self.name,self.startYear):
            return Series.getSeriesKey(self.name,self.startYear)

    def addIssue(self, issueObject : Issue) -> None:
        if isinstance(issueObject, Issue):
            issueObject.series = self
            self.issueList[str(issueObject.issueNumber)] = issueObject

    def getIssue(self, issueNum : str) -> Issue:
        issue = None
        issueNum = str(issueNum)

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
            for issueNum, issueDict in issueDetailsDict.items():
                if issueNum in self.issueList:
                    self.issueList[issueNum].updateDetailsFromDict(issueDict)
                else:
                    #Create new issue from dict
                    self.issueList[issueNum] = Issue.fromDict(issueDict)
                    self.issueList[issueNum].series = self
                #if isinstance(issue, Issue) and issue.issueNumber in issueDetailsDict:
                #    issue.updateDetailsFromDict(issueDetailsDict[issue.issueNumber])

    def getIssueNumsList(self):
        for issueNum in self.issueList.keys():
            self._issueNums.add(issueNum)
        return sorted(self._issueNums)

    def hasCompleteSeriesDetails(self):
        if self.hasValidID() and None not in (self.name, self.startYear, self.numIssues):
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
            self.key = Series.getSeriesKey(self._name, self.startYear)

        def fdel(self):
            del self._name
        return locals()
    name = property(**name())

    def title():
        doc = "The series title (including start year)"

        def fget(self):
            return "%s (%s)" % (self.name,self.startYear)

        return locals()

    title = property(**title())

    @classmethod
    def fromDict(self, match : dict):
        newSeries = Series(match['name'],match['startYear'])
        newSeries.updateDetailsFromDict(match)
        return newSeries

    def getDict(self):
        data = {
            'Database': self.sourceList.getSourcesJSON(),
            'name': self.name, 
            'dynamicName': self.dynamicName, 
            'startYear': self.startYear, 
            'numIssues': self.numIssues, 
            'publisher': self.publisher, 
            'dateAdded': self.dateAdded
            }
        return data

class CoreSeries(Series):
# Used for creating and managing series event summary data

    def __init__(self, series):
        self.series = series
        self.readingListReferences = dict()
        self.nonEventIssueNums = None
        self.eventsByFirstIssue = dict()

    def __getattr__(self, attr):
        return getattr(self.series, attr)
    
    def addReadingListReference(self, readingList : str, issueNum : str):
        if issueNum == ".":
            pass

        if readingList not in self.readingListReferences: 
            self.readingListReferences[readingList] = set([issueNum])
        else:
            self.readingListReferences[readingList].add(issueNum)

    def organiseIssueNums(self, seriesIssueNums):
        
        self._organiseNonEventIssueNums(seriesIssueNums)

        self._organiseEventIssueNums()

        self._populateIssuesBetweenEvents()

        self._setEventRelationships()


    def _organiseNonEventIssueNums(self, seriesIssueNums : list):

        # 1. Get all series issue numbers
        #allIssueNums = set(self.series.getIssueNumsList())
        allIssueNums = set(seriesIssueNums)
        eventIssueNums = set()

        # 2. Drop all issue numbers that have already been accounted for by events
        for eventIssues in self.readingListReferences.values():
            if eventIssues is not None:
                for issueNum in eventIssues:
                    eventIssueNums.add(issueNum)

        nonEventIssueNums = allIssueNums - eventIssueNums

        # 3. Group remaining issue numbers
        if "." in nonEventIssueNums:
            pass

        self.nonEventIssueNums = IssueRangeCollection.fromListOfNumbers(nonEventIssueNums)


    def _organiseEventIssueNums(self):

        for readingList, issueNumList in self.readingListReferences.items():
            if "." in issueNumList:
                pass

            issueRangeCollection = IssueRangeCollection.fromListOfNumbers(issueNumList)
            self.readingListReferences[readingList] = Event(issueRangeCollection, Event.EventType.ReadingList, readingList)


    def _populateIssuesBetweenEvents(self):

        # 1. Organise events by first issue number
        for readingList, event in self.readingListReferences.items():
            if event is not None:
                firstIssueNum = event.issueRange.firstIssueNum
                
                if firstIssueNum in self.eventsByFirstIssue:
                    #There is a problem! Shouldn't have the same first issue num for multiple events!
                    pass

                self.eventsByFirstIssue[firstIssueNum] = event

        # 2. Insert issue groups between events
        if self.nonEventIssueNums is not None:
            nonEventIssueRangeDict = self.nonEventIssueNums.issueRangeDict
            for firstIssueNum, issueRange in nonEventIssueRangeDict.items():
                self.eventsByFirstIssue[firstIssueNum] = Event(IssueRangeCollection([issueRange]), Event.EventType.SeriesIssueRange, self.series)

#            for issueRange in self.nonEventIssueNums.issueRangeList:
#                firstIssueNum = issueRange.firstIssueNum
#
#                if firstIssueNum in self.eventsByFirstIssue:
#                    #There is a problem! Shouldn't have the same first issue num for multiple events!
#                    pass
#
#                self.eventsByFirstIssue[firstIssueNum] = {'issueNums': issueRange}

        sortedIssues = sorted(self.eventsByFirstIssue.items(),key=lambda x:utilities.convertToNumber(x[0]) if x[0] is not None and utilities.isNumber(x[0]) else float('inf'))
        self.eventsByFirstIssue = dict(sortedIssues)

    def _setEventRelationships(self):
        eventList = list(self.eventsByFirstIssue.values())
        for i in range(len(eventList) - 1): # Exclude last value (necessary for i+1 to work!)
            RelationshipList.addPair(eventList[i], eventList[i+1])

    def getReadingListReferences(self):
        return self.readingListReferences

    def getEventsSummary(self) -> str:

        textLines = [self.series.title]

        for event in self.eventsByFirstIssue.values():
            textLines.append(event.getString())

        textLines.append("\n")

        return textLines

    def getEventRelationshipPUMLString(self):
        textLines = ['\'%s' % (self.series.title)]

        eventDetailsList = dict()
        seriesPackageList = ['package %s {' % (self.series.title.replace(" ", "-"))]
        seriesRelationsList = list()


        global readingListCounter, readingListPUMLTracker

        #for event in self.eventsByFirstIssue.values():
        eventsList = list(self.eventsByFirstIssue.values())
        for i in range(len(eventsList)):
            # Required to sync reading list class names between series
            if eventsList[i].type == Event.EventType.ReadingList:
                classTitle = eventsList[i].getTitle()

                if classTitle in readingListPUMLTracker:
                    className = readingListPUMLTracker[classTitle]['className']
                else:
                    className = "reading_list_%s" % readingListCounter

                    readingListPUMLTracker[classTitle] = {
                        'classTitle': classTitle,
                        'className': className,
                        'event' : eventsList[i]
                    }

                    readingListCounter += 1
            else:
                className = "%s%s" % (self.series.key.replace('-',''), i)
                classTitle = eventsList[i].getTitle().replace("#", "")

            eventDetailsList[eventsList[i]] = {
                'classTitle': classTitle,
                'className': className,
                'event' : eventsList[i]
            }
        
        #Add in hidden relationship with next event in current series
        prevEvent = None
        for event, details in eventDetailsList.items():
            if event.type == Event.EventType.SeriesIssueRange:
                if prevEvent is not None:
                    relationString = "%s -down[hidden]-> %s" % (prevEvent['className'], details['className'])
                    seriesRelationsList.append(relationString)
                prevEvent = details

        for event, details in eventDetailsList.items():
            seriesPackageList.append('  class \"%s\" as %s' % (details['classTitle'], details['className']))
            for followingEvent in event.getFollowing():
                if followingEvent in eventDetailsList:
                    relationString = "%s -down-> %s" % (eventDetailsList[event]['className'], eventDetailsList[followingEvent]['className'])
                    seriesRelationsList.append(relationString)

        
        seriesPackageList.append('}')


        textLines.extend(seriesPackageList)
        textLines.extend(seriesRelationsList)
        textLines.append("\n")

        return textLines

    def getEventRelationshipGraphVizString(self):
        
        #Get next colour in list
        global curColourIndex

        if curColourIndex == len(graphVizColourList):
            curColourIndex = 0

        curListColour = graphVizColourList[curColourIndex]
        curColourIndex += 1

        # Create new subgraph for CoreSeries
        textLines = list()
        textLines.append('  subgraph cluster_%s{' % (str(self.series.key).replace("-","_")))
        textLines.append('      label = \"%s\";' % (self.series.title))
        textLines.append('      color = \"%s\";' % (curListColour))
        textLines.append('      edge [color = \"%s\";];' % (curListColour))
        textLines.append('')


        eventDetailsList = dict()
        seriesPackageList = list()
        seriesRelationsList = list()
        seriesHiddenRelationsList = list()


        global readingListVizCounter, readingListVizTracker

        # Generate details and add to dicts
         
        eventsList = list(self.eventsByFirstIssue.values())
        for i in range(len(eventsList)):
            # Required to sync reading list class names between series
            if eventsList[i].type == Event.EventType.ReadingList:
                classTitle = eventsList[i].getTitle()

                if classTitle in readingListVizTracker:
                    #className = None
                    className = readingListVizTracker[classTitle]['className']
                else:
                    className = "reading_list_%s" % readingListVizCounter

                    readingListVizTracker[classTitle] = {
                        'classTitle': classTitle,
                        'className': className,
                        'event' : eventsList[i],
                        'coreSeries' : self
                    }

                    readingListVizCounter += 1
            else:
                className = "%s%s" % (self.series.key.replace('-','_'), i)
                classTitle = eventsList[i].getTitle()

            if className is not None:
                eventDetailsList[eventsList[i]] = {
                    'classTitle': classTitle,
                    'className': className,
                    'event' : eventsList[i],
                    'coreSeries' : self
                }
        
        #Add in hidden relationship with next event in current series
        #prevEvent = None
        #for event, details in eventDetailsList.items():
        #    if event.type == Event.EventType.SeriesIssueRange:
        #        if prevEvent is not None:
        #            relationString = "%s -> %s" % (prevEvent['className'], details['className'])
        #            seriesRelationsList.append(relationString)
        #        prevEvent = details

        # Add label details and relationships
        prevClassDetails = None
        for event, details in eventDetailsList.items():

            # Only add class for reading list if this is the coreSeries it relates to!
            curClassTitle = details['classTitle']
            propertiesString = ""
            addClass = True

            #Modify additions for reading lists
            if curClassTitle in readingListVizTracker and readingListVizTracker[curClassTitle]['event'].type == Event.EventType.ReadingList:
                # Only add class if the coreSeries for the reading list is this one!
                if readingListVizTracker[curClassTitle]['coreSeries'] == self:
                    propertiesString = " shape=\"oval\"; color=\"%s\"" % (curListColour) if readingListVizTracker[curClassTitle]['coreSeries'] == self else ""
                else:
                    # Event is not based in current coreSeries!
                    # Don't add label
                    addClass = False

                    #Create hidden link between

            if addClass:
                if prevClassDetails is not None:
                    prevEvent = prevClassDetails['className']
                    hiddenRelationString = "      %s -> %s[style=invis; weight=10;];" % (prevClassDetails['className'], eventDetailsList[event]['className'])
                    seriesHiddenRelationsList.append(hiddenRelationString)

                seriesPackageList.append('      %s [label = \"%s\";%s];' % (details['className'], details['classTitle'], propertiesString))
                prevClassDetails = details

            for followingEvent in event.getFollowing():
                if followingEvent in eventDetailsList:
                    linkProperties = ""
                    followingSeriesDetails = eventDetailsList[followingEvent]
                    curSeriesDetails = eventDetailsList[event]

                    if followingEvent.type == Event.EventType.ReadingList:
                        followingEventTitle = eventDetailsList[followingEvent]['classTitle']
                        followingSeriesDetails = readingListVizTracker[followingEventTitle]
                    if event.type == Event.EventType.ReadingList:
                        curEventTitle = eventDetailsList[event]['classTitle']
                        curSeriesDetails = readingListVizTracker[curEventTitle]

                    if followingSeriesDetails['coreSeries'] == curSeriesDetails['coreSeries']:
                        linkProperties = " [weight=10;]"

                    relationString = "      %s -> %s%s;" % (eventDetailsList[event]['className'], eventDetailsList[followingEvent]['className'], linkProperties)
                    seriesRelationsList.append(relationString)


        seriesPackageList.append('')
        seriesRelationsList.append('')
        seriesHiddenRelationsList.append('')


        textLines.extend(seriesPackageList)
        textLines.extend(seriesRelationsList)
        textLines.extend(seriesHiddenRelationsList)
        textLines.append('      graph[style=dotted];')
        textLines.append('  }')
        textLines.append("\n")

        return textLines


class CoreSeriesCollection():
    def __init__(self):
        # Dictionary of {'coreSeriesName' : dict(startYear : set(coreSeries))}
        self.coreSeriesDict = dict()

    def addCoreSeries(self, series : CoreSeries):
        if isinstance(series, CoreSeries):
            if series.name not in self.coreSeriesDict:
                self.coreSeriesDict[series.name] = dict()
            
            if series.startYear not in self.coreSeriesDict[series.name].keys():
                self.coreSeriesDict[series.name][series.startYear] = set()

            self.coreSeriesDict[series.name][series.startYear].add(series)

    def _sortCoreSeries(self):
        for seriesName, seriesDict in self.coreSeriesDict.items():
            self.coreSeriesDict[seriesName] = dict(sorted(seriesDict.items(), key=lambda item: item.startYear if isinstance(item, CoreSeries) else float('inf')))

    def getCoreSeriesDict(self):
        self._sortCoreSeries()
        return self.coreSeriesDict
    

    def getPUMLString(self) -> str:

        stringData = ["@startuml\n"]
        stringData.append('top to bottom direction')

        for seriesName, seriesDict in self.getCoreSeriesDict().items():
            for seriesStartYear, seriesSet in seriesDict.items():
                for curSeries in seriesSet:
                    if isinstance(curSeries, CoreSeries):
                        string = curSeries.getEventRelationshipString()
                        
                        #Export series event list to file
                        stringData.extend(string)
        
        stringData.extend(["@enduml"])

        return stringData

    def getVizGraphString(self) -> str:

        stringData = [
            "digraph {",
            "   rankdir = TB;",
            "   splines=ortho;",
            "   newrank=true;",
            "   ranksep=0.5;",
            "   nodesep=0.5;",
            "   node [shape=\"rect\";];"
            ]

        for seriesName, seriesDict in self.getCoreSeriesDict().items():
            for seriesStartYear, seriesSet in seriesDict.items():
                for curSeries in seriesSet:
                    if isinstance(curSeries, CoreSeries):
                        string = curSeries.getEventRelationshipGraphVizString()
                        
                        #Export series event list to file
                        stringData.extend(string)
        
        stringData.append("}")

        return stringData