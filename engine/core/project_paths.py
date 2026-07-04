"""Caminhos partilhados — bots em Lex-Rocha/ e lex-rocha-pt/."""

from __future__ import annotations

from pathlib import Path


def monorepo_root() -> Path:
    p = Path(__file__).resolve().parent.parent.parent
    if (p / "signalhub_v2" / "core").is_dir():
        return p
    raise RuntimeError("Raiz do monorepo não encontrada (signalhub_v2/core)")


def signalhub_root() -> Path:
    return monorepo_root() / "signalhub_v2"


def bot_paths(project_dir: Path) -> dict[str, Path]:
    """project_dir = Lex-Rocha ou lex-rocha-pt"""
    sh = signalhub_root()
    bot_dir = project_dir / "bot"
    cfg = project_dir / "config"
    return {
        "project": project_dir,
        "bot": bot_dir,
        "config": cfg,
        "keywords": cfg / "keywords.yaml",
        "varredura": cfg / "varredura.yaml",
        "env": bot_dir / ".env",
        "log": project_dir / "logs" / "bot.log",
        "signalhub": sh,
    }
