import os
import json
import discord
import random
from utils.player_handler import add_pokemon_to_player, read_user_record
from utils.spawn_utils import update_active_spawn_status, update_wild_pokemon_message

def calculate_capture_success(player_power, pokemon_cp):
    if player_power <= 0 or pokemon_cp <= 0:
        print(f"[CAPTURE] Invalid values: player_power={player_power}, pokemon_cp={pokemon_cp} -> False")
        return False
    success_chance = min(0.95, max(0.05, player_power / (player_power + pokemon_cp)))
    roll = random.random()
    result = roll < success_chance
    print(f"[CAPTURE] player_power={player_power}, pokemon_cp={pokemon_cp}, success_chance={success_chance:.2f}, roll={roll:.2f} -> {result}")
    return result

class CaptureButton(discord.ui.View):
    def __init__(self, guild_id, pokemon_id):
        super().__init__(timeout=180)
        self.guild_id = guild_id
        self.pokemon_id = pokemon_id
        self.message = None  # Will hold the sent message object

    @discord.ui.button(label="Capture Pokémon", style=discord.ButtonStyle.green)
    async def capture(self, interaction: discord.Interaction, button: discord.ui.Button):
        trainer_name = interaction.user.display_name
        user_id = interaction.user.id
        guild_id = self.guild_id
        pokemon_id = self.pokemon_id

        servers_dir = os.path.join(os.getcwd(), "servers")
        data_file = os.path.join(servers_dir, str(guild_id), "data.json")
        if not os.path.isfile(data_file):
            await interaction.response.send_message("Server data not found.", ephemeral=True)
            return
        with open(data_file, "r", encoding="utf-8") as f:
            data = json.load(f)
        spawn = data.get("active_spawn")
        if not spawn or spawn.get("id") != pokemon_id or spawn.get("status") != "active":
            # Remove the capture button if the Pokémon has left the area
            await interaction.response.edit_message(
                content="The Pokémon has left the area!",
                view=None  # This removes all buttons
            )
            return

        user_data = read_user_record(guild_id, user_id)
        if user_data is None:
            await interaction.response.send_message("You need to set up your profile first with `/join`.", ephemeral=True)
            return

        player_power = user_data.get("power", 0)
        bot = interaction.client
        pokemon_obj = next((p for p in bot.pokemon if p.get("id") == pokemon_id), None)
        if not pokemon_obj:
            await interaction.response.send_message("Pokémon data not found.", ephemeral=True)
            return
        pokemon_cp = pokemon_obj.get("cp", 100)

        success = calculate_capture_success(player_power, pokemon_cp)
        if success:
            update_active_spawn_status(guild_id, pokemon_id, "captured", trainer_name)
            # Update the wild Pokémon message to show it was caught
            await update_wild_pokemon_message(
                bot,
                guild_id,
                status_message=f"🎉 {trainer_name} successfully captured {pokemon_obj.get('name', 'the Pokémon')}!"
            )
            result = await add_pokemon_to_player(bot, guild_id, user_id, pokemon_id, interaction)
            if result == "duplicate":
                await interaction.response.edit_message(
                    content=f"You already have {pokemon_obj.get('name', 'the Pokémon')} in your active team!",
                    view=None
                )
                return
            elif result == "not_found":
                await interaction.response.edit_message(
                    content="Pokémon data not found.",
                    view=None
                )
                return
            elif result == "full":
                await interaction.response.edit_message(
                    content="Your active team is full and no replacement was made.",
                    view=None
                )
                return
            elif result == "timeout":
                await interaction.response.edit_message(
                    content="No selection made. Pokémon not added.",
                    view=None
                )
                return
            # If "success", continue with your normal capture success flow
            await interaction.response.edit_message(
                content=f"🎉 {trainer_name} successfully captured {pokemon_obj.get('name', 'the Pokémon')}!",
                view=None
            )
            await interaction.channel.send(
                f"{trainer_name} captured {pokemon_obj.get('name', 'the Pokémon')}!"
            )
        else:
            update_active_spawn_status(guild_id, pokemon_id, "escaped", trainer_name)
            await interaction.response.edit_message(
                content=f"{pokemon_obj.get('name', 'The Pokémon')} broke free! Better luck next time, {trainer_name}.",
                view=None  # This removes all buttons
            )
            await interaction.channel.send(
                f"{trainer_name} tried to capture {pokemon_obj.get('name', 'the Pokémon')}, but it escaped!"
            )

    async def on_timeout(self):
        # Remove the button and update the message if the Pokémon is still active
        servers_dir = os.path.join(os.getcwd(), "servers")
        data_file = os.path.join(servers_dir, str(self.guild_id), "data.json")
        if os.path.isfile(data_file):
            with open(data_file, "r", encoding="utf-8") as f:
                data = json.load(f)
            spawn = data.get("active_spawn")
            if spawn and spawn.get("id") == self.pokemon_id and spawn.get("status") == "active":
                from utils.spawn_utils import update_active_spawn_status
                update_active_spawn_status(self.guild_id, self.pokemon_id, "escaped", "System")
                # Edit the message to remove the button and show that the Pokémon left
                if self.message:
                    try:
                        await self.message.edit(
                            content="The Pokémon has left the area!",
                            view=None
                        )
                    except Exception as e:
                        print(f"[Timeout Edit Error] {e}")
        await super().on_timeout()