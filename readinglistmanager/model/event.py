#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from readinglistmanager.model.relationshipList import RelationshipList
from enum import Enum

class Event(RelationshipList):

    class EventType(Enum):
        SeriesIssueRange = "Series"
        ReadingList = "Reading List"

    def __hash__(self):
        return hash(self.sourceObject)

    def __init__(self, issueRange, eventType, sourceObject):
        self.issueRange = issueRange
        self.sourceObject = sourceObject
        self.type = eventType

    def getString(self):
        if self.type == Event.EventType.ReadingList:
            return "%s: %s" % (self.sourceObject.title, self.issueRange.issueRangeString)
        else:
            return self.issueRange.issueRangeString

    def getTitle(self):
        if self.type == Event.EventType.ReadingList:
            return self.sourceObject.getFileName()
        else:
            return self.issueRange.issueRangeString
        