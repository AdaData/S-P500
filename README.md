# S-P500
Discord bot to track the number of Somie Coins in S&P. Could theoretically be extended to track more emojis.

## Setup
- You need python 3
- You'll need to install (discord.py([https://discordpy.readthedocs.io/en/stable/]. I had to do the "potentially breaking" pip3 option on WSL. On a normal ubuntu vm the usual pip3 method (`pip3 install discord.py`) worked fine.

### Environment
The bot uses 2 environment variables:
1. `S_P_500_KEY`: The bot's API Key. You'll have to reach out to Ada for this if you for some reason need it - I'd recommend doing local testing with your own bot though. Hit up ada if you want help getting a discord bot created.
2. `COIN_EMOJI_NAME`: Which emoji "counts" as the S&P Coin. We've been using `kekw` for testing. It's :spcoin: in prod.

## Running
`python3 coin-tracker.py` (note that on the Google Cloud VM it uses `python3 coin-tracker.py &` so it runs in the background)

The bot creates 2 files to persist the coin counts per user and the last market value of S&P coin. On initial startup, `on_ready` will throw an error because those files don't exist, but that's fine, everything should work and they'll be created during normal use.

A third file is also used but is a disabled feature currently, `slow_mode_hours.txt`. This limits queries by the same user to `/value` to 1 per the number in that file hours. If it's null or 0, it treats that as unlimited queries.

## Deployment
The bot is currently deployed on a Google Compute platform VM owned by Ada. She just copy-pastes the current code of coin-tracker.py and runs it, there's no CI/CD.
