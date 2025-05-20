import discord
from discord.ext import commands
from discord import app_commands
from utils.player_handler import create_user_record, update_user_record

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
        await interaction.response.send_message("Profile setup complete! Check your DMs.", ephemeral=True)

async def setup(bot):
    await bot.add_cog(PlayerSetup(bot))