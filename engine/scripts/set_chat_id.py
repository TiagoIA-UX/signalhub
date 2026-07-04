"""Define TELEGRAM_CHAT_ID nos dois bots (mesmo ID para Lex + Zairyx)."""

import re
import sys
from pathlib import Path

ROOT = Path(__file__).parent.parent


def update_env(path: Path, chat_id: str) -> None:
    txt = path.read_text(encoding="utf-8")
    if "TELEGRAM_CHAT_ID=" in txt:
        txt = re.sub(r"TELEGRAM_CHAT_ID=.*", f"TELEGRAM_CHAT_ID={chat_id}", txt)
    else:
        txt += f"\nTELEGRAM_CHAT_ID={chat_id}\n"
    path.write_text(txt, encoding="utf-8")
    print(f"OK: {path}")


def main() -> None:
    if len(sys.argv) < 2:
        print("Uso: python scripts/set_chat_id.py SEU_CHAT_ID")
        print("Obtenha o ID no Telegram: @userinfobot → /start → copie 'Id'")
        sys.exit(1)

    chat_id = sys.argv[1].strip()
    if not chat_id.isdigit():
        print("CHAT_ID deve ser número (ex: 123456789)")
        sys.exit(1)

    update_env(ROOT / "lex" / ".env", chat_id)
    update_env(ROOT / "zairyx" / ".env", chat_id)
    print(f"\nTELEGRAM_CHAT_ID={chat_id} aplicado em lex e zairyx.")


if __name__ == "__main__":
    main()
