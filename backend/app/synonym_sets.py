from __future__ import annotations

import json
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import urlopen

from .models import ContainsFilter


DATAMUSE_WORDS_URL = "https://api.datamuse.com/words"
DATAMUSE_TIMEOUT_SECONDS = 2.5
DATAMUSE_MAX_RESULTS = 10
DATAMUSE_TOPICS = "computer science software electrical engineering"
TERMSETS: dict[str, list[str]] = {}


def expand_synonym_seed(
    seed: str,
    *,
    max_results: int = DATAMUSE_MAX_RESULTS,
    topics: str = DATAMUSE_TOPICS,
) -> list[str]:
    normalized_seed = _normalize_synonym_seed(seed)
    if not normalized_seed:
        return []

    terms = _dedupe_terms([normalized_seed, *_fetch_datamuse_synonyms(normalized_seed, max_results, topics)])
    if TERMSETS.get(normalized_seed) != terms:
        TERMSETS[normalized_seed] = terms
    return terms


def expand_termset(seed: str) -> list[str]:
    normalized_seed = _normalize_synonym_seed(seed)
    terms = TERMSETS.get(normalized_seed)
    if terms is None:
        saved = ", ".join(f'"{term}"' for term in sorted(TERMSETS))
        suffix = f" Saved termsets: {saved}" if saved else " No termsets have been saved yet."
        raise ValueError(f'Unknown termset: "{seed}". Run synonym_of:"{normalized_seed}" first to fetch and save it.{suffix}')

    return list(terms)


def synonym_seed_summaries() -> list[dict[str, list[str] | str]]:
    return [
        {"seed": seed, "terms": list(terms)}
        for seed, terms in sorted(TERMSETS.items())
    ]


def synonym_contains_filters(
    seed: str,
    *,
    max_results: int = DATAMUSE_MAX_RESULTS,
    topics: str = DATAMUSE_TOPICS,
) -> list[ContainsFilter]:
    return [
        ContainsFilter(kind="contains", value=term)
        for term in expand_synonym_seed(seed, max_results=max_results, topics=topics)
    ]


def termset_contains_filters(seed: str) -> list[ContainsFilter]:
    return [ContainsFilter(kind="contains", value=term) for term in expand_termset(seed)]


def clear_saved_termsets() -> None:
    TERMSETS.clear()


def _fetch_datamuse_synonyms(seed: str, max_results: int, topics: str) -> tuple[str, ...]:
    query = urlencode({"ml": seed, "max": max_results, "topics": topics})
    url = f"{DATAMUSE_WORDS_URL}?{query}"

    try:
        with urlopen(url, timeout=DATAMUSE_TIMEOUT_SECONDS) as response:
            payload = json.loads(response.read().decode("utf-8"))
    except (HTTPError, URLError, TimeoutError, json.JSONDecodeError, OSError) as error:
        raise ValueError(f'Unable to fetch synonyms for "{seed}" from Datamuse.') from error

    if not isinstance(payload, list):
        raise ValueError(f'Unable to fetch synonyms for "{seed}" from Datamuse.')

    terms: list[str] = []
    for item in payload:
        if not isinstance(item, dict):
            continue

        term = item.get("word")
        if isinstance(term, str) and term.strip():
            terms.append(_normalize_synonym_seed(term))

    return tuple(terms)


def _dedupe_terms(terms: list[str]) -> list[str]:
    seen: set[str] = set()
    ordered_terms: list[str] = []
    for term in terms:
        normalized = _normalize_synonym_seed(term)
        key = normalized.casefold()
        if not normalized or key in seen:
            continue
        seen.add(key)
        ordered_terms.append(normalized)

    return ordered_terms


def _normalize_synonym_seed(seed: str) -> str:
    return " ".join(seed.strip().split()).casefold()
