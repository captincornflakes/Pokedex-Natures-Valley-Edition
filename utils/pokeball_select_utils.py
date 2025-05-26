import discord

class PokeballSelect(discord.ui.Select):
    def __init__(self, available_balls):
        options = [
            discord.SelectOption(
                label=f"{ball['name']} (x{ball['amount']})",
                value=str(ball['id'])
            )
            for ball in available_balls
        ]
        super().__init__(placeholder="Choose a Poké Ball to use...", min_values=1, max_values=1, options=options)

    async def callback(self, interaction: discord.Interaction):
        self.view.selected_ball_id = int(self.values[0])
        self.view.stop()

class PokeballSelectView(discord.ui.View):
    def __init__(self, available_balls, timeout=30):
        super().__init__(timeout=timeout)
        self.selected_ball_id = None
        self.add_item(PokeballSelect(available_balls))

async def prompt_for_pokeball(interaction, available_balls):
    """
    Prompts the user to select a Poké Ball and returns the selected ball ID, or None if timed out.
    Also deletes the selector message after selection or timeout.
    """
    select_view = PokeballSelectView(available_balls)
    await interaction.response.send_message(
        "Which Poké Ball would you like to use?",
        view=select_view,
        ephemeral=True
    )
    await select_view.wait()
    selected_ball_id = select_view.selected_ball_id

    # Remove the Poké Ball selector message immediately after a selection or timeout
    try:
        await interaction.delete_original_response()
    except Exception:
        pass

    return selected_ball_id