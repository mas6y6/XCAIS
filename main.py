import time
import traceback
import discord, os, sys, logging, yaml
from discord.ext.commands.bot import Bot
import modals
from datetime import datetime
from warnshandler import WarningHandler, Warning
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

permconfig:
    # Include the ID's to the roles to give moderator commands too
    # If left empty it will use @everyone

    moderatorcommands: []

    saycommands: []



""")
    f.close()

config = yaml.safe_load(open("config.yaml"))
guild = config["config"]["guild"]

# Bot version
ver = "v0.1.3-alpha"

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

async def sendtoconsole(text: str,embed=None):
    global consolechannel
    
    t = f"<t:{int(time.time())}:R> [**{bot.user.display_name}**]: {text}"
    
    await consolechannel.send(t,embed=None)

@bot.tree.command(name="say",description="Sends a message")
@discord.app_commands.describe(message="Message to send", channel="To send message too")
async def send_message(interaction: discord.Interaction ,message: str, channel: discord.TextChannel):
    await interaction.response.defer(ephemeral=True)
    await sendtoconsole(f"[SAY] [CHL: {channel.name}]: {message}")
    await channel.send(message)
    
    embed = discord.Embed(color=discord.Color.green(),title="**Sent**")
    
    await interaction.followup.send(embed=embed,ephemeral=True)

@bot.tree.command(name="senddm",description="Sends a message to a user")
@discord.app_commands.describe(message="Message to send", user="To send message too")
async def senddm(interaction: discord.Interaction, message: str, user: discord.Member):
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
    await interaction.response.send_modal(modals.SendTextModal(channel))

@bot.tree.command(name="sendfile", description="Sends the contents of the file (Text files only)")
@discord.app_commands.describe(file="File to send content from.",channel="Channel to send")
async def sendbyfile(interaction: discord.Interaction, file: discord.Attachment, channel: discord.TextChannel):
    await interaction.response.defer(ephemeral=True)
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
    
    if not hasperm(user, config["permconfig"]["moderatorcommands"]):
        embed = discord.Embed(color=discord.Color.red(),title="**You dont have access to this command**")
        await interaction.followup.send(embed=embed,ephemeral=True)
        return None
    
    status = await warnhandler.addwarning(user.id,reason,interaction.user.id)
    await sendtoconsole(f"[WARN] {user.name} has been warned\n {reason} \n by {interaction.user.name}")
    
    if status["status"] == "warned":
        embed = discord.Embed(color=discord.Color.green(),title=f"**{user.name} has been warned**")
    elif status["status"] == "timeout":
        embed = discord.Embed(color=discord.Color.orange(),title=f"**{user.name} has been timed out**",description=f"""**{user.name}** has been timed out for {status["days"]}""")
    elif status["status"] == "forbidden":
        embed = discord.Embed(color=discord.Color.green(),title=f"**{user.name} has been warned but could not be timed out**")
    elif status["status"] == "askowner_month_ban":
        embed = discord.Embed(color=discord.Color.red(),title=f"**{xcaisguild.get_member(config["config"]["owner"]).name} has been notifed about your many warnings**")
    elif status["status"] == "askowner_perm_ban":
        embed = discord.Embed(color=discord.Color.red(),title=f"**{xcaisguild.get_member(config["config"]["owner"]).name} has been notifed about your many warnings**")
        await 
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
    
    warnings: list[Warning] = await warnhandler.getwarns(user.id)
    if len(warnings) == 0:
        embed = discord.Embed(color=discord.Color.orange(), title=f"**{user.name} has no warnings**")
    else:
        embed = discord.Embed(color=discord.Color.orange(), title=f"**Warnings for {user.name}**",description=f"**{user.name}** has **{len(warnings)} warnings**")
        for i in warnings:
            embed.add_field(name=f"Moderator: {interaction.guild.get_member(i.assignedby).global_name}",value=f"""{i.reason} - <t:{int(i.timestamp)}:R>""",inline=False)
    
    await interaction.followup.send(embed=embed, ephemeral=True)

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
async def on_ready():
    global xcaisguild, consolechannel, warnhandler
    """Event handler for when the bot is ready."""
    
    xcaisguild = bot.get_guild(config["config"]["guild"])
    consolechannel = xcaisguild.get_channel(config["config"]["consolechannel"])
    print(f"Connected as {bot.user}")
    
    await sendtoconsole("Bot restarted syncing commands...")
    
    c = await bot.tree.sync()
    print(f"Synced {len(c)} commands")

    await sendtoconsole(f"Synced {len(c)} slash commands.")
    await sendtoconsole("Starting warning handler")
    warnhandler = WarningHandler(config["config"]["data"],bot.get_guild(config["config"]["guild"]))
    await sendtoconsole("Warning handler thread started")

@bot.event
async def on_error(event: str, *args, **kwargs):
    global consolechannel
    if consolechannel is not None:
        error_message = f"[**INTERNAL ERROR OCCURRED**]: `{event}`\n```{traceback.format_exc()}```"
        await consolechannel.send(error_message)
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
    

def hasperm(userid: discord.Member,permlist: list[int]):
    if "everyone" in permlist:
        return True
    
    for role in userid.roles:
        if role.id in permlist:
            return True
    return False

bot.run(token=open(os.path.join(config["config"]["secretspath"],"token.key"),"r").readline())