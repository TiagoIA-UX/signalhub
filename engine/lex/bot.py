#!/usr/bin/env python3
"""Compatibilidade — canônico: 09-lex-rocha-brasil/signalhub-br"""
import runpy
import sys
from pathlib import Path

_projetos = Path(__file__).resolve().parents[2].parent
_target = _projetos / "09-lex-rocha-brasil" / "signalhub-br" / "hub.py"
if not _target.is_file():
    raise SystemExit(
        "Bot Brasil não encontrado. Use E:\\01_Projetos\\09-lex-rocha-brasil\\signalhub-br"
    )
sys.argv[0] = str(_target)
runpy.run_path(str(_target), run_name="__main__")
