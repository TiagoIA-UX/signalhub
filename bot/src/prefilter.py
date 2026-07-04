"""Camada 1 — pré-filtro por keywords YAML (sem IA)."""

from __future__ import annotations

from dataclasses import dataclass

from src.config_loader import CONFIG_DIR, load_yaml


@dataclass
class PrefilterMatch:
    tenant: str
    tema: str
    group: str
    keyword: str


class KeywordPrefilter:
    def __init__(self) -> None:
        self._rules: list[tuple[str, str, str, str]] = []
        self._load_all()

    def _load_all(self) -> None:
        for filename in ("keywords_lexrocha.yaml", "keywords_zairyx.yaml"):
            data = load_yaml(CONFIG_DIR / filename)
            for group_id, group in (data.get("groups") or {}).items():
                tenant = group["tenant"]
                tema = group["tema"]
                for kw in group.get("keywords", []):
                    self._rules.append((kw.lower(), tenant, tema, group_id))

    def match(self, text: str) -> list[PrefilterMatch]:
        normalized = text.lower()
        matches: list[PrefilterMatch] = []
        seen_groups: set[str] = set()

        for keyword, tenant, tema, group_id in self._rules:
            if keyword in normalized and group_id not in seen_groups:
                seen_groups.add(group_id)
                matches.append(
                    PrefilterMatch(
                        tenant=tenant,
                        tema=tema,
                        group=group_id,
                        keyword=keyword,
                    )
                )
        return matches

    def has_match(self, text: str) -> bool:
        return bool(self.match(text))
