"""
agent.py

The FitFindr planning loop. Orchestrates the FitFindr tools in response to a
natural language user query, passing state between them via a session dict.
"""

import re

from tools import (
    search_listings,
    suggest_outfit,
    create_fit_card,
    compare_price,
    load_style_profile,
    save_style_profile,
    check_trends,
)


# ── session state ─────────────────────────────────────────────────────────────

def _new_session(query: str, wardrobe: dict) -> dict:
    """
    Initialize and return a fresh session dict for one user interaction.
    """
    return {
        "query": query,
        "parsed": {},
        "search_results": [],
        "selected_item": None,
        "wardrobe": wardrobe,
        "style_profile": {},
        "price_assessment": None,
        "trend_data": None,
        "outfit_suggestion": None,
        "fit_card": None,
        "fallback_message": None,
        "error": None,
    }


# ── query parsing helpers ─────────────────────────────────────────────────────

def _extract_max_price(query: str) -> float | None:
    """Extract prices from phrases like 'under $30', 'max 40', or '$25'."""
    patterns = [
        r"under\s*\$?(\d+(?:\.\d+)?)",
        r"below\s*\$?(\d+(?:\.\d+)?)",
        r"less than\s*\$?(\d+(?:\.\d+)?)",
        r"max(?:imum)?\s*\$?(\d+(?:\.\d+)?)",
        r"budget\s*\$?(\d+(?:\.\d+)?)",
        r"\$(\d+(?:\.\d+)?)",
    ]

    for pattern in patterns:
        match = re.search(pattern, query, flags=re.IGNORECASE)
        if match:
            return float(match.group(1))

    return None


def _extract_size(query: str) -> str | None:
    """Extract simple clothing/shoe sizes from the user query."""
    size_patterns = [
        r"size\s+([a-zA-Z0-9./-]+)",
        r"\b(xs|s|m|l|xl|xxl|xxs)\b",
    ]

    for pattern in size_patterns:
        match = re.search(pattern, query, flags=re.IGNORECASE)
        if match:
            return match.group(1).strip(".,;:!?").upper()

    return None


def _clean_description(query: str) -> str:
    """
    Remove budget, size, and extra styling language to get the search phrase.
    This keeps the search simple and reliable for the mock dataset.
    """
    description = query.lower()

    # Remove text after wardrobe/style hints.
    split_markers = [
        "i mostly wear",
        "i usually wear",
        "my wardrobe",
        "how would i style",
        "what's out there",
        "what is out there",
    ]

    for marker in split_markers:
        if marker in description:
            description = description.split(marker)[0]

    # Remove price and size phrases.
    description = re.sub(r"under\s*\$?\d+(?:\.\d+)?", " ", description)
    description = re.sub(r"below\s*\$?\d+(?:\.\d+)?", " ", description)
    description = re.sub(r"less than\s*\$?\d+(?:\.\d+)?", " ", description)
    description = re.sub(r"max(?:imum)?\s*\$?\d+(?:\.\d+)?", " ", description)
    description = re.sub(r"budget\s*\$?\d+(?:\.\d+)?", " ", description)
    description = re.sub(r"\$\d+(?:\.\d+)?", " ", description)
    description = re.sub(r"size\s+[a-zA-Z0-9./-]+", " ", description)

    # Remove common filler phrases.
    filler_phrases = [
        "i'm looking for",
        "im looking for",
        "looking for",
        "find me",
        "i want",
        "show me",
        "please",
    ]

    for phrase in filler_phrases:
        description = description.replace(phrase, " ")

    # Keep letters, numbers, spaces, and basic punctuation used in fashion terms.
    description = re.sub(r"[^a-z0-9\s./-]", " ", description)
    description = re.sub(r"\s+", " ", description).strip()

    return description or query.strip()


def _parse_query(query: str) -> dict:
    """
    Parse the natural-language query into the fields needed by search_listings.
    This is intentionally simple and deterministic so it is easy to test.
    """
    return {
        "description": _clean_description(query),
        "size": _extract_size(query),
        "max_price": _extract_max_price(query),
    }


def _extract_style_preferences(query: str) -> dict:
    """
    Pull simple reusable style preferences from the query for stretch memory.
    """
    query_lower = query.lower()

    known_keywords = [
        "baggy",
        "oversized",
        "chunky",
        "minimal",
        "grunge",
        "streetwear",
        "vintage",
        "classic",
        "casual",
        "quiet luxury",
        "soft",
        "edgy",
    ]

    known_items = [
        "baggy jeans",
        "straight-leg jeans",
        "chunky sneakers",
        "boots",
        "docs",
        "hoodie",
        "cardigan",
        "blazer",
        "platforms",
    ]

    style_keywords = [word for word in known_keywords if word in query_lower]
    preferred_items = [item for item in known_items if item in query_lower]

    return {
        "style_keywords": style_keywords,
        "preferred_items": preferred_items,
        "notes": query.strip() if style_keywords or preferred_items else "",
    }


# ── planning loop ─────────────────────────────────────────────────────────────

def run_agent(query: str, wardrobe: dict) -> dict:
    """
    Main agent entry point. Runs the FitFindr planning loop for a single
    user interaction and returns the completed session dict.
    """
    session = _new_session(query, wardrobe)

    if not query or not query.strip():
        session["error"] = "Please enter what kind of secondhand item you want to find."
        return session

    # Load cross-session style memory stretch feature.
    session["style_profile"] = load_style_profile()

    # Parse natural-language query into tool inputs.
    parsed = _parse_query(query)
    session["parsed"] = parsed

    description = parsed["description"]
    size = parsed["size"]
    max_price = parsed["max_price"]

    # Tool 1: search listings.
    results = search_listings(description, size=size, max_price=max_price)

    # Stretch: retry fallback if the strict search fails.
    if not results and size is not None:
        fallback_results = search_listings(description, size=None, max_price=max_price)

        if fallback_results:
            results = fallback_results
            session["fallback_message"] = (
                f"No exact results matched size {size}, so I retried without the size filter."
            )

    session["search_results"] = results

    # Required error branch: do not continue without a selected item.
    if not results:
        session["error"] = (
            "I couldn't find listings for that search. Try a broader item description, "
            "a larger budget, or a different size."
        )
        return session

    # State: selected item from search flows into later tools.
    selected_item = results[0]
    session["selected_item"] = selected_item

    # Stretch: price comparison.
    session["price_assessment"] = compare_price(selected_item, results)

    # Stretch: trend awareness.
    session["trend_data"] = check_trends(description, size=size)

    # Tool 2: suggest outfit.
    outfit = suggest_outfit(selected_item, wardrobe)

    if not outfit or not outfit.strip():
        session["error"] = "I found an item, but I could not generate an outfit suggestion for it."
        return session

    session["outfit_suggestion"] = outfit

    # Tool 3: create fit card.
    fit_card = create_fit_card(outfit, selected_item)
    session["fit_card"] = fit_card

    # Stretch: save style memory if the user gave reusable preferences.
    preferences = _extract_style_preferences(query)
    if preferences["style_keywords"] or preferences["preferred_items"]:
        session["style_profile_save"] = save_style_profile(preferences)

    return session


# ── CLI test ──────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    from utils.data_loader import get_example_wardrobe, get_empty_wardrobe

    print("=== Happy path: graphic tee ===\n")
    session = run_agent(
        query="I'm looking for a vintage graphic tee under $30, size M. I mostly wear baggy jeans and chunky sneakers.",
        wardrobe=get_example_wardrobe(),
    )

    if session["error"]:
        print(f"Error: {session['error']}")
    else:
        print(f"Parsed: {session['parsed']}")
        if session["fallback_message"]:
            print(f"Fallback: {session['fallback_message']}")
        print(f"Found: {session['selected_item']['title']}")
        print(f"Price: {session['price_assessment']['reasoning']}")
        print(f"Trend: {session['trend_data']['trend_summary']}")
        print(f"\nOutfit: {session['outfit_suggestion']}")
        print(f"\nFit card: {session['fit_card']}")

    print("\n\n=== Empty wardrobe path ===\n")
    session_empty = run_agent(
        query="vintage graphic tee under $30",
        wardrobe=get_empty_wardrobe(),
    )
    print(f"Error: {session_empty['error']}")
    print(f"Outfit: {session_empty['outfit_suggestion']}")

    print("\n\n=== No-results path ===\n")
    session2 = run_agent(
        query="designer ballgown size XXS under $5",
        wardrobe=get_example_wardrobe(),
    )
    print(f"Error message: {session2['error']}")
    print(f"Fit card should be None: {session2['fit_card']}")