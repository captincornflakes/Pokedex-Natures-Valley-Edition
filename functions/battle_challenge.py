import discord
from discord.ext import commands
from discord import app_commands
from utils.battle_channel_utils import create_battle_channel, delete_battle_channel
import os
import json

class BattleChallenge(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="challenge", description="Challenge another user to a Pokémon battle!")
    @app_commands.describe(opponent="The user you want to challenge")
    async def challenge(self, interaction: discord.Interaction, opponent: discord.Member):
        if opponent.id == interaction.user.id:
            await interaction.response.send_message("You can't challenge yourself!", ephemeral=True)
            return
        if opponent.bot:
            await interaction.response.send_message("You can't challenge a bot!", ephemeral=True)
            return

        # Create the battle channel
        channel = await create_battle_channel(
            interaction.guild,
            interaction.user,
            opponent
        )
        await interaction.response.send_message(
            f"{opponent.mention}, you have been challenged to a Pokémon battle by {interaction.user.mention}!\n"
            f"Head to {channel.mention} to begin your battle!",
            ephemeral=False
        )

    @app_commands.command(name="endbattle", description="End the current Pokémon battle (only for participants).")
    async def endbattle(self, interaction: discord.Interaction):
        channel = interaction.channel
        guild = interaction.guild

        # Check if this channel is an active battle channel and if the user is a participant
        servers_dir = os.path.join(os.getcwd(), "servers")
        data_file = os.path.join(servers_dir, str(guild.id), "data.json")
        if not os.path.isfile(data_file):
            await interaction.response.send_message("No battle data found for this server.", ephemeral=True)
            return

        with open(data_file, "r", encoding="utf-8") as f:
            data = json.load(f)
        found = False
        for battle in data.get("active_battles", []):
            if battle["channel_id"] == channel.id and interaction.user.id in (battle["user1_id"], battle["user2_id"]):
                found = True
                break

        if not found:
            await interaction.response.send_message("You can only end a battle if you are a participant in this battle channel.", ephemeral=True)
            return

        await delete_battle_channel(guild, channel.id)
        await interaction.response.send_message("Battle ended and channel will be deleted.", ephemeral=False)

async def setup(bot):
    await bot.add_cog(BattleChallenge(bot))