#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import unicodedata  # Needed to strip character accents
import re, os,string
from datetime import datetime
from readinglistmanager import filemanager

resultsFile = filemanager.resultsFile
problemsFile = filemanager.problemsFile
dateFormat = '%Y-%m-%d'
dynamicNameTemplate = '[^a-zA-Z0-9]'
stop_words = ['the', 'a', 'and']
yearStringCleanTemplate = '[^0-9]'
cleanStringTemplate = '[^a-zA-Z0-9\:\-\(\) ]'

def getCurrentTimeStamp():
    return int(round(datetime.now().timestamp()))

def getTodaysDate():
    return datetime.today().strftime(dateFormat)

def getStringFromDate(dateObject):
    if dateObject is not None:
        try:
            return datetime.strftime(dateObject, dateFormat)
        except Exception as e:
            return

def getDateFromString(dateString):
    if dateString is not None:
        try:
            return datetime.strptime(dateString, dateFormat)
        except Exception as e:
            return
 
def escapeString(string):
    """HTML-escape the text in `t`."""
    return (string
        .replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
        .replace("'", "&#39;").replace('"', "&quot;")
        )

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

def hasValidEncoding(string):
    return all(ord(c) < 128 for c in string)

def fixEncoding(string):
    utf8_string = (
        unicodedata.normalize('NFKC', string).
        encode('utf-8', errors='ignore').decode()
    )

    return utf8_string

def isValidID(ID):
    if ID is not None:
        isDigit = str(ID).isdigit()
        return isDigit
    return False

#def fixEncoding(string): 
#    wrong = 'windows-1252'
#    right = 'utf-8'
#
#    try:
#        s1 = bytes(string, wrong)
#    except:
#        s1 = bytes(string, right)
#
#    try:
#        s2 = s1.decode(right)
#    except:
#        s1 = bytes(string, right)
#        s2 = s1.decode('utf-8')
#
#    return s2
#

def checkPath(string):
    folder = os.path.dirname(string)
    if not os.path.exists(folder):
        os.makedirs(folder)

def getCleanYear(string):
    cleanString = re.sub(yearStringCleanTemplate, '', str(string))
    
    if cleanString == '':
        return None
    else:
        return cleanString

def padNumber(number):
    if number < 10:
        return '000' + str(number)
    elif number < 100:
        return '00' + str(number)
    elif number < 1000:
        return '0' + str(number)
    else:
        return number

def os_path_separators():
    seps = []
    for sep in os.path.sep, os.path.altsep:
        if sep:
            seps.append(sep)
    return seps

def sanitisePathString(fileNameString):
    # Replace path separators with underscores
    for sep in os_path_separators():
        valid_filename = fileNameString.replace(sep, '_')
    # Ensure only valid characters
    valid_chars = "-_.() {0}{1}".format(string.ascii_letters, string.digits)
    valid_filename = "".join(ch for ch in valid_filename if ch in valid_chars)
    # Ensure at least one letter or number to ignore names such as '..'
    valid_chars = "{0}{1}".format(string.ascii_letters, string.digits)
    test_filename = "".join(ch for ch in fileNameString if ch in valid_chars)
    if len(test_filename) == 0:
        # Replace empty file name or file path part with the following
        valid_filename = "(Empty Name)"
    return valid_filename

def printResults(string, indentation=0, lineBreak=False, replace=False):
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

def writeProblemData(string):
    with open(problemsFile, mode='a') as file:
        file.write("\n%s" % (string))
        file.flush()
