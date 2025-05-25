import os
import json
from utils.player_handler import read_user_record
import discord

def is_battle_channel(guild, channel_id):
    """
    Returns True if the channel_id is an active battle channel in the guild.
    """
    servers_dir = os.path.join(os.getcwd(), "servers")
    data_file = os.path.join(servers_dir, str(guild.id), "data.json")
    if os.path.isfile(data_file):
        with open(data_file, "r", encoding="utf-8") as f:
            data = json.load(f)
        for battle in data.get("active_battles", []):
            if battle.get("channel_id") == channel_id:
                return True
    return False

async def on_message_battle_commands(bot, message):
    if message.author.bot:
        return
    if not message.guild:
        return
    if not message.content.startswith("!"):
        return
    if not is_battle_channel(message.guild, message.channel.id):
        return

    if message.content.strip().lower().startswith("!choose"):
        parts = message.content.strip().split(maxsplit=1)
        chosen_arg = parts[1] if len(parts) > 1 else None
        await handle_choose_command(bot, message, chosen_arg)
        try:
            await message.delete()
        except Exception:
            pass
        return

    if message.content.strip().lower().startswith("!attack"):
        await handle_attack_command(bot, message)
        try:
            await message.delete()
        except Exception:
            pass
        return

    if message.content.strip().lower().startswith("!forfeit"):
        await handle_forfeit_command(bot, message)
        try:
            await message.delete()
        except Exception:
            pass
        return

    if message.content.strip().lower() == "!hello":
        await message.channel.send(
            f"Hello, {message.author.mention}! This is your battle channel."
        )
    else:
        await message.channel.send(
            f"Unknown battle command: `{message.content}`"
        )

async def handle_choose_command(bot, message, chosen_arg):
    # Load battle info
    servers_dir = os.path.join(os.getcwd(), "servers")
    data_file = os.path.join(servers_dir, str(message.guild.id), "data.json")
    if not os.path.isfile(data_file):
        await message.channel.send(f"{message.author.mention} Battle data not found.")
        return
    with open(data_file, "r", encoding="utf-8") as f:
        data = json.load(f)
    battle = next((b for b in data.get("active_battles", []) if b.get("channel_id") == message.channel.id), None)
    if not battle:
        await message.channel.send(f"{message.author.mention} Battle not found.")
        return
    played_key = None
    pokemon_key = None
    if message.author.id == battle.get("user1_id"):
        played_key = "user1_played"
        pokemon_key = "user1_pokemon"
    elif message.author.id == battle.get("user2_id"):
        played_key = "user2_played"
        pokemon_key = "user2_pokemon"
    else:
        await message.channel.send(f"{message.author.mention} You are not a participant in this battle.")
        return
    user_data = read_user_record(message.guild.id, message.author.id)
    if not user_data or not user_data.get("active_pokemon"):
        await message.channel.send(f"{message.author.mention} You have no active Pokémon.")
        return
    played_pokemon = battle.get(played_key, [])
    played_ids = {p.get("id") for p in played_pokemon if p.get("id")}
    available_pokemon = [
        poke for poke in user_data["active_pokemon"]
        if poke.get("id") not in played_ids
    ]

    if not available_pokemon:
        await message.channel.send(f"{message.author.mention} You have no available Pokémon left to choose.")
        return
    if chosen_arg:
        chosen_poke = None
        if chosen_arg.isdigit():
            idx = int(chosen_arg) - 1
            if 0 <= idx < len(available_pokemon):
                chosen_poke = available_pokemon[idx]
        if not chosen_poke:
            for poke in available_pokemon:
                if poke.get("name", "").lower() == chosen_arg.lower():
                    chosen_poke = poke
                    break
        if not chosen_poke:
            await message.channel.send(f"{message.author.mention} Could not find that Pokémon in your available list.")
            return
        played_pokemon.append(chosen_poke)
        battle[played_key] = played_pokemon
        battle[pokemon_key] = chosen_poke
        for i, b in enumerate(data.get("active_battles", [])):
            if b.get("channel_id") == message.channel.id:
                data["active_battles"][i] = battle
                break
        with open(data_file, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)

        embed = discord.Embed(
            title=f"{message.author.display_name} chose {chosen_poke.get('name', chosen_poke.get('id'))}!",
            description=(
                f"**CP:** {chosen_poke.get('cp', '?')}\n"
                f"**HP:** {chosen_poke.get('hp', '?')}\n"
                f"**ATK:** {chosen_poke.get('attack', '?')}\n"
                f"**DEF:** {chosen_poke.get('defense', '?')}"
            ),
            color=discord.Color.green()
        )
        # Add Pokémon image if id is present
        poke_id = chosen_poke.get('id')
        if poke_id:
            embed.set_thumbnail(url=f"https://bots.media/pokemon/{poke_id}.png")
        await message.channel.send(f"{message.author.mention}", embed=embed)
        user1_pokemon = battle.get("user1_pokemon")
        user2_pokemon = battle.get("user2_pokemon")
        if user1_pokemon and user2_pokemon:
            user1_id = battle.get("user1_id")
            user2_id = battle.get("user2_id")
            turn_id = battle.get("turn")
            turn_member = message.guild.get_member(turn_id)
            user1_mention = message.guild.get_member(user1_id).mention if message.guild.get_member(user1_id) else f"<@{user1_id}>"
            user2_mention = message.guild.get_member(user2_id).mention if message.guild.get_member(user2_id) else f"<@{user2_id}>"
            turn_mention = turn_member.mention if turn_member else f"<@{turn_id}>"
            try:
                await message.channel.purge()
            except Exception:
                pass 
            # Show both Pokémon side by side with images
            def poke_stats(poke):
                return (
                    f"**Name:** {poke.get('name', poke.get('id'))}\n"
                    f"**CP:** {poke.get('cp', '?')}\n"
                    f"**HP:** {poke.get('hp', '?')}\n"
                    f"**ATK:** {poke.get('attack', '?')}\n"
                    f"**DEF:** {poke.get('defense', '?')}"
                )

            battle_embed = discord.Embed(
                title="Battle Start!",
                description=f"{user1_mention} vs {user2_mention}\nBoth Pokémon have been chosen! The battle can begin!",
                color=discord.Color.orange()
            )
            # Load player records for nicknames
            user1_data = read_user_record(message.guild.id, user1_id)
            user2_data = read_user_record(message.guild.id, user2_id)
            user1_nick = user1_data.get("nickname", user1_mention) if user1_data else user1_mention
            user2_nick = user2_data.get("nickname", user2_mention) if user2_data else user2_mention

            battle_embed.add_field(
                name=f"{user1_nick}'s Pokémon",
                value=poke_stats(user1_pokemon),
                inline=True
            )
            battle_embed.add_field(
                name=f"{user2_nick}'s Pokémon",
                value=poke_stats(user2_pokemon),
                inline=True
            )
            # Add images for both Pokémon
            if user1_pokemon.get("id"):
                battle_embed.set_thumbnail(url=f"https://bots.media/pokemon/{user1_pokemon.get('id')}.png")
            if user2_pokemon.get("id"):
                battle_embed.set_image(url=f"https://bots.media/pokemon/{user2_pokemon.get('id')}.png")
            battle_embed.add_field(
                name="It's your turn!",
                value=f"{turn_mention}, it's your turn to attack!",
                inline=False
            )
            await message.channel.send(embed=battle_embed)
        return

    # No argument: show available Pokémon
    embed = discord.Embed(
        title=f"{message.author.display_name}'s Available Pokémon",
        description="Pokémon you can choose for battle:",
        color=discord.Color.blue()
    )
    for idx, poke in enumerate(available_pokemon, 1):
        name = poke.get("name", poke.get("id"))
        cp = poke.get("cp", "?")
        hp = poke.get("hp", "?")
        attack = poke.get("attack", "?")
        defense = poke.get("defense", "?")
        embed.add_field(
            name=f"{idx}: {name}",
            value=f"CP: {cp} | HP: {hp} | ATK: {attack} | DEF: {defense}",
            inline=False
        )
    await message.channel.send(f"{message.author.mention}", embed=embed)
    return

async def handle_attack_command(bot, message):
    import os
    import json
    from utils.player_handler import read_user_record

    servers_dir = os.path.join(os.getcwd(), "servers")
    data_file = os.path.join(servers_dir, str(message.guild.id), "data.json")
    if not os.path.isfile(data_file):
        await message.channel.send(f"{message.author.mention} Battle data not found.")
        return
    with open(data_file, "r", encoding="utf-8") as f:
        data = json.load(f)
    battle = next((b for b in data.get("active_battles", []) if b.get("channel_id") == message.channel.id), None)
    if not battle:
        await message.channel.send(f"{message.author.mention} Battle not found.")
        return

    # Check if it's the sender's turn
    if message.author.id != battle.get("turn"):
        await message.channel.send(f"{message.author.mention} It's not your turn!")
        return

    # Get both Pokémon
    user1_pokemon = battle.get("user1_pokemon")
    user2_pokemon = battle.get("user2_pokemon")
    if not user1_pokemon or not user2_pokemon:
        await message.channel.send(f"{message.author.mention} Both players must choose a Pokémon first.")
        return

    # Determine attacker and defender
    if message.author.id == battle.get("user1_id"):
        attacker = user1_pokemon
        defender = user2_pokemon
        defender_key = "user2_pokemon"
        next_turn = battle.get("user2_id")
    else:
        attacker = user2_pokemon
        defender = user1_pokemon
        defender_key = "user1_pokemon"
        next_turn = battle.get("user1_id")

    # Ensure current_hp is tracked
    if "current_hp" not in defender:
        defender["current_hp"] = defender.get("hp", 0)
    if "current_hp" not in attacker:
        attacker["current_hp"] = attacker.get("hp", 0)

    # Calculate damage and apply
    attack_points = attacker.get("attack", 0) or 0
    defender["current_hp"] = max(0, defender["current_hp"] - attack_points)

    # Update battle state
    battle[defender_key] = defender
    battle["turn"] = next_turn

    # Save changes to data.json
    for i, b in enumerate(data.get("active_battles", [])):
        if b.get("channel_id") == message.channel.id:
            data["active_battles"][i] = battle
            break
    with open(data_file, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)

    # Announce attack
    attacker_name = attacker.get("name", attacker.get("id"))
    defender_name = defender.get("name", defender.get("id"))
    defender_hp = defender["current_hp"]
    attack_embed = discord.Embed(
        title="Attack!",
        description=(
            f"{message.author.mention}'s **{attacker_name}** attacks **{defender_name}** for {attack_points} damage!\n"
            f"**{defender_name}** now has {defender_hp} HP left."
        ),
        color=discord.Color.red() if defender_hp <= 0 else discord.Color.blue()
    )
    if attacker.get("id"):
        attack_embed.set_thumbnail(url=f"https://bots.media/pokemon/{attacker.get('id')}.png")
    if defender.get("id"):
        attack_embed.set_image(url=f"https://bots.media/pokemon/{defender.get('id')}.png")
    if defender_hp <= 0:
        attack_embed.add_field(name="KO!", value=f"**{defender_name}** has fainted!", inline=False)
    await message.channel.send(embed=attack_embed)

    # If defender faints, handle round logic
    if defender_hp <= 0:
        # Track the winner of each round
        if "round_winners" not in battle:
            battle["round_winners"] = []
        round_winner_id = message.author.id
        battle["round_winners"].append(round_winner_id)

        # Add fainted Pokémon to played list if not already there
        if defender_key == "user2_pokemon":
            played_key = "user2_played"
            player_id = battle.get("user2_id")
            opponent_id = battle.get("user1_id")
        else:
            played_key = "user1_played"
            player_id = battle.get("user1_id")
            opponent_id = battle.get("user2_id")

        played_list = battle.get(played_key, [])
        if not any(p.get("id") == defender.get("id") for p in played_list):
            played_list.append(defender)
            battle[played_key] = played_list

        # Remove the fainted Pokémon from the current slot
        battle[defender_key] = None

        # Increment round
        battle["round"] = battle.get("round", 1) + 1

        # Save changes to data.json
        for i, b in enumerate(data.get("active_battles", [])):
            if b.get("channel_id") == message.channel.id:
                data["active_battles"][i] = battle
                break
        with open(data_file, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)

        # Prompt the player to choose a new Pokémon if they have any left
        user_data = read_user_record(message.guild.id, player_id)
        available_pokemon = [
            poke for poke in user_data.get("active_pokemon", [])
            if poke.get("id") not in {p.get("id") for p in played_list}
        ]
        player_member = message.guild.get_member(player_id)
        opponent_member = message.guild.get_member(opponent_id)

        # Check for win condition: no Pokémon left or 3 rounds complete
        if not available_pokemon or len(battle["round_winners"]) >= 3:
            # Best of 3: winner is who won more rounds
            round_winners = battle.get("round_winners", [])
            user1_id = battle.get("user1_id")
            user2_id = battle.get("user2_id")
            user1_wins = round_winners.count(user1_id)
            user2_wins = round_winners.count(user2_id)

            if user1_wins > user2_wins:
                winner = message.guild.get_member(user1_id).mention if message.guild.get_member(user1_id) else f"<@{user1_id}>"
            elif user2_wins > user1_wins:
                winner = message.guild.get_member(user2_id).mention if message.guild.get_member(user2_id) else f"<@{user2_id}>"
            else:
                winner = "It's a tie!"

            # Clear the chat before declaring the winner
            try:
                await message.channel.purge()
            except Exception:
                pass

            # Remove the battle from active_battles and save
            data["active_battles"] = [
                b for b in data.get("active_battles", [])
                if b.get("channel_id") != message.channel.id
            ]
            with open(data_file, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2)

            # Delete the battle channel
            try:
                await message.channel.delete()
            except Exception:
                pass

            # Post results in the general channel
            general_channel_id = None
            if "channels" in data and "general" in data["channels"]:
                general_channel_id = data["channels"]["general"]
            elif "general_channel" in data:
                general_channel_id = data["general_channel"]

            if general_channel_id:
                general_channel = message.guild.get_channel(general_channel_id)
                if general_channel:
                    await general_channel.send(
                        f"Battle over!\nWinner: {winner}"
                    )
            return

        # If not over, prompt for next Pokémon
        if available_pokemon and player_member:
            embed = discord.Embed(
                title=f"{player_member.display_name}, choose your next Pokémon!",
                description="Your available Pokémon:",
                color=discord.Color.orange()
            )
            for idx, poke in enumerate(available_pokemon, 1):
                name = poke.get("name", poke.get("id"))
                cp = poke.get("cp", "?")
                hp = poke.get("hp", "?")
                attack = poke.get("attack", "?")
                defense = poke.get("defense", "?")
                embed.add_field(
                    name=f"{idx}: {name}",
                    value=f"CP: {cp} | HP: {hp} | ATK: {attack} | DEF: {defense}",
                    inline=False
                )
            await message.channel.send(f"{player_member.mention}", embed=embed)
            await message.channel.send(
                f"{player_member.mention}, please choose your next Pokémon with `!choose`."
            )
        else:
            await message.channel.send(f"No available Pokémon left for <@{player_id}>!")

async def handle_forfeit_command(bot, message):
    import os
    import json

    servers_dir = os.path.join(os.getcwd(), "servers")
    data_file = os.path.join(servers_dir, str(message.guild.id), "data.json")
    if not os.path.isfile(data_file):
        await message.channel.send(f"{message.author.mention} Battle data not found.")
        return
    with open(data_file, "r", encoding="utf-8") as f:
        data = json.load(f)
    battle = next((b for b in data.get("active_battles", []) if b.get("channel_id") == message.channel.id), None)
    if not battle:
        await message.channel.send(f"{message.author.mention} Battle not found.")
        return

    user1_id = battle.get("user1_id")
    user2_id = battle.get("user2_id")
    if message.author.id == user1_id:
        winner_id = user2_id
    elif message.author.id == user2_id:
        winner_id = user1_id
    else:
        await message.channel.send(f"{message.author.mention} You are not a participant in this battle.")
        return

    winner_mention = message.guild.get_member(winner_id).mention if message.guild.get_member(winner_id) else f"<@{winner_id}>"
    loser_mention = message.author.mention

    # Remove the battle from active_battles and save
    data["active_battles"] = [
        b for b in data.get("active_battles", [])
        if b.get("channel_id") != message.channel.id
    ]
    with open(data_file, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)

    # Announce forfeit and winner
    try:
        await message.channel.purge()
    except Exception:
        pass

    try:
        await message.channel.send(
            f"{loser_mention} has forfeited the battle!\nWinner: {winner_mention}"
        )
    except Exception:
        pass

    # Delete the battle channel
    try:
        await message.channel.delete()
    except Exception:
        pass

    # Post results in the general channel
    general_channel_id = None
    if "channels" in data and "general" in data["channels"]:
        general_channel_id = data["channels"]["general"]
    elif "general_channel" in data:
        general_channel_id = data["general_channel"]

    if general_channel_id:
        general_channel = message.guild.get_channel(general_channel_id)
        if general_channel:
            await general_channel.send(
                f"Battle over! {loser_mention} forfeited.\nWinner: {winner_mention}"
            )