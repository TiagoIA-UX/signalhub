"""CLI — um ciclo manual para teste."""

from __future__ import annotations

import argparse
import json
import logging
import sys

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

from src.pipeline import SignalPipeline
from src.telegram_alert import RawPost

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")


def main() -> None:
    parser = argparse.ArgumentParser(description="SignalHub — ciclo manual")
    parser.add_argument("--mock", action="store_true", help="Usar IA mock (sem Groq)")
    parser.add_argument("--dry-run", action="store_true", help="Não enviar Telegram")
    parser.add_argument("--sample", action="store_true", help="Testar post simulado")
    args = parser.parse_args()

    pipeline = SignalPipeline(use_mock_ai=args.mock)

    if args.sample:
        from datetime import datetime

        ts = datetime.now().strftime("%Y%m%d%H%M%S")
        post = RawPost(
            url=f"https://reddit.com/r/brasil/test-post-{ts}",
            title="Conta bloqueada e produto com defeito — o que fazer?",
            body=(
                "Comprei um produto com defeito e a loja não resolve. "
                "Além disso minha conta bloqueada no app. Vale a pena procon?"
            ),
            source="Reddit",
            subreddit="brasil",
        )
        alert = pipeline.process_post(post, send_telegram=not args.dry_run)
        if alert:
            print(json.dumps({"ok": True, "tenant": alert.classification.tenant}, indent=2))
            print("\n--- ALERTA ---\n")
            print(alert.format_message())
        else:
            print(json.dumps({"ok": False, "reason": "filtered"}, indent=2))
            sys.exit(1)
        return

    alerts = pipeline.run_cycle()
    print(json.dumps({"alerts": len(alerts)}, indent=2))


if __name__ == "__main__":
    main()
