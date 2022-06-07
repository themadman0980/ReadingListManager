#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from readinglistmanager.utilities import printResults
from readinglistmanager import utilities,importer,datasource,db,config
from readinglistmanager.filemanager import files
from readinglistmanager.series import Series
from readinglistmanager.issue import Issue
from readinglistmanager.readinglist import ReadingList
#from simyan.session import Session

cvSession = None #Session(api_key=config.CV.api_key)
CV_LAST_USED = utilities.getCurrentTimeStamp()


def main():
    printResults("Initialising...", 1, True)

    cvSource = datasource.CVSource("CV", files.cvCache)
    cvCache = db.CVDB(cvSource)

    printResults("Reading data from sources...", 1, True)
    readingLists = []

    if config.Troubleshooting.process_cbl:
        readingLists = importer.parseCBLfiles(cvCache)

    if config.Troubleshooting.process_web_dl:
        readingLists += importer.getOnlineLists(cvCache)

    numLists = len(readingLists)
    sources = set()

    for list in readingLists:
        sources.add(list.source.name)

    numListSources = len(sources)

    printResults("%s reading lists found from %s source files" %
                 (numLists, numListSources), 2)

    printResults("Validating data...", 1, True)

    Series.validateAll(cvCache.connection, cvSession)

    printResults("Summarising results...", 1, True)

    ReadingList.printSummaryResults(readingLists)
    Series.printSummaryResults()
    Issue.printSummaryResults()

if __name__ == "__main__":
    main()