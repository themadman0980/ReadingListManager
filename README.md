# ReadingListManager
A tool for validating and managing comic book reading lists.

# Use
This tool:
1. Reads list entries from CBL files (/ReadingLists dir) or DB files (/Data dir)
2. Validates entries for series/issue matches:
  - Checks data.db
  - Checks CV.cache for existing search results
  - Runs new CV search using CV API key (entered in config.ini)
3. Outputs new CBL files including CV ID's for each readinglist provided (/Output dir)

# Information Logging
The /Results directory outputs 2x txt files every time the script is run
1. Direct dump of the console log ("results-TIMESTAMP.txt")
2. Details of invalid data ("problems-TIMESTAMP.txt")

# DB
To add db files for use with this script, simply add them to the /Data dir and ensure that the db details are included in the readingListDB var in importer.py. At present, this script relies on a fairly specific db schema. 
