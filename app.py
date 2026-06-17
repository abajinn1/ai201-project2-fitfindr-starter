"""
app.py

Gradio interface for FitFindr. The layout and wiring are already set up —
handle_query() calls run_agent() and maps the session results to output panels.

Run with:
    python app.py
"""

import gradio as gr

from agent import run_agent
from utils.data_loader import get_example_wardrobe, get_empty_wardrobe


# ── formatting helpers ────────────────────────────────────────────────────────

def _format_listing(item: dict, session: dict) -> str:
    """Format the selected listing and stretch-feature info for the first panel."""
    if not item:
        return session.get("error") or "No listing was selected."

    title = item.get("title", "Untitled listing")
    price = item.get("price", "Unknown")
    platform = item.get("platform", "Unknown platform")
    size = item.get("size", "Unknown size")
    condition = item.get("condition", "Unknown condition")
    category = item.get("category", "Unknown category")
    brand = item.get("brand", "Unknown brand")
    colors = ", ".join(item.get("colors", []) or [])
    style_tags = ", ".join(item.get("style_tags", []) or [])
    description = item.get("description", "")

    lines = [
        f"Top listing: {title}",
        f"Price: ${float(price):.0f}" if isinstance(price, (int, float)) else f"Price: {price}",
        f"Platform: {platform}",
        f"Size: {size}",
        f"Condition: {condition}",
        f"Category: {category}",
        f"Brand: {brand}",
    ]

    if colors:
        lines.append(f"Colors: {colors}")

    if style_tags:
        lines.append(f"Style tags: {style_tags}")

    if description:
        lines.append(f"\nDescription: {description}")

    fallback_message = session.get("fallback_message")
    if fallback_message:
        lines.append(f"\nFallback used: {fallback_message}")

    price_assessment = session.get("price_assessment")
    if price_assessment:
        lines.append(f"\nPrice check: {price_assessment.get('reasoning', '')}")

    trend_data = session.get("trend_data")
    if trend_data:
        lines.append(f"\nTrend note: {trend_data.get('trend_summary', '')}")
        lines.append(f"Trend styling tip: {trend_data.get('styling_tip', '')}")

    style_profile = session.get("style_profile")
    if style_profile:
        keywords = style_profile.get("style_keywords", [])
        preferred_items = style_profile.get("preferred_items", [])
        if keywords or preferred_items:
            lines.append("\nSaved style memory loaded:")
            if keywords:
                lines.append(f"- Style keywords: {', '.join(keywords)}")
            if preferred_items:
                lines.append(f"- Preferred items: {', '.join(preferred_items)}")

    return "\n".join(lines)


# ── query handler ─────────────────────────────────────────────────────────────

def handle_query(user_query: str, wardrobe_choice: str) -> tuple[str, str, str]:
    """
    Called by Gradio when the user submits a query.

    Returns:
        (listing_text, outfit_suggestion, fit_card)
    """
    if not user_query or not user_query.strip():
        return "Please enter what kind of secondhand item you want to find.", "", ""

    if wardrobe_choice == "Empty wardrobe (new user)":
        wardrobe = get_empty_wardrobe()
    else:
        wardrobe = get_example_wardrobe()

    session = run_agent(user_query, wardrobe)

    if session.get("error"):
        error_text = session["error"]

        if session.get("fallback_message"):
            error_text = f"{session['fallback_message']}\n\n{error_text}"

        return error_text, "", ""

    listing_text = _format_listing(session.get("selected_item"), session)
    outfit_suggestion = session.get("outfit_suggestion") or ""
    fit_card = session.get("fit_card") or ""

    return listing_text, outfit_suggestion, fit_card


# ── interface ─────────────────────────────────────────────────────────────────

EXAMPLE_QUERIES = [
    "vintage graphic tee under $30",
    "90s track jacket in size M",
    "flowy midi skirt under $40",
    "black combat boots size 8",
    "designer ballgown size XXS under $5",   # deliberate no-results test
]


def build_interface():
    with gr.Blocks(title="FitFindr") as demo:
        gr.Markdown("""
# FitFindr 🛍️
Find secondhand pieces and get outfit ideas based on your wardrobe.
Describe what you're looking for — include size and price if you want to filter.
        """)

        with gr.Row():
            query_input = gr.Textbox(
                label="What are you looking for?",
                placeholder="e.g. vintage graphic tee under $30, size M",
                lines=2,
                scale=3,
            )
            wardrobe_choice = gr.Radio(
                choices=["Example wardrobe", "Empty wardrobe (new user)"],
                value="Example wardrobe",
                label="Wardrobe",
                scale=1,
            )

        submit_btn = gr.Button("Find it", variant="primary")

        with gr.Row():
            listing_output = gr.Textbox(
                label="🛍️ Top listing found",
                lines=12,
                interactive=False,
            )
            outfit_output = gr.Textbox(
                label="👗 Outfit idea",
                lines=12,
                interactive=False,
            )
            fitcard_output = gr.Textbox(
                label="✨ Your fit card",
                lines=12,
                interactive=False,
            )

        gr.Examples(
            examples=[[q, "Example wardrobe"] for q in EXAMPLE_QUERIES],
            inputs=[query_input, wardrobe_choice],
            label="Try these queries",
        )

        submit_btn.click(
            fn=handle_query,
            inputs=[query_input, wardrobe_choice],
            outputs=[listing_output, outfit_output, fitcard_output],
        )
        query_input.submit(
            fn=handle_query,
            inputs=[query_input, wardrobe_choice],
            outputs=[listing_output, outfit_output, fitcard_output],
        )

    return demo


if __name__ == "__main__":
    demo = build_interface()
    demo.launch()