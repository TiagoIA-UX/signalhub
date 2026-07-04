#!/usr/bin/env python3
"""
Importa dorks de signal_hub_portugal_v2.py (Downloads) para config/portugal/dorks.yaml.

Uso:
  copy "C:\\Users\\...\\signal_hub_portugal_v2.py" portugal\\signal_hub_portugal_v2.py
  python scripts/importar_signal_hub_v2.py
  python scripts/importar_signal_hub_v2.py --ficheiro "C:\\Users\\omago\\Downloads\\files (2)\\signal_hub_portugal_v2.py"
"""

from __future__ import annotations

import argparse
import importlib.util
import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "config" / "portugal" / "dorks.yaml"


def carregar_modulo(path: Path):
    spec = importlib.util.spec_from_file_location("signal_hub_portugal_v2", path)
    if not spec or not spec.loader:
        raise RuntimeError(f"Não foi possível carregar {path}")
    mod = importlib.util.module_from_spec(spec)
    sys.modules["signal_hub_portugal_v2"] = mod
    spec.loader.exec_module(mod)
    return mod


def extrair_dorks(mod) -> list[dict]:
    for attr in ("DORKS", "DORKS_PT", "ALL_DORKS", "dorks"):
        if hasattr(mod, attr):
            raw = getattr(mod, attr)
            if isinstance(raw, list):
                return _normalizar(raw)
            if isinstance(raw, dict):
                out = []
                for canal, items in raw.items():
                    for item in items:
                        if isinstance(item, str):
                            out.append({"canal": canal, "query": item})
                        elif isinstance(item, dict):
                            item.setdefault("canal", canal)
                            out.append(item)
                return _normalizar(out)
    raise AttributeError(
        "Módulo sem DORKS / DORKS_PT / ALL_DORKS. Verifique o ficheiro descarregado."
    )


def _normalizar(items: list) -> list[dict]:
    dorks = []
    for i, item in enumerate(items, start=1):
        if isinstance(item, str):
            dorks.append({"id": f"import_{i:03d}", "query": item})
        elif isinstance(item, dict) and item.get("query"):
            item.setdefault("id", f"import_{i:03d}")
            dorks.append(item)
    return dorks


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--ficheiro", type=Path, help="Caminho para signal_hub_portugal_v2.py")
    args = ap.parse_args()

    candidatos = [
        args.ficheiro,
        ROOT / "portugal" / "signal_hub_portugal_v2.py",
        Path.home() / "Downloads" / "files (2)" / "signal_hub_portugal_v2.py",
        Path.home() / "Downloads" / "signal_hub_portugal_v2.py",
    ]
    src = next((p for p in candidatos if p and p.is_file()), None)
    if not src:
        print("Ficheiro signal_hub_portugal_v2.py não encontrado.")
        print("Copie para signalhub_v2/portugal/ ou use --ficheiro CAMINHO")
        sys.exit(1)

    mod = carregar_modulo(src)
    dorks = extrair_dorks(mod)

    base = yaml.safe_load((ROOT / "config" / "portugal" / "dorks.yaml.example").read_text(encoding="utf-8"))
    base["dorks"] = dorks
    base["meta"]["importado_de"] = str(src.name)
    OUT.write_text(yaml.dump(base, allow_unicode=True, sort_keys=False), encoding="utf-8")
    print(f"Importados {len(dorks)} dorks → {OUT}")


if __name__ == "__main__":
    main()
