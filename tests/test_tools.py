import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from tools import (
    search_listings,
    suggest_outfit,
    create_fit_card,
    compare_price,
    check_trends,
    load_style_profile,
)
from utils.data_loader import get_empty_wardrobe


def test_search_returns_results():
    results = search_listings("vintage graphic tee", size=None, max_price=50)
    assert isinstance(results, list)
    assert len(results) > 0


def test_search_empty_results():
    results = search_listings("designer ballgown", size="XXS", max_price=5)
    assert results == []


def test_search_price_filter():
    results = search_listings("jacket", size=None, max_price=10)
    assert all(item["price"] <= 10 for item in results)


def test_suggest_outfit_empty_wardrobe():
    results = search_listings("vintage graphic tee", size=None, max_price=50)
    outfit = suggest_outfit(results[0], get_empty_wardrobe())
    assert isinstance(outfit, str)
    assert len(outfit.strip()) > 0


def test_create_fit_card_empty_outfit():
    results = search_listings("vintage graphic tee", size=None, max_price=50)
    fit_card = create_fit_card("", results[0])
    assert isinstance(fit_card, str)
    assert "outfit suggestion was missing" in fit_card.lower()


def test_compare_price_returns_assessment():
    results = search_listings("vintage graphic tee", size=None, max_price=50)
    assessment = compare_price(results[0], results)
    assert isinstance(assessment, dict)
    assert "assessment" in assessment
    assert "reasoning" in assessment


def test_check_trends_returns_tip():
    trend = check_trends("vintage graphic tee", size="M")
    assert isinstance(trend, dict)
    assert "trend_summary" in trend
    assert "styling_tip" in trend


def test_load_style_profile_returns_dict():
    profile = load_style_profile()
    assert isinstance(profile, dict)