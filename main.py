#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from readinglistmanager.errorhandling import problemdata
from readinglistmanager.utilities import printResults, confirmMylarImports
from readinglistmanager import config, filemanager
#from readinglistmanager.model.series import Series
#from readinglistmanager.model.issue import Issue
from readinglistmanager.datamanager import dataManager, mylarManager, importer, datasource,save
from readinglistmanager.model.readinglist import ReadingList

def main():

    # Confirm with user before proceeding if add to mylar is enabled
    if config.Mylar().add_missing_series and not confirmMylarImports():
        return
    
    printResults("Reading data from sources...", 1, True)
    readingLists = []

    if config.Troubleshooting.process_files:
        readingLists += importer.parseCBLfiles()
        readingLists += importer.parseTXTfiles()

    if config.Troubleshooting.process_web_db:
        readingLists += importer.getOnlineLists()

    numLists = len(readingLists)
    sources = set()

    for list in readingLists:
        if isinstance(list, ReadingList) and isinstance(list.source,datasource.Source):
            sources.add(list.source.name)

    numListSources = len(sources)

    printResults("%s reading lists found from %s source files" % (numLists, numListSources), 2)
    printResults("%s reading lists were found to contain %s total invalid entries" % (importer.totalProblemReadingLists, importer.totalProblemEntries), 2)

    printResults("Validating data...", 1, True)

    dataManager.validateSeries()
    dataManager.validateReadingLists(readingLists)
    dataManager.processProblemData()

    #Reorder generated lists
    if config.Export.sort_generated_by_release_date:
        ReadingList.sortListsByReleaseDate(readingLists)


    printResults("Summarising results...", 1, True)

    dataManager.printSummaryResults()
    problemdata.ProblemData.printSummaryResults()

    stringData = ReadingList.getEventSeriesSummary(readingLists)
    save.saveEventSeriesSummary(stringData)

    stringData = dataManager.getSeriesEvents()
    save.saveSeriesEventSummary(stringData)

    stringData = dataManager.getVizGraphString()
    save.saveVizGraphFile(stringData)
    #ReadingList.printSummaryResults(readingLists)
    #problemdata.ProblemData.printSummaryResults()
    #problemdata.ProblemData.exportToFile()

    if config.Mylar().add_missing_series:
        printResults("Adding series to Mylar...", 1, True)
        mylarManager.addSeriesToMylar(dataManager.getSeriesIDList())

    printResults("Writing data to files...", 1, True)
    dataManager.saveReadingLists()

    printResults("Saving problem data...", 1, True)
    problemdata.ProblemData.exportToFile()

if __name__ == "__main__":
    main()