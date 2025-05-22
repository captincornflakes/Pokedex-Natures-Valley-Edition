import discord
from discord.ext import commands
from discord import app_commands
from utils.server_handler import generate_pokemon_channels

class ServerSetup(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="setup", description="Initializes server save data for this guild.")
    async def setup_server(self, interaction: discord.Interaction):
        if not interaction.user.guild_permissions.administrator:
            await interaction.response.send_message("You must be an administrator to use this command.", ephemeral=True)
            return
        folder_path = await generate_pokemon_channels(interaction.guild)
        await interaction.response.send_message(f"Server data folder created and channels set up.", ephemeral=True)

async def setup(bot):
    await bot.add_cog(ServerSetup(bot))