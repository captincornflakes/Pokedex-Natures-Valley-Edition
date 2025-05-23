import discord
from discord.ext import commands
from discord import app_commands
from utils.player_handler import read_user_record

class Pokedex(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.pokemon = bot.pokemon

    @app_commands.command(name="pokedex", description="Show your Pokédex progress.")
    @app_commands.describe(page="Page number (20 Pokémon per page)")
    async def pokedex(self, interaction: discord.Interaction, page: int = 1):
        print(f"[DEBUG] /pokedex called by user {interaction.user.id} in guild {interaction.guild.id} (page {page})")
        user_data = read_user_record(interaction.guild.id, interaction.user.id)
        if not user_data:
            print("[DEBUG] No user data found.")
            await interaction.response.send_message("You need to set up your profile first with `/join`.", ephemeral=True)
            return

        pokedex_ids = set(user_data.get("pokedex", []))
        print(f"[DEBUG] User has {len(pokedex_ids)} Pokémon in their Pokédex.")

        pokemon_data = self.pokemon
        print(f"[DEBUG] Loaded {len(pokemon_data)} Pokémon from self.pokemon.")

        per_page = 50
        total_pokemon = len(pokemon_data)
        max_page = (total_pokemon + per_page - 1) // per_page
        print(f"[DEBUG] Total Pokémon: {total_pokemon}, Pages: {max_page}")
        if page < 1 or page > max_page:
            print(f"[DEBUG] Invalid page: {page}")
            await interaction.response.send_message(f"Invalid page. Please choose a page between 1 and {max_page}.", ephemeral=True)
            return

        start = (page - 1) * per_page
        end = start + per_page
        page_pokemon = pokemon_data[start:end]
        print(f"[DEBUG] Showing Pokémon {start} to {end} (actual: {len(page_pokemon)})")

        # Each Pokémon on a new line, show id and data if caught, else 5 question marks
        lines = []
        for p in page_pokemon:
            poke_id = p.get("id", "?")
            if poke_id in pokedex_ids:
                name = p.get("name", "?")
                poke_type = ", ".join(p.get("type", []))
                rarity = p.get("rarity", "?")
                lore = p.get("lore", "")
                name_display = f"**{name}**"
                line = f"#{poke_id} {name_display} [{poke_type}, {rarity}]"
                if lore:
                    line += f"\n    *{lore}*"
            else:
                line = f"#{poke_id} ? ? ? ? ?"
            lines.append(line)

        pokedex_str = "\n".join(lines)

        print("[DEBUG] Sending pokedex to user.")
        try:
            await interaction.response.send_message(
                f"**Your Pokédex Progress (Page {page}/{max_page}):**\n"
                f"{pokedex_str}",
                ephemeral=True
            )
        except Exception as e:
            print(f"[ERROR] Failed to send pokedex: {e}")
            await interaction.followup.send(
                "Pokédex could not be displayed. Try a higher page number or contact the bot owner.",
                ephemeral=True
            )

async def setup(bot):
    await bot.add_cog(Pokedex(bot))