#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import configparser
import os

config = configparser.ConfigParser()

def checkConfig():
    global config

    scriptDirectory = os.getcwd()
    #rootDirectory = os.path.dirname(scriptDirectory)
    configFile = os.path.join(scriptDirectory, 'config.ini')

    if not os.path.exists(configFile):
        generateNewConfig(configFile)

    config.read(configFile)

        
def generateNewConfig(configFile):
    with open(configFile, mode='a') as file:
        lines = []
        lines.append('[CV]')
        lines.append('check_volumes = True  # Enable/disable CV api calls for volume searches')
        lines.append('check_issues = True  # Enable/disable CV api calls for issue searches')
        lines.append('api_key = CV_API_KEY')
        lines.append('publisher_blacklist = "Panini Comics", "Editorial Televisa", "Planeta DeAgostini", "Unknown" # Ignore these results')
        lines.append('publisher_preferred = "Marvel", "DC Comics" # If multiple matches found, prefer these results')
        lines.append('\n')

        lines.append('[Troubleshooting]')
        lines.append('process_cbl = True #Validate entries in CBL files')
        lines.append('process_web_dl = True #Validate entries in databases')
        lines.append('update_clean_names = False #Regenerate CleanName field for series in db')
        lines.append('verbose = False #Enable verbose logging')

        for line in lines:
            if isinstance(line, str):
                file.write(line + '\n')

checkConfig()

verbose = eval(config['Troubleshooting']['verbose'])

class CV():
    cv = config['CV']
    check_volumes = eval(cv['check_volumes'])
    check_issues = eval(cv['check_issues'])
    api_key = cv['api_key']
    publisher_blacklist = cv['publisher_blacklist']
    publisher_preferred = cv['publisher_preferred']


class Troubleshooting():
    troubleshooting = config['Troubleshooting']
    process_cbl = eval(troubleshooting['process_cbl'])
    process_web_dl = eval(troubleshooting['process_web_dl'])
    update_clean_names = eval(troubleshooting['update_clean_names'])
