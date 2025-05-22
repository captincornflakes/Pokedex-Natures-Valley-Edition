import discord
from discord.ext import commands
from discord import app_commands
from utils.player_handler import create_user_record, update_user_record, add_pokemon_to_pokedex, add_active_pokemon
import random
import json

COMMON_GENDERS = [
    "Man",
    "Woman",
    "Non-binary",
    "Transgender Man",
    "Transgender Woman",
    "Trans Fem",
    "Trans Masc",
    "Genderfluid",
    "Bigender",
    "Genderqueer",
    "Two-Spirit",
    "Demiboy",
    "Demigirl",
    "Agender",
    "Other"
]

COMMON_PRONOUNS = [
    "he/him",
    "she/her",
    "they/them",
    "he/they",
    "she/they",
    "they/he",
    "they/she",
    "xe/xem",
    "ze/zir",
    "fae/faer",
    "any",
    "prefer not to say",
    "other"
]

STARTER_IDS = [1, 4, 7]  # Bulbasaur, Charmander, Squirtle
RARE_STARTER_ID = 25     # Pikachu

class GenderDropdown(discord.ui.Select):
    def __init__(self):
        options = [discord.SelectOption(label=gender) for gender in COMMON_GENDERS]
        super().__init__(placeholder="Select your gender...", min_values=1, max_values=1, options=options)

    async def callback(self, interaction: discord.Interaction):
        self.view.gender = self.values[0]
        self.view.stop()

class PronounsDropdown(discord.ui.Select):
    def __init__(self):
        options = [discord.SelectOption(label=pronoun) for pronoun in COMMON_PRONOUNS]
        super().__init__(placeholder="Select your pronouns...", min_values=1, max_values=1, options=options)

    async def callback(self, interaction: discord.Interaction):
        self.view.pronouns = self.values[0]
        self.view.stop()

class GenderView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=60)
        self.gender = None
        self.add_item(GenderDropdown())

class PronounsView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=60)
        self.pronouns = None
        self.add_item(PronounsDropdown())

class StarterDropdown(discord.ui.Select):
    def __init__(self, starters):
        options = [
            discord.SelectOption(label=p["name"], description=f"#{p['id']} - {', '.join(p['type'])}", value=str(p["id"]))
            for p in starters
        ]
        super().__init__(placeholder="Choose your starter Pokémon...", min_values=1, max_values=1, options=options)

    async def callback(self, interaction: discord.Interaction):
        self.view.starter_id = int(self.values[0])
        self.view.stop()

class StarterView(discord.ui.View):
    def __init__(self, starters):
        super().__init__(timeout=60)
        self.starter_id = None
        self.add_item(StarterDropdown(starters))

def get_starter_pokemon(bot):
    # Use bot.pokemon for the starter selection
    pokemon_data = bot.pokemon
    # 1% chance for Pikachu (id 25)
    if random.randint(1, 100) == 1:
        starter_ids = STARTER_IDS + [RARE_STARTER_ID]
    else:
        starter_ids = STARTER_IDS
    starters = [p for p in pokemon_data if p["id"] in starter_ids]
    return starters, pokemon_data

async def give_starter_pokemon_menu(interaction, guild_id, user_id):
    print(f"[DEBUG] give_starter_pokemon_menu called for user {user_id} in guild {guild_id}")
    starters, pokemon_data = get_starter_pokemon(interaction.client)
    starter_view = StarterView(starters)
    prompt = await interaction.user.send("Choose your starter Pokémon:", view=starter_view)
    print(f"[Output] Sent starter selection to user {interaction.user.id}")

    starter_interaction = await interaction.client.wait_for(
        "interaction",
        check=lambda i: i.user == interaction.user and i.message.id == prompt.id,
        timeout=60
    )
    await starter_interaction.response.defer()
    starter_id = starter_view.starter_id or int(starter_interaction.data["values"][0])
    starter_obj = next((p for p in pokemon_data if p["id"] == starter_id), None)

    if not starter_obj:
        await interaction.user.send("Error: Could not find starter Pokémon data.")
        print(f"[Output] Could not find starter Pokémon data for id {starter_id}")
        return

    add_pokemon_to_pokedex(guild_id, user_id, starter_id)
    add_active_pokemon(guild_id, user_id, starter_obj)

    await interaction.user.send(
        f"Congratulations! Your starter Pokémon is **{starter_obj['name']}**!\n"
        f"It has been added to your Pokédex and your active team."
    )
    print(f"[Output] User {user_id} received starter Pokémon {starter_obj['name']} (id {starter_id})")

class PlayerSetup(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="join", description="Set up your player profile with gender, pronouns, and nickname.")
    async def start_profile(self, interaction: discord.Interaction):
        # Gender selection
        gender_view = GenderView()
        prompt = await interaction.user.send("Let's set up your profile! Please select your gender:", view=gender_view)
        print(f"[Output] Sent gender selection to user {interaction.user.id}")
        gender_interaction = await self.bot.wait_for(
            "interaction",
            check=lambda i: i.user == interaction.user and i.message.id == prompt.id,
            timeout=60
        )
        await gender_interaction.response.defer()
        gender = gender_view.gender or gender_interaction.data["values"][0]
        print(f"[Output] User {interaction.user.id} selected gender: {gender}")

        # Pronouns selection
        pronouns_view = PronounsView()
        prompt2 = await interaction.user.send("Please select your pronouns:", view=pronouns_view)
        print(f"[Output] Sent pronouns selection to user {interaction.user.id}")
        pronouns_interaction = await self.bot.wait_for(
            "interaction",
            check=lambda i: i.user == interaction.user and i.message.id == prompt2.id,
            timeout=60
        )
        await pronouns_interaction.response.defer()
        pronouns = pronouns_view.pronouns or pronouns_interaction.data["values"][0]
        print(f"[Output] User {interaction.user.id} selected pronouns: {pronouns}")

        # Nickname input
        await interaction.user.send("What nickname would you like to use?")
        print(f"[Output] Prompted user {interaction.user.id} for nickname")
        def check(m):
            return m.author == interaction.user and isinstance(m.channel, discord.DMChannel)
        nickname_msg = await self.bot.wait_for('message', check=check, timeout=60)
        nickname = nickname_msg.content.strip()
        print(f"[Output] User {interaction.user.id} entered nickname: {nickname}")

        guild_id = interaction.guild.id
        user_id = interaction.user.id

        user_data = create_user_record(guild_id, user_id)
        user_data["gender"] = gender
        user_data["pronouns"] = pronouns
        user_data["nickname"] = nickname
        update_user_record(guild_id, user_id, user_data)
        print(f"[Output] Created/updated player record for user {user_id} in guild {guild_id}")

        await interaction.user.send(f"Profile created! Gender: **{gender}**, Pronouns: **{pronouns}**, Nickname: **{nickname}**")
        await interaction.response.send_message(
            "Profile setup complete! Check your DMs.\n"
            "To collect your first Pokémon, use the `/starter` command.",
            ephemeral=True
        )

        # Starter selection menu
        await give_starter_pokemon_menu(interaction, interaction.guild.id, interaction.user.id)

    @app_commands.command(name="starter", description="Choose your starter Pokémon if you haven't already.")
    async def starter(self, interaction: discord.Interaction):
        """Allows a user to select a starter Pokémon if they haven't already."""
        from utils.player_handler import read_user_record
        user_data = read_user_record(interaction.guild.id, interaction.user.id)
        if not user_data:
            await interaction.response.send_message(
                "You need to set up your profile first with `/join`.", ephemeral=True
            )
            return
        if user_data.get("active_pokemon"):
            await interaction.response.send_message(
                "You already have a starter Pokémon!", ephemeral=True
            )
            return
        await interaction.response.send_message(
            "Opening the starter Pokémon selection menu in your DMs...", ephemeral=True
        )
        await give_starter_pokemon_menu(interaction, interaction.guild.id, interaction.user.id)

async def setup(bot):
    await bot.add_cog(PlayerSetup(bot))