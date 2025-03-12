import discord
from discord import ui

class SendTextModal(discord.ui.Modal, title="Send a message"):
    def __init__(self, channel: discord.TextChannel):
        super().__init__()
        self.channel = channel

        self.text = discord.ui.TextInput(
            label="Message to send",
            style=discord.TextStyle.paragraph,
            placeholder="I am XCAIS",
            max_length=4000
        )
        self.add_item(self.text)

    async def on_submit(self, interaction: discord.Interaction):
        await self.channel.send(self.text.value)
        embed = discord.Embed(color=discord.Color.green(),title="Sent!")
        await interaction.response.send_message(ephemeral=True,embed=embed)