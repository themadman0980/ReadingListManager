#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import datetime
from readinglistmanager import utilities
from enum import Enum

class PublicationDate:
    class DateType(Enum):
        Day = {'StringFormats':['%Y-%m-%d']}
        Month = {'StringFormats':['%Y-%MM']}
        Year = {'StringFormats':['%Y']}

        def getStringFormats(self):
            return self.value['StringFormats']

    @classmethod
    def fromDateTimeObj(self, entryDateTime : datetime.date):
        if isinstance(entryDateTime, datetime.date):
            dateString = utilities.getStringFromDate(entryDateTime)
            return PublicationDate(dateString)
    
    def __init__(self, data : str = None):
        self.data = data
        
        self.type = None
        self.year = None
        self.month = None
        self.day = None

        self._processDate()

    def setDate(self, data : str = None):
        if data is not None:
            if self.data is not None:
                # Overwriting existing data is not good!
                pass
            self.data = data
        else:
            pass

        self._processDate()

    def getString(self):
        if self.type == PublicationDate.DateType.Day:
            return "%s-%s-%s" % (self.year, self.month, self.day)
        elif self.type == PublicationDate.DateType.Month:
            return "%s-%s" % (self.year, self.month)
        elif self.type == PublicationDate.DateType.Year:
            return "%s" % (self.year)
        else:
            return ""

    def _processDate(self):
        if self.data is not None:
            for dateType in PublicationDate.DateType:
                try:
                    dateObj = utilities.getDateFromStringFormats(str(self.data),dateType.getStringFormats())

                    if dateObj is not None:
                        self.type = dateType

                        if dateType == PublicationDate.DateType.Day:
                            self.day = dateObj.day
                            self.month = dateObj.month
                            self.year = dateObj.year
                        elif dateType == PublicationDate.DateType.Month:
                            self.month = dateObj.month
                            self.year = dateObj.year
                        elif dateType == PublicationDate.DateType.Year:
                            self.year = dateObj.year

                        return

                except ValueError as e:
                    pass
                except Exception as e:
                    pass

    def isValid(self):
        if self.type is not None and self.type in PublicationDate.DateType:
            return True

        return False



