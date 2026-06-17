# FitFindr — Starter Kit (Ryan DeJong for CodePath)

This starter kit contains everything needed to complete CodePath AI201 Project 2: FitFindr. FitFindr is a multi-tool AI agent that helps a user search secondhand clothing listings, decide how a selected item fits with their wardrobe, and generate a short shareable fit card caption.

My completed implementation uses the starter project structure, fills in the required tools, wires them through a conditional planning loop, stores state across tool calls, handles failure paths, and adds stretch features for retry fallback, price comparison, style profile memory, and local trend awareness.

## What's Included

```
ai201-project2-fitfindr-starter/
├── data/
│   ├── listings.json              # 40 mock secondhand listings
│   └── wardrobe_schema.json       # Wardrobe format + example and empty wardrobe data
├── utils/
│   └── data_loader.py             # Helper functions for loading listings and wardrobe data
├── tests/
│   └── test_tools.py              # Pytest tests for required tools and stretch tools
├── planning.md                    # Completed planning document, tool specs, agent diagram, and AI tool plan
├── tools.py                       # Required tools and stretch tools
├── agent.py                       # Planning loop, query parsing, session state, and tool orchestration
├── app.py                         # Gradio interface and output formatting
├── README.md                      # Project documentation
└── requirements.txt               # Python dependencies
```

The main implementation files are:

* `tools.py`: contains the standalone tools that can be tested individually.
* `agent.py`: contains the planning loop and session state management.
* `app.py`: contains the Gradio interface and maps agent results into the output panels.
* `planning.md`: documents the implementation plan, architecture, tool specs, error paths, and AI tool plan.
* `tests/test_tools.py`: verifies the core tool behavior and failure handling.

## Setup

**macOS / Linux:**

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

**Windows:**

```bash
python -m venv .venv
source .venv/Scripts/activate
pip install -r requirements.txt
```

Set your Groq API key in a `.env` file. The `.env` file should be in the project root and should not be committed to GitHub.

```
GROQ_API_KEY=your_key_here
```

Verify the starter data loads correctly:

```bash
python utils/data_loader.py
```

Expected behavior: the script should report that 40 listings loaded and that the example wardrobe has 10 items.

Run the tool tests:

```bash
pytest tests/
```

Run the Gradio app:

```bash
python app.py
```

Then open the local URL shown in the terminal. During testing, my app ran at:

```text
http://127.0.0.1:7860
```

## The Mock Listings Dataset

`data/listings.json` contains 40 mock secondhand listings across categories such as tops, bottoms, outerwear, shoes, and accessories. The styles include vintage, y2k, grunge, cottagecore, streetwear, and more.

Each listing has these fields:

* `id`: unique listing ID
* `title`: listing title
* `description`: text description of the item
* `category`: item category such as tops, bottoms, shoes, or outerwear
* `style_tags`: list of style keywords
* `size`: listed size
* `condition`: item condition
* `price`: item price as a number
* `colors`: list of item colors
* `brand`: brand name or `None`
* `platform`: resale platform such as Depop, Poshmark, or eBay

Load the listing data with:

```python
from utils.data_loader import load_listings

listings = load_listings()
```

My `search_listings` tool uses these fields to filter by size and price, then score relevance against the user’s description. For example, a query like `"vintage graphic tee under $30, size M"` is parsed into a description, size, and price limit, then compared against listing titles, descriptions, categories, colors, platforms, brands, and style tags.

## The Wardrobe Schema

`data/wardrobe_schema.json` defines the format the agent uses to represent a user's existing wardrobe. It includes:

* `schema`: field definitions for a wardrobe item
* `example_wardrobe`: a sample wardrobe with 10 items used for testing and demos
* `empty_wardrobe`: a starting template for a new user with no saved wardrobe items

Load an example wardrobe with:

```python
from utils.data_loader import get_example_wardrobe

wardrobe = get_example_wardrobe()
```

Load an empty wardrobe with:

```python
from utils.data_loader import get_empty_wardrobe

wardrobe = get_empty_wardrobe()
```

The app lets the user choose between:

* `Example wardrobe`
* `Empty wardrobe (new user)`

This matters because `suggest_outfit(new_item, wardrobe)` must work in both cases. If the wardrobe has items, the agent suggests an outfit using named wardrobe pieces. If the wardrobe is empty, the agent gives general styling advice instead of crashing.

## Tool Inventory

This section documents each tool’s function name, input parameters, return value, purpose, and failure behavior. The documented interfaces match the actual function signatures in `tools.py`.

### Required Tool 1: `search_listings(description: str, size: str | None = None, max_price: float | None = None) -> list[dict]`

**Purpose:**
Searches the mock secondhand listings dataset for items matching the user's requested description, size, and maximum price.

**Inputs:**

* `description` (`str`): The item the user wants, such as `"vintage graphic tee"`, `"denim jacket"`, or `"black boots"`.
* `size` (`str | None`): Requested size, such as `"M"` or `"L"`. If `None`, the tool skips size filtering.
* `max_price` (`float | None`): The highest price the user wants to pay. If `None`, the tool skips price filtering.

**Output:**
Returns a list of listing dictionaries sorted by relevance. Each listing dictionary may contain:

* `id`
* `title`
* `description`
* `category`
* `style_tags`
* `size`
* `condition`
* `price`
* `colors`
* `brand`
* `platform`

**Failure behavior:**
If no listings match, the tool returns an empty list `[]` instead of crashing. The planning loop checks for this and either retries with loosened constraints or returns a helpful error message.

---

### Required Tool 2: `suggest_outfit(new_item: dict, wardrobe: dict) -> str`

**Purpose:**
Given a selected thrift item and the user's wardrobe, suggests a complete outfit.

**Inputs:**

* `new_item` (`dict`): A single listing dictionary selected from the results returned by `search_listings`.
* `wardrobe` (`dict`): A wardrobe dictionary with an `items` list. The list may contain saved clothing items, or it may be empty for a new user.

**Output:**
Returns a non-empty string with a complete outfit suggestion. If the wardrobe has items, the output references specific wardrobe pieces. If the wardrobe is empty, the output gives general styling advice using common basics.

**Failure behavior:**
If `new_item` is missing, the tool returns a clear error string explaining that no selected item was provided. If the wardrobe is empty, the tool still returns styling advice instead of raising an exception.

---

### Required Tool 3: `create_fit_card(outfit: str, new_item: dict) -> str`

**Purpose:**
Turns the outfit suggestion and selected item into a short, shareable fit card caption.

**Inputs:**

* `outfit` (`str`): The outfit suggestion returned by `suggest_outfit`.
* `new_item` (`dict`): The selected listing returned by `search_listings`.

**Output:**
Returns a short social-media-style caption that naturally references the thrifted item, price, platform, and outfit vibe.

**Failure behavior:**
If `outfit` is empty or missing, the tool returns this clear error string instead of throwing an exception:

```text
I could not create a fit card because the outfit suggestion was missing.
```

---

### Stretch Tool 4: `compare_price(new_item: dict, all_listings: list[dict] | None = None) -> dict`

**Purpose:**
Estimates whether the selected listing is a good deal, fair price, or pricey by comparing it against similar listings.

**Inputs:**

* `new_item` (`dict`): The selected listing.
* `all_listings` (`list[dict] | None`): Listings to compare against. If `None`, the tool loads the full listing dataset.

**Output:**
Returns a dictionary with:

```python
{
    "assessment": str,
    "item_price": float,
    "average_comparable_price": float,
    "comparison_count": int,
    "reasoning": str
}
```

**Failure behavior:**
If there are too few comparable listings, the tool returns a limited estimate and explains that the comparison set was small. It does not crash.

---

### Stretch Tool 5: `load_style_profile() -> dict`

**Purpose:**
Loads saved user style preferences from a local JSON file.

**Inputs:**
None.

**Output:**
Returns a style profile dictionary:

```python
{
    "style_keywords": list,
    "preferred_items": list,
    "notes": str
}
```

**Failure behavior:**
If no saved style profile exists, the tool returns an empty default profile instead of crashing.

---

### Stretch Tool 6: `save_style_profile(preferences: dict) -> dict`

**Purpose:**
Saves reusable style preferences from the user query so later interactions can use them.

**Inputs:**

* `preferences` (`dict`): A dictionary containing style keywords, preferred items, or notes.

**Output:**
Returns a dictionary showing whether the save worked and what profile was stored.

**Failure behavior:**
If saving fails, the tool returns a dictionary with `saved: False` and an explanation. The current interaction can still continue.

---

### Stretch Tool 7: `check_trends(description: str, size: str | None = None) -> dict`

**Purpose:**
Returns style trend guidance related to the user's requested item. This implementation uses a local trend map instead of a live external API so the project remains reliable during grading.

**Inputs:**

* `description` (`str`): The user’s requested item or style.
* `size` (`str | None`): The requested size, if provided.

**Output:**
Returns a dictionary with:

```python
{
    "trend_summary": str,
    "tags": list[str],
    "styling_tip": str,
    "size_note": str   # optional
}
```

**Failure behavior:**
If no exact trend match exists, the tool returns a general thrift styling trend and the agent continues.

---

### Planning Loop Explanation

The planning loop is implemented in `run_agent()` inside `agent.py`. It is conditional, meaning the agent checks what happened before deciding which tool to call next. It does not call all tools blindly.

The planning loop works like this:

1. A user enters a natural language query.
2. The agent creates a new session dictionary.
3. The agent parses the query into:

   * `description`
   * `size`
   * `max_price`
4. The agent loads saved style memory with `load_style_profile()`.
5. The agent calls `search_listings(description, size, max_price)`.
6. If no results are found and the user provided a size, the agent retries once with `size=None`.
7. If the fallback search also returns no results, the agent sets `session["error"]` and returns early.
8. If results are found, the agent stores all results in `session["search_results"]`.
9. The agent stores the top result in `session["selected_item"]`.
10. The agent calls `compare_price(session["selected_item"], session["search_results"])`.
11. The agent stores the result in `session["price_assessment"]`.
12. The agent calls `check_trends(description, size)`.
13. The agent stores the result in `session["trend_data"]`.
14. The agent calls `suggest_outfit(session["selected_item"], wardrobe)`.
15. If the outfit suggestion is missing, the agent sets `session["error"]` and returns early.
16. If the outfit suggestion exists, the agent stores it in `session["outfit_suggestion"]`.
17. The agent calls `create_fit_card(session["outfit_suggestion"], session["selected_item"])`.
18. The agent stores the final caption in `session["fit_card"]`.
19. The agent saves reusable style preferences with `save_style_profile()` when the query contains clear preferences.
20. The completed session is returned to the Gradio app.

The most important adaptive behavior is the no-results path. If `search_listings` fails, the agent does not continue to `suggest_outfit` or `create_fit_card` with empty input.

---

### State Management Approach

The agent uses a session dictionary as the single source of truth for one interaction.

The session structure includes:

```python
session = {
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
```

The main state flow is:

1. `search_listings` returns listing dictionaries.
2. The agent stores the full result list in `session["search_results"]`.
3. The agent stores the top listing in `session["selected_item"]`.
4. `session["selected_item"]` is passed directly into `suggest_outfit`.
5. `suggest_outfit` returns a string.
6. That string is stored in `session["outfit_suggestion"]`.
7. `session["outfit_suggestion"]` and `session["selected_item"]` are passed into `create_fit_card`.
8. The final caption is stored in `session["fit_card"]`.

This proves the agent passes information across tools without asking the user to re-enter the selected listing or outfit suggestion.

## Interaction Walkthrough

**User query:**
`I'm looking for a vintage graphic tee under $30, size M. I mostly wear baggy jeans and chunky sneakers.`

**Step 1 — Tool called:**

* Tool: query parser inside `agent.py`
* Input: the full user query
* Why this tool: the natural language request needs to be turned into structured search inputs.
* Output:

```python
{
    "description": "vintage graphic tee",
    "size": "M",
    "max_price": 30.0
}
```

The agent also detects reusable style preferences such as `baggy`, `chunky`, `vintage`, `baggy jeans`, and `chunky sneakers`.

**Step 2 — Tool called:**

* Tool: `search_listings`
* Input:

```python
search_listings("vintage graphic tee", size="M", max_price=30.0)
```

* Why this tool: the agent needs to find a real listing before it can suggest an outfit or create a fit card.
* Output from app testing:

```text
Top listing: Y2K Baby Tee — Butterfly Print
Price: $18
Platform: depop
Size: S/M
Condition: excellent
Category: tops
Brand: None
Colors: white, pink, purple
Style tags: y2k, vintage, graphic tee, cottagecore
```

The selected item is stored in `session["selected_item"]`.

**Step 3 — Tool called:**

* Tool: `compare_price`
* Input:

```python
compare_price(session["selected_item"], session["search_results"])
```

* Why this tool: this stretch tool checks whether the selected listing is reasonably priced compared with similar listings.
* Output from app testing:

```text
This looks like a good deal: the item is $18, while comparable listings average about $23.
```

The result is stored in `session["price_assessment"]`.

**Step 4 — Tool called:**

* Tool: `check_trends`
* Input:

```python
check_trends("vintage graphic tee", size="M")
```

* Why this tool: this stretch tool adds trend guidance that can influence the outfit suggestion.
* Output from app testing:

```text
Vintage tees are leaning into relaxed 90s and early-2000s styling.
```

The trend styling tip recommends balancing the tee with baggy denim, chunky sneakers, and one intentional accessory. The result is stored in `session["trend_data"]`.

**Step 5 — Tool called:**

* Tool: `suggest_outfit`
* Input:

```python
suggest_outfit(session["selected_item"], wardrobe)
```

* Why this tool: the agent now has a selected listing and can suggest how to wear it with the user’s wardrobe.
* Output from app testing:

```text
Pair the Y2K Baby Tee with the baggy straight-leg jeans, chunky white sneakers, and vintage black denim jacket. This outfit has a casual, retro vibe.
```

The outfit suggestion is stored in `session["outfit_suggestion"]`.

**Step 6 — Tool called:**

* Tool: `create_fit_card`
* Input:

```python
create_fit_card(session["outfit_suggestion"], session["selected_item"])
```

* Why this tool: the agent has a complete outfit suggestion and can turn it into a shareable caption.
* Output from app testing:

```text
Just scored this adorable butterfly print tee on Depop for $18 and I'm obsessed. Paired it with my fave baggy jeans, chunky sneakers, and a vintage denim jacket for a casual retro look.
```

The fit card is stored in `session["fit_card"]`.

**Final output to user:**

The Gradio app displays:

1. The selected listing
2. Price comparison
3. Trend note
4. Saved style memory if available
5. Outfit idea
6. Fit card caption

This interaction shows the full state flow from user query to listing, from listing to outfit, and from outfit to final fit card.

## Error Handling and Fail Points

| Tool                 | Failure mode                          | Agent response                                                                                                                                                                                                                                                                                                                                                       |
| -------------------- | ------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `search_listings`    | No results match the query            | The tool returns `[]`. If a size was provided, the agent retries once with the size filter removed. If there are still no results, the agent sets `session["error"]` and returns: `"I couldn't find listings for that search. Try a broader item description, a larger budget, or a different size."` The agent does not call `suggest_outfit` or `create_fit_card`. |
| `suggest_outfit`     | Wardrobe is empty                     | The tool still returns general styling advice using common basics. In testing, the empty wardrobe path returned an outfit suggestion instead of crashing.                                                                                                                                                                                                            |
| `create_fit_card`    | Outfit input is missing or incomplete | The tool returns: `"I could not create a fit card because the outfit suggestion was missing."` It does not raise an exception.                                                                                                                                                                                                                                       |
| `compare_price`      | Too few comparable listings exist     | The tool returns a limited price assessment and explains that the comparison set was small.                                                                                                                                                                                                                                                                          |
| `load_style_profile` | No saved profile exists               | The tool returns an empty default profile.                                                                                                                                                                                                                                                                                                                           |
| `save_style_profile` | Style profile cannot be saved         | The tool returns `saved: False` and preserves the current app flow.                                                                                                                                                                                                                                                                                                  |
| `check_trends`       | No exact trend match exists           | The tool returns a general thrift styling trend.                                                                                                                                                                                                                                                                                                                     |

I deliberately tested this failure query:

```text
designer ballgown size XXS under $5
```

The app returned this specific message in the first output panel:

```text
I couldn't find listings for that search. Try a broader item description, a larger budget, or a different size.
```

The outfit and fit card panels stayed blank. This proves the agent handled the failure without crashing and did not call later tools with missing search input.

I also tested the empty wardrobe path. With `Empty wardrobe (new user)` selected, the agent still returned an outfit suggestion instead of failing.

## Spec Reflection

**One way planning.md helped during implementation:**

The `planning.md` file helped because it forced me to define each tool’s inputs, return values, and failure behavior before writing code. That made implementation faster because I could compare each function against the spec instead of guessing what it should return. The planning loop section was especially useful because it reminded me that the agent should branch after `search_listings` and should not call later tools when no listing was found.

**One divergence from your spec, and why:**

One divergence was that I used a simple rule-based parser for `description`, `size`, and `max_price` instead of using an LLM to parse the query. I chose this because the dataset is small and predictable, and deterministic parsing was faster to test and easier to debug. The LLM is still used for the generative parts of the project, including `suggest_outfit` and `create_fit_card`.

**AI usage transparency:**

I used ChatGPT in several specific ways during the project.

1. For `tools.py`, I gave ChatGPT the tool specifications from `planning.md`, including the function names, input parameters, return values, and failure modes. ChatGPT produced implementations for `search_listings`, `suggest_outfit`, `create_fit_card`, and the stretch tools. I reviewed the generated code to make sure the function signatures matched the README and that failure paths returned useful values instead of crashing.

2. For `agent.py`, I gave ChatGPT the Planning Loop, State Management, and Architecture sections from `planning.md`. ChatGPT helped produce a session-based planning loop that parses the query, calls `search_listings`, branches on empty search results, stores `selected_item`, calls `suggest_outfit`, and then calls `create_fit_card`. I revised the generated code after testing because the original size parser treated `"size M."` as `"M."`; I fixed it by stripping punctuation from extracted sizes.

3. For `app.py`, I used ChatGPT to help finish `handle_query()` and map the session dictionary into the three Gradio output panels. I verified the output manually in the browser by testing a happy-path query and a deliberate no-results query.

**Testing completed:**

I added pytest tests in `tests/test_tools.py`.

The tests cover:

* successful listing search
* empty listing search
* price filter behavior
* empty wardrobe outfit generation
* empty outfit fit card error handling
* price comparison output
* trend guidance output
* style profile loading

I ran:

```bash
pytest tests/
```

The result was:

```text
8 passed
```

I also tested the full CLI flow with:

```bash
python agent.py
```

That tested the happy path, empty wardrobe path, and no-results path.

I tested the Gradio app with:

```bash
python app.py
```

The happy-path app test populated all three output panels:

* Top listing found
* Outfit idea
* Fit card

The failure-path app test showed a specific error in the first panel and kept the outfit and fit card panels blank.

**Stretch features completed:**

* Retry logic with fallback: if the search has no results and a size was provided, the agent retries once without the size filter.
* Price comparison: `compare_price` returns an assessment and reasoning based on comparable listings.
* Style profile memory: the agent saves and loads preferences in `style_profile.json`.
* Trend awareness: `check_trends` returns a local trend summary, tags, and styling tip.

## Where to Start

To run or review this completed project:

1. Create and activate the virtual environment.
2. Install dependencies with `pip install -r requirements.txt`.
3. Add a `.env` file with `GROQ_API_KEY=your_key_here`.
4. Verify data loading with:

```bash
python utils/data_loader.py
```

5. Run the tests with:

```bash
pytest tests/
```

6. Run the app with:

```bash
python app.py
```

7. Open the local Gradio URL shown in the terminal.
8. Test a happy-path query:

```text
I'm looking for a vintage graphic tee under $30, size M. I mostly wear baggy jeans and chunky sneakers.
```

9. Test a deliberate failure query:

```text
designer ballgown size XXS under $5
```

10. For the demo video, show:

    * the happy-path interaction from query to fit card
    * the top listing flowing into the outfit suggestion
    * the outfit suggestion flowing into the fit card
    * the failure query returning a specific error
    * the outfit and fit card panels staying blank during the failure path
    * stretch feature outputs such as price comparison, trend note, style memory, and retry fallback when triggered

Completed files:

* `planning.md`
* `tools.py`
* `agent.py`
* `app.py`
* `tests/test_tools.py`
* `README.md`
