import discord
from discord.ext import commands
from discord import app_commands
from utils.player_handler import read_user_record, remove_active_pokemon

class RemovePokemonButton(discord.ui.Button):
    def __init__(self, idx, poke_name):
        super().__init__(label=f"Remove #{idx+1} ({poke_name})", style=discord.ButtonStyle.danger, custom_id=f"remove_{idx}")
        self.idx = idx

    async def callback(self, interaction: discord.Interaction):
        # Ask for confirmation
        view = ConfirmRemoveView(self.idx)
        await interaction.response.send_message(
            f"Are you sure you want to remove Pokémon #{self.idx+1}? This cannot be undone.",
            view=view,
            ephemeral=True
        )

class ConfirmRemoveView(discord.ui.View):
    def __init__(self, idx):
        super().__init__(timeout=30)
        self.idx = idx
        self.value = None

    @discord.ui.button(label="Confirm Remove", style=discord.ButtonStyle.danger)
    async def confirm(self, interaction: discord.Interaction, button: discord.ui.Button):
        guild_id = interaction.guild.id
        user_id = interaction.user.id
        success = remove_active_pokemon(guild_id, user_id, self.idx)
        if success:
            await interaction.response.edit_message(content=f"Pokémon #{self.idx+1} has been removed from your active team.", view=None)
        else:
            await interaction.response.edit_message(content="Failed to remove Pokémon. It may have already been removed.", view=None)
        self.value = True
        self.stop()

    @discord.ui.button(label="Cancel", style=discord.ButtonStyle.secondary)
    async def cancel(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.edit_message(content="Removal cancelled.", view=None)
        self.value = False
        self.stop()

class ActivePokemon(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="active", description="Show your active Pokémon team and their stats.")
    async def active(self, interaction: discord.Interaction):
        user_data = read_user_record(interaction.guild.id, interaction.user.id)
        if not user_data or not user_data.get("active_pokemon"):
            await interaction.response.send_message("You have no active Pokémon. Use `/starter` to get started!", ephemeral=True)
            return

        active_pokemon = user_data["active_pokemon"]
        # Build a table of stats
        headers = ["#", "Name", "Type", "CP", "HP", "Atk", "Def", "Rarity"]
        rows = []
        for idx, poke in enumerate(active_pokemon, 1):
            rows.append([
                str(idx),
                poke.get("name", "Unknown"),
                ", ".join(poke.get("type", [])),
                str(poke.get("cp", "")),
                str(poke.get("hp", "")),
                str(poke.get("attack", "")),
                str(poke.get("defense", "")),
                poke.get("rarity", "")
            ])

        # Format as a code block table
        col_widths = [max(len(str(row[i])) for row in [headers] + rows) for i in range(len(headers))]
        def format_row(row):
            return " | ".join(str(cell).ljust(col_widths[i]) for i, cell in enumerate(row))
        table = [format_row(headers)]
        table.append("-+-".join("-" * w for w in col_widths))
        table += [format_row(row) for row in rows]
        table_str = "```\n" + "\n".join(table) + "\n```"
        # Add a remove button for each Pokémon, but only if more than 1 Pokémon
        view = discord.ui.View(timeout=120)
        if len(active_pokemon) > 1:
            for idx, poke in enumerate(active_pokemon):
                view.add_item(RemovePokemonButton(idx, poke.get("name", f"#{idx+1}")))

        await interaction.response.send_message(
            f"**Your Active Pokémon:**\n{table_str}\n\n"
            + ("To remove a Pokémon, press the corresponding button below." if len(active_pokemon) > 1 else ""),
            view=view if len(active_pokemon) > 1 else None,
            ephemeral=True
        )

async def setup(bot):
    await bot.add_cog(ActivePokemon(bot))