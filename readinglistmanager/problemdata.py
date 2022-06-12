from readinglistmanager import utilities
from enum import Enum

class ProblemData():

    class ProblemType(Enum):
        CVNoResults = "No CV Results"
        CVNoMatch = "No CV Match"
        CVSimilarMatch = "Similar CV Match"
        CVIncorrectYear = "CV Match With Incorrect Year"
        MultipleMatch = "Multiple Matches"
        InvalidSeriesNameEncoding = "Invalid Series Name Encoding"
        DBError = "DB Error"
        IssueError = "Issue Error"
        IssueNotFound = "Issue Not Found In CV Series"

    problemCount = 0

    _list = dict((problem,[]) for problem in ProblemType)
    _problemSeries = []

    def __init__(self,type):
        self.type = type
        ProblemData.problemCount += 1

    def _addToList(self):
        ProblemData._list[self.type].append(self)
        if hasattr(self,'series'): ProblemData._problemSeries.append(self.series)

    @classmethod
    def addSeries(self,series,problemType):
        if series not in ProblemData._problemSeries:
            ProblemSeries(series,problemType)
            ProblemData._problemSeries.append(series)


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
                        string = "Series : %s = %s (%s) [%s] - '%s (%s)'" % (entry.type.value,entry.name,entry.startYear,entry.id,entry.nameClean,entry.startYearClean)
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
        self._addToList()


    def __getattr__(self, attr):
        return getattr(self.issue, attr)

class ProblemSeries(ProblemData):

    def __init__(self,series,problemType):
        super().__init__(problemType)
        #self._checkForPartialMatch(series.nameClean,series.cvResultsSeries)
        self.series = series
        self._addToList()

    def __getattr__(self, attr):
        return getattr(self.series, attr)
