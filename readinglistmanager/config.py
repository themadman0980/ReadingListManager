#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import configparser
import os

scriptDirectory = os.getcwd()
#rootDirectory = os.path.dirname(scriptDirectory)
configFile = os.path.join(scriptDirectory, 'config.ini')
config = configparser.ConfigParser()
config.read(configFile)

verbose = eval(config['Troubleshooting']['verbose'])


class CV():
    cv = config['CV']
    check_volumes = eval(cv['check_volumes'])
    check_issues = eval(cv['check_issues'])
    api_key = cv['api_key']
#    api_rate = int(cv['api_rate'])
    publisher_blacklist = cv['publisher_blacklist']
    publisher_preferred = cv['publisher_preferred']


class Troubleshooting():
    troubleshooting = config['Troubleshooting']
    process_cbl = eval(troubleshooting['process_cbl'])
    process_web_dl = eval(troubleshooting['process_web_dl'])
    update_clean_names = eval(troubleshooting['update_clean_names'])