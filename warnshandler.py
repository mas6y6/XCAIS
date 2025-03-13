import json, discord, os, datetime, time

class WarningHandler:
    def __init__(self, path, guild: discord.Guild):
        self.path = path
        self.guild = guild
        if not os.path.exists(os.path.join(path,"warns.json")):
            jsn = {guild.id: {}}
            json.dump(jsn, open(os.path.join(path,"warns.json"), "w"), indent=4)
        else:
            with open(os.path.join(path,"warns.json"), "r") as file:
                jsn = json.load(file)
                if str(guild.id) not in jsn:
                    jsn[str(guild.id)] = {}
                with open(os.path.join(path,"warns.json"), "w") as file:
                    json.dump(jsn, file, indent=4)

    async def getuser(self,userid):
        jsn = json.load(open(os.path.join(self.path,"warns.json"),"r"))
        if str(userid) not in jsn[str(self.guild.id)]:
            jsn[str(self.guild.id)][str(userid)] = {"timeout_count":0,"max_warnings_before_timeout":3,"warns":[]}
        
        with open(os.path.join(self.path,"warns.json"), "w", encoding="utf-8") as file:
            json.dump(jsn, file, indent=4, default=str)

    async def addwarning(self,userid,reason,assignedby,expire=None):
        jsn = json.load(open(os.path.join(self.path,"warns.json"),"r"))
        
        if str(userid) not in jsn[str(self.guild.id)]:
            jsn[str(self.guild.id)][str(userid)] = {"timeout_count":0,"max_warnings_before_timeout":3,"warns":[]}
        
        jsn[str(self.guild.id)][str(userid)]["warns"].append({
            "reason":reason,
            "timestamp":datetime.datetime.now().timestamp(),
            "expire": expire,
            "userid": userid,
            "assignedby": assignedby
        })
        
        returnstatus = {"status":"warned"}
        
        if len(jsn[str(self.guild.id)][str(userid)]["warns"]) >= jsn[str(self.guild.id)][str(userid)]["max_warnings_before_timeout"]:
            days = 1
            mb = False
            pb = False
            if len(jsn[str(self.guild.id)][str(userid)]["warns"]) == 3:
                days = 1
            elif len(jsn[str(self.guild.id)][str(userid)]["warns"]) == 6:
                days = 3
            elif len(jsn[str(self.guild.id)][str(userid)]["warns"]) == 9:
                mb = True
                returnstatus = {"status":"askowner_month_ban"}
            elif len(jsn[str(self.guild.id)][str(userid)]["warns"]) == 12:
                pb = True
                returnstatus = {"status":"askowner_perm_ban"}
            else:
                pass
            
            jsn[str(self.guild.id)][str(userid)]["timeout_count"] += 1
            jsn[str(self.guild.id)][str(userid)]["max_warnings_before_timeout"] += 3
            
            if not mb and not pb:
                duration = datetime.timedelta(days=days)
                
                until = datetime.datetime.now(datetime.timezone.utc) + duration
                
                try:
                    await self.guild.get_member(int(userid)).timeout(until)
                except discord.errors.Forbidden:
                    returnstatus = {"status":"forbidden"}
                else:
                    returnstatus = {"status":"timeout","days":days}
                
            
        with open(os.path.join(self.path,"warns.json"), "w", encoding="utf-8") as file:
            json.dump(jsn, file, indent=4, default=str)
            
        return returnstatus
            
    async def getwarns(self, userid) -> list[Warning]:
        jsn = json.load(open(os.path.join(self.path, "warns.json"), "r"))
        
        if str(userid) not in jsn[str(self.guild.id)]:
            jsn[str(self.guild.id)][str(userid)] = {"timeout_count": 0, "max_warnings_before_timeout": 3, "warns": []}
            
        warnslist = []
        
        for i in jsn[str(self.guild.id)][str(userid)]["warns"]:
            warnslist.append(Warning(i["reason"], i["timestamp"], i["expire"], i["userid"], i["assignedby"]))
        
        warnslist.sort(key=lambda x: x.timestamp, reverse=True)
        
        return warnslist

class Warning:
    def __init__(self,reason, timestamp, expire, userid, assignedby):
        self.reason = reason
        self.timestamp = timestamp
        self.expire = expire
        self.userid = userid
        self.assignedby = assignedby

class User:
    def __init__(self,data):
        self.timeout_count = data["timeout_count"]
        self.max_warnings_before_timeout = data["max_warnings_before_timeout"]
        self.warns: list[Warning] = []
        for i in data["warns"]:
            self.warns.append(Warning(i["reason"],i["timestamp"],i["expire"],i["userid"],i["assignedby"]))