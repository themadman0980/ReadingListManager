#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from readinglistmanager.utilities import printResults
from readinglistmanager import utilities,importer,datasource,db,config,problemdata
from readinglistmanager.filemanager import files
from readinglistmanager.series import Series
from readinglistmanager.issue import Issue
from readinglistmanager.readinglist import ReadingList


def main():
    printResults("Initialising...", 1, True)

    data = datasource.DataSource("Data", files.dataFile)
    dataDB = db.DataDB(data)
    Series.database = dataDB

    printResults("Reading data from sources...", 1, True)
    readingLists = []

    if config.Troubleshooting.process_cbl:
        readingLists = importer.parseCBLfiles(dataDB)

    if config.Troubleshooting.process_web_dl:
        readingLists += importer.getOnlineLists(dataDB)

    numLists = len(readingLists)
    sources = set()

    for list in readingLists:
        sources.add(list.source.name)

    numListSources = len(sources)

    printResults("%s reading lists found from %s source files" %
                 (numLists, numListSources), 2)

    printResults("Validating data...", 1, True)

    Series.validateAll()

    printResults("Summarising results...", 1, True)

    ReadingList.printSummaryResults(readingLists)
    Series.printSummaryResults()
    Issue.printSummaryResults()
    problemdata.ProblemData.exportToFile()

if __name__ == "__main__":
    main()