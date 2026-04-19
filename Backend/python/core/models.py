from sqlalchemy import Column, Integer, BigInteger, String, Boolean, DateTime, Text
from sqlalchemy.orm import declarative_base
import datetime

Base = declarative_base()

class GuildConfig(Base):
    __tablename__ = 'guild_configs'
    guild_id = Column(BigInteger, primary_key=True)
    moderation_enabled = Column(Boolean, default=True)
    base_enabled = Column(Boolean, default=True)
    logging_enabled = Column(Boolean, default=False)
    tickets_enabled = Column(Boolean, default=False)
    frogboard_enabled = Column(Boolean, default=False)
    levels_enabled = Column(Boolean, default=False)
    economy_enabled = Column(Boolean, default=False)
    counting_enabled = Column(Boolean, default=False)
    mod_log_channel_id = Column(BigInteger, nullable=True)
    commands_ran = Column(Integer, default=0)
    message_count = Column(Integer, default=0)
    joined_at = Column(DateTime, default=datetime.datetime.utcnow)
    peak_online = Column(Integer, default=0)

class ModerationAction(Base):
    __tablename__ = 'moderation_actions'
    id = Column(Integer, primary_key=True, autoincrement=True)
    guild_id = Column(BigInteger, index=True)
    user_id = Column(BigInteger, index=True)
    moderator_id = Column(BigInteger)
    action_type = Column(String(50))  # kick, ban, mute, warn, unmute
    reason = Column(Text, nullable=False)
    proof = Column(Text, nullable=True)
    verbal = Column(Boolean, default=False)
    timestamp = Column(DateTime, default=datetime.datetime.utcnow)
    duration = Column(String(50), nullable=True)

class DashboardLog(Base):
    __tablename__ = 'dashboard_logs'
    id = Column(Integer, primary_key=True, autoincrement=True)
    guild_id = Column(BigInteger, index=True)
    user_id = Column(BigInteger)
    user_name = Column(String(100))
    user_avatar = Column(String(255), nullable=True)
    action = Column(String(255))
    timestamp = Column(DateTime, default=datetime.datetime.utcnow)
