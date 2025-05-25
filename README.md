# Pokedex-Natures-Valley-Edition

Pokedex-Natures-Valley-Edition is a Discord bot game where you can capture, collect, battle, and trade Pokémon with friends in your server!  
Build your team, complete your Pokédex, earn badges, and become the top trainer in your community.

## Features

- **Wild Pokémon Spawns:** Pokémon appear randomly in your server's wild channel. Try to capture them before they escape!
- **Capture Pokémon:** Encounter and catch Pokémon to expand your collection. Capture success is based on your team's power and the Pokémon's CP.
- **Active Team Management:** Manage your team of up to 6 active Pokémon. Replace team members easily with interactive buttons.
- **Battles:** Challenge other trainers in best-of-3 Pokémon battles using `!challenge`, `!choose`, `!attack`, and `!forfeit` commands.
- **Server-based Progress:** Each server has its own save data and player records.
- **Easy Setup:** Use slash commands to set up your server and player profile.
- **Modern Discord UI:** Uses Discord's buttons and dropdowns for interactive menus.
- **Automatic Cleanup:** When the bot leaves a server, all Pokémon channels and server data are automatically deleted.

## Coming Soon

- **Trade:** Trade Pokémon with other players to complete your Pokédex or build your dream team.
- **Trainer Profiles:** Set up your own profile with gender, pronouns, nickname, and more.
- **Inventory & Badges:** Earn coins, collect items, and win badges as you play.

## Getting Started

1. **[Invite the bot to your server.](https://discord.com/oauth2/authorize?client_id=1374209265912512543)**
2. Use `/setup` (admin only) to initialize server data and channels (`guide`, `general`, `wild`).
3. Use `/join` to set up your trainer profile (DM-based, private).
4. Use `/starter` to choose your first Pokémon.
5. Watch for wild Pokémon in the wild channel and try to capture them!

## Commands

- `/setup` — Initializes server save data and channels (admin only).
- `/join` — Set up your player profile (DM-based, private).
- `/starter` — Choose your starter Pokémon if you haven't already.
- `/pokedex` — View your Pokédex progress.
- `/active` — View and manage your active Pokémon team.
- `/help` — Show all available commands.
- `!challenge @user` — Challenge another trainer to a battle.
- `!choose` — Pick your Pokémon for the round in a battle.
- `!attack` — Attack your opponent on your turn in a battle.
- `!forfeit` — Forfeit the current battle.
- More commands coming soon for trading and inventory!

## Data Storage

- Server data is stored in `servers/<guild_id>/data.json`.
- Each player has a separate file for their profile and progress in `servers/<guild_id>/<user_id>.json`.

## Requirements

- Python 3.9+
- `discord.py` 2.0+ (for buttons/views support)
- `mysql-connector-python`
- `requests`

Install requirements with:
```
pip install -r requirements.txt
```

## Contributing

Pull requests and suggestions are welcome! Please open an issue to discuss changes or new features.

---

*This project is for fun and is not affiliated with Nintendo, Game Freak, or The Pokémon Company.*

