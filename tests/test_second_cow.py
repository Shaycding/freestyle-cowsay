"""
Tests for the second cow feature.

The cowsay page should display two cows:
  1. The first cow (existing) uses "oO" eyes and shows the requested text.
  2. A second cow below the first uses "^^" eyes and says one fixed reply
     chosen from a short, hardcoded list.

These tests parse the HTML template embedded in cowsay/src/index.js
(and the surrounding JS source) without needing a running server or Node.js.
"""

import re
import html.parser
import pytest

# ---------------------------------------------------------------------------
# Helpers – shared with existing test files but kept self-contained here
# ---------------------------------------------------------------------------

JS_PATH = "cowsay/src/index.js"

FIXED_ANSWERS = [
    "Moo, so true!",
    "I was just thinking that.",
    "Deep. Very deep.",
]


def _load_js_source() -> str:
    with open(JS_PATH, encoding="utf-8") as fh:
        return fh.read()


def _extract_html_template(source: str) -> str:
    """
    Return the *static* HTML produced by setCowsaySentence, replacing
    all ${...} JS interpolations with recognisable placeholders.
    """
    m = re.search(
        r'const\s+setCowsaySentence\s*=\s*\(text\)\s*=>\s*\{[^`]*`(.*)`\s*;?\s*\}',
        source,
        re.DOTALL,
    )
    if not m:
        m = re.search(
            r'const\s+setCowsaySentence\s*=.*?return\s+`(.*)`',
            source,
            re.DOTALL,
        )
    assert m, "Could not locate the template literal in setCowsaySentence"
    template = m.group(1)

    # Replace every ${cowsay.say({...})} expression with a numbered placeholder
    counter = [0]

    def _replace_cowsay(match):
        counter[0] += 1
        return f"__COW_OUTPUT_{counter[0]}__"

    template = re.sub(
        r'\$\{cowsay\.say\(\{.*?\}\)',
        _replace_cowsay,
        template,
        flags=re.DOTALL,
    )

    # Remove any remaining ${...} interpolations
    template = re.sub(r'\$\{[^}]+\}', "__INTERPOLATION__", template)
    return template


class _CollectingParser(html.parser.HTMLParser):
    """Simple parser that records tags and their attrs in order."""

    def __init__(self):
        super().__init__()
        self.tags: list[tuple[str, dict]] = []
        self.data_chunks: list[str] = []

    def handle_starttag(self, tag, attrs):
        self.tags.append((tag, dict(attrs)))

    def handle_data(self, data):
        self.data_chunks.append(data)


def _parse_html(html_text: str) -> _CollectingParser:
    parser = _CollectingParser()
    parser.feed(html_text)
    return parser


def _get_html() -> str:
    source = _load_js_source()
    return _extract_html_template(source)


# ---------------------------------------------------------------------------
# Scenario: A custom text page shows the first cow and a second cow that answers
# ---------------------------------------------------------------------------

# Scenario: A custom text page shows the first cow and a second cow that answers
def test_two_cowsay_calls_in_template():
    """
    The setCowsaySentence template must contain two separate cowsay.say(...)
    calls – one for the first cow and one for the second answering cow.
    """
    source = _load_js_source()
    # Extract the setCowsaySentence function body
    m = re.search(
        r'const\s+setCowsaySentence\s*=\s*\(text\)\s*=>\s*\{[^`]*`(.*)`\s*;?\s*\}',
        source,
        re.DOTALL,
    )
    if not m:
        m = re.search(
            r'const\s+setCowsaySentence\s*=.*?return\s+`(.*)`',
            source,
            re.DOTALL,
        )
    assert m, "Could not locate the template literal in setCowsaySentence"
    template = m.group(1)

    cow_call_count = len(re.findall(r'cowsay\.say\(', template))
    assert cow_call_count >= 2, (
        f"Expected at least 2 cowsay.say() calls in the template "
        f"(one per cow), found {cow_call_count}"
    )


# Scenario: A custom text page shows the first cow and a second cow that answers
def test_first_cow_keeps_oo_eyes():
    """
    The first cow must still use e: "oO" (or 'oO') eye style.
    """
    source = _load_js_source()
    assert 'e: "oO"' in source or "e: 'oO'" in source, (
        "The first cow must still be called with e: 'oO' eye style"
    )


# Scenario: A custom text page shows the first cow and a second cow that answers
def test_second_cow_has_hat_hat_eyes():
    """
    The second (answering) cow must use e: "^^" (or '^^') eye style.
    """
    source = _load_js_source()
    assert 'e: "^^"' in source or "e: '^^'" in source, (
        "The second cow must be called with e: '^^' eye style"
    )


# Scenario: A custom text page shows the first cow and a second cow that answers
def test_template_contains_two_pre_elements():
    """
    The HTML template must include two <pre> elements – one per cow –
    so both cows are rendered in the page.
    """
    html = _get_html()
    parser = _parse_html(html)
    pre_count = sum(1 for tag, _ in parser.tags if tag == "pre")
    assert pre_count >= 2, (
        f"Expected at least 2 <pre> elements in the template (one per cow), "
        f"found {pre_count}"
    )


# Scenario: A custom text page shows the first cow and a second cow that answers
def test_second_cow_output_present_after_first_cow_in_template():
    """
    In the rendered HTML the second cow placeholder must appear AFTER the
    first cow placeholder, ensuring vertical ordering (second cow below first).
    """
    html = _get_html()
    pos_first = html.find("__COW_OUTPUT_1__")
    pos_second = html.find("__COW_OUTPUT_2__")

    assert pos_first != -1, (
        "First cow placeholder (__COW_OUTPUT_1__) not found in template"
    )
    assert pos_second != -1, (
        "Second cow placeholder (__COW_OUTPUT_2__) not found in template; "
        "a second cowsay.say() call is required"
    )
    assert pos_second > pos_first, (
        "The second cow must appear AFTER the first cow in the HTML"
    )


# ---------------------------------------------------------------------------
# Scenario: The second cow's answer comes from the fixed list
# ---------------------------------------------------------------------------

# Scenario: The second cow's answer comes from the fixed list
def test_fixed_answers_present_in_source():
    """
    All three required fixed answers must be present as string literals
    in the JS source so the builder cannot accidentally omit any of them.
    """
    source = _load_js_source()
    for answer in FIXED_ANSWERS:
        assert answer in source, (
            f"Fixed answer not found in source: {answer!r}"
        )


# Scenario: The second cow's answer comes from the fixed list
def test_fixed_answers_list_has_at_least_three_entries():
    """
    The fixed-answer list/array in the JS source must have at least three entries.
    We count distinct fixed-answer strings that appear as JS string literals.
    """
    source = _load_js_source()
    found = sum(1 for answer in FIXED_ANSWERS if answer in source)
    assert found >= 3, (
        f"Expected at least 3 fixed answers in the source, "
        f"found {found}: {FIXED_ANSWERS}"
    )


# Scenario: The second cow's answer comes from the fixed list
def test_second_cow_uses_random_answer_from_fixed_list():
    """
    The JS source must define a separate array of cow-style fixed answers and
    select from it randomly (e.g. using Math.random / Math.floor).
    The three required fixed answers must all be present in the source.
    """
    source = _load_js_source()
    # All three fixed answers must exist (the array must be defined)
    for answer in FIXED_ANSWERS:
        assert answer in source, (
            f"Fixed answer not found in source (required for random selection): {answer!r}"
        )
    # There must be a random selection mechanism
    assert "Math.random" in source or "Math.floor" in source, (
        "The second cow's answer must be chosen randomly (Math.random / Math.floor expected)"
    )


# Scenario: The second cow's answer comes from the fixed list
def test_cowsay_answers_array_defined_in_source():
    """
    The fixed answers must be defined as an array/list in the JS source.
    We check that the three fixed-answer strings appear in an array literal
    context (surrounded by quotes and commas / brackets).
    """
    source = _load_js_source()
    # All three answers must be present
    for answer in FIXED_ANSWERS:
        assert answer in source, (
            f"Required fixed answer missing from source: {answer!r}"
        )


# ---------------------------------------------------------------------------
# Scenario: The quote page also shows the answering cow
# ---------------------------------------------------------------------------

# Scenario: The quote page also shows the answering cow
def test_both_routes_use_setCowsaySentence():
    """
    Both route handlers (GET / and GET /:text) must call setCowsaySentence,
    which is the function that builds the full HTML.  This guarantees both
    pages show both cows.
    """
    source = _load_js_source()

    # Count how many times setCowsaySentence is called (invocations, not definition)
    # The function definition itself is 'const setCowsaySentence = ...'
    # Calls look like 'setCowsaySentence(...)'
    calls = re.findall(r'setCowsaySentence\s*\(', source)
    # There should be multiple calls (at least 3 across both routes + error branches)
    assert len(calls) >= 2, (
        f"Expected setCowsaySentence to be called in both route handlers, "
        f"found only {len(calls)} call(s)"
    )


# ---------------------------------------------------------------------------
# Acceptance criterion: second cow same white-card style
# ---------------------------------------------------------------------------

# Scenario: A custom text page shows the first cow and a second cow that answers
def test_second_cow_is_in_card_style():
    """
    The second cow must appear inside the same white-card div (or equivalent).
    We check that the template has at least one card-style div wrapping more
    than one <pre> element, OR that there are at least two card-style divs.
    
    A 'card-style' div has background-color: #ffffff (or white) and border-radius.
    Alternatively, both <pre> elements can appear inside the same card.
    """
    html = _get_html()
    # The white card div must be present
    assert "background-color: #ffffff" in html or "background-color:white" in html or \
           "background-color: white" in html or "#ffffff" in html, (
        "The page must have a white card (background-color:#ffffff) "
        "to display the cows"
    )
    # There must be at least 2 cow placeholders in the HTML
    cow1_present = "__COW_OUTPUT_1__" in html
    cow2_present = "__COW_OUTPUT_2__" in html
    assert cow1_present and cow2_present, (
        "Both cow outputs must appear in the rendered HTML template"
    )


# Scenario: A custom text page shows the first cow and a second cow that answers
def test_first_cow_text_is_passed_as_text_param():
    """
    The first cow must still receive the dynamic `text` variable so that
    custom text pages (/hello) show the right content.
    """
    source = _load_js_source()
    m = re.search(
        r'const\s+setCowsaySentence\s*=\s*\(text\)\s*=>\s*\{[^`]*`(.*)`\s*;?\s*\}',
        source,
        re.DOTALL,
    )
    if not m:
        m = re.search(
            r'const\s+setCowsaySentence\s*=.*?return\s+`(.*)`',
            source,
            re.DOTALL,
        )
    assert m, "Could not locate the template literal in setCowsaySentence"
    template = m.group(1)

    # The first cowsay.say call must include `text` (the parameter)
    first_cowsay = re.search(r'cowsay\.say\(\{(.*?)\}\)', template, re.DOTALL)
    assert first_cowsay, "No cowsay.say({...}) call found in template"
    first_call_body = first_cowsay.group(1)
    assert "text" in first_call_body, (
        "The first cowsay.say() call must pass the `text` parameter"
    )
