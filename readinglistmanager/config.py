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
        'publisher_blacklist': ["Panini Comics", "Editorial Televisa", "Planeta DeAgostini", "Abril", "Ediciones Zinco", "Dino Comics", "Unknown"],
        'publisher_preferred': ["Marvel", "DC Comics"],
    },
    'Mylar': {
        'api_key' : 'API_KEY_HERE',
        'endpoint' : 'http://localhost:8090',
        'add_missing_series' : False
    },
    'Export': {
        'preserve_file_structure' : False,
        'sort_generated_by_release_date' : False
    },
    'Troubleshooting' : {
        'process_files': True,
        'process_web_db': False,
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

class Mylar():
    sectionName = 'Mylar'

    api_key = getConfigOption('api_key', sectionName, str, None)
    if api_key is not None and api_key == 'API_KEY_HERE':
        api_key = None

    if api_key is not None:
        add_missing_series = getConfigOption('add_missing_series', sectionName, bool, False)
        endpoint = getConfigOption('endpoint', sectionName, str, "http://localhost:8090")
    else:
        #Turn off all Mylar functionality due to missing key
        add_missing_series = False

class Export():
    sectionName = 'Export'

    preserve_file_structure = getConfigOption('preserve_file_structure', sectionName, bool, False)
    sort_generated_by_release_date = getConfigOption('sort_generated_by_release_date', sectionName, bool, False)

class Troubleshooting():
    sectionName = 'Troubleshooting'

    process_files = getConfigOption('process_files', sectionName, bool, True)
    process_web_db = getConfigOption('process_web_db', sectionName, bool, False)
    verbose = getConfigOption('verbose', sectionName, bool, False)
