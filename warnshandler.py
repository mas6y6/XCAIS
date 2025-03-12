import json, discord, os, datetime


class WarningHandler:
    def __init__(self, path, guild):
        self.path = path
        self.guild = guild
    
    def addwarning(self,userid,reason):
        d = json.load(self.path)
        if self.guild in d: