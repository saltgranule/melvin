import discord
from discord import app_commands
from discord.ext import commands
from core.database import get_session
from core.models import ModerationAction, GuildConfig
from core.utils import parse_duration
import datetime

class Moderation(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    async def log_action(self, interaction, user, action_type, reason, proof=None, verbal=False, duration=None):
        if verbal and action_type == "warn":
            return
        
        session = get_session()
        action = ModerationAction(
            guild_id=interaction.guild_id,
            user_id=user.id,
            moderator_id=interaction.user.id,
            action_type=action_type,
            reason=reason,
            proof=proof,
            verbal=verbal,
            duration=duration
        )
        session.add(action)
        session.commit() # Commit first to get action.id if needed, or just commit later

        # discord logging
        config = session.query(GuildConfig).filter_by(guild_id=interaction.guild_id).first()
        if config and config.mod_log_channel_id:
            channel = self.bot.get_channel(config.mod_log_channel_id)
            if channel:
                embed = discord.Embed(
                    description=f"**{action_type}** | member: {user.mention} ({user.id})\n**reason**: {reason.lower()}\n**moderator**: {interaction.user.mention}",
                    color=0x98aa63
                )
                if duration:
                    embed.description += f"\n**duration**: {duration}"
                if proof:
                    embed.description += f"\n**proof**: [link]({proof})"
                
                await channel.send(embed=embed)
        
        session.close()

    @app_commands.command(name="setlogs", description="set the moderation log channel")
    @app_commands.describe(channel="channel to send logs to")
    @app_commands.checks.has_permissions(administrator=True)
    async def setlogs(self, interaction: discord.Interaction, channel: discord.TextChannel):
        session = get_session()
        config = session.query(GuildConfig).filter_by(guild_id=interaction.guild_id).first()
        if not config:
            config = GuildConfig(guild_id=interaction.guild_id, mod_log_channel_id=channel.id)
            session.add(config)
        else:
            config.mod_log_channel_id = channel.id
        session.commit()
        session.close()
        
        await interaction.response.send_message(f"moderation logs will now be sent to {channel.mention}.")

    @app_commands.command(name="mute", description="timeout a member")
    @app_commands.describe(user="member to mute", reason="reason for mute", duration="duration (example 1h)", proof="proof url", purge="number of messages to purge")
    @app_commands.checks.has_permissions(moderate_members=True)
    @app_commands.checks.cooldown(1, 10, key=None)
    async def mute(self, interaction: discord.Interaction, user: discord.Member, reason: str, duration: str, proof: str = None, purge: int = 0):
        delta = parse_duration(duration)
        if not delta:
            return await interaction.response.send_message("invalid duration format. use 1s, 1m, 1h, 1d, 1w.", ephemeral=True)
        
        await user.timeout(delta, reason=reason)
        
        if purge > 0:
            def is_user(m):
                return m.author == user
            await interaction.channel.purge(limit=purge, check=is_user)
            
        await self.log_action(interaction, user, "mute", reason, proof, duration=duration)
        
        embed = discord.Embed(description=f"muted {user.mention} for {duration}. reason: {reason.lower()}.", color=0x98aa63)
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="unmute", description="remove timeout from a member")
    @app_commands.describe(user="member to unmute", reason="reason for unmute")
    @app_commands.checks.has_permissions(moderate_members=True)
    @app_commands.checks.cooldown(1, 10, key=None)
    async def unmute(self, interaction: discord.Interaction, user: discord.Member, reason: str = "no reason provided"):
        await user.timeout(None, reason=reason)
        await self.log_action(interaction, user, "unmute", reason)
        
        embed = discord.Embed(description=f"unmuted {user.mention}. reason: {reason.lower()}.", color=0x98aa63)
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="kick", description="kick a member")
    @app_commands.describe(user="member to kick", reason="reason for kick", proof="proof url", purge="number of messages to purge")
    @app_commands.checks.has_permissions(kick_members=True)
    @app_commands.checks.cooldown(1, 10, key=None)
    async def kick(self, interaction: discord.Interaction, user: discord.Member, reason: str, proof: str = None, purge: int = 0):
        await user.kick(reason=reason)
        
        if purge > 0:
            def is_user(m):
                return m.author == user
            await interaction.channel.purge(limit=purge, check=is_user)
            
        await self.log_action(interaction, user, "kick", reason, proof)
        
        embed = discord.Embed(description=f"kicked {user.mention}. reason: {reason.lower()}.", color=0x98aa63)
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="ban", description="ban a member")
    @app_commands.describe(user="member to ban", reason="reason for ban", proof="proof url", purge="days of messages to purge", duration="duration (optional)")
    @app_commands.checks.has_permissions(ban_members=True)
    @app_commands.checks.cooldown(1, 10, key=None)
    async def ban(self, interaction: discord.Interaction, user: discord.Member, reason: str, proof: str = None, purge: int = 0, duration: str = None):
        # purge in ban context is usually days of messages, converting to seconds
        delete_seconds = purge * 86400 if purge > 0 else 0
        await user.ban(reason=reason, delete_message_seconds=delete_seconds)
        
        await self.log_action(interaction, user, "ban", reason, proof, duration=duration)
        
        msg = f"banned {user.mention}. reason: {reason.lower()}."
        if duration:
            msg = f"temp-banned {user.mention} for {duration}. reason: {reason.lower()}."
            
        embed = discord.Embed(description=msg, color=0x98aa63)
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="warn", description="warn a member")
    @app_commands.describe(user="member to warn", reason="reason for warn", proof="proof url", verbal="if true, will not be logged")
    @app_commands.checks.has_permissions(moderate_members=True)
    @app_commands.checks.cooldown(1, 10, key=None)
    async def warn(self, interaction: discord.Interaction, user: discord.Member, reason: str, proof: str = None, verbal: bool = False):
        await self.log_action(interaction, user, "warn", reason, proof, verbal=verbal)
        
        type_str = "verbally warned" if verbal else "warned"
        embed = discord.Embed(description=f"{type_str} {user.mention}. reason: {reason.lower()}.", color=0x98aa63)
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="record", description="show moderation history for a user")
    @app_commands.describe(user="user to check history for")
    @app_commands.checks.has_permissions(moderate_members=True)
    @app_commands.checks.cooldown(1, 10, key=None)
    async def record(self, interaction: discord.Interaction, user: discord.User):
        session = get_session()
        actions = session.query(ModerationAction).filter_by(guild_id=interaction.guild_id, user_id=user.id).order_by(ModerationAction.timestamp.desc()).all()
        session.close()
        
        if not actions:
            return await interaction.response.send_message(f"no records found for {user.name.lower()}.", ephemeral=True)
        
        embed = discord.Embed(title=f"records: {user.name.lower()}", color=0x98aa63)
        for action in actions[:10]: # show last 10
            proof_str = f" | [proof]({action.proof})" if action.proof else ""
            verbal_str = " (verbal)" if action.verbal else ""
            embed.add_field(
                name=f"{action.action_type}{verbal_str} | case #{action.id}",
                value=f"reason: {action.reason.lower()}\nmoderator: <@{action.moderator_id}>\ndate: {action.timestamp.strftime('%y-%m-%d')}{proof_str}",
                inline=False
            )
        
        await interaction.response.send_message(embed=embed)

async def setup(bot: commands.Bot):
    await bot.add_cog(Moderation(bot))
