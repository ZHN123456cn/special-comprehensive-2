from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.database import get_db
from app.deps import get_current_user
from app.game_generator import generate_game, revise_game, validate_game_html
from app.models import Game, GameVersion, User
from app.schemas import (
    GameDetail,
    GameDraftResponse,
    GameSummary,
    GameVersionDetail,
    GenerateGameRequest,
    MessageResponse,
    ReviseGameRequest,
    SaveGameRequest,
    SaveVersionRequest,
)

router = APIRouter(prefix="/api/games", tags=["games"])


def _get_owned_game(game_id: int, user_id: int, db: Session) -> Game:
    game = db.query(Game).filter(Game.id == game_id, Game.user_id == user_id).first()
    if game is None:
        raise HTTPException(status_code=404, detail="游戏不存在或无权访问")
    return game


def _validate_html(html: str) -> None:
    try:
        validate_game_html(html)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


def _summary(game: Game) -> dict:
    latest = game.versions[-1]
    return {
        "id": game.id,
        "title": game.title,
        "description": game.description,
        "original_prompt": game.original_prompt,
        "version_count": len(game.versions),
        "latest_version_no": latest.version_no,
        "created_at": game.created_at,
        "updated_at": game.updated_at,
    }


def _detail(game: Game) -> dict:
    latest = game.versions[-1]
    return {
        **_summary(game),
        "html": latest.html,
        "versions": list(reversed(game.versions)),
    }


@router.post("/generate", response_model=GameDraftResponse)
async def create_draft(
    payload: GenerateGameRequest,
    _current_user: User = Depends(get_current_user),
):
    """生成未保存草稿，不写入数据库。"""
    return await generate_game(payload.prompt.strip())


@router.post("/revise", response_model=GameDraftResponse)
async def create_revision_draft(
    payload: ReviseGameRequest,
    _current_user: User = Depends(get_current_user),
):
    """基于当前草稿生成修改结果，不写入数据库。"""
    try:
        return await revise_game(
            payload.original_prompt.strip(),
            payload.current_html,
            payload.instruction.strip(),
        )
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@router.post("", response_model=GameDetail, status_code=status.HTTP_201_CREATED)
def save_new_game(
    payload: SaveGameRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """首次点击保存时创建游戏与第 1 版。"""
    _validate_html(payload.html)
    game = Game(
        user_id=current_user.id,
        title=payload.title.strip(),
        original_prompt=payload.original_prompt.strip(),
        description=payload.description.strip(),
    )
    db.add(game)
    db.flush()
    db.add(
        GameVersion(
            game_id=game.id,
            version_no=1,
            change_prompt="初始保存",
            html=payload.html,
            generation_ms=payload.generation_ms,
            model_name=payload.model_name.strip(),
        )
    )
    db.commit()
    db.refresh(game)
    return _detail(game)


@router.get("", response_model=list[GameSummary])
def list_games(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    games = (
        db.query(Game)
        .filter(Game.user_id == current_user.id)
        .order_by(Game.updated_at.desc())
        .all()
    )
    return [_summary(game) for game in games]


@router.get("/{game_id}", response_model=GameDetail)
def get_game(
    game_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return _detail(_get_owned_game(game_id, current_user.id, db))


@router.post("/{game_id}/versions", response_model=GameDetail, status_code=status.HTTP_201_CREATED)
def save_new_version(
    game_id: int,
    payload: SaveVersionRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """将修改或恢复后的草稿显式保存为新版本。"""
    _validate_html(payload.html)
    game = _get_owned_game(game_id, current_user.id, db)
    latest_no = (
        db.query(func.max(GameVersion.version_no))
        .filter(GameVersion.game_id == game.id)
        .scalar()
        or 0
    )
    game.title = payload.title.strip()
    game.description = payload.description.strip()
    game.updated_at = datetime.utcnow()
    db.add(
        GameVersion(
            game_id=game.id,
            version_no=latest_no + 1,
            change_prompt=payload.change_prompt.strip(),
            html=payload.html,
            generation_ms=payload.generation_ms,
            model_name=payload.model_name.strip(),
        )
    )
    db.commit()
    db.refresh(game)
    return _detail(game)


@router.get("/{game_id}/versions/{version_id}", response_model=GameVersionDetail)
def get_game_version(
    game_id: int,
    version_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    game = _get_owned_game(game_id, current_user.id, db)
    version = (
        db.query(GameVersion)
        .filter(GameVersion.id == version_id, GameVersion.game_id == game.id)
        .first()
    )
    if version is None:
        raise HTTPException(status_code=404, detail="游戏版本不存在")
    return version


@router.delete("/{game_id}", response_model=MessageResponse)
def delete_game(
    game_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    game = _get_owned_game(game_id, current_user.id, db)
    db.delete(game)
    db.commit()
    return {"message": "游戏已删除"}
