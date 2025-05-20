import discord
from discord.ext import commands
from discord import app_commands
from discord.ui import View, Select

class Help(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="help", description="help function.")
    @app_commands.default_permissions(administrator=True)
    async def help_command(self, interaction: discord.Interaction):
        # Create an embed for the help message
        embed = discord.Embed(
            title="Bot Commands",
            description="Here is a list of available commands:",
            color=discord.Color.blue()
        )
        for command in self.bot.tree.walk_commands():
            embed.add_field(
                name=f"/{command.name}", 
                value=command.description or "No description", 
                inline=False
            )
        embed.add_field(name="Discord Server", value="[Join our Discord](https://discord.gg/dWspvErgSt)", inline=False)
        embed.add_field(name="Website", value="[Visit our Website](https://echodebates.com)", inline=False)
        await interaction.response.send_message(embed=embed)

async def setup(bot):
    await bot.add_cog(Help(bot))
