import discord, os, sys, logging, yaml
from discord.ext.commands.bot import Bot
import modals
from datetime import datetime

# Creates config.yaml if it doesnt exist
if not os.path.exists("config.yaml"):
    f = open("config.yaml","w")
    f.write("""# Configuration for XCAIS
            
config:
    secretspath: ./secrets
    logfile: ./discord.log
    guild: 
    data: ./data
""")
    f.close()

config = yaml.safe_load(open("config.yaml"))
guild = config["config"]["guild"]

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
    

@bot.tree.command(name="say",description="Sends a message")
@discord.app_commands.describe(message="Message to send", channel="To send message too")
async def send_message(interaction: discord.Interaction ,message: str, channel: discord.TextChannel):
    await interaction.response.defer()
    await channel.send(message)
    
    embed = discord.Embed(color=discord.Color.green(),title="Sent!")
    
    await interaction.followup.send(embed=embed, ephemeral=True)

@bot.tree.command(name="senddm",description="Sends a message to a user")
@discord.app_commands.describe(message="Message to send", user="To send message too")
async def senddm(interaction: discord.Interaction, message: str, user: discord.Member):
    await interaction.response.defer()
    if user.id == bot.user.id:
        embed = discord.Embed(color=discord.Color.red(),title="Error: i can't DM myself >:C")
        await interaction.followup.send(ephemeral=True,embed=embed)
    
    await user.send(message)
    
    embed = discord.Embed(color=discord.Color.green(),title="Sent!")
    
    await interaction.followup.send(ephemeral=True,embed=embed)
    
@bot.tree.command(name="send", description="Sends a message (Opens UI)")
@discord.app_commands.describe(channel="Channel to send message to")
async def sendlongmessage(interaction: discord.Interaction, channel: discord.TextChannel):
    await interaction.response.send_modal(modals.SendTextModal(channel))

@bot.tree.command(name="sendfile", description="Sends the contents of the file (Text files only)")
@discord.app_commands.describe(file="File to send content from.",channel="Channel to send")
async def sendbyfile(interaction: discord.Interaction, file: discord.Attachment, channel: discord.TextChannel):
    await interaction.response.defer()
    if not file is None:
        if not "text" in file.content_type:
            embed = discord.Embed(color=discord.Color.red(),title="Error: can't read that file format :c")
            await interaction.followup.send(ephemeral=True,embed=embed)
        else:
            await file.save("temp.txt")
            txt = open("temp.txt").read()
            await channel.send(txt)
            
            try: # If a error occures like temp.txt doesnt exist for some reason it just ignores it
                os.remove("temp.txt")
            except:
                pass
            
            embed = discord.Embed(color=discord.Color.green(),title="Sent!")
            await interaction.followup.send(ephemeral=True,embed=embed)
    else:
        embed = discord.Embed(color=discord.Color.red(),title="Error: can't read that file format :c")
        await interaction.followup.send(ephemeral=True,embed=embed)



@bot.event
async def on_message(message: discord.Message):
    pass

@bot.event
async def on_ready():
    """Event handler for when the bot is ready."""
    print(f"Connected as {bot.user}")
    c = await bot.tree.sync()
    print(f"Synced {len(c)} commands")
    

    
bot.run(token=open(os.path.join(config["config"]["secretspath"],"token.key"),"r").readline())