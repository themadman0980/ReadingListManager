#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import unicodedata  # Needed to strip character accents
import re
import os
from datetime import datetime

timeString = datetime.today().strftime("%y%m%d%H%M%S")

scriptDirectory = os.getcwd()
rootDirectory = os.path.dirname(scriptDirectory)
resultsDirectory = os.path.join(rootDirectory, "Results")
resultsFile = os.path.join(resultsDirectory, "results-%s.txt" % (timeString))


def getCurrentTimeStamp():
    return int(round(datetime.now().timestamp()))


def getTodaysDate():
    return datetime.today().strftime('%Y-%m-%d')


def getCVSleepTimeRemaining(timestamp_last_used, api_access_rate):
    #get time since last CV API call
    timeDif = getCurrentTimeStamp() - timestamp_last_used
    return max(0, api_access_rate - timeDif)


def stripAccents(s):
    # Converts accented letters to their basic english counterpart
    s = str(s)
    return ''.join(c for c in unicodedata.normalize('NFD', s) if unicodedata.category(c) != 'Mn')


def cleanNameString(string):
    nameStringCleanTemplate = '[^a-zA-Z0-9]'
    stop_words = ['the', 'a', 'and']

    string = str(string)
    string = stripAccents(string.lower())
    cleanString = " ".join([word for word in str(
        string).split() if word not in stop_words])
    cleanString = re.sub(nameStringCleanTemplate, '', str(cleanString))

    return cleanString


def cleanYearString(string):
    yearStringCleanTemplate = '[^0-9]'
    cleanString = re.sub(yearStringCleanTemplate, '', str(string))
    return cleanString


def printResults(string, indentation, lineBreak=False, replace=False):
    with open(resultsFile, mode='a') as file:
        if not replace:
            if lineBreak:
                print("")
                file.write("\n")
            file.write("\n%s%s" % ('\t'*indentation, string))
            file.flush()

        string = string.replace("Unknown", "\033[31mUnknown\033[0m")
        string = string.replace("Warning", "\033[93mWarning\033[0m")
        string = string.replace("Error", "\033[91mWarning\033[0m")

        if replace:
            print("%s%s" % ('\t'*indentation, string), end="\r", flush=True)
        else:
            print("%s%s" % ('\t'*indentation, string))
