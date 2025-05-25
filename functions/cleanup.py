import discord
from discord.ext import commands
import os
import shutil
from utils.server_handler import read_server_data, generate_pokemon_channels, send_welcome_embed, send_general_guide_embed, send_battle_guide_embed

class ServerCleanup(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_guild_remove(self, guild):
        print(f"[Listener] Bot removed from guild {guild.id}. Cleaning up Pokémon channels and data.")
        data = read_server_data(guild.id)
        # Delete channels listed in data.json
        if data and "channels" in data:
            channels = data["channels"]
            # Delete text channels
            for ch_name in ["guide", "general", "wild"]:
                ch_id = channels.get(ch_name)
                if ch_id:
                    channel = guild.get_channel(ch_id)
                    if channel:
                        try:
                            await channel.delete()
                            print(f"[Cleanup] Deleted channel '{ch_name}' ({ch_id}) in guild {guild.id}")
                        except Exception as e:
                            print(f"[Cleanup] Failed to delete channel '{ch_name}' ({ch_id}): {e}")
            # Delete category
            cat_id = channels.get("category")
            if cat_id:
                category = discord.utils.get(guild.categories, id=cat_id)
                if category:
                    try:
                        await category.delete()
                        print(f"[Cleanup] Deleted category ({cat_id}) in guild {guild.id}")
                    except Exception as e:
                        print(f"[Cleanup] Failed to delete category ({cat_id}): {e}")

        # Delete the server folder from the servers directory
        servers_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "servers")
        guild_folder = os.path.join(servers_dir, str(guild.id))
        if os.path.exists(guild_folder):
            try:
                shutil.rmtree(guild_folder)
                print(f"[Cleanup] Deleted server folder for guild {guild.id}")
            except Exception as e:
                print(f"[Cleanup] Failed to delete server folder for guild {guild.id}: {e}")
        else:
            print(f"[Cleanup] No server folder found for guild {guild.id}")

    @commands.Cog.listener()
    async def on_guild_join(self, guild):
        print(f"[Listener] Bot joined guild {guild.id}. Setting up Pokémon channels and guide embeds.")
        channels = await generate_pokemon_channels(guild)
        guide_channel = guild.get_channel(channels["guide"])
        if guide_channel:
            import asyncio
            await asyncio.sleep(5)
            bot = self.bot
            image_url = getattr(bot, "media", None)
            if image_url:
                image_url = f"{image_url}/professor_oak.png"
            await send_welcome_embed(guide_channel, image_url)
            await send_general_guide_embed(guide_channel, image_url)
            await send_battle_guide_embed(guide_channel)
            print(f"[Listener] Sent guide embeds to 'guide' channel in guild {guild.id}")

async def setup(bot):
    await bot.add_cog(ServerCleanup(bot))