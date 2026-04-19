import discord
from discord.ext import commands
import os
import asyncio
from core.database import init_db
from dotenv import load_dotenv

# load env from the api directory
dotenv_path = os.path.join(os.path.dirname(__file__), "..", "api", ".env")
load_dotenv(dotenv_path)

# Basic bot configuration
TOKEN = os.getenv("DISCORD_BOT_TOKEN")
PREFIX = "!" # Even though we use slash commands, prefix might be needed for some things

class MelvinBot(commands.Bot):
    def __init__(self):
        intents = discord.Intents.default()
        intents.members = True
        intents.message_content = True
        super().__init__(command_prefix=PREFIX, intents=intents)

    async def setup_hook(self):
        # Initialize database
        init_db()
        
        # Load extensions
        initial_extensions = [
            'modules.base',
            'modules.moderation',
            'modules.logging',
            'modules.tickets',
            'modules.frogboard',
            'modules.levels',
            'modules.economy',
            'modules.counting',
        ]
        
        for extension in initial_extensions:
            try:
                await self.load_extension(extension)
                print(f'loaded {extension}')
            except Exception as e:
                print(f'failed to load {extension}: {e}')

bot = MelvinBot()

if __name__ == "__main__":
    if TOKEN:
        bot.run(TOKEN)
    else:
        print("discord token not found in environment variables.")
