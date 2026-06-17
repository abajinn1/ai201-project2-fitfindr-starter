# FitFindr — planning.md

> Complete this document before writing any implementation code.
> This spec and diagram will guide the implementation of FitFindr, a multi-tool AI agent that searches secondhand listings, suggests outfits, creates fit cards, and includes stretch features.

---

## Tools

List every tool your agent will use. For each tool, fill in all four fields.
You must have at least 3 tools. The three required tools are listed — add any additional tools below them.

### Tool 1: search_listings

**What it does:**
`search_listings` searches the mock secondhand listings dataset for items that match the user's requested item description, size, and maximum price. It returns a ranked list of matching thrift listings so the agent can choose one item to style.

**Input parameters:**

* `description` (`str`): The item the user is looking for, such as `"vintage graphic tee"`, `"denim jacket"`, or `"black boots"`.
* `size` (`str` or `None`): The requested size, such as `"M"`, `"L"`, or `None` if the user does not provide a size.
* `max_price` (`float` or `None`): The highest price the user wants to pay, such as `30.0`, or `None` if the user does not give a budget.

**What it returns:**
A list of listing dictionaries. Each dictionary can include fields from the mock data such as `id`, `title`, `description`, `category`, `style_tags`, `size`, `condition`, `price`, `colors`, `brand`, and `platform`. The list is filtered by size and price when those values are provided and ranked by how closely the listing matches the description.

**What happens if it fails or returns nothing:**
If no listings match, the tool returns an empty list `[]` instead of crashing. The planning loop then either retries once with loosened constraints or stops with a clear message telling the user to try a broader item description, a different size, or a higher budget. The agent must not call `suggest_outfit` or `create_fit_card` when no item was found.

---

### Tool 2: suggest_outfit

**What it does:**
`suggest_outfit` takes the selected thrift listing and the user's wardrobe, then creates a complete outfit suggestion. It explains how the new item could be worn with existing wardrobe pieces or, if the wardrobe is empty, gives general styling advice.

**Input parameters:**

* `new_item` (`dict`): The selected listing from `search_listings`.
* `wardrobe` (`dict`): The user's wardrobe object. It should contain an `items` list with clothing pieces such as tops, bottoms, shoes, and accessories.

**What it returns:**
A string containing a complete outfit suggestion. The suggestion should mention the selected item, recommend specific styling choices, and use wardrobe pieces when available.

**What happens if it fails or returns nothing:**
If the wardrobe is empty or minimal, the tool still returns useful general styling advice based on the selected item. It does not crash or return a blank string. If `new_item` is missing or invalid, the agent sets an error and does not continue to `create_fit_card`.

---

### Tool 3: create_fit_card

**What it does:**
`create_fit_card` turns the outfit suggestion and selected thrift item into a short, social-media-style fit card caption. The caption should sound like something someone might actually post, not like a product description.

**Input parameters:**

* `outfit` (`str`): The outfit suggestion returned by `suggest_outfit`.
* `new_item` (`dict`): The selected listing from `search_listings`.

**What it returns:**
A short caption string that references the thrifted item, style vibe, and price or platform when useful. The output should vary across different inputs.

**What happens if it fails or returns nothing:**
If `outfit` is empty or missing, the tool returns a clear error message string such as `"I could not create a fit card because the outfit suggestion was missing."` It does not throw a Python exception.

---

### Additional Tools

### Tool 4: compare_price

**What it does:**
`compare_price` is a stretch-feature tool. It estimates whether the selected listing is a good deal, fair price, or pricey by comparing it with similar listings in the mock dataset.

**Input parameters:**

* `new_item` (`dict`): The selected listing.
* `all_listings` (`list[dict]` or `None`): Listings to compare against. If `None`, the tool can load the listings dataset itself.

**What it returns:**
A dictionary containing:

* `assessment` (`str`): A label such as `"good deal"`, `"fair price"`, or `"pricey"`.
* `item_price` (`float`): The selected listing's price.
* `average_comparable_price` (`float`): The average price of comparable listings.
* `comparison_count` (`int`): The number of comparable listings used.
* `reasoning` (`str`): A short explanation of the price judgment.

**What happens if it fails or returns nothing:**
If there are too few comparable listings, the tool returns a limited assessment based on the available data and explains that the comparison set was small. It does not crash.

---

### Tool 5: load_style_profile and save_style_profile

**What it does:**
These stretch-feature tools remember the user's style preferences across sessions. `load_style_profile` retrieves saved preferences, and `save_style_profile` saves useful style hints from the current query.

**Input parameters:**

* `load_style_profile()` takes no input.
* `save_style_profile(preferences)` takes `preferences` (`dict`), such as preferred fit, shoes, colors, or style keywords.

**What it returns:**

* `load_style_profile` returns a saved style profile dictionary or an empty default profile.
* `save_style_profile` returns a confirmation dictionary showing what was saved.

**What happens if it fails or returns nothing:**
If no profile exists yet, `load_style_profile` returns an empty profile instead of crashing. If saving fails, the agent continues the current interaction and tells the user the outfit was generated, but preferences could not be saved.

---

### Tool 6: check_trends

**What it does:**
`check_trends` is a stretch-feature tool that returns style trend guidance related to the user's requested item. To keep the project reliable during grading, it uses a small local trend map based on common public fashion tags and thrift styling categories instead of depending on a live external API.

**Input parameters:**

* `description` (`str`): The item or style the user is searching for.
* `size` (`str` or `None`): The requested size, if provided.

**What it returns:**
A dictionary containing:

* `trend_summary` (`str`): A short explanation of a relevant style trend.
* `tags` (`list[str]`): Trend-related tags, such as `"90s grunge"`, `"oversized"`, `"quiet luxury"`, or `"gorpcore"`.
* `styling_tip` (`str`): A concrete styling suggestion that can influence the outfit recommendation.

**What happens if it fails or returns nothing:**
If no exact trend match exists, the tool returns a general thrift styling trend. The agent can continue even if trend data is generic.

---

## Planning Loop

**How does your agent decide which tool to call next?**

The agent uses a conditional planning loop controlled by the session state. It does not call every tool blindly. It checks what each tool returned before deciding whether to continue, retry, or stop.

1. The user enters a natural-language request.
2. The agent extracts or infers:

   * `description`
   * `size`
   * `max_price`
   * wardrobe or style hints
3. The agent initializes a `session` dictionary with empty values for search results, selected item, price assessment, trend data, outfit suggestion, fit card, fallback message, and error.
4. The agent calls `load_style_profile()` to retrieve saved preferences if available.
5. The agent calls `search_listings(description, size, max_price)`.
6. If `search_listings` returns an empty list:

   * The agent retries once with loosened constraints by removing the size filter.
   * The agent stores a fallback explanation in `session["fallback_message"]`.
   * If the fallback search also returns no results, the agent stores a specific message in `session["error"]`, leaves `session["selected_item"]`, `session["outfit_suggestion"]`, and `session["fit_card"]` as `None`, and returns early.
7. If listings are found:

   * The agent stores all results in `session["search_results"]`.
   * The agent chooses the top result and stores it as `session["selected_item"]`.
8. The agent calls `compare_price(session["selected_item"], session["search_results"])` and stores the result in `session["price_assessment"]`.
9. The agent calls `check_trends(description, size)` and stores the result in `session["trend_data"]`.
10. The agent calls `suggest_outfit(session["selected_item"], wardrobe)`.
11. If `suggest_outfit` returns an empty or invalid string:

* The agent stores an error in `session["error"]`.
* The agent does not call `create_fit_card`.

12. If the outfit suggestion is valid:

* The agent stores it in `session["outfit_suggestion"]`.

13. The agent calls `create_fit_card(session["outfit_suggestion"], session["selected_item"])`.
14. The agent stores the final caption in `session["fit_card"]`.
15. The agent saves clear style preferences from the user query with `save_style_profile()`.
16. The agent returns the final session to the Gradio app.

This loop is adaptive because a successful search continues through all tools, while a failed search retries once and then stops early if there is still no item to style.

---

## State Management

**How does information from one tool get passed to the next?**

The agent uses a `session` dictionary to track state during one interaction. Each tool's output is stored in the session so later tools can reuse it without asking the user to repeat information.

The session tracks:

```python
session = {
    "query": user_query,
    "description": description,
    "size": size,
    "max_price": max_price,
    "wardrobe": wardrobe,
    "style_profile": {},
    "search_results": [],
    "selected_item": None,
    "price_assessment": None,
    "trend_data": None,
    "outfit_suggestion": None,
    "fit_card": None,
    "fallback_message": None,
    "error": None
}
```

The main state flow is:

1. `search_listings` returns a list of listing dictionaries.
2. The planning loop stores the full list in `session["search_results"]`.
3. The planning loop stores the top listing in `session["selected_item"]`.
4. `session["selected_item"]` is passed directly into `suggest_outfit`.
5. The outfit string from `suggest_outfit` is stored in `session["outfit_suggestion"]`.
6. `session["outfit_suggestion"]` and `session["selected_item"]` are passed into `create_fit_card`.
7. The final caption is stored in `session["fit_card"]`.

This proves that state is flowing across tools. The user does not need to re-enter the selected listing or outfit suggestion.

---

## Error Handling

For each tool, describe the specific failure mode you're handling and what the agent does in response.

| Tool                 | Failure mode                          | Agent response                                                                                                                                                                                                                                                                                                        |
| -------------------- | ------------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `search_listings`    | No results match the query            | The tool returns `[]`. The agent retries once with the size filter removed. If fallback also fails, it sets `session["error"]` to: `"I couldn't find listings for that search. Try a broader item description, a larger budget, or a different size."` The agent does not call `suggest_outfit` or `create_fit_card`. |
| `suggest_outfit`     | Wardrobe is empty                     | The tool returns a general outfit suggestion based on the selected item and common styling basics. The agent continues instead of crashing.                                                                                                                                                                           |
| `create_fit_card`    | Outfit input is missing or incomplete | The tool returns a clear error message string instead of raising an exception. The agent stores the message instead of displaying a fake caption.                                                                                                                                                                     |
| `compare_price`      | Too few comparable listings exist     | The tool returns a limited assessment using available listing data and explains that the estimate is based on a small comparison set.                                                                                                                                                                                 |
| `load_style_profile` | No saved profile exists               | The tool returns an empty/default profile and the agent continues normally.                                                                                                                                                                                                                                           |
| `save_style_profile` | Style profile cannot be saved         | The agent continues the current interaction and tells the user the outfit was generated but preferences were not saved.                                                                                                                                                                                               |
| `check_trends`       | No specific trend match exists        | The tool returns a general thrift styling trend and the agent continues.                                                                                                                                                                                                                                              |

---

## Architecture

```mermaid
flowchart TD
    A[User Query] --> B[Planning Loop / run_agent]
    B --> C[Load Style Profile]
    C --> D[Parse description, size, max_price, wardrobe hints]
    D --> E[search_listings(description, size, max_price)]

    E --> F{Any results?}
    F -- No --> G[Retry search with loosened constraints]
    G --> H{Fallback results?}
    H -- No --> I[Set session error and return early]
    H -- Yes --> J[Store fallback message]
    F -- Yes --> K[Store search_results]

    J --> K
    K --> L[Store selected_item = search_results[0]]

    L --> M[compare_price(selected_item, search_results)]
    M --> N[Store price_assessment]

    N --> O[check_trends(description, size)]
    O --> P[Store trend_data]

    P --> Q[suggest_outfit(selected_item, wardrobe)]
    Q --> R{Outfit suggestion valid?}
    R -- No --> S[Set session error and return early]
    R -- Yes --> T[Store outfit_suggestion]

    T --> U[create_fit_card(outfit_suggestion, selected_item)]
    U --> V[Store fit_card]

    V --> W[Save style preferences if found]
    W --> X[Return session to Gradio app]

    I --> X
    S --> X
```

---

## AI Tool Plan

**Milestone 3 — Individual tool implementations:**

I will use ChatGPT to help implement one tool at a time. For each required tool, I will give ChatGPT the matching tool section from this `planning.md` file, including the function name, inputs, return value, and failure mode. I will ask it to implement the function directly inside `tools.py` using the existing starter repo helpers, especially `load_listings()` from `utils/data_loader.py`.

Before using generated code, I will verify that:

* the function signature matches the starter code,
* the return value matches this spec,
* the failure mode is handled without crashing,
* and the tool can be tested directly from the terminal.

For the stretch tools, I will give ChatGPT the Additional Tools section and ask for the simplest reliable implementation that supports the demo and README.

**Milestone 4 — Planning loop and state management:**

I will give ChatGPT the Planning Loop, State Management, and Architecture sections from this file. I will ask it to implement `run_agent()` in `agent.py` so that it branches after `search_listings`, stores values in the session dictionary, retries once when no results are found, and does not call later tools when earlier required data is missing.

Before using generated code, I will check that:

* `search_listings` is not followed blindly if it returns `[]`,
* `selected_item` is stored before `suggest_outfit`,
* `outfit_suggestion` is stored before `create_fit_card`,
* `session["error"]` is set for failure paths,
* and the stretch outputs are stored in session keys.

**Milestone 5 — App wiring and testing:**

I will use ChatGPT to help map the `session` dictionary to the Gradio output panels in `app.py`. I will provide the expected session keys from the State Management section. I will verify the app manually by running a happy-path query and a no-results query.

---

## A Complete Interaction (Step by Step)

Write out what a full user interaction looks like from start to finish — tool call by tool call. Use a specific example query.

**Example user query:** `"I'm looking for a vintage graphic tee under $30, size M. I mostly wear baggy jeans and chunky sneakers. What's out there and how would I style it?"`

**Step 1:**
The agent receives the query and extracts:

* `description = "vintage graphic tee"`
* `size = "M"`
* `max_price = 30.0`
* wardrobe/style hints = baggy jeans and chunky sneakers

The first required tool called is:

```python
search_listings("vintage graphic tee", size="M", max_price=30.0)
```

**Step 2:**
If results are found, the agent stores them:

```python
session["search_results"] = results
session["selected_item"] = results[0]
```

For example, the selected item could be a faded band tee from Depop for $22.

If no results are found, the agent retries with a looser search:

```python
search_listings("vintage graphic tee", size=None, max_price=30.0)
```

If that also fails, the agent returns a useful error message and stops.

**Step 3:**
The agent calls the price comparison stretch tool:

```python
compare_price(session["selected_item"], session["search_results"])
```

The result is stored in:

```python
session["price_assessment"]
```

The user may see something like: `"This looks like a good deal because similar tops average around $28 and this one is $22."`

**Step 4:**
The agent calls the trend awareness stretch tool:

```python
check_trends("vintage graphic tee", size="M")
```

The result is stored in:

```python
session["trend_data"]
```

The trend data can influence the outfit suggestion by adding a 90s grunge or oversized styling direction.

**Step 5:**
The agent calls the second required tool:

```python
suggest_outfit(session["selected_item"], wardrobe)
```

The selected item is passed from session state. The user does not need to re-enter it.

The result is stored:

```python
session["outfit_suggestion"] = outfit
```

**Step 6:**
The agent calls the third required tool:

```python
create_fit_card(session["outfit_suggestion"], session["selected_item"])
```

The outfit suggestion and selected item are both passed from session state.

The result is stored:

```python
session["fit_card"] = fit_card
```

**Final output to user:**
The user sees:

1. the selected listing,
2. a price assessment,
3. a trend note,
4. an outfit suggestion,
5. and a shareable fit card caption.

Example final fit card:

`"thrifted this faded band tee for $22 and built the whole fit around baggy denim + chunky sneakers. very casual 90s main character energy."`

---

## Stretch Feature Plan

I plan to implement the stretch features after the core agent works.

1. **Retry logic with fallback (+1):**

   * If `search_listings` returns no results, retry once with the size filter removed.
   * The agent tells the user what changed.

2. **Price comparison tool (+2):**

   * Compare the selected item's price against similar listings from the same category or overlapping style tags.
   * Return a simple assessment with reasoning.

3. **Style profile memory (+2):**

   * Save basic preferences to a local JSON file.
   * Load the file at the start of future sessions.
   * Demo two interactions where the second uses saved preferences.

4. **Trend awareness tool (+2):**

   * Use a local trend map for reliability during grading.
   * Return trend tags and a styling tip that visibly influence the outfit suggestion.
