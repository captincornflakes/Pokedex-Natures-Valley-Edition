import discord
from discord.ext import commands
from discord import app_commands
from utils.inventory_utils import add_item_to_inventory, get_player_inventory

def get_item_data(bot, item_id):
    # Use bot.items, which should be a list of item dicts
    for item in getattr(bot, "items", []):
        if item["id"] == item_id:
            return item
    return {"name": f"Item #{item_id}", "description": "No description."}

class InventoryCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="give", description="Give an item to a player by user, item ID, and amount.")
    @app_commands.describe(
        user="The user to give the item to",
        item_id="The item ID (number)",
        amount="The amount to give"
    )
    async def give(self, interaction: discord.Interaction, user: discord.Member, item_id: int, amount: int = 1):
        if not interaction.user.guild_permissions.administrator:
            await interaction.response.send_message("You must be an administrator to use this command.", ephemeral=True)
            return
        if amount < 1:
            await interaction.response.send_message("Amount must be at least 1.", ephemeral=True)
            return
        add_item_to_inventory(interaction.guild.id, user.id, item_id, amount)
        item_data = get_item_data(self.bot, item_id)
        await interaction.response.send_message(
            f"Gave {amount} × **{item_data['name']}** to {user.mention}.", ephemeral=True
        )

    @app_commands.command(name="inventory", description="View a player's inventory.")
    @app_commands.describe(
        user="The user whose inventory you want to view"
    )
    async def inventory(self, interaction: discord.Interaction, user: discord.Member = None):
        if not interaction.user.guild_permissions.administrator:
            await interaction.response.send_message("You must be an administrator to use this command.", ephemeral=True)
            return
        user = user or interaction.user
        inventory = get_player_inventory(interaction.guild.id, user.id)
        if not inventory:
            await interaction.response.send_message(f"{user.display_name} has no items.", ephemeral=True)
            return

        # Use bot.items for item names and descriptions
        item_lookup = {item["id"]: item for item in getattr(self.bot, "items", [])}

        lines = []
        for entry in inventory:
            item = item_lookup.get(entry["id"], {"name": f"Item #{entry['id']}", "description": "No description."})
            lines.append(f"**{item['name']}** × {entry['amount']}\n*{item['description']}*")
        embed = discord.Embed(
            title=f"{user.display_name}'s Inventory",
            description="\n\n".join(lines),
            color=discord.Color.blurple()
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)

async def setup(bot):
    await bot.add_cog(InventoryCog(bot))