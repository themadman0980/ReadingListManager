from readinglistmanager import utilities
#from readinglistmanager.series import Series
#from readinglistmanager.issue import Issue
from enum import Enum

class ProblemData():

    class ProblemType(Enum):
        Invalid = "Invalid"
        CVNoResults = "No CV Results"
        CVNoMatch = "No CV Match"
        CVPartialMatch = "Partial CV Match"
        MultipleMatch = "Multiple Matches"
        DBError = "DB Error"
        CVError = "CV Error"
        IssueError = "Issue Error"

    problemCount = 0

    _list = dict((problem,[]) for problem in ProblemType)

    def __init__(self,type):
        self.type = type
        ProblemData.problemCount += 1
        self._addToList()

    def _addToList(self):
        ProblemData._list[self.type].append(self)

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
        for type,results in ProblemData._list:
            utilities.printResults("%s : %s" % (type,len(results)), 3)

class ProblemIssue(ProblemData):

    def __init__(self,issue,type):
        super().__init__(type)
        self.issue = issue

    def __getattr__(self, attr):
        return getattr(self.issue, attr)

class ProblemSeries(ProblemData):

    def __init__(self,series,type):
        if type == ProblemData.ProblemType.CVNoMatch:
            for result in series._cvResults:
                if series.cleanName in result.name:
                    type = ProblemData.ProblemType.CVPartialMatch

        super().__init__(type)
        self.series = series

    def __getattr__(self, attr):
        return getattr(self.series, attr)
