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
                    m: discord.Member = self.guild.get_member(int(userid))
                    
                    embed = discord.Embed(color=discord.Color.red(),title="Timed out", description=f"""You have been timed out for violating the guidelines.
Reason: Reaching {len(jsn[str(self.guild.id)][str(userid)]["warns"])} warnings
""")
                    await m.send(embed=embed)
                    await m.timeout(until)
                    pass
                except discord.errors.Forbidden:
                    returnstatus = {"status":"forbidden"}
                else:
                    returnstatus = {"status":"timeout","days":days}
        else:
            m: discord.Member = self.guild.get_member(int(userid))
            
            embed = discord.Embed(color=discord.Color.red(),title="You have been warned", description=f"""You have been warned in the Xportation Corporation Hub for:
**{reason}**

**You have {len(jsn[str(self.guild.id)][str(userid)]["warns"])} warnings**

Assigened by: **{self.guild.get_member(assignedby).name}**
Assigened at: <t:{int(time.time())}:F>""")
            await m.send(embed=embed)
                
            
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

# 1244125895862648937 slient - 0
# 1244125039486439555 cool - 100
# 1244124950395359314 epic - 500
# 1244124124494827550 ultralegend - 1000
# 1349983055133020171 truexportationer - 5000
# 1349983581803646986 TILL MY LAST BREATH I'LL SUPPORT XPORTATION - 10000


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
            jsn[str(self.guild.id)][str(userid)] = {"count":0}
        
        if not jsn[str(self.guild.id)][str(userid)]["count"] >= 10000:
            jsn[str(self.guild.id)][str(userid)]["count"] += 1
        
        m: discord.Member = self.guild.get_member(userid)
        
        if jsn[str(self.guild.id)][str(userid)]["count"] >= 10000:
            r = self.guild.get_role(1349983581803646986)
            if not r in m.roles:
                await m.add_roles(r)
            
                embed = discord.Embed(color=discord.Color.blue(),description=f"You have been leveled up to the **{r.name}** rank!")
                await m.send(embed=embed)
        elif jsn[str(self.guild.id)][str(userid)]["count"] >= 5000:
            r = self.guild.get_role(1349983055133020171)
            if not r in m.roles:
                await m.add_roles(r)
            
                embed = discord.Embed(color=discord.Color.blue(),description=f"You have been leveled up to the **{r.name}** rank!")
                await m.send(embed=embed)
        elif jsn[str(self.guild.id)][str(userid)]["count"] >= 1000:
            r = self.guild.get_role(1244124124494827550)
            if not r in m.roles:
                await m.add_roles(r)
            
                embed = discord.Embed(color=discord.Color.blue(),description=f"You have been leveled up to the **{r.name}** rank!")
                await m.send(embed=embed)
        elif jsn[str(self.guild.id)][str(userid)]["count"] >= 500:
            r = self.guild.get_role(1244124950395359314)
            if not r in m.roles:
                await m.add_roles(r)
            
                embed = discord.Embed(color=discord.Color.blue(),description=f"You have been leveled up to the **{r.name}** rank!")
                m.send(embed=embed)
        elif jsn[str(self.guild.id)][str(userid)]["count"] >= 100:
            r = self.guild.get_role(1244125039486439555)
            if not r in m.roles:
                await m.add_roles(r)
            
                embed = discord.Embed(color=discord.Color.blue(),description=f"You have been leveled up to the **{r.name}** rank!")
                await m.send(embed=embed)
        else:
            pass
        
        with open(os.path.join(self.path,"messages.json"), "w", encoding="utf-8") as file:
            json.dump(jsn, file, indent=4, default=str)
            
class BanHammerHandler:
    def __init__(self, path, guild: discord.Guild):
        self.path = path
        self.guild = guild
        if not os.path.exists(os.path.join(path,"tempban.json")):
            jsn = {guild.id: {}}
            json.dump(jsn, open(os.path.join(path,"tempban.json"), "w"), indent=4)
        else:
            with open(os.path.join(path,"tempban.json"), "r") as file:
                jsn = json.load(file)
                if str(guild.id) not in jsn:
                    jsn[str(guild.id)] = {}
                with open(os.path.join(path,"tempban.json"), "w") as file:
                    json.dump(jsn, file, indent=4)
                    
class DevWarnHandler:
    def __init__(self, path, guild: discord.Guild):
        self.path = path
        self.guild = guild
        if not os.path.exists(os.path.join(path,"devwarn.json")):
            jsn = {guild.id: {}}
            json.dump(jsn, open(os.path.join(path,"devwarn.json"), "w"), indent=4)
        else:
            with open(os.path.join(path,"devwarn.json"), "r") as file:
                jsn = json.load(file)
                if str(guild.id) not in jsn:
                    jsn[str(guild.id)] = {}
                with open(os.path.join(path,"devwarn.json"), "w") as file:
                    json.dump(jsn, file, indent=4)
                    
class Radio:
    def __init__(self, voice):
        self.queue = []
        self.playing = False
        self.index = 0
        self.volume = 1.0
        self.voice: discord.VoiceClient = voice
        self.audiocl: discord.PCMVolumeTransformer = None
        self.override = "continue"
    
    async def start(self, index=0):
        self.index = index
        if not self.playing:
            if self.index < len(self.queue):
                self.audiocl = discord.PCMVolumeTransformer(discord.FFmpegPCMAudio(self.queue[self.index]))
                self.voice.play(self.audiocl, after=self.queuetick)
    
    async def addtoqueue(self, file: str):
        self.queue.append(file)
        
    def queuetick(self, error=None):
        if error:
            print(f"Error in queuetick: {error}")
        
        if self.playing:
            if self.override == "continue":
                self.index += 1
            elif self.override == "forward":
                self.index += 1
            elif self.override == "backward":
                if self.index > 0:
                    self.index -= 1
            elif self.override == "replay":
                pass
            else:
                self.index += 1
            
            self.override = "continue"
            
            if self.index < len(self.queue):
                self.audiocl = discord.PCMVolumeTransformer(discord.FFmpegPCMAudio(self.queue[self.index]))
                self.voice.play(self.audiocl, after=self.queuetick)
    
    async def setvolume(self, volume: float):
        if self.audiocl:
            self.audiocl.volume = volume
            
    async def stop(self):
        self.playing = False
        self.voice.stop()
    
    async def pause(self):
        self.voice.pause()
        
    async def resume(self):
        self.voice.resume()
    
    async def close(self):
        self.voice.disconnect()