#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import unicodedata  # Needed to strip character accents
import re
import os
from datetime import datetime
from . import filemanager

dateFormat = '%Y-%m-%d'
dynamicNameTemplate = '[^a-zA-Z0-9]'
stop_words = ['the', 'a', 'and']
yearStringCleanTemplate = '[^0-9]'
cleanStringTemplate = '[^a-zA-Z0-9 ]'

def getCurrentTimeStamp():
    return int(round(datetime.now().timestamp()))

def getTodaysDate():
    return datetime.today().strftime(dateFormat)

def parseDate(dateString):
    return datetime.strftime(dateString, dateFormat)

def stripAccents(s):
    # Converts accented letters to their basic english counterpart
    s = str(s)
    return ''.join(c for c in unicodedata.normalize('NFD', s) if unicodedata.category(c) != 'Mn')

def stripSymbols(string):
    return re.sub(cleanStringTemplate, '', str(string))

def getDynamicName(string):
    string = str(string)
    string = stripAccents(string.lower())
    cleanString = " ".join([word for word in str(
        string).split() if word not in stop_words])
    cleanString = re.sub(dynamicNameTemplate, '', str(cleanString))

    return cleanString


def cleanYearString(string):
    cleanString = re.sub(yearStringCleanTemplate, '', str(string))
    return cleanString


def printResults(string, indentation, lineBreak=False, replace=False):
    with open(filemanager.files.resultsFile, mode='a') as file:
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
