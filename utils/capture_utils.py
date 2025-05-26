import os
import json
import discord
import random
from utils.player_handler import add_pokemon_to_player, read_user_record, add_pokemon_to_player_no_interaction
from utils.server_handler import update_active_spawn_status
from utils.inventory_utils import get_item_amount, remove_item_from_inventory 
from utils.pokeball_select_utils import prompt_for_pokeball

POKEBALLS = [
    {"id": 1, "name": "Poké Ball"},
    {"id": 2, "name": "Great Ball"},
    {"id": 3, "name": "Ultra Ball"},
    {"id": 4, "name": "Master Ball"},
]

async def update_wild_pokemon_message(bot, guild_id, status_message, new_embed=None):
    servers_dir = os.path.join(os.getcwd(), "servers")
    data_file = os.path.join(servers_dir, str(guild_id), "data.json")
    if not os.path.isfile(data_file):
        return False

    with open(data_file, "r", encoding="utf-8") as f:
        data = json.load(f)

    active_spawn = data.get("active_spawn")
    if not active_spawn or "message_id" not in active_spawn:
        return False

    channels = data.get("channels", {})
    wild_channel_id = channels.get("wild")
    if not wild_channel_id:
        return False

    channel = bot.get_channel(int(wild_channel_id))
    if not channel:
        return False

    try:
        message = await channel.fetch_message(active_spawn["message_id"])
        # Keep original content, append status message
        original_content = message.content or ""
        updated_content = f"{original_content}\n\n{status_message}"
        await message.edit(
            content=updated_content,
            embed=new_embed if new_embed is not None else (message.embeds[0] if message.embeds else None),
            view=None  # Remove the button
        )
        return True
    except Exception as e:
        return False

def calculate_capture_success(player_power, pokemon_cp, pokeball_id=1):
    if player_power <= 0 or pokemon_cp <= 0:
        print(f"[CAPTURE] Invalid values: player_power={player_power}, pokemon_cp={pokemon_cp} -> False")
        return False
    base_chance = min(0.95, max(0.05, player_power / (player_power + pokemon_cp)))
    # Poké Ball bonus
    bonus = 1.0
    if pokeball_id == 2:
        bonus = 1.2
    elif pokeball_id == 3:
        bonus = 1.5
    elif pokeball_id == 4:
        bonus = 2.0
    success_chance = min(0.95, base_chance * bonus)
    roll = random.random()
    result = roll < success_chance
    print(f"[CAPTURE] player_power={player_power}, pokemon_cp={pokemon_cp}, pokeball_id={pokeball_id}, success_chance={success_chance:.2f}, roll={roll:.2f} -> {result}")
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
        available_balls = []
        for ball in POKEBALLS:
            amount = get_item_amount(guild_id, user_id, ball["id"])
            if amount > 0:
                available_balls.append({"id": ball["id"], "name": ball["name"], "amount": amount})
        if not available_balls:
            await interaction.response.send_message(
                "You need at least one Poké Ball, Great Ball, Ultra Ball, or Master Ball to attempt a capture!",
                ephemeral=True
            )
            return
        servers_dir = os.path.join(os.getcwd(), "servers")
        data_file = os.path.join(servers_dir, str(guild_id), "data.json")
        if not os.path.isfile(data_file):
            await interaction.response.send_message("Server data not found.", ephemeral=True)
            return
        with open(data_file, "r", encoding="utf-8") as f:
            data = json.load(f)
        spawn = data.get("active_spawn")
        if not spawn or spawn.get("id") != pokemon_id or spawn.get("status") != "active":
            # Update the original message to show the Pokémon left and remove the view/buttons
            try:
                await interaction.message.edit(
                    content="The Pokémon has left the area!",
                    view=None
                )
            except Exception as e:
                print(f"[Edit Error] {e}")
            return

        selected_ball_id = await prompt_for_pokeball(interaction, available_balls)

        if not selected_ball_id:
            return
        user_data = read_user_record(guild_id, user_id)
        if user_data is None:
            await interaction.followup.send("You need to set up your profile first with `/join`.", ephemeral=True)
            return

        player_power = user_data.get("power", 0)
        bot = interaction.client
        pokemon_obj = next((p for p in bot.pokemon if p.get("id") == pokemon_id), None)
        pokemon_cp = pokemon_obj.get("cp", 100)

        # Use selected_ball_id for bonus
        success = calculate_capture_success(player_power, pokemon_cp, selected_ball_id)
        if success:
            removed = remove_item_from_inventory(guild_id, user_id, selected_ball_id, 1)
            if not removed:
                await interaction.followup.send("You don't have that Poké Ball anymore!", ephemeral=True)
                return
            update_active_spawn_status(guild_id, pokemon_id, "captured", trainer_name)
            await update_wild_pokemon_message(
                bot,
                guild_id,
                status_message=f"🎉 {trainer_name} successfully captured {pokemon_obj.get('name', 'the Pokémon')}!"
            )
            result = await add_pokemon_to_player(bot, guild_id, user_id, pokemon_id, interaction)
            print(f"[add_pokemon_to_player] result={result}")  # Log the result
            if result == "duplicate":
                await interaction.followup.send(
                    f"You already have {pokemon_obj.get('name', 'the Pokémon')} in your active team!",
                    ephemeral=True
                )
                return
            elif result == "not_found":
                await interaction.followup.send(
                    "Pokémon data not found.",
                    ephemeral=True
                )
                return
            elif result == "full":
                await interaction.followup.send(
                    "Your active team is full and no replacement was made.",
                    ephemeral=True
                )
                return
            elif result == "timeout":
                await interaction.followup.send(
                    "No selection made. Pokémon not added.",
                    ephemeral=True
                )
                return
            await interaction.followup.send(
                f"🎉 {trainer_name} successfully captured {pokemon_obj.get('name', 'the Pokémon')}!",
                ephemeral=True
            )
            await interaction.channel.send(
                f"{trainer_name} captured {pokemon_obj.get('name', 'the Pokémon')}!"
            )
        else:
            removed = remove_item_from_inventory(guild_id, user_id, selected_ball_id, 1)
            if not removed:
                await interaction.followup.send("You don't have that Poké Ball anymore!", ephemeral=True)
                return
            update_active_spawn_status(guild_id, pokemon_id, "escaped", trainer_name)
            await interaction.channel.send(
                f"{trainer_name} tried to capture {pokemon_obj.get('name', 'the Pokémon')}, but it escaped!"
            )

    async def on_timeout(self):
        servers_dir = os.path.join(os.getcwd(), "servers")
        data_file = os.path.join(servers_dir, str(self.guild_id), "data.json")
        if os.path.isfile(data_file):
            with open(data_file, "r", encoding="utf-8") as f:
                data = json.load(f)
            spawn = data.get("active_spawn")
            if spawn and spawn.get("id") == self.pokemon_id and spawn.get("status") == "active":
                from utils.spawn_utils import update_active_spawn_status
                update_active_spawn_status(self.guild_id, self.pokemon_id, "escaped", "System")
                if self.message:
                    try:
                        await self.message.edit(
                            content="The Pokémon has left the area!",
                            view=None
                        )
                    except Exception as e:
                        print(f"[Timeout Edit Error] {e}")
        await super().on_timeout()
