#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import json
from enum import Enum
from readinglistmanager.model.readinglist import ReadingList
from readinglistmanager.model.issue import Issue
from readinglistmanager.model.series import CoreSeries
from readinglistmanager.datamanager import summaryManager
from readinglistmanager.datamanager.datasource import Source, ListSourceType
from readinglistmanager import filemanager, utilities, config


class OutputFileType(Enum):
    JSON = ('.json', filemanager.jsonOutputDirectory)
    CBL = ('.cbl', filemanager.cblOutputDirectory)
    TXT = ('.txt', filemanager.outputDirectory)

    def getExtension(self) -> str:
        return self.value[0]

    def getDirectory(self) -> str:
        return self.value[1]

    def getReadingListData(self, readingList: ReadingList):
        if isinstance(readingList, ReadingList):
            if self == OutputFileType.CBL:
                return readingList.getCBLData()
            elif self == OutputFileType.JSON:
                return readingList.getJSONData()
            elif self == OutputFileType.TXT:
                return readingList.getTXTData()


def getOutputFile(readingList: ReadingList, fileType: OutputFileType) -> str:
    if isinstance(readingList, ReadingList) and isinstance(fileType, OutputFileType):
        fileName = readingList.getFileName() + fileType.getExtension()
        fileName = utilities.cleanFileName(fileName)

        if config.Export.preserve_file_structure and fileType == OutputFileType.CBL:
            fileDir = getReadingListOutputDirectory(readingList, fileType)
        else:
            fileDir = fileType.getDirectory()

        file = os.path.join(fileDir, fileName)

        filemanager.checkFilePath(file)

        return file

    return None


def saveReadingList(readingList: ReadingList, outputFileType: OutputFileType) -> None:
    if isinstance(readingList, ReadingList) and isinstance(outputFileType, OutputFileType):
        file = getOutputFile(readingList, outputFileType)
        outputData = outputFileType.getReadingListData(readingList)

        if outputFileType == OutputFileType.CBL:
            with open(file, 'w') as outputFile:
                outputFile.writelines(outputData)

        elif outputFileType == OutputFileType.JSON:
            with open(file, 'w') as outputFile:
                json.dump(outputData, outputFile, indent=4)


def saveReadingLists(readingLists: list[ReadingList], outputFileType: OutputFileType) -> None:

    if isinstance(readingLists, list) and isinstance(outputFileType, OutputFileType):
        for readingList in readingLists:
            if isinstance(readingList, ReadingList):
                saveReadingList(readingList, outputFileType)


def saveDataListToTXT(fileName: str, listData: list, isCompleteFilePath=False) -> None:
    outputFileType = OutputFileType.TXT
    if not isinstance(listData, list):
        if isinstance(listData, set) or isinstance(listData, tuple):
            listData = list(listData)
        elif isinstance(listData, dict):
            listData = list(listData.values())

    if isCompleteFilePath:
        file = fileName
    else:
        fileName = fileName + outputFileType.getExtension()
        file = os.path.join(outputFileType.getDirectory(), fileName)


    if isinstance(listData, list) and isinstance(fileName, str):
        with open(file, mode='w') as outputFile:
            for line in listData:
                outputFile.write(f"{line}\n")

def saveEventSeriesSummary(stringData : str):
    saveDataListToTXT(filemanager.eventSeriesFile, stringData, True)

def saveSeriesEventSummary(stringData : str):
    saveDataListToTXT(filemanager.seriesEventFile, stringData, True)

def getReadingListOutputDirectory(readingList: ReadingList, outputFileType: OutputFileType) -> str:
    originFolder = filemanager.readingListDirectory
    destFolder = outputFileType.getDirectory()

    if isinstance(readingList.source, Source):
        if isinstance(readingList.source.file, str):
            sourceFolder = os.path.dirname(readingList.source.file)
        # Set output to subdirectory of output folder
        # Set top level of cbl output destination
        destFolder = os.path.join(destFolder, readingList.source.type.value)
        if readingList.source.type == ListSourceType.CBL and config.Export.preserve_file_structure:
            # Set full path to CBL, keeping relative location
            destFolder = str(sourceFolder).replace(originFolder, destFolder)
        elif readingList.source.type == ListSourceType.Website:
            destFolder = os.path.join(destFolder, readingList.source.name)

    return destFolder
