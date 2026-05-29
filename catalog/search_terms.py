from __future__ import annotations

import re
from typing import Iterable


def _normalize(value: str) -> str:
    return re.sub(r"\s+", " ", value.strip().lower())


SEARCH_ALIAS_GROUPS: dict[str, set[str]] = {
    "shoes": {"shoes", "shoe", "sneakers", "sneaker", "footwear", "trainers"},
    "headphones": {
        "headphones",
        "headphone",
        "earbuds",
        "earbud",
        "earphones",
        "audio",
    },
    "watches": {"watch", "watches", "smartwatch", "smartwatches", "wearable"},
    "bags": {"bag", "bags", "backpack", "backpacks", "rucksack", "luggage"},
    "home-appliances": {
        "home appliances",
        "toaster",
        "microwave",
        "blender",
        "kettle",
        "airfryer",
        "air fryer",
        "iron",
        "heater",
        "fan",
        "purifier",
        "dehumidifier",
        "humidifier",
        "massager",
    },
    "laptop": {"laptop", "notebook", "ultrabook"},
    "speakers": {"speaker", "speakers", "soundbar"},
    "electronics": {"electronics"},
    "sports": {"sports", "outdoor", "fitness", "yoga", "mat"},
}

TERM_TO_CANONICAL: dict[str, str] = {}
for canonical, terms in SEARCH_ALIAS_GROUPS.items():
    for term in terms:
        TERM_TO_CANONICAL[_normalize(term)] = canonical


def expand_search_terms(value: str) -> set[str]:
    expanded_terms: set[str] = set()
    normalized = _normalize(value)
    if not normalized:
        return expanded_terms

    direct_canonical = TERM_TO_CANONICAL.get(normalized)
    if direct_canonical:
        expanded_terms.update(SEARCH_ALIAS_GROUPS[direct_canonical])
        expanded_terms.add(direct_canonical)

    for token in normalized.split(" "):
        canonical = TERM_TO_CANONICAL.get(token)
        if canonical:
            expanded_terms.update(SEARCH_ALIAS_GROUPS[canonical])
            expanded_terms.add(canonical)
        else:
            expanded_terms.add(token)

    expanded_terms.add(normalized)
    return expanded_terms


def infer_product_tag_names(*values: Iterable[str] | str) -> list[str]:
    """Infer canonical search tags from product text."""

    parts: list[str] = []
    for value in values:
        if isinstance(value, str):
            parts.append(value)
        else:
            parts.extend(str(item) for item in value)

    text = _normalize(" ".join(parts))
    inferred: list[str] = []

    for canonical, terms in SEARCH_ALIAS_GROUPS.items():
        if any(term in text for term in terms):
            inferred.append(canonical)

    return inferred
