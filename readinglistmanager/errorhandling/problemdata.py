from readinglistmanager import utilities
from enum import Enum
from datetime import datetime

class ProblemData():

    class ProblemType(Enum):
        CVNoResults = "No CV Results"
        CVNoNameYearMatch = "No CV Match"
        CVNoIssueMatch = "Issue Not Found In CV Series"
        CVSimilarMatch = "Similar CV Match"
        CVIncorrectYear = "CV Match With Incorrect Year"
        PublisherBlacklisted = "Publisher on Blacklist"
        NameCleaned = "Name Cleaned"
        MultipleMatch = "Multiple Matches"
        InvalidSeriesNameEncoding = "Invalid Series Name Encoding"
        DBError = "DB Error"
        IssueError = "Issue Error"
        OverrideError = "Override ID not found"

    problemCount = 0

    _list = dict((problem,[]) for problem in ProblemType)
    _problemSeries = set()
    _problemReadingLists = set()

    def __init__(self,type,data=None):
        self.type = type
        self.data = data
        ProblemData.problemCount += 1

#    def _addToList(self):
#        ProblemData._list[self.type].append(self)
#        if hasattr(self,'series'): ProblemData._problemSeries.append(self.series)

    @classmethod
    def addSeriesEntry(self,series,problemType, extraData=None):
        #if series not in ProblemData._problemSeries:
        if isinstance(problemType, ProblemData.ProblemType):
            ProblemData._list[problemType].append(ProblemSeries(series,problemType,extraData))
            ProblemData._problemSeries.add(series)

    @classmethod
    def addReadingListEntry(self, readingList, problemType : ProblemType, extraData=None):
        #if series not in ProblemData._problemSeries:
        if isinstance(problemType, ProblemData.ProblemType):
            ProblemData._list[problemType].append(ProblemReadingList(readingList, problemType, extraData))
            ProblemData._problemReadingLists.add(readingList)


#    def _checkForPartialMatch(self,nameClean,cvResults):
#        if self.type == ProblemData.ProblemType.CVNoMatch and cvResults is not None:
#            for result in cvResults:
#                cleanResultName = utilities.getDynamicName(result.name)
#                if nameClean in cleanResultName:
#                    self.type = ProblemData.ProblemType.CVPartialMatch
#                    return

    @classmethod
    def exportToFile(self):
        for section in ProblemData.ProblemType:
            # Exclude empty sections
            if len(ProblemData._list[section]) > 0:
                # Print header
                utilities.writeProblemData("\n\n*** %s ***\n" % (section.value.upper()))
                for entry in ProblemData._list[section]:
                    string = "Unknown"
                    if isinstance(entry,ProblemIssue):
                        string = "Issue : %s = %s (%s) [%s] #%s [%s]" % (entry.type.value,entry.series.name,entry.series.startYear,entry.series.id,entry.issueNumber,entry.id)
                    if isinstance(entry,ProblemSeries):
                        string = "\nSeries : %s = %s (%s) [%s] - '%s (%s)'" % (entry.type.value,entry.name,entry.startYear,entry.id,entry.dynamicName,entry.startYear)
                        issueList = []
                        for issue in entry.issueList.values():
                            issueYear = None
                            if issue.coverDate is not None and isinstance(issue.coverDate,datetime): 
                                issueYear = issue.coverDate.year
                            else:
                                issueYear = issue.year
                            issueList.append("%s (%s)" % (issue.issueNumber,issueYear))

                        string += '\n Issues: %s' % entry.getIssueNumsList()
                        if entry.data is not None:
                            if isinstance(entry.data,list):
                                for item in entry.data:
                                    string += '\n   ' + str(item)
                            else:
                                string += '\n   ' + str(entry.data)
                    # Print entry
                    utilities.writeProblemData(string)

    @classmethod
    def printSummaryResults(self):
        utilities.printResults("Problem Data: %s" % (ProblemData.problemCount), 2, True)
        for type in ProblemData.ProblemType:
            count = len(ProblemData._list[type])
            utilities.printResults("%s : %s" % (type.value,count), 3)

class ProblemIssue(ProblemData):

    def __init__(self,issue,type):
        super().__init__(type)
        self.issue = issue
#        self._addToList()


    def __getattr__(self, attr):
        return getattr(self.issue, attr)

class ProblemSeries(ProblemData):

    def __init__(self,series,problemType,extraData=None):
        super().__init__(problemType,extraData)
        #self._checkForPartialMatch(series.nameClean,series.cvResultsSeries)
        self.series = series
#        self._addToList()

    def __getattr__(self, attr):
        return getattr(self.series, attr)


class ProblemReadingList(ProblemData):

    def __init__(self, readingList : 'ReadingList', problemType : ProblemData.ProblemType, extraData=None):
        super().__init__(problemType,extraData)
        #self._checkForPartialMatch(series.nameClean,series.cvResultsSeries)
        self.readingList = readingList
#        self._addToList()

    def __getattr__(self, attr):
        return getattr(self.readingList, attr)
