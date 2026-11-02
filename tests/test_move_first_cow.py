"""
Tests for the "Move the first cow left and right with buttons" feature.

Strategy: static analysis of cowsay/src/index.js (the HTML template produced
by setCowsaySentence) and cowsay/src/public/move-cow.js.  No running server
or Node.js is required — the same pattern used by all existing test files.

Gherkin scenarios covered
--------------------------
- Move right shifts the first cow to the right
- Move left shifts the first cow back to the left
- The first cow cannot leave the white card
- The second cow does not move
- Reloading the page resets the first cow
"""

import os
import re
import html.parser

JS_PATH = "cowsay/src/index.js"
MOVE_COW_JS_PATH = "cowsay/src/public/move-cow.js"


# ---------------------------------------------------------------------------
# Helpers shared across tests
# ---------------------------------------------------------------------------

def _load_js_source() -> str:
    with open(JS_PATH, encoding="utf-8") as fh:
        return fh.read()


def _extract_html_template(source: str) -> str:
    """
    Return the static HTML produced by setCowsaySentence, replacing
    ${...} JS interpolations with recognisable placeholders.
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
    template = re.sub(r'\$\{[^}]+\}', "__INTERPOLATION__", template)
    return template


def _get_html() -> str:
    return _extract_html_template(_load_js_source())


class _FullParser(html.parser.HTMLParser):
    """Records every start-tag, end-tag and data chunk in order."""

    def __init__(self):
        super().__init__()
        self.events: list = []   # ('start', tag, attrs) | ('end', tag) | ('data', text)

    def handle_starttag(self, tag, attrs):
        self.events.append(("start", tag, dict(attrs)))

    def handle_endtag(self, tag):
        self.events.append(("end", tag))

    def handle_data(self, data):
        self.events.append(("data", data))


def _parse_html(html_text: str) -> _FullParser:
    parser = _FullParser()
    parser.feed(html_text)
    return parser


def _start_tags(parser: _FullParser) -> list:
    return [(tag, attrs) for kind, tag, *rest in parser.events
            if kind == "start" for attrs in [rest[0]]]


# ---------------------------------------------------------------------------
# Acceptance criterion: both pages contain the Move left / Move right buttons
# ---------------------------------------------------------------------------

# Scenario: Move right shifts the first cow to the right
def test_move_right_button_present_in_template():
    """
    The HTML template must contain a <button type="button" id="move-right">
    with the text 'Move right' so both GET / and GET /hello show the button.
    """
    html = _get_html()
    parser = _parse_html(html)
    buttons = [
        attrs for tag, attrs in _start_tags(parser)
        if tag == "button" and attrs.get("id") == "move-right"
    ]
    assert buttons, (
        "No <button id='move-right'> found in the setCowsaySentence template"
    )
    btn = buttons[0]
    assert btn.get("type") == "button", (
        "The Move right button must have type='button'"
    )


# Scenario: Move right shifts the first cow to the right
def test_move_right_button_text():
    """
    The Move right button element must contain the visible text 'Move right'.
    """
    html = _get_html()
    # Find 'Move right' text in proximity to id="move-right"
    assert "Move right" in html, (
        "The text 'Move right' must appear in the template"
    )
    # More specifically: the button with id move-right must precede the text
    btn_pos = html.find('id="move-right"')
    if btn_pos == -1:
        btn_pos = html.find("id='move-right'")
    text_pos = html.find("Move right")
    assert btn_pos != -1, "Button id='move-right' not found in template"
    assert text_pos > btn_pos, (
        "The text 'Move right' must appear after the move-right button open tag"
    )


# Scenario: Move left shifts the first cow back to the left
def test_move_left_button_present_in_template():
    """
    The HTML template must contain a <button type="button" id="move-left">
    with the text 'Move left' so both GET / and GET /hello show the button.
    """
    html = _get_html()
    parser = _parse_html(html)
    buttons = [
        attrs for tag, attrs in _start_tags(parser)
        if tag == "button" and attrs.get("id") == "move-left"
    ]
    assert buttons, (
        "No <button id='move-left'> found in the setCowsaySentence template"
    )
    btn = buttons[0]
    assert btn.get("type") == "button", (
        "The Move left button must have type='button'"
    )


# Scenario: Move left shifts the first cow back to the left
def test_move_left_button_text():
    """
    The Move left button element must contain the visible text 'Move left'.
    """
    html = _get_html()
    btn_pos = html.find('id="move-left"')
    if btn_pos == -1:
        btn_pos = html.find("id='move-left'")
    text_pos = html.find("Move left")
    assert btn_pos != -1, "Button id='move-left' not found in template"
    assert text_pos > btn_pos, (
        "The text 'Move left' must appear after the move-left button open tag"
    )


# ---------------------------------------------------------------------------
# Acceptance criterion: the buttons live inside a cow-controls container
# ---------------------------------------------------------------------------

# Scenario: Move right shifts the first cow to the right
def test_cow_controls_div_present():
    """
    The template must contain a <div id='cow-controls'> that holds both buttons,
    placed inside the white card before the first <pre>.
    """
    html = _get_html()
    parser = _parse_html(html)
    controls = [
        attrs for tag, attrs in _start_tags(parser)
        if tag == "div" and attrs.get("id") == "cow-controls"
    ]
    assert controls, (
        "No <div id='cow-controls'> found in the setCowsaySentence template"
    )


# Scenario: Move right shifts the first cow to the right
def test_cow_controls_appears_before_first_pre():
    """
    The #cow-controls div must appear before the first <pre> element in the HTML
    (i.e. before the first cow is rendered).
    """
    html = _get_html()
    controls_pos = html.find('id="cow-controls"')
    if controls_pos == -1:
        controls_pos = html.find("id='cow-controls'")
    first_pre_pos = html.find("<pre")
    assert controls_pos != -1, "id='cow-controls' not found in template"
    assert first_pre_pos != -1, "No <pre> element found in template"
    assert controls_pos < first_pre_pos, (
        "The #cow-controls div must appear before the first <pre> in the HTML"
    )


# ---------------------------------------------------------------------------
# Acceptance criterion: first cow is wrapped in #first-cow span
# ---------------------------------------------------------------------------

# Scenario: Move right shifts the first cow to the right
def test_first_cow_span_present():
    """
    The template must contain exactly one element with id='first-cow' that
    wraps the first cowsay.say() output.
    """
    html = _get_html()
    parser = _parse_html(html)
    first_cow_elements = [
        attrs for tag, attrs in _start_tags(parser)
        if attrs.get("id") == "first-cow"
    ]
    assert len(first_cow_elements) == 1, (
        f"Expected exactly one element with id='first-cow', "
        f"found {len(first_cow_elements)}"
    )


# Scenario: Move right shifts the first cow to the right
def test_first_cow_span_wraps_first_cow_output():
    """
    The #first-cow element must appear before the first cow placeholder
    (__COW_OUTPUT_1__) and the placeholder must appear before the
    next start tag or closing element after #first-cow.
    """
    html = _get_html()
    first_cow_span_pos = html.find('id="first-cow"')
    if first_cow_span_pos == -1:
        first_cow_span_pos = html.find("id='first-cow'")
    cow1_pos = html.find("__COW_OUTPUT_1__")
    assert first_cow_span_pos != -1, "id='first-cow' not found"
    assert cow1_pos != -1, "First cow output placeholder not found"
    assert first_cow_span_pos < cow1_pos, (
        "The #first-cow element must open before the first cow output"
    )


# Scenario: Move right shifts the first cow to the right
def test_first_cow_span_has_position_relative_style():
    """
    The #first-cow span must have style with position:relative and left:0px
    so that JavaScript can shift it horizontally with the left property.
    """
    html = _get_html()
    parser = _parse_html(html)
    first_cow_elements = [
        attrs for tag, attrs in _start_tags(parser)
        if attrs.get("id") == "first-cow"
    ]
    assert first_cow_elements, "id='first-cow' element not found"
    style = first_cow_elements[0].get("style", "")
    assert "position" in style and "relative" in style, (
        f"#first-cow must have position:relative in its style; got: '{style}'"
    )
    assert "left" in style, (
        f"#first-cow must have a 'left' property in its style; got: '{style}'"
    )


# Scenario: Move right shifts the first cow to the right
def test_first_cow_span_has_data_cow_first():
    """
    The #first-cow element must have data-cow='first' (per the contract).
    """
    html = _get_html()
    parser = _parse_html(html)
    first_cow_elements = [
        attrs for tag, attrs in _start_tags(parser)
        if attrs.get("id") == "first-cow"
    ]
    assert first_cow_elements, "id='first-cow' element not found"
    assert first_cow_elements[0].get("data-cow") == "first", (
        "The #first-cow element must have data-cow='first'"
    )


# Scenario: Move right shifts the first cow to the right
def test_first_cow_span_has_data_offset_zero():
    """
    The #first-cow element must have data-offset='0' on initial render
    (the JavaScript offset starts at 0).
    """
    html = _get_html()
    parser = _parse_html(html)
    first_cow_elements = [
        attrs for tag, attrs in _start_tags(parser)
        if attrs.get("id") == "first-cow"
    ]
    assert first_cow_elements, "id='first-cow' element not found"
    assert first_cow_elements[0].get("data-offset") == "0", (
        "The #first-cow element must have data-offset='0' on initial render"
    )


# Scenario: Move right shifts the first cow to the right
def test_first_cow_still_says_page_text_with_oo_eyes():
    """
    The first cow must still be built with e: 'oO' eyes from the page text
    (acceptance criterion: 'The first cow is still built with oO eyes').
    """
    source = _load_js_source()
    assert 'e: "oO"' in source or "e: 'oO'" in source, (
        "The first cowsay.say() call must still use e: 'oO' eye style"
    )


# ---------------------------------------------------------------------------
# Scenario: The second cow does not move
# ---------------------------------------------------------------------------

# Scenario: The second cow does not move
def test_second_cow_has_data_cow_second():
    """
    The second <pre> (the ^^ cow) must have data-cow='second'.
    The JavaScript only ever modifies #first-cow; data-cow='second' makes the
    distinction explicit in the HTML.
    """
    html = _get_html()
    parser = _parse_html(html)
    pre_tags = [attrs for tag, attrs in _start_tags(parser) if tag == "pre"]
    assert len(pre_tags) >= 2, "Expected at least 2 <pre> elements"
    second_pre = pre_tags[1]
    assert second_pre.get("data-cow") == "second", (
        f"The second <pre> must have data-cow='second'; got: {second_pre}"
    )


# Scenario: The second cow does not move
def test_second_cow_still_comes_after_first_cow_in_html():
    """
    The second cow output placeholder (__COW_OUTPUT_2__) must appear after
    the first cow output placeholder (__COW_OUTPUT_1__) in the template —
    i.e. the second cow is still shown below the first cow.
    """
    html = _get_html()
    pos_first = html.find("__COW_OUTPUT_1__")
    pos_second = html.find("__COW_OUTPUT_2__")
    assert pos_first != -1, "First cow placeholder not found"
    assert pos_second != -1, "Second cow placeholder not found"
    assert pos_second > pos_first, (
        "The second cow (^^) must appear after the first cow in the HTML"
    )


# Scenario: The second cow does not move
def test_second_cow_has_no_first_cow_id():
    """
    The second cow element must NOT have id='first-cow'. Only the first cow
    should be identified for movement; the second cow must be untouched.
    """
    html = _get_html()
    # Find the second cow output and check id='first-cow' is not on/near the second pre
    parser = _parse_html(html)
    # Collect all elements with id=first-cow
    first_cow_ids = [
        attrs for tag, attrs in _start_tags(parser)
        if attrs.get("id") == "first-cow"
    ]
    assert len(first_cow_ids) == 1, (
        f"Exactly one id='first-cow' must exist; found {len(first_cow_ids)}"
    )
    # The second cow output must come after #first-cow closes
    pos_first_cow_id = html.find('id="first-cow"')
    if pos_first_cow_id == -1:
        pos_first_cow_id = html.find("id='first-cow'")
    pos_second_output = html.find("__COW_OUTPUT_2__")
    # The second cow output is NOT inside first-cow wrapper (it comes later)
    assert pos_second_output > pos_first_cow_id, (
        "The second cow output must appear after the #first-cow element opens"
    )


# ---------------------------------------------------------------------------
# Acceptance criterion: script tag for move-cow.js (no inline script)
# ---------------------------------------------------------------------------

# Scenario: Move right shifts the first cow to the right
def test_script_tag_references_move_cow_js():
    """
    The template must include <script src='/move-cow.js'> (or with defer)
    and must NOT have any inline script content (no inline event handlers,
    no script body).
    """
    html = _get_html()
    parser = _parse_html(html)
    script_tags = [
        attrs for tag, attrs in _start_tags(parser)
        if tag == "script"
    ]
    assert script_tags, "No <script> tag found in the template"
    move_cow_scripts = [
        attrs for attrs in script_tags
        if "/move-cow.js" in attrs.get("src", "")
    ]
    assert move_cow_scripts, (
        "No <script src='/move-cow.js'> found in the template; "
        f"script tags present: {script_tags}"
    )


# Scenario: Move right shifts the first cow to the right
def test_no_inline_script_content():
    """
    There must be no inline script body (i.e. no <script>...code...</script>
    without a src attribute) in the template. The button logic must live
    entirely in move-cow.js.
    """
    html = _get_html()
    # Look for script tags with inline content (no src)
    # Replace the placeholder so we can search cleanly
    inline_script = re.search(
        r'<script(?![^>]*\bsrc\b)[^>]*>(.+?)</script>',
        html,
        re.DOTALL | re.IGNORECASE,
    )
    assert not inline_script, (
        "Found an inline <script> block with content — all JS must be in move-cow.js: "
        f"{inline_script.group(0)[:200]}"
    )


# Scenario: Move right shifts the first cow to the right
def test_no_inline_event_handler_attributes():
    """
    No element in the template may have onclick, onkeydown or similar
    inline event handler attributes. All interaction must be wired up
    by move-cow.js via addEventListener.
    """
    html = _get_html()
    inline_handler = re.search(
        r'\bon\w+\s*=\s*["\']',
        html,
        re.IGNORECASE,
    )
    assert not inline_handler, (
        "Found an inline event handler attribute — all event wiring must be "
        f"in move-cow.js: {inline_handler.group(0)}"
    )


# ---------------------------------------------------------------------------
# Acceptance criterion: move-cow.js file exists in the public folder
# ---------------------------------------------------------------------------

# Scenario: Move right shifts the first cow to the right
def test_move_cow_js_file_exists():
    """
    GET /move-cow.js must return 200 with a JS content type. The file is
    served by express.static from the public folder, so it must exist there.
    """
    assert os.path.isfile(MOVE_COW_JS_PATH), (
        f"move-cow.js not found at {MOVE_COW_JS_PATH}; "
        "it must be created so the static middleware can serve it"
    )


# ---------------------------------------------------------------------------
# move-cow.js content tests (contract checks)
# ---------------------------------------------------------------------------

def _load_move_cow_js() -> str:
    with open(MOVE_COW_JS_PATH, encoding="utf-8") as fh:
        return fh.read()


# Scenario: Move right shifts the first cow to the right
def test_move_cow_js_defines_step_20():
    """
    The contract specifies STEP = 20. The script must define this constant
    so that each button click moves the cow by 20 pixels.
    """
    js = _load_move_cow_js()
    assert re.search(r'\bSTEP\s*=\s*20\b', js), (
        "move-cow.js must define STEP = 20 (20-pixel step per click)"
    )


# Scenario: Move right shifts the first cow to the right
def test_move_cow_js_uses_iife():
    """
    The contract specifies the script is wrapped in an IIFE so its variables
    do not pollute the global scope.
    """
    js = _load_move_cow_js()
    # An IIFE looks like (function(){...})() or (() => {...})()
    has_iife = bool(re.search(r'\(function\s*\(', js)) or \
               bool(re.search(r'\(\s*\(\s*\)\s*=>', js)) or \
               bool(re.search(r'}\s*\)\s*\(\s*\)', js))
    assert has_iife, (
        "move-cow.js must be wrapped in an IIFE "
        "(e.g. (function(){ ... })() or (() => { ... })())"
    )


# Scenario: Move right shifts the first cow to the right
def test_move_cow_js_wires_move_right_button():
    """
    The script must reference the move-right button (by id) and add a
    click handler that increases the cow's offset.
    """
    js = _load_move_cow_js()
    assert "move-right" in js, (
        "move-cow.js must reference the 'move-right' button id"
    )


# Scenario: Move left shifts the first cow back to the left
def test_move_cow_js_wires_move_left_button():
    """
    The script must reference the move-left button (by id) and add a
    click handler that decreases the cow's offset.
    """
    js = _load_move_cow_js()
    assert "move-left" in js, (
        "move-cow.js must reference the 'move-left' button id"
    )


# Scenario: Move right shifts the first cow to the right
def test_move_cow_js_looks_up_first_cow_element():
    """
    The script must look up the #first-cow element to be able to shift it.
    """
    js = _load_move_cow_js()
    assert "first-cow" in js, (
        "move-cow.js must look up the '#first-cow' element"
    )


# Scenario: Move left shifts the first cow back to the left
def test_move_cow_js_defines_clamp():
    """
    The contract specifies a clamp() function:
      clamp(offset, max) = Math.min(Math.max(offset, 0), max)
    The script must clamp the offset so it stays within [0, maxOffset].
    """
    js = _load_move_cow_js()
    has_clamp = "clamp" in js or (
        "Math.min" in js and "Math.max" in js
    )
    assert has_clamp, (
        "move-cow.js must implement clamping "
        "(either a clamp() function or Math.min/Math.max)"
    )


# Scenario: The first cow cannot leave the white card
def test_move_cow_js_clamps_offset_to_zero_minimum():
    """
    The offset must never go below 0 (the left edge of the card).
    The script must apply Math.max(..., 0) or equivalent so clicking
    Move left at position 0 keeps the cow at 0.
    """
    js = _load_move_cow_js()
    # Must use Math.max with 0 (directly or via clamp)
    assert "Math.max" in js or re.search(r'clamp\b', js), (
        "move-cow.js must prevent the offset from going below 0 "
        "(Math.max or clamp required)"
    )


# Scenario: The first cow cannot leave the white card
def test_move_cow_js_computes_max_offset():
    """
    The contract specifies maxOffset() = Math.max(0, parentElement.clientWidth - offsetWidth).
    The script must compute a maximum offset based on the container width,
    clamping the cow to the right edge of the card.
    """
    js = _load_move_cow_js()
    has_client_width = "clientWidth" in js
    has_offset_width = "offsetWidth" in js
    assert has_client_width and has_offset_width, (
        "move-cow.js must compute maxOffset using clientWidth and offsetWidth "
        "to keep the cow inside the card"
    )


# Scenario: Reloading the page resets the first cow
def test_move_cow_js_uses_no_persistent_storage():
    """
    Reloading the page must reset the first cow to its start position.
    The script must NOT use localStorage, sessionStorage, cookies or the URL
    to persist the offset between page loads.
    """
    js = _load_move_cow_js()
    assert "localStorage" not in js, (
        "move-cow.js must not use localStorage (reload must reset the cow)"
    )
    assert "sessionStorage" not in js, (
        "move-cow.js must not use sessionStorage (reload must reset the cow)"
    )
    assert "document.cookie" not in js, (
        "move-cow.js must not use cookies (reload must reset the cow)"
    )
    assert "location.hash" not in js and "history.push" not in js and \
           "history.replace" not in js, (
        "move-cow.js must not persist state in the URL (reload must reset the cow)"
    )


# Scenario: Reloading the page resets the first cow
def test_move_cow_js_offset_starts_at_zero():
    """
    The in-memory offset variable must start at 0 so the cow begins at its
    initial (start) position after every page load.
    """
    js = _load_move_cow_js()
    assert re.search(r'\boffset\s*=\s*0\b', js), (
        "move-cow.js must initialise the offset variable to 0"
    )


# Scenario: Move right shifts the first cow to the right
def test_move_cow_js_applies_offset_to_style_left():
    """
    The apply() function (or equivalent) must set cow.style.left to the
    new offset in pixels, so the browser actually shifts the element.
    """
    js = _load_move_cow_js()
    assert "style.left" in js, (
        "move-cow.js must set cow.style.left to apply the offset"
    )


# Scenario: Move right shifts the first cow to the right
def test_move_cow_js_updates_data_offset():
    """
    The apply() function must also update cow.dataset.offset (or
    cow.setAttribute('data-offset', ...)) so the data attribute reflects
    the current offset.
    """
    js = _load_move_cow_js()
    assert "dataset.offset" in js or "setAttribute" in js, (
        "move-cow.js must update data-offset on #first-cow when the offset changes"
    )


# Scenario: Move right shifts the first cow to the right
def test_move_cow_js_does_not_touch_second_cow():
    """
    The script must NOT reference the second cow or any 'data-cow=second'
    selector — only #first-cow is ever modified.
    """
    js = _load_move_cow_js()
    # The script should not reference 'second' or 'data-cow' in ways
    # that would select the second cow; it only touches #first-cow.
    # We check that "second-cow" or selecting the second pre is absent.
    assert "second-cow" not in js, (
        "move-cow.js must not reference 'second-cow'; only #first-cow is modified"
    )


# ---------------------------------------------------------------------------
# Acceptance criterion: helmet / CSP unchanged
# ---------------------------------------------------------------------------

# Scenario: Move right shifts the first cow to the right
def test_helmet_configuration_unchanged():
    """
    The helmet() call must still be present in index.js without modification
    (the Content-Security-Policy header must still be applied).
    The helmet configuration must not add any 'unsafe-inline' exception.
    """
    source = _load_js_source()
    assert "helmet()" in source, (
        "helmet() must still be called in index.js (CSP must remain active)"
    )
    assert "unsafe-inline" not in source, (
        "helmet configuration must not add 'unsafe-inline' to the CSP"
    )


# Scenario: Move right shifts the first cow to the right
def test_no_helmet_script_src_change():
    """
    The helmet contentSecurityPolicy configuration must not override
    script-src to allow inline scripts. The default helmet CSP (script-src 'self')
    must remain effective.
    """
    source = _load_js_source()
    # If someone adds a contentSecurityPolicy override allowing 'unsafe-inline'
    # that would violate the acceptance criterion.
    assert "unsafe-inline" not in source, (
        "The CSP must not be weakened by adding 'unsafe-inline'"
    )


# ---------------------------------------------------------------------------
# Acceptance criterion: script tag is last child of body
# ---------------------------------------------------------------------------

# Scenario: Move right shifts the first cow to the right
def test_script_tag_is_near_end_of_body():
    """
    The <script src='/move-cow.js'> tag must be placed at or near the
    end of <body> (after the card div) so the DOM is ready when it runs,
    or it must have the 'defer' attribute.
    """
    html = _get_html()
    script_pos = html.find("/move-cow.js")
    body_close_pos = html.rfind("</body>")
    assert script_pos != -1, "move-cow.js script tag not found in template"
    if body_close_pos != -1:
        # Either it's near the end of body, or it has defer
        is_near_end = script_pos > body_close_pos - 500
        parser = _parse_html(html)
        script_tags = [
            attrs for tag, attrs in _start_tags(parser)
            if tag == "script" and "/move-cow.js" in attrs.get("src", "")
        ]
        has_defer = any("defer" in attrs for attrs in script_tags)
        assert is_near_end or has_defer, (
            "The move-cow.js script must either be placed at the end of <body> "
            "or have the 'defer' attribute"
        )
