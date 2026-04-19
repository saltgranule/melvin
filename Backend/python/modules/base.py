import discord
from discord import app_commands
from discord.ext import commands
from core.database import get_session
from core.models import GuildConfig

class Base(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.command(name="help", description="display available modules and commands")
    @app_commands.checks.cooldown(1, 10, key=None) # Global cooldown
    async def help(self, interaction: discord.Interaction):
        embed = discord.Embed(
            title="melvin help",
            description="modular discord bot. all interfaces are lowercase and minimal.",
            color=0x98aa63
        )
        
        # In a full implementation, we would check which modules are enabled for the guild
        embed.add_field(name="base", value="/help, /ping", inline=False)
        embed.add_field(name="moderation", value="/mute, /kick, /ban, /warn, /record", inline=False)
        
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="ping", description="check bot latency")
    @app_commands.checks.cooldown(1, 10, key=None)
    async def ping(self, interaction: discord.Interaction):
        latency = round(self.bot.latency * 1000)
        await interaction.response.send_message(f"pong. {latency}ms.")

    @commands.Cog.listener()
    async def on_app_command_completion(self, interaction: discord.Interaction, command: app_commands.Command | app_commands.ContextMenu):
        if not interaction.guild:
            return
            
        db = get_session()
        try:
            config = db.query(GuildConfig).filter(GuildConfig.guild_id == interaction.guild.id).first()
            if not config:
                config = GuildConfig(guild_id=interaction.guild.id)
                db.add(config)
            
            config.commands_ran += 1
            db.commit()
        except Exception as e:
            print(f"error tracking command: {e}")
        finally:
            db.close()

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if not message.guild or message.author.bot:
            return
            
        db = get_session()
        try:
            config = db.query(GuildConfig).filter(GuildConfig.guild_id == message.guild.id).first()
            if not config:
                config = GuildConfig(guild_id=message.guild.id)
                db.add(config)
            
            config.message_count += 1
            db.commit()
        except Exception as e:
            print(f"error tracking message: {e}")
        finally:
            db.close()

async def setup(bot: commands.Bot):
    await bot.add_cog(Base(bot))
