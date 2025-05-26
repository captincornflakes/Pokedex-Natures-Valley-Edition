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

        per_page = 20  # Limit to 25 per page
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
                    line += f"\n*{lore}*"
            else:
                line = f"#{poke_id} ? ? ? ? ?"
            lines.append(line)

        pokedex_str = "\n\n".join(lines)
        header = f"**Your Pokédex Progress (Page {page}/{max_page}):**"

        # Discord embed field value limit is 1024, description limit is 4096
        if len(pokedex_str) > 4000:
            pokedex_str = pokedex_str[:4000] + "\n... (truncated)"

        embed = discord.Embed(
            title=f"Pokédex Progress (Page {page}/{max_page})",
            description=pokedex_str,
            color=discord.Color.green()
        )
        embed.set_footer(text=f"Showing {start+1}-{min(end, total_pokemon)} of {total_pokemon} Pokémon")

        print("[DEBUG] Sending pokedex to user (embed).")
        try:
            await interaction.response.send_message(embed=embed, ephemeral=True)
        except Exception as e:
            print(f"[ERROR] Failed to send pokedex as embed: {e}")
            # Fallback to plain text
            try:
                await interaction.followup.send(
                    f"{header}\n{pokedex_str}",
                    ephemeral=True
                )
            except Exception as e2:
                print(f"[ERROR] Failed to send pokedex as text: {e2}")

    @app_commands.command(name="pokedex_summary", description="Show your or another user's Pokédex summary and profile.")
    @app_commands.describe(user="The user whose Pokédex summary you want to view (leave blank for yourself)")
    async def pokedex_summary(self, interaction: discord.Interaction, user: discord.Member = None):
        target_user = user or interaction.user
        print(f"[DEBUG] /pokedex_summary called by user {interaction.user.id} in guild {interaction.guild.id} (target: {target_user.id})")
        user_data = read_user_record(interaction.guild.id, target_user.id)
        if not user_data:
            if user:
                await interaction.response.send_message(f"{target_user.display_name} has not set up their profile yet.", ephemeral=True)
            else:
                await interaction.response.send_message("You need to set up your profile first with `/join`.", ephemeral=True)
            return

        pokedex_ids = set(user_data.get("pokedex", []))
        total_discovered = len(pokedex_ids)
        total_pokemon = len(self.pokemon)

        # Profile fields
        profile_name = user_data.get("nickname") or target_user.display_name
        coin = user_data.get("coin", 0)
        gender = user_data.get("gender", "Not set")
        pronouns = user_data.get("pronouns", "Not set")
        power = user_data.get("power", 0)
        badges = user_data.get("badges", [])
        inventory = user_data.get("inventory", [])
        active_pokemon = user_data.get("active_pokemon", [])

        embed = discord.Embed(
            title=f"{profile_name}'s Pokédex Summary",
            color=discord.Color.blue()
        )
        embed.add_field(name="Pokémon Discovered", value=f"{total_discovered} / {total_pokemon}", inline=False)
        embed.add_field(name="Coin", value=f"${coin}", inline=True)
        embed.add_field(name="Power", value=str(power), inline=True)
        embed.add_field(name="Gender", value=gender, inline=True)
        embed.add_field(name="Pronouns", value=pronouns, inline=True)

        # Inventory (show item names, amounts, and descriptions using bot.items)
        if inventory:
            item_lookup = {item["id"]: item for item in getattr(self.bot, "items", [])}
            inventory_lines = []
            for entry in inventory:
                item = item_lookup.get(entry["id"], {"name": f"Item #{entry['id']}", "description": "No description."})
                inventory_lines.append(f"**{item['name']}** × {entry['amount']}\n*{item['description']}*")
            inventory_str = "\n\n".join(inventory_lines)
        else:
            inventory_str = "None"
        embed.add_field(name="Inventory", value=inventory_str, inline=False)

        # Badges
        if badges:
            badges_str = ", ".join(str(badge) for badge in badges)
        else:
            badges_str = "None"
        embed.add_field(name="Badges", value=badges_str, inline=False)

        # Active Pokémon
        if active_pokemon:
            active_lines = []
            for poke in active_pokemon:
                poke_name = poke.get("name", "?")
                poke_type = ", ".join(poke.get("type", []))
                poke_cp = poke.get("cp", "?")
                poke_hp = poke.get("hp", "?")
                active_lines.append(f"**{poke_name}** [{poke_type}] (CP: {poke_cp}, HP: {poke_hp})")
            embed.add_field(
                name="Active Pokémon",
                value="\n".join(active_lines),
                inline=False
            )
        else:
            embed.add_field(name="Active Pokémon", value="None", inline=False)

        embed.set_footer(text="Use /pokedex to view your full Pokédex.")

        await interaction.response.send_message(embed=embed, ephemeral=True)

async def setup(bot):
    await bot.add_cog(Pokedex(bot))