import discord
from discord.ext import commands
from discord import app_commands
from utils.wild_utils import log_active_spawn, generate_wild_pokemon
from utils.capture_utils import CaptureButton

class ForceSpawn(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="forcespawn", description="Force spawn a wild Pokémon in the server's wild channel (admin only).")
    @app_commands.checks.has_permissions(administrator=True)
    async def force_spawn(self, interaction: discord.Interaction):
        guild_id = str(interaction.guild.id)
        servers_dir = "servers"
        data_file = f"{servers_dir}/{guild_id}/data.json"

        # Load server data
        try:
            with open(data_file, "r", encoding="utf-8") as f:
                data = __import__("json").load(f)
        except Exception:
            await interaction.response.send_message("Server data not found or not set up.", ephemeral=True)
            return

        channels = data.get("channels", {})
        wild_channel_id = channels.get("wild")
        if not wild_channel_id:
            await interaction.response.send_message("Wild channel not set up for this server.", ephemeral=True)
            return

        # Ignore if there is currently one active
        active_spawn = data.get("active_spawn")
        if active_spawn and active_spawn.get("status") == "active":
            await interaction.response.send_message("A wild Pokémon is already active! Wait until it is captured or escapes.", ephemeral=True)
            return

        # Generate and log a wild Pokémon
        pokemon_id = generate_wild_pokemon(self.bot)
        pokemon = next((p for p in self.bot.pokemon if p.get("id") == pokemon_id), None)
        if not pokemon:
            await interaction.response.send_message("Failed to generate a Pokémon.", ephemeral=True)
            return

        log_active_spawn(guild_id, pokemon_id, status="active", trainer=None)

        # Build the embed
        name = pokemon.get("name", "Unknown")
        poke_type = ", ".join(pokemon.get("type", []))
        rarity = pokemon.get("rarity", "Unknown")
        abilities = ", ".join(pokemon.get("special_abilities", []))
        embed = discord.Embed(
            title=f"A wild {name} appeared!",
            color=discord.Color.green()
        )
        embed.add_field(name="Type", value=poke_type or "Unknown", inline=True)
        embed.add_field(name="Rarity", value=rarity, inline=True)
        embed.add_field(name="Abilities", value=abilities or "Unknown", inline=False)

        channel = self.bot.get_channel(int(wild_channel_id))
        if channel:
            view = CaptureButton(guild_id, pokemon_id)
            await channel.send(embed=embed, view=view)
            await interaction.response.send_message(f"Forced a wild {name} to spawn in <#{wild_channel_id}>.", ephemeral=True)
        else:
            await interaction.response.send_message("Wild channel not found.", ephemeral=True)

    async def cog_app_command_error(self, interaction: discord.Interaction, error):
        if isinstance(error, app_commands.errors.MissingPermissions):
            await interaction.response.send_message("You do not have permission to use this command.", ephemeral=True)
        else:
            await interaction.response.send_message(f"An error occurred: {error}", ephemeral=True)

async def setup(bot):
    await bot.add_cog(ForceSpawn(bot))