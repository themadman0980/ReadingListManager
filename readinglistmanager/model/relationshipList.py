#!/usr/bin/env python3
# -*- coding: utf-8 -*-

class RelationshipList:
    # a set of IssueRange and ReadingLists which are related to this one!

    def __init__(self):
        self.previous = set()
        self.following = set()

    def addPrevious(self, event):
        if not hasattr(self, 'previous'):
            self.previous = set()
        self.previous.add(event)
    
    def addFollowing(self, event):
        if not hasattr(self, 'following'):
            self.following = set()
        self.following.add(event)

    def getPrevious(self):
        try:
            return self.previous
        except AttributeError:
            return []

    def getFollowing(self):
        try:
            return self.following
        except AttributeError:
            return []

    @classmethod
    def addPair(self, first, second):
        try:
            first.addFollowing(second)
            second.addPrevious(first)
        except Exception as e:
            pass
