#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os, json
from datetime import datetime

_timeString = datetime.today().strftime("%y%m%d%H%M%S")

rootDirectory = os.getcwd()
#rootDirectory = os.path.dirname(rootDirectory)
dataDirectory = os.path.join(rootDirectory, "Data")
readingListDirectory = os.path.join(rootDirectory, "ReadingLists")
resultsDirectory = os.path.join(rootDirectory, "Results")
outputDirectory = os.path.join(rootDirectory, "Output")
jsonOutputDirectory = os.path.join(outputDirectory, "JSON")
cblOutputDirectory = os.path.join(outputDirectory, "CBL")

dataFile = os.path.join(dataDirectory, "data.db")
cvCacheFile = os.path.join(dataDirectory, "cv.db")
overridesFile = os.path.join(dataDirectory,'SeriesOverrides.json')
configFile = os.path.join(rootDirectory, 'config.ini')
resultsFile = os.path.join(resultsDirectory, "results-%s.txt" % (_timeString))
problemsFile = os.path.join(resultsDirectory, "problems-%s.txt" % (_timeString))
seriesFile = os.path.join(resultsDirectory, "series-%s.txt" % (_timeString))

def checkDirectories():

    directories = [
        dataDirectory,
        readingListDirectory,
        resultsDirectory,
        outputDirectory,
        jsonOutputDirectory,
        cblOutputDirectory
        ]

    for directory in directories:
        if not os.path.exists(directory):
            os.makedirs(directory)

checkDirectories()

def getJSONData(jsonFile : str) -> dict :
    jsonData = None

    if fileExists(jsonFile):
        altSeriesDataFile = open(jsonFile,'r')
        jsonData = json.load(altSeriesDataFile)
        
    return jsonData

def fileExists(file : str) -> bool:
    if file is not None and os.path.exists(file):
        return True
    
    return False

def checkFilePath(string):
    folder = os.path.dirname(string)
    if not os.path.exists(folder):
        os.makedirs(folder)

def checkFolderPath(string):
    if not os.path.exists(string):
        os.makedirs(string)
