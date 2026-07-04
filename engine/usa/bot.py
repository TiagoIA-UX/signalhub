#!/usr/bin/env python3
"""Compatibilidade — canônico: 04-judicial-intelligence/signalhub/usa"""
import runpy
import sys
from pathlib import Path

_projetos = Path(__file__).resolve().parents[2].parent
_target = _projetos / "04-judicial-intelligence" / "signalhub" / "usa" / "bot.py"
if not _target.is_file():
    raise SystemExit(
        "Bot EUA não encontrado. Use E:\\01_Projetos\\04-judicial-intelligence\\signalhub\\usa"
    )
sys.argv[0] = str(_target)
runpy.run_path(str(_target), run_name="__main__")
