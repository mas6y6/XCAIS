import json, discord, os, datetime, time
import random

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
            
        return User(jsn[str(self.guild.id)][str(userid)])

    async def addwarning(self,userid,reason,assignedby,expire=None):
        jsn = json.load(open(os.path.join(self.path,"warns.json"),"r"))
        
        if str(userid) not in jsn[str(self.guild.id)]:
            jsn[str(self.guild.id)][str(userid)] = {"timeout_count":0,"max_warnings_before_timeout":3,"warns":[]}
        
        jsn[str(self.guild.id)][str(userid)]["warns"].append({
            "reason":reason,
            "timestamp":datetime.datetime.now().timestamp(),
            "expire": expire,
            "userid": userid,
            "assignedby": assignedby,
            "id":random.randint(10000000000000000000000,99999999999999999999999)
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
                    # TODO: Uncomment this line below as its the function that times out users
                    await self.guild.get_member(int(userid)).timeout(until)
                    pass
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
            warnslist.append(Warning(i["reason"], i["timestamp"], i["expire"], i["userid"], i["assignedby"], i["id"]))
        
        warnslist.sort(key=lambda x: x.timestamp, reverse=True)
        
        with open(os.path.join(self.path,"warns.json"), "w", encoding="utf-8") as file:
            json.dump(jsn, file, indent=4, default=str)
        return warnslist

    async def getwarnindex(self, userid, id):
        jsn = json.load(open(os.path.join(self.path, "warns.json"), "r"))
        
        if str(userid) not in jsn[str(self.guild.id)]:
            jsn[str(self.guild.id)][str(userid)] = {"timeout_count": 0, "max_warnings_before_timeout": 3, "warns": []}
        
        with open(os.path.join(self.path,"warns.json"), "w", encoding="utf-8") as file:
            json.dump(jsn, file, indent=4, default=str)
        
        for index, warn in enumerate(jsn[str(self.guild.id)][str(userid)]["warns"]):
            if warn["id"] == id:
                return index
        
        return None
    
    async def deletewarning(self, userid, index):
        jsn = json.load(open(os.path.join(self.path, "warns.json"), "r"))
        
        if str(userid) not in jsn[str(self.guild.id)]:
            jsn[str(self.guild.id)][str(userid)] = {"timeout_count": 0, "max_warnings_before_timeout": 3, "warns": []}
        
        jsn[str(self.guild.id)][str(userid)]["warns"].pop(index)
        
        with open(os.path.join(self.path,"warns.json"), "w", encoding="utf-8") as file:
            json.dump(jsn, file, indent=4, default=str)
            
    async def clearwarnings(self, userid):
        jsn = json.load(open(os.path.join(self.path, "warns.json"), "r"))
        
        if str(userid) not in jsn[str(self.guild.id)]:
            jsn[str(self.guild.id)][str(userid)] = {"timeout_count": 0, "max_warnings_before_timeout": 3, "warns": []}
        
        jsn[str(self.guild.id)][str(userid)]["warns"] = []
        
        with open(os.path.join(self.path,"warns.json"), "w", encoding="utf-8") as file:
            json.dump(jsn, file, indent=4, default=str)

class Warning:
    def __init__(self,reason, timestamp, expire, userid, assignedby, id):
        self.reason = reason
        self.timestamp = timestamp
        self.expire = expire
        self.userid = userid
        self.assignedby = assignedby
        self.id = id

class User:
    def __init__(self,data):
        self.timeout_count = data["timeout_count"]
        self.max_warnings_before_timeout = data["max_warnings_before_timeout"]
        self.warns: list[Warning] = []
        for i in data["warns"]:
            self.warns.append(Warning(i["reason"],i["timestamp"],i["expire"],i["userid"],i["assignedby"],i["id"]))


# COOL MESSAGE Tiers

# slient - 0
# cool - 100
# epic - 500
# ultralegend - 1000
# truexportationer - 5000
# TILL MY LAST BREATH I'LL SUPPORT XPORTATION - 10000
    
class COOLMessageHandler:
    def __init__(self, path, guild: discord.Guild):
        self.path = path
        self.guild = guild
        if not os.path.exists(os.path.join(path,"messages.json")):
            jsn = {guild.id: {}}
            json.dump(jsn, open(os.path.join(path,"messages.json"), "w"), indent=4)
        else:
            with open(os.path.join(path,"messages.json"), "r") as file:
                jsn = json.load(file)
                if str(guild.id) not in jsn:
                    jsn[str(guild.id)] = {}
                with open(os.path.join(path,"messages.json"), "w") as file:
                    json.dump(jsn, file, indent=4)
    
    async def add_message(self,userid):
        jsn = json.load(open(os.path.join(self.path, "messages.json"), "r"))
        
        if str(userid) not in jsn[str(self.guild.id)]:
            jsn[str(self.guild.id)][str(userid)] = {"count"}
        
        
        with open(os.path.join(self.path,"warns.json"), "w", encoding="utf-8") as file:
            json.dump(jsn, file, indent=4, default=str)