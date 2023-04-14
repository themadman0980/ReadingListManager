#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import unicodedata  # Needed to strip character accents
import re
import os
import string
from datetime import datetime, date
from readinglistmanager import filemanager

resultsFile = filemanager.resultsFile
problemsFile = filemanager.problemsFile
dateFormats = ['%Y-%m-%d','%Y-%MM', '%Y']
dynamicNameTemplate = '[^a-zA-Z0-9]'
stop_words = ['the', 'a', 'and']
yearStringCleanTemplate = '[^0-9]'
cleanStringTemplate = '[^a-zA-Z0-9\:\-\(\) ]'


def getCurrentTimeStamp():
    return int(round(datetime.now().timestamp()))


def getTodaysDate():
    return datetime.today().strftime(dateFormats[0])


def getStringFromDate(dateObject):
    if dateObject is not None and isinstance(dateObject, date):
        try:
            return datetime.strftime(dateObject, dateFormats[0])
        except Exception as e:
            pass

    return

def getDateFromStringFormats(dateString : str, stringFormats: list):
    if None not in [dateString, stringFormats]:
        matchDate = None
        for dateFormat in stringFormats:
            try:
                matchDate = datetime.strptime(dateString, dateFormat)
                return matchDate
            except ValueError as e:
                pass
            except Exception as e:
                pass
            

def getDateFromString(dateString : str):
    if dateString is not None:
        for dateFormat in dateFormats:
            try:
                return datetime.strptime(dateString, dateFormat)
            except ValueError as e:
                pass
            except Exception as e:
                pass


def escapeString(string):
    """HTML-escape the text in `t`."""
    return (str(string)
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

# def fixEncoding(string):
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

def _isWebSource(sourceName : str) -> bool:
    pattern = r'(WEB)?-?([A-Za-z0-9]+)?'

    match = re.search(pattern, sourceName, re.IGNORECASE)

    return True if match.group(1) == "WEB" else False     

def _getWebSourceName(sourceName : str) -> str:
    pattern = r'(?P<webSourceIdentifier>WEB)?-?(?P<sourceName>[A-Za-z0-9]+)'

    match = re.search(pattern, sourceName, re.IGNORECASE)
    match = match.groupdict()

    if 'webSourceIdentifier' in match: 
        return match['sourceName']
    else: 
        return None


def _cleanReadingListName(listName: str) -> dict:
    patterns = [
        r'(?P<partNumber>\d+)? *(?P<listName>.*?[^()]) *\(?(?P<listYears>\d+(?:-\d+)?)\)?$',
        r'(?:\[(?P<publisher>[A-Za-z ]+)\])? *(?:\(?(?P<startYear>\d{4})\))? *(?P<listName>[^()]+) *(?:\((?P<source>[A-Za-z0-9\-]*)\))?$',
        r'(?P<publisher>Marvel|DC) Events?: *(?P<listName>.*)$'
    ]

    result = {'listName': listName}

    if listName is not None and isinstance(listName, str):
        # Regex to strip annual, volume, year etc. from name
        for pattern in patterns:
            match = re.search(pattern, listName, re.IGNORECASE)
            if match:
                # Regex match found
                result = match.groupdict()

                break

    return result


def _getReadingListPart(listName: str) -> str:
    patterns = [
        r'(?P<listName>^.*?) *[-:]* *[Pp]art *?(?P<partNumber>[\w]+)$'
    ]

    result = None

    if listName is not None and isinstance(listName, str):
        # Regex to strip annual, volume, year etc. from name
        for pattern in patterns:
            match = re.search(pattern, listName, re.IGNORECASE)
            if match:
                # Regex match found
                result = match.groupdict()

                break

    return result


def _cleanSeriesName(seriesName: str):
    volPattern = r'(?P<seriesName>.*?) *(Vol(ume)?\.?) *\(?(?P<volumeNum>\d+)?\)?$'
    patterns = {
        'volume': volPattern + '$',
        'volumeAnnual': volPattern + r' *(?P<annualTag>Annual)$',
        'year': r'(?P<seriesName>.*?) *\(?(?P<seriesYear>19[2-9]\d|20[0-4]\d|\'\d{2})\)?$'
    }

    newSeriesName = seriesName

    if seriesName is not None and isinstance(seriesName, str):
        # Regex to strip annual, volume, year etc. from name
        for type, pattern in patterns.items():
            match = re.search(pattern, seriesName, re.IGNORECASE)
            if match:
                matchDict = match.groupdict()
                # Regex match found
                newSeriesName = matchDict['seriesName']
                if 'annualTag' in matchDict:
                    newSeriesName += matchDict['annualTag']

                break

    return newSeriesName


def cleanFileName(orig_name: str):
    orig_name = str(orig_name)
    fixed_name = orig_name.replace('\\\\', '⑊')
    forbidden_characters = '"*/:<>?\|'
    substitute_characters = '\'---[]   '
    for a, b in zip(forbidden_characters, substitute_characters):
        fixed_name = fixed_name.replace(a, b)

    return fixed_name

def getFirstIssueNum(issueNums) -> str:

    if isinstance(issueNums, list):
        firstIssueNum = issueNums[0]
    else:
        firstIssueNum = issueNums

    if isinstance(firstIssueNum, str):
        # Don't order by issue #0 if present!
        if firstIssueNum.isdigit() and int(firstIssueNum) == 0:
            if isinstance(issueNums, list):
                firstIssueNum = issueNums[1]

        # Extract first issue from issue group
        if '-' in firstIssueNum:
            firstIssueNum = firstIssueNum.split('-')[0]

        return firstIssueNum
        
    
    return None
    



def simplifyListOfNumbers(listNumbers : list) -> list:
    # Intended to organise and simplify issue numbers into concatenated groups where possible

    outputList = []
    intList = set()

    if isinstance(listNumbers, list) and len(listNumbers) > 1:
        #Filter out non-digit issue numbers
        for listNum in listNumbers:
            if isinstance(listNum,str) and listNum.isdigit():
                intList.add(int(listNum))
            else:
                outputList.append(listNum)
    
        curStartingInt = None
        prevInt = None
        sortedInts = list(sorted(intList))

        #if len(outputList) == 1 :
        #    outputList = listNumbers
        #    return sorted(outputList)
        
        endOfCurRange = False
        endOfList = False
        
        #Iterate through digit issue numbers
        numItems = len(sortedInts)
        for i in range(numItems):
            #if sortedInts[i] == 7:
            #    pass

            if curStartingInt == None:
                # Starting a new consecutive number trail
                curStartingInt = sortedInts[i]
            elif sortedInts[i] == sortedInts[i-1] + 1:
                # Current int is next consecutive number
                pass
            else:
                endOfCurRange = True
            
            if i == len(sortedInts) - 1:
                endOfList = True
            
            if endOfCurRange or endOfList:
                if endOfCurRange:
                    finishingInt = sortedInts[i-1]
                elif endOfList:
                    finishingInt = sortedInts[i]

                if curStartingInt != finishingInt:
                    outputList.append("%s-%s" % (curStartingInt,finishingInt))
                else:
                    outputList.append("%s" % (finishingInt))

                #Reset number trail
                curStartingInt = sortedInts[i]
                endOfCurRange = False

    else: 
        outputList = listNumbers
    
    return sorted(outputList)


def confirmMylarImports() -> bool:
    yes = {'yes','y', 'ye'}
    no = {'no','n'}

    printResults("WARNING: Mylar imports are enabled! [Enter y to proceed]")
    choice = input().lower()
    if choice in yes:
        return True
    else:
        return False



