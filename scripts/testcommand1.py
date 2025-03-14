
@bot.command(name="test")
async def testcommand(ctx: discord.ext.commands.Context, userid: int):
    moderatorchan: discord.TextChannel = xcaisguild.get_channel(config["config"]["moderatorchannel"])
    target: discord.Member = xcaisguild.get_member(userid)
    warnings = 9
    
    embed = discord.Embed(
                color=discord.Color.red(),
                title=f"**{target.name}** has reached 9 warnings",
                description=f"""{xcaisguild.get_role(config["config"]["moderatorrole"]).mention}
                I am programmed to notify all moderators of this server to ask you for your consent to **temporarily ban {target.name} for one month** from the server due to the number of warnings received.""")
    await moderatorchan.send(embed=embed,view=BanView(userid))