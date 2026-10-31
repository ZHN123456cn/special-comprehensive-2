from datetime import datetime

from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.dialects.mysql import LONGTEXT
from sqlalchemy.orm import relationship

from app.database import Base


class User(Base):
    """用户表"""
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, autoincrement=True, comment="用户ID")
    username = Column(String(50), unique=True, nullable=False, index=True, comment="用户名")
    password_hash = Column(String(255), nullable=False, comment="密码哈希")
    created_at = Column(DateTime, default=datetime.utcnow, comment="创建时间")


class Game(Base):
    """用户主动保存的游戏"""
    __tablename__ = "games"

    id = Column(Integer, primary_key=True, autoincrement=True, comment="游戏ID")
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    title = Column(String(100), nullable=False, comment="游戏标题")
    original_prompt = Column(Text, nullable=False, comment="原始游戏需求")
    description = Column(Text, nullable=False, comment="当前玩法说明")
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, comment="创建时间")
    updated_at = Column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False,
        comment="更新时间",
    )

    versions = relationship(
        "GameVersion",
        back_populates="game",
        cascade="all, delete-orphan",
        order_by="GameVersion.version_no",
    )


class GameVersion(Base):
    """点击保存后形成的正式游戏版本"""
    __tablename__ = "game_versions"
    __table_args__ = (
        UniqueConstraint("game_id", "version_no", name="uq_game_version_number"),
    )

    id = Column(Integer, primary_key=True, autoincrement=True, comment="版本ID")
    game_id = Column(
        Integer,
        ForeignKey("games.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    version_no = Column(Integer, nullable=False, comment="版本号")
    change_prompt = Column(Text, nullable=False, comment="本次修改意见")
    html = Column(LONGTEXT, nullable=False, comment="完整单文件HTML游戏")
    generation_ms = Column(Integer, default=0, nullable=False, comment="最近生成耗时（毫秒）")
    model_name = Column(String(100), nullable=False, comment="生成模型")
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, comment="保存时间")

    game = relationship("Game", back_populates="versions")
