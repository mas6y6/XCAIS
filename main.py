import time
import traceback
import discord, os, sys, logging, yaml
from discord.ext.commands.bot import Bot
import modals
from datetime import datetime
from handlers import WarningHandler, Warning, User, COOLMessageHandler
import discord.ext.commands

# Creates config.yaml if it doesnt exist
if not os.path.exists("config.yaml"):
    f = open("config.yaml","w")
    f.write("""# Configuration for XCAIS
            
config:
    secretspath: ./secrets # To store security keys and bot tokens and discord tokens
    logfile: ./discord.log # Log file to store logs
    guild: # Server ID of the server to interact
    data: ./data # Store data for server to use like warns
    consolechannel: # Channel ID to the console channel
    owner: # User ID of the owner of the server
    moderatorchannel: # Moderator channel of the server
    moderatorrole: # Role ID for Moderators
    xc_board: 

permconfig:
    # Include the ID's to the roles to give moderator commands too
    # If left empty it will use @everyone

    moderatorcommands: []

    saycommands: []

emoji:
    XC: 
""")
    f.close()

config = yaml.safe_load(open("config.yaml"))
guild = config["config"]["guild"]

# Bot version
ver = "v1.0.9-beta"

if not os.path.exists(config["config"]["secretspath"]):
    os.makedirs(config["config"]["secretspath"])

if not os.path.exists(config["config"]["data"]):
    os.makedirs(config["config"]["data"])

if not os.path.exists(os.path.join(config["config"]["secretspath"],"token.key")):
    open(os.path.join(config["config"]["secretspath"],"token.key"),"w").close()

# logging.basicConfig(filemode=config["config"]["logfile"],level=logging.INFO)

intents = discord.Intents.default()
intents.all()
intents.message_content = True
intents.guilds = True
intents.members = True

bot = Bot(command_prefix="x>",intents=intents)

warnhandler: WarningHandler = None
xcaisguild: discord.Guild = None
consolechannel: discord.TextChannel = None
messagehandler: COOLMessageHandler = None

async def sendtoconsole(text: str,embed=None):
    global consolechannel
    
    t = f"<t:{int(time.time())}:R> [**{bot.user.display_name}**]: {text}"
    
    if not consolechannel == None:
        await consolechannel.send(t,embed=None)
class DeleteWarnMenu(discord.ui.View):
    def __init__(self, user: discord.Member,warns: list[Warning], timeout=180):
        super().__init__(timeout=timeout)
        self.user = user
        
        opt = []
        
        for i in warns:
            opt.append(discord.SelectOption(label=i.reason,value=i.id))
        
        self.select = discord.ui.Select(
            placeholder="Select a warning to view",
            min_values=1,
            max_values=1,
            options=opt
        )
        self.select.callback = self.select_callback
        self.add_item(self.select)

    async def select_callback(self, interaction: discord.Interaction):
        global warnhandler
        print(self.select.values)
        
        selected_warn = int(self.select.values[0])
        
        iw = await warnhandler.getwarnindex(self.user.id,selected_warn)
        await warnhandler.deletewarning(self.user.id,iw)
        
        warns = await warnhandler.getwarns(self.user.id)
        opt = []
        for i in warns:
            opt.append(discord.SelectOption(label=i.reason, value=i.id))
        
        self.select.options = opt
        
        embed = discord.Embed(
            color=discord.Color.red(),
            title=f"{self.user.name} has {len(warns)} warnings",
            description="Select the warning from the drop menu below to delete"
        )
        
        if len(opt) == 0:
            embed = discord.Embed(color=discord.Color.red(),description="**All warnings are cleared**")
            await interaction.response.edit_message(embed=embed,view=None)
        else:
            await interaction.response.edit_message(embed=embed,view=self)
        
        embed = discord.Embed(color=discord.Color.red(),title="**Warning removed**")
        await interaction.followup.send(embed=embed, ephemeral=True)

class ClearWarnsView(discord.ui.View):
    def __init__(self, user: discord.Member, timeout = 180):
        super().__init__(timeout=timeout)
        self.user = user
        
    @discord.ui.button(label="Cancel",style=discord.ButtonStyle.gray)
    async def cancel(self, interaction: discord.Interaction, button: discord.Button):
        await interaction.delete_original_response()
    
    @discord.ui.button(label="Proceed",style=discord.ButtonStyle.danger)
    async def cancel(self, interaction: discord.Interaction, button: discord.Button):
        await interaction.response.defer(ephemeral=True)
        
        await warnhandler.clearwarnings(self.user.id)
        
        embed = discord.Embed(description="Warnings cleared",color=discord.Color.green())
        
        await interaction.response.edit_message(embed=embed,view=None)

class DeleteWarnView(discord.ui.View):
    def __init__(self, user: discord.Member, timeout = 180, zerowarns=False):
        super().__init__(timeout=timeout)
        self.user = user
        
        self.deletewarnbutton = discord.ui.Button(label="Delete a warning",style=discord.ButtonStyle.danger, disabled=zerowarns)
        self.deletewarnbutton.callback = self.deletewarn
        
        self.add_item(self.deletewarnbutton)
    
    async def deletewarn(self,interaction: discord.Interaction):
        if not hasperm(interaction.user,config["permconfig"]["moderatorcommands"]):
            embed = discord.Embed(color=discord.Color.red(),title="**You dont have access to this command**")
            await interaction.response.send_message(embed=embed,ephemeral=True)
        else:
            warns = await warnhandler.getwarns(self.user.id)
            embed = discord.Embed(
                color=discord.Color.red(),
                title=f"{self.user.name} has {len(warns)} warnings",
                description="Select the warning from the drop menu below to delete"
            )
            
            if len(warns) == 0:
                embed = discord.Embed(
                    color=discord.Color.red(),
                    description=f"{self.user.name} has 0 warnings",
                )
                await interaction.response.send_message(embed=embed,ephemeral=True)
            else:
                embed = discord.Embed(
                color=discord.Color.red(),
                title=f"{self.user.name} has {len(warns)} warnings",
                description="Select the warning from the drop menu below to delete"
            )
                await interaction.response.send_message(embed=embed,view=DeleteWarnMenu(self.user,warns),ephemeral=True)

class BanView(discord.ui.View):
    def __init__(self,userid, timeout=None, action=True):
        self.userid = userid
        self.action = action
        super().__init__(timeout=timeout)
    
    @discord.ui.button(label="Cancel",style=discord.ButtonStyle.grey)
    async def cancel(self, interaction: discord.Interaction, button: discord.Button):
        button.disabled = True
        embed = discord.Embed(title="Operation Canceled")
        await interaction.response.edit_message(embed=embed,view=None)
        
    @discord.ui.button(label="Proceed",style=discord.ButtonStyle.red)
    async def proceed(self, interaction: discord.Interaction, button: discord.Button):
        try:
            member: discord.Member = await xcaisguild.get_member(self.userid)
            if self.action:
                await member.ban(reason="Member banned for reaching higher then 12 warnings")
            else:
                await member.timeout(datetime.timedelta(days=30), reason="Member temporarily banned for reaching higher than 9 warnings")
        except:
            embed = discord.Embed(title="An error occurred", description="An unexpected error has occurred")
            traceback.print_exc()
        await interaction.response.pong()
 

async def notifyowner(userid, md = True, warnings = 9):
    moderatorchan: discord.TextChannel = xcaisguild.get_channel(config["config"]["moderatorchannel"])
    target: discord.Member = xcaisguild.get_member(userid)
    
    if target is None:
        raise TypeError("Target is NoneType")
    else:
        if md:
            embed = discord.Embed(
                color=discord.Color.red(),
                title=f"**{target.name}** has reached {warnings} warnings",
                description=f"""{xcaisguild.get_role(config["config"]["moderatorrole"]).mention}
                I am programmed to notify all moderators of this server to ask you for your consent to **permanently ban {target.name}** from the server due to the number of warnings received."""
            )
        else:
            embed = discord.Embed(
                color=discord.Color.red(),
                title=f"**{target.name}** has reached {warnings} warnings",
                description=f"""{xcaisguild.get_role(config["config"]["moderatorrole"]).mention}
                I am programmed to notify all moderators of this server to ask you for your consent to **temporarily ban {target.name} for one month** from the server due to the number of warnings received.""")

    await moderatorchan.send(embed=embed,view=BanView(userid,action=md))

@bot.tree.command(name="say",description="Sends a message")
@discord.app_commands.describe(message="Message to send", channel="To send message too")
async def send_message(interaction: discord.Interaction ,message: str, channel: discord.TextChannel):
    if not hasperm(interaction.user, config["permconfig"]["saycommands"]):
        embed = discord.Embed(color=discord.Color.red(), description="**You don't have access to this command**")
        await interaction.response.send_message(embed=embed, ephemeral=True)
        return
    await interaction.response.defer(ephemeral=True)
    await sendtoconsole(f"[SAY] [CHL: {channel.name}]: {message}")
    await channel.send(message)
    
    embed = discord.Embed(color=discord.Color.green(),title="**Sent**")
    
    await interaction.followup.send(embed=embed,ephemeral=True)

@bot.tree.command(name="senddm",description="Sends a message to a user")
@discord.app_commands.describe(message="Message to send", user="To send message too")
async def senddm(interaction: discord.Interaction, message: str, user: discord.Member):
    if not hasperm(interaction.user, config["permconfig"]["saycommands"]):
        embed = discord.Embed(color=discord.Color.red(), description="**You don't have access to this command**")
        await interaction.response.send_message(embed=embed, ephemeral=True)
        return
    await interaction.response.defer(ephemeral=True)
    if user.id == bot.user.id:
        embed = discord.Embed(color=discord.Color.red(),title="Error: i can't DM myself >:C")
        await interaction.followup.send(ephemeral=True,embed=embed)
    
    await sendtoconsole(f"[SENDDM] [TO: {user.name}]: {message}")
    await user.send(message)
    
    embed = discord.Embed(color=discord.Color.green(),title="**Sent**")
    
    await interaction.followup.send(embed=embed,ephemeral=True)
    
@bot.tree.command(name="send", description="Sends a message (Opens UI)")
@discord.app_commands.describe(channel="Channel to send message to")
async def sendlongmessage(interaction: discord.Interaction, channel: discord.TextChannel):
    if not hasperm(interaction.user, config["permconfig"]["saycommands"]):
        embed = discord.Embed(color=discord.Color.red(), description="**You don't have access to this command**")
        await interaction.response.send_message(embed=embed, ephemeral=True)
        return
    await interaction.response.send_modal(modals.SendTextModal(channel))

@bot.tree.command(name="sendfile", description="Sends the contents of the file (Text files only)")
@discord.app_commands.describe(file="File to send content from.",channel="Channel to send")
async def sendbyfile(interaction: discord.Interaction, file: discord.Attachment, channel: discord.TextChannel):
    await interaction.response.defer(ephemeral=True)
    
    if not hasperm(interaction.user, config["permconfig"]["saycommands"]):
        embed = discord.Embed(color=discord.Color.red(), description="**You don't have access to this command**")
        await interaction.response.send_message(embed=embed, ephemeral=True)
        return
    
    if not file is None:
        if not "text" in file.content_type:
            embed = discord.Embed(color=discord.Color.red(),title="Error: can't read that file format :c")
            await interaction.followup.send(ephemeral=True,embed=embed)
        else:
            await file.save("temp.txt")
            txt = open("temp.txt").read()
            
            await sendtoconsole(f"[SAY] [CHL: {channel.name}]: {txt}")
            
            await channel.send(txt)
            
            try: # If a error occures like temp.txt doesnt exist for some reason it just ignores it
                os.remove("temp.txt")
            except:
                pass
            
            embed = discord.Embed(color=discord.Color.green(),title="**Sent**")
    
            await interaction.followup.send(embed=embed,ephemeral=True)
    else:
        embed = discord.Embed(color=discord.Color.red(),title="Error: can't read that file format :c")
        await interaction.followup.send(ephemeral=True,embed=embed)

@bot.tree.command(name="version",description="Version of XCAIS")
async def version(interaction: discord.Interaction):
    
    embed = discord.Embed(color=discord.Color.orange(),title="XCAIS",description=f"""Xportation Corporation Automated Intercom System

Running Version: `{ver}`""")
    
    await interaction.response.send_message(embed=embed,ephemeral=True)

@bot.tree.command(name="warn",description="Warns a user")
@discord.app_commands.describe(user="User to warn",reason="Reason for the warning")
async def warn(interaction: discord.Interaction,user: discord.Member, reason: str):
    global warnhandler
    await interaction.response.defer()
    
    if not hasperm(interaction.user, config["permconfig"]["moderatorcommands"]):
        embed = discord.Embed(color=discord.Color.red(),description="**You dont have access to this command**")
        await interaction.followup.send(embed=embed,ephemeral=True)
        return None
    
    if user.id == bot.user.id:
        embed = discord.Embed(color=discord.Color.red(),title="**I cant warn myself >:C**")
        await interaction.followup.send(embed=embed,ephemeral=True)
        return None
    
    status = await warnhandler.addwarning(user.id,reason,interaction.user.id)
    await sendtoconsole(f"[WARN] {user.name} has been warned\n {reason} \n by {interaction.user.name}")
    
    if status["status"] == "warned":
        embed = discord.Embed(color=discord.Color.green(),title=f"**{user.name} has been warned**")
    elif status["status"] == "timeout":
        embed = discord.Embed(color=discord.Color.orange(),title=f"**{user.name} has been timed out**",description=f"""**{user.name}** has been timed out for {status['days']}""")
    elif status["status"] == "forbidden":
        embed = discord.Embed(color=discord.Color.green(),title=f"**{user.name} has been warned but could not be timed out**")
    elif status["status"] == "askowner_month_ban":
        embed = discord.Embed(color=discord.Color.red(),title=f"**{xcaisguild.get_member(config['config']['owner']).name} has been notifed about your many warnings**")
        await notifyowner(user.id,md=False)
    elif status["status"] == "askowner_perm_ban":
        embed = discord.Embed(color=discord.Color.red(),title=f"**{xcaisguild.get_member(config['config']['owner']).name} has been notifed about your many warnings**")
        await notifyowner(user.id,md=True)
    else:
        pass
    await interaction.followup.send(embed=embed,ephemeral=True)

@bot.tree.command(name="warns",description="View warns")
@discord.app_commands.describe(user="User to check warnings for (optional)")
async def warns(interaction: discord.Interaction, user: discord.Member = None):
    global warnhandler
    await interaction.response.defer()
    
    if user is None:
        user = interaction.user
    
    if user.id == bot.user.id:
        embed = discord.Embed(color=discord.Color.red(),title="**I cant warn myself >:C**")
        await interaction.followup.send(embed=embed,ephemeral=True)
        return None
    
    userd: User = await warnhandler.getuser(user.id)
    if len(userd.warns) == 0:
        embed = discord.Embed(color=discord.Color.orange(), title=f"**{user.name} has 0 warnings**",description=f"""**{user.name}** has **{len(userd.warns)} warnings**
**{userd.max_warnings_before_timeout - len(userd.warns)}** More warnings until next punish ment (You are in the safe for now :) )""")
    else:
        embed = discord.Embed(color=discord.Color.orange(), title=f"**Warnings for {user.name}**",description=f"""**{user.name}** has **{len(userd.warns)} warnings**
**{userd.max_warnings_before_timeout - len(userd.warns)}** More warnings until more suffering :3""")
        for i in userd.warns:
            embed.add_field(name=f"Moderator: {interaction.guild.get_member(i.assignedby).global_name}",value=f"""{i.reason} - <t:{int(i.timestamp)}:R>""",inline=False)
    
    await interaction.followup.send(embed=embed, ephemeral=True, view=DeleteWarnView(user,zerowarns=len(userd.warns) == 0))

@bot.tree.command(name="purge", description="Purges a number of messages from a channel")
@discord.app_commands.describe(amount="Number of messages to delete (Max 100)", channel="Channel to purge messages from", user="User whose messages to delete (optional)")
async def purge(interaction: discord.Interaction, amount: int, channel: discord.TextChannel = None, user: discord.Member = None):
    if not hasperm(interaction.user, config["permconfig"]["moderatorcommands"]):
        embed = discord.Embed(color=discord.Color.red(), description="**You don't have access to this command**")
        await interaction.response.send_message(embed=embed, ephemeral=True)
        return

    if channel is None:
        channel = interaction.channel

    await interaction.response.defer(ephemeral=True)
    
    def is_user(msg):
        result = msg.author == user
        print(f"Checking message: {msg.content}, Author: {msg.author}, Result: {result}")
        return result
    
    if user is None:
        deleted = await channel.purge(limit=amount)
    else:
        deleted = await channel.purge(limit=amount, check=is_user)
    
    embed = discord.Embed(color=discord.Color.green(), description=f"**Purged {len(deleted)} messages**")
    await interaction.followup.send(embed=embed, ephemeral=True)

@bot.tree.command(name="deletewarn", description="Deletes a warning")
@discord.app_commands.describe(user="User to delete warning from")
async def deletewarning(interaction: discord.Interaction, user: discord.Member):
    if not hasperm(interaction.user, config["permconfig"]["saycommands"]):
        embed = discord.Embed(color=discord.Color.red(), description="**You don't have access to this command**")
        await interaction.response.send_message(embed=embed, ephemeral=True)
        return
    
    await interaction.response.defer(ephemeral=True)
    
    warns = await warnhandler.getwarns(user.id)
    
    embed = discord.Embed(
                color=discord.Color.red(),
                title=f"{user.name} has {len(warns)} warnings",
                description="Select the warning from the drop menu below to delete"
            )
    
    await interaction.followup.send(embed=embed,view=DeleteWarnMenu(user,warns),ephemeral=True)

@bot.tree.command(name="clearwarns",description="Clears all")
@discord.app_commands.describe(user="User to delete warning from")
async def deletewarning(interaction: discord.Interaction, user: discord.Member):
    if not hasperm(interaction.user, config["permconfig"]["saycommands"]):
        embed = discord.Embed(color=discord.Color.red(), description="**You don't have access to this command**")
        await interaction.response.send_message(embed=embed, ephemeral=True)
        return
    
    await interaction.response.defer(ephemeral=True)
    
    embed = discord.Embed(title="Are you sure?",description=f"""You are about to clear all the warnings from **{user.name}**
Do you wish to proceed?""")
    await interaction.followup.send(embed=embed,ephemeral=True)

@bot.event
async def on_message(message: discord.Message):
    await bot.process_commands(message)
    
    if not message.author.id == bot.user.id:
        if not isinstance(message.channel,discord.DMChannel):
            await sendtoconsole(f"[MSG_SEND] [{message.channel.name}]: {message.author.name}: {message.content}")
        else:
            await sendtoconsole(f"[MSG_SEND] [**Direct Msg**]: {message.author.name}: {message.content}")

@bot.event
async def on_message_delete(message: discord.Message):
    if not message.author.id == bot.user.id:
        if not isinstance(message.channel,discord.DMChannel):
            await sendtoconsole(f"[MSG_DEL] [{message.channel.name}]: {message.author.name}: {message.content}")
        else:
            await sendtoconsole(f"[MSG_DEL] [**Direct Msg**]: {message.author.name}: {message.content}")

@bot.event
async def on_reaction_add(reaction: discord.Reaction, user: discord.Member):
    print(reaction.message.reactions)
    
    def checka():
        reaction_id = 1349975663871787038
        
        for react in reaction.message.reactions:
            if react.emoji.id == reaction_id and react.count >= 1:
                return True
        return False
    
    if reaction.emoji.id == 1248777821439004694:
        if reaction.count >= 2:
            if checka():
                pass
            else:
                msg: discord.Message = reaction.message
                chl: discord.TextChannel = xcaisguild.get_channel(config["config"]["xc_board"])
                await chl.send(content=f"**Message from {reaction.message.channel.name}:\n**"+msg.content, embeds=msg.embeds, files=[await attachment.to_file() for attachment in msg.attachments])
                await reaction.message.add_reaction(discord.PartialEmoji(name="success",id=1349975663871787038))
        
    await sendtoconsole(f"[REACTION_ADD] [{user.name}]: {reaction.emoji} to: {reaction.message.content}")

@bot.event
async def on_ready():
    global xcaisguild, consolechannel, warnhandler
    """Event handler for when the bot is ready."""
    
    xcaisguild = bot.get_guild(config["config"]["guild"])
    consolechannel = xcaisguild.get_channel(config["config"]["consolechannel"])
    print(f"Connected as {bot.user}")
    
    await sendtoconsole("Bot restarted syncing commands...")
    
    warnhandler = WarningHandler(config["config"]["data"],bot.get_guild(config["config"]["guild"]))
    await sendtoconsole("Warning handler thread started")
    
    c = await bot.tree.sync()
    print(f"Synced {len(c)} commands")

    await sendtoconsole(f"Synced {len(c)} slash commands.")
    await bot.change_presence(activity=discord.Game(name="XCAIS Online", type=5))

@bot.event
async def on_error(event: str, *args, **kwargs):
    global consolechannel
    if consolechannel is not None:
        error_message = f"[**INTERNAL ERROR OCCURRED**]: `{event}`\n```{traceback.format_exc()}```"
        await consolechannel.send(error_message)
        traceback.print_exc()
    else:
        print(f"Error in {event}:")
        traceback.print_exc()

@bot.tree.error
async def command_error(interaction: discord.Interaction, error: discord.app_commands.AppCommandError):
    embed = discord.Embed(title="An error occurred", description="An unexpected error has occurred")
    global consolechannel
    await interaction.followup.send(embed=embed, ephemeral=True)
    
    errortxt = traceback.format_exc()
    
    log_filename = f"{datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}.log"
    with open(log_filename, "w") as log_file:
        log_file.write(errortxt)
    
    if consolechannel is not None:
        error_message = f"[**INTERNAL ERROR OCCURRED**]: `{error}` Full traceback in log file attached"
        traceback.print_exc()
        await consolechannel.send(error_message, file=discord.File(log_filename, filename=log_filename, description="Error log"))
    else:
        traceback.print_exc()

    os.remove(log_filename)

def hasperm(userid: discord.Member, permlist: list[int]):
    if "everyone" in permlist:
        return True

    for role in userid.roles:
        if int(role.id) in permlist:
            return True
    return False

bot.run(token=open(os.path.join(config["config"]["secretspath"],"token.key"),"r").readline())