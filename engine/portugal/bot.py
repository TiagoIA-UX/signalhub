#!/usr/bin/env python3
"""Compatibilidade — canônico: 08-lex-rocha-portugal/signalhub"""
import runpy
import sys
from pathlib import Path

_projetos = Path(__file__).resolve().parents[2].parent
_target = _projetos / "08-lex-rocha-portugal" / "signalhub" / "portugal" / "bot.py"
if not _target.is_file():
    raise SystemExit(
        "Bot Portugal não encontrado. Use E:\\01_Projetos\\08-lex-rocha-portugal"
    )
sys.argv[0] = str(_target)
runpy.run_path(str(_target), run_name="__main__")
