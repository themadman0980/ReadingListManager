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

    def __init__(self, data: str = None, dateTimeObj: datetime.datetime = None):
        self.data = data

        self.dateTimeObj = dateTimeObj

        self.type = None
        self.year = None
        self.month = None
        self.day = None

        self._processDate()

    def __eq__(self, other):
        if not isinstance(other, PublicationDate):
            # don't attempt to compare against unrelated types
            return NotImplemented

        if self.year == other.year:
            if None in (self.month, other.month):
                return True
            elif self.month == other.month:
                if None in (self.day, other.day):
                    return True
                elif self.day == other.day:
                    return True

        return False

    def __hash__(self):
        # necessary for instances to behave sanely in dicts and sets.
        return hash((self.year, self.month, self.day))

    def __lt__(self, other):
        try:
            return self.dateTimeObj.timestamp() < other.dateTimeObj.timestamp()
        finally:
            return None

    def __le__(self, other):
        try:
            return self < other or self == other
        finally:
            return None

    def __gt__(self, other):
        try:
            return self.dateTimeObj.timestamp() > other.dateTimeObj.timestamp()
        finally:
            return None

    def __ge__(self, other):
        try:
            return self > other or self == other
        finally:
            return None

    def setDate(self, data: str = None):
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

            return "%s-%s-%s" % (self.year, utilities.padNumber(self.month,2), utilities.padNumber(self.day,2))
        elif self.type == PublicationDate.DateType.Month:
            return "%s-%s" % (self.year, utilities.padNumber(self.month,2))
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
                        self.dateTimeObj = dateObj

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

    def isValidDate(self):
        if self.type is not None and self.type in PublicationDate.DateType:
            return True

        return False

    def getDateTimeObject(self):
        return self.dateTimeObj
