#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from readinglistmanager import utilities

class IssueRange():

    def __init__(self, issueString : str = None):
        self.issueList = []
        self.relationshipList = set()

        if issueString is not None and issueString != "":
            self.issueString = str(issueString)
        else: 
            self.issueString = None
        
        self.firstIssueNum, self.lastIssueNum = None, None

        self._getFirstLastIssueNums()


    def _getFirstLastIssueNums(self):
        if self.issueString is not None and isinstance(self.issueString, str): 
            if "-" in self.issueString:
                # IssueString is a range
                self.firstIssueNum, self.lastIssueNum = self.issueString.split('-')
                
                # Convert values to int
                if utilities.isInteger(self.firstIssueNum) and utilities.isInteger(self.lastIssueNum,):
                    self.firstIssueNum = int(self.firstIssueNum)
                    self.lastIssueNum = int(self.lastIssueNum)

                    # Get list of issue numbers from first and last
                    #if '.' in self.firstIssueNum:
                    #    rangeIncrement = len(self.firstIssueNum.split('.')[1])
                    #else:
                    #    rangeIncrement = 1
                    #if '.' in str(self.firstIssueNum) or '.' in str(self.lastIssueNum):
                    #    numDecimalPlaces = len(str(self.firstIssueNum).split('.')[1])
                    #    self.issueList = list(utilities.float_range(self.firstIssueNum, self.lastIssueNum, float(1/(10 ^ numDecimalPlaces))))
                    #else:
                    self.issueList = list(range(self.firstIssueNum, self.lastIssueNum + 1))
                else:
                    #Uh-oh! There's no easy way to handle a range which doesn't have digits as first & last!
                    pass
            else:
                if utilities.isNumber(self.issueString):
                    issueNum = utilities.convertToNumber(self.issueString)
                else: 
                    issueNum = self.issueString

                self.issueList.append(issueNum)
                self.firstIssueNum = issueNum
            
            if self.firstIssueNum is None:
                pass

    def getNumIssues(self):
        return len(self.issueList)


    def isIssueNumInGroup(self, issueNum : str):
        if issueNum is not None and isinstance(issueNum, str) and len(self.issueList) > 0:

            if utilities.isNumber(issueNum):
                cleanedIssueNum = utilities.convertToNumber(issueNum)
            else:
                cleanedIssueNum = issueNum

            if cleanedIssueNum in self.issueList:
                return True
        
        return False

    @classmethod
    def fromFirstLast(self, firstIssue : int, lastIssue: int):
        issueList = "%s-%s" % (firstIssue, lastIssue)
        return IssueRange(issueList)

class IssueRangeCollection:

    def __init__(self, values : list = None):
        self.issueRangeList = list()
        self.issueRangeDict = dict()
        self.issueRangeString = None
        self.firstIssueNum = None

        if values is not None:
            pass

        self._updateIssueRangeList(values)

        self._sortIssueRanges()

        self._getString()

        self._getFirstIssueNum()

    
    def _updateIssueRangeList(self, values : list):

        #Create IssueRange object for each item in list

        if isinstance(values, list):
            for item in values:
                if isinstance(item, IssueRange):
                    self.issueRangeList.append(item)
                else:
                    try:
                        if item is None or item in ["", " "]:
                            pass
                        if item == ".":
                            pass
                        self.issueRangeList.append(IssueRange(item))
                    except Exception as e:
                        pass

    def _sortIssueRanges(self):

        # Sort issue ranges using firstIssueNum in each IssueRange
        # using dict with firstIssueNum as key and IssueRange as value
        sortedIssueRangeList = list()

        if len(self.issueRangeList) > 0:
            for curIssueRange in self.issueRangeList:
                if isinstance(curIssueRange, IssueRange):
                    self.issueRangeDict[curIssueRange.firstIssueNum] = curIssueRange

        #for firstIssueNum, curIssueRange in self.issueRangeDict.items():


        self.issueRangeDict = dict(sorted(self.issueRangeDict.items(), key=lambda item: utilities.convertToNumber(item[0]) if item[0] is not None and utilities.isNumber(item[0]) else float('inf')))
        self.issueRangeList = list(self.issueRangeDict.values())

        #self.issueRangeList = sortedIssueRangeList

    def _getString(self):

        #Generate string from list of IssueRange objects

        issueListString = "#"
        firstLoop = True

        if len(self.issueRangeList) > 0:
            for curIssueRange in self.issueRangeList:
                if curIssueRange is not None:
                    
                    # Add comma between entries 
                    if not firstLoop:
                        issueListString += ", "
                    else:
                        firstLoop = False

                    issueListString += curIssueRange.issueString
                    
        self.issueRangeString = issueListString

#    def simplifyListOfNumbers(listNumbers : list) -> list:

    def _getFirstIssueNum(self) -> str:
        #Get first issue number from list of IssueRange objects
        firstIssueNum = None

        if len(self.issueRangeList) > 0:
            for issueRange in self.issueRangeList:
                if isinstance(issueRange, IssueRange):
                    if firstIssueNum == None or (utilities.isNumber(issueRange.firstIssueNum) and issueRange.firstIssueNum < firstIssueNum):
                        if issueRange.firstIssueNum not in [0, "0"] or len(self.issueRangeList) == 1:
                            # Don't order by issue #0 if present and more than one entry!
                            firstIssueNum = issueRange.firstIssueNum
                        
            
        self.firstIssueNum = firstIssueNum

#        if firstIssueNum is None:
#            firstIssueNum = issueNums
#
#        if isinstance(firstIssueNum, str):
#            # Don't order by issue #0 if present!
#            if firstIssueNum.isdigit() and int(firstIssueNum) == 0:
#                if isinstance(issueNums, list):
#                    firstIssueNum = issueNums[1]
#
#            # Extract first issue from issue group
#            if '-' in firstIssueNum:
#                firstIssueNum = firstIssueNum.split('-')[0]
#
#            return firstIssueNum
         

    @classmethod
    def fromListOfNumbers(self, listNumbers : list):
        # Create IssueRangeCollection from a list of str/int issue numbers

        outputList = []
        intList = set()

        if isinstance(listNumbers, set):
            listNumbers = list(listNumbers)
        
        if isinstance(listNumbers, list) and len(listNumbers) == 0:
            return None

        if isinstance(listNumbers, list) and len(listNumbers) > 1:
            #Filter out non-digit issue numbers
            for listNum in listNumbers:
                if utilities.isInteger(listNum):
                    intList.add(int(listNum))
                else:
                    if listNum in [None, "", " "]:
                        pass

                    if listNum == ".":
                        pass

                    outputList.append(IssueRange(listNum))
        
            curStartingInt = None
            prevInt = None
            sortedInts = list(sorted(intList))

            #if len(outputList) == 1 :
            #    outputList = listNumbers
            #    return sorted(outputList)
            
            endOfCurRange = False
            endOfList = False
            
            #Iterate through digit issue numbers
            numItems = len(sortedInts)
            for i in range(numItems):
                #if sortedInts[i] == 7:
                #    pass

                if curStartingInt == None:
                    # Starting a new consecutive number trail
                    curStartingInt = sortedInts[i]
                elif sortedInts[i] - sortedInts[i-1] <= 1:
                    # Current int is next consecutive number
                    pass
                else:
                    endOfCurRange = True
                
                if i == len(sortedInts) - 1:
                    endOfList = True
                
                if '.' in [sortedInts[i-1], sortedInts[i]]:
                    pass

                if endOfCurRange or endOfList:
                    if endOfCurRange:
                        finishingInt = sortedInts[i-1]
                    elif endOfList:
                        finishingInt = sortedInts[i]

                    if curStartingInt != finishingInt:
                        outputList.append(IssueRange.fromFirstLast(curStartingInt, finishingInt))        
                        #"%s-%s" % (curStartingInt,finishingInt))
                    else:
                        outputList.append(IssueRange(finishingInt))

                    #Reset number trail
                    curStartingInt = sortedInts[i]
                    endOfCurRange = False

        else: 
            if isinstance(listNumbers, list):
                outputList.append(IssueRange(listNumbers[0]))
            else:
                outputList.append(IssueRange(listNumbers))

        return IssueRangeCollection(outputList)