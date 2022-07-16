#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import configparser
import os

scriptDirectory = os.getcwd()
configFile = os.path.join(scriptDirectory, 'config.ini')

config = configparser.ConfigParser(allow_no_value=True)

configDict = {
    'CV': {
        'check_arcs': True,
        'check_series': True,
        'check_issues': True,
        'api_key': 'API_KEY_HERE',
        'publisher_blacklist': [],
        'publisher_preferred': [],
    },
    'Export': {
        'preserve_file_structure' : False
    },
    'Troubleshooting' : {
        'process_cbl': True,
        'process_web_dl': True,
        'verbose': False,
    }
}

def checkConfig():
    if not os.path.exists(configFile):
        # Read default values from dict if no file found
        config.read_dict(configDict)
    else:
        # Read user values from file
        config.read(configFile)

    # Save updated config file, including any new parameters
    saveConfig()
        

def saveConfig():
    with open(configFile, mode='w') as file:
        config.write(file)


checkConfig()

def getConfigOption(option : str, configSection : str, type, defaultValue):
    #Check if default matches specified type
    if isinstance(defaultValue, type):
        result = defaultValue
    else:
        result = None

    if isinstance(configSection,str) and isinstance(option,str):
        if config.has_section(configSection):
            if config.has_option(configSection,option):
                # Grab existing value
                if type == bool:
                    result = config.getboolean(configSection,option)
                else:
                    tempResult = config.get(configSection,option)
                    if isinstance(tempResult, type):
                        result = tempResult
            else:
                # Create new from default value
                config.set(configSection, option, defaultValue)
        else:
            # Create new from default value
            config.add_section(configSection)
            config.set(configSection, option, defaultValue)
       
    return result

class CV():
    sectionName = 'CV'

    api_key = getConfigOption('api_key', sectionName, str, None)
    if api_key is not None and api_key == 'API_KEY_HERE':
        api_key = None

    if api_key is not None:
        check_arcs = getConfigOption('check_arcs', sectionName, bool, True)
        check_series = getConfigOption('check_series', sectionName, bool, True)
        check_issues = getConfigOption('check_issues', sectionName, bool, True)
    else:
        #Turn off all CV searching due to missing key
        check_arcs = check_series = check_issues = False

    publisher_blacklist = getConfigOption('publisher_blacklist', sectionName, list, list())
    publisher_preferred = getConfigOption('publisher_preferred', sectionName, list, list())

class Export():
    sectionName = 'Export'

    preserve_file_structure = getConfigOption('preserve_file_structure', sectionName, bool, False)

class Troubleshooting():
    sectionName = 'Troubleshooting'
    process_cbl = getConfigOption('process_cbl', sectionName, bool, True)
    process_web_dl = getConfigOption('process_web_dl', sectionName, bool, True)
    verbose = getConfigOption('verbose', sectionName, bool, False)
