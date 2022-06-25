#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from readinglistmanager.errorhandling import problemdata
from readinglistmanager.utilities import printResults
from readinglistmanager import config, filemanager
#from readinglistmanager.model.series import Series
#from readinglistmanager.model.issue import Issue
from readinglistmanager.datamanager import dataManager, importer, datasource
from readinglistmanager.model.readinglist import ReadingList

def main():
    
    printResults("Reading data from sources...", 1, True)
    readingLists = []

    if config.Troubleshooting.process_cbl:
        readingLists = importer.parseCBLfiles()

    if config.Troubleshooting.process_web_dl:
        readingLists += importer.getOnlineLists()

    numLists = len(readingLists)
    sources = set()

    for list in readingLists:
        if isinstance(list, ReadingList) and isinstance(list.source,datasource.Source):
            sources.add(list.source.name)

    numListSources = len(sources)

    printResults("%s reading lists found from %s source files" %
                 (numLists, numListSources), 2)

    printResults("Validating data...", 1, True)

    dataManager.validateSeries()
    dataManager.processProblemData()

    printResults("Summarising results...", 1, True)

    dataManager.printSummaryResults(readingLists)
    problemdata.ProblemData.printSummaryResults()
    #ReadingList.printSummaryResults(readingLists)
    #problemdata.ProblemData.printSummaryResults()
    #problemdata.ProblemData.exportToFile()
    printResults("Generating CBL files...", 1, True)
    ReadingList.generateCBLs(readingLists)
    problemdata.ProblemData.exportToFile()

if __name__ == "__main__":
    main()