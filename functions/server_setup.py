import discord
from discord.ext import commands
from discord import app_commands
from utils.server_handler import generate_pokemon_channels, send_welcome_embed, send_general_guide_embed, send_battle_guide_embed

class ServerSetup(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="setup", description="Initializes server save data for this guild.")
    async def setup_server(self, interaction: discord.Interaction):
        if not interaction.user.guild_permissions.administrator:
            await interaction.response.send_message("You must be an administrator to use this command.", ephemeral=True)
            return
        channels = await generate_pokemon_channels(interaction.guild)
        await interaction.response.send_message(f"Server data folder created and channels set up.", ephemeral=True)

        # Post guide embeds to the guide channel after setup
        guide_channel = interaction.guild.get_channel(channels["guide"])
        if guide_channel:
            # Optional: Wait a moment to ensure permissions propagate
            import asyncio
            await asyncio.sleep(5)
            bot = interaction.client
            image_url = getattr(bot, "media", None)
            if image_url:
                image_url = f"{image_url}/professor_oak.png"
            await send_welcome_embed(guide_channel, image_url)
            await send_general_guide_embed(guide_channel, image_url)
            await send_battle_guide_embed(guide_channel)

async def setup(bot):
    await bot.add_cog(ServerSetup(bot))
