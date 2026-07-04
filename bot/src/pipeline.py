"""Pipeline principal — orquestra todas as camadas."""

from __future__ import annotations

import logging
import os
from pathlib import Path

from dotenv import load_dotenv

from src.classifier import Classification, GroqClassifier, MockClassifier
from src.config_loader import CONFIG_DIR, ROOT_DIR, load_yaml
from src.deduper import Deduper
from src.prefilter import KeywordPrefilter
from src.responder import GroqResponder, MockResponder, build_cta_url
from src.sources.reddit import RedditSource
from src.telegram_alert import AlertPayload, RawPost, sanitize_for_groq
from src.telegram_bot import TelegramNotifier

logger = logging.getLogger(__name__)


class SignalPipeline:
    def __init__(
        self,
        *,
        use_mock_ai: bool = False,
        dedup_path: Path | None = None,
    ) -> None:
        load_dotenv(ROOT_DIR / ".env")
        self.config = load_yaml(CONFIG_DIR / "tenants.yaml")
        self.min_score = int(os.getenv("MIN_SCORE", self.config["defaults"]["min_score"]))
        self.max_alerts = int(
            os.getenv("MAX_ALERTS_PER_DAY", self.config["defaults"]["max_alerts_per_day"])
        )

        db_path = dedup_path or Path(
            os.getenv("DEDUP_DB_PATH", str(ROOT_DIR / "data" / "seen.sqlite"))
        )
        self.deduper = Deduper(db_path)
        self.prefilter = KeywordPrefilter()

        if use_mock_ai:
            self.classifier = MockClassifier()
            self.responder = MockResponder()
        else:
            api_key = os.getenv("GROQ_API_KEY", "")
            model = os.getenv("GROQ_MODEL", "openai/gpt-oss-120b")
            if not api_key:
                raise ValueError("GROQ_API_KEY obrigatório (ou use use_mock_ai=True)")
            self.classifier = GroqClassifier(api_key, model)
            self.responder = GroqResponder(api_key, model)

        self.telegram: TelegramNotifier | None = None
        token = os.getenv("TELEGRAM_BOT_TOKEN")
        chat_id = os.getenv("TELEGRAM_CHAT_ID")
        if token and chat_id:
            self.telegram = TelegramNotifier(token, chat_id)

        reddit_cfg = self.config.get("reddit", {})
        self.reddit = RedditSource(
            subreddits=reddit_cfg.get("subreddits", ["brasil"]),
            limit=reddit_cfg.get("limit", 25),
        )

    def process_post(self, post: RawPost, *, send_telegram: bool = True) -> AlertPayload | None:
        if self.deduper.is_seen(post.url):
            logger.debug("Skip seen: %s", post.url)
            return None

        text = f"{post.title}\n{post.body}"
        matches = self.prefilter.match(text)
        if not matches:
            return None

        hint = matches[0].tenant
        safe_title = sanitize_for_groq(post.title)
        safe_body = sanitize_for_groq(post.body)

        classification: Classification = self.classifier.classify(
            safe_title, safe_body, hint_tenant=hint
        )
        if not classification.is_actionable or classification.score < self.min_score:
            self.deduper.mark_seen(post.url)
            return None

        if not self.deduper.can_send_alert(self.max_alerts):
            logger.warning("Limite diário de alertas atingido")
            return None

        fonte = post.subreddit or post.source.lower()
        cta = build_cta_url(classification.tenant, fonte, classification.tema)
        responses = self.responder.generate(
            classification.tenant,
            classification.tema,
            safe_body[:1500],
            cta,
        )

        alert = AlertPayload(
            post=post,
            classification=classification,
            responses=responses,
            cta_url=cta,
        )

        self.deduper.mark_seen(post.url)
        self.deduper.log_alert(
            post.url, classification.tenant, classification.tema, classification.score
        )
        self.deduper.increment_daily_alerts()

        if send_telegram and self.telegram:
            self.deduper.save_pending_responses(
                alert.callback_id(),
                post.url,
                responses.r1,
                responses.r2,
                responses.r3,
            )
            self.telegram.send_alert(alert)

        return alert

    def run_cycle(self) -> list[AlertPayload]:
        alerts: list[AlertPayload] = []
        posts = self.reddit.fetch_new()
        logger.info("Reddit: %d posts fetched", len(posts))

        for post in posts:
            alert = self.process_post(post)
            if alert:
                alerts.append(alert)
                logger.info(
                    "Alert: %s score=%d tenant=%s",
                    post.url,
                    alert.classification.score,
                    alert.classification.tenant,
                )
        return alerts
