from readinglistmanager import utilities
#from readinglistmanager.series import Series
#from readinglistmanager.issue import Issue
from enum import Enum

class ProblemData():

    class ProblemType(Enum):
        Invalid = "Invalid"
        NoMatch = "No Match"
        MultipleMatch = "Multiple Matches"
        DBError = "DB Error"
        CVError = "CV Error"
        IssueError = "Issue Error"

    _list = dict((problem,[]) for problem in ProblemType)

    def __init__(self,type):
        self.type = type
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

class ProblemIssue(ProblemData):

    def __init__(self,issue,type):
        super().__init__(type)
        self.issue = issue

    def __getattr__(self, attr):
        return getattr(self.issue, attr)

class ProblemSeries(ProblemData):

    def __init__(self,series,type):
        super().__init__(type)
        self.series = series

    def __getattr__(self, attr):
        return getattr(self.series, attr)
