from __future__ import annotations

from .models import ContainsFilter


SYNONYM_SETS: dict[str, list[str]] = {
    "routing table": [
        "routing table",
        "forwarding table",
        "FIB",
        "routing cache",
    ],
    "virtual machine": [
        "virtual machine",
        "hypervisor",
        "guest operating system",
    ],
}


def expand_synonym_seed(seed: str) -> list[str]:
    normalized_seed = _normalize_synonym_seed(seed)
    expanded = SYNONYM_SETS.get(normalized_seed)
    if expanded is None:
        supported = ", ".join(f'"{term}"' for term in sorted(SYNONYM_SETS))
        raise ValueError(f'Unknown synonym seed: "{seed}". Supported built-in synonym seeds: {supported}')

    seen: set[str] = set()
    ordered_terms: list[str] = []
    for term in expanded:
        key = term.casefold()
        if key in seen:
            continue
        seen.add(key)
        ordered_terms.append(term)

    return ordered_terms


def synonym_seed_summaries() -> list[dict[str, list[str] | str]]:
    return [
        {"seed": seed, "terms": expand_synonym_seed(seed)}
        for seed in sorted(SYNONYM_SETS)
    ]


def synonym_contains_filters(seed: str) -> list[ContainsFilter]:
    return [ContainsFilter(kind="contains", value=term) for term in expand_synonym_seed(seed)]


def _normalize_synonym_seed(seed: str) -> str:
    return " ".join(seed.strip().split()).casefold()