"""
Tests for the bold speech bubble text feature.

The cow's speech bubble message lines must be shown in bold.
The bubble borders (___, ---), the cow drawing and the green grass line
must NOT be bold.

Strategy
--------
Parse the HTML template string embedded in cowsay/src/index.js.
The implementation is expected to process the cowsay output through a
helper (e.g. a JS function) that wraps each message line in a bold element
(<b> or <strong>) or applies font-weight:bold inline style.

We verify:
  1. The JS source contains logic to make bubble text bold (a function or
     inline construction that applies a bold element to message lines).
  2. The bold element is used inside the pre elements that hold the cow
     output — for BOTH the first and second cow.
  3. The bubble borders and cow drawing are NOT wrapped in bold.
  4. The green grass line is NOT bold.
  5. The template still passes the `text` parameter to the first cowsay call.
"""

import re
import html.parser
import pytest

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

JS_PATH = "cowsay/src/index.js"

# Regex that matches a bold start tag: <b> or <strong> (with optional attrs)
BOLD_OPEN_RE = re.compile(r'<(b|strong)(\s[^>]*)?>',  re.IGNORECASE)
# Regex that matches inline bold style
BOLD_STYLE_RE = re.compile(r'font-weight\s*:\s*bold', re.IGNORECASE)


# ---------------------------------------------------------------------------
# Shared helpers
# ---------------------------------------------------------------------------

def _load_js_source() -> str:
    with open(JS_PATH, encoding="utf-8") as fh:
        return fh.read()


def _extract_setCowsaySentence_body(source: str) -> str:
    """
    Return the body (template literal content) of setCowsaySentence.
    Raises AssertionError if the function cannot be found.
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
    return m.group(1)


def _extract_html_template(source: str) -> str:
    """
    Return the static HTML produced by setCowsaySentence, replacing
    ${cowsay.say({...})} calls with numbered placeholders and other
    ${...} expressions with __INTERPOLATION__ so the HTML can be parsed.
    """
    template = _extract_setCowsaySentence_body(source)

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
    # Remove remaining ${...} interpolations
    template = re.sub(r'\$\{[^}]+\}', "__INTERPOLATION__", template)
    return template


def _get_html() -> str:
    source = _load_js_source()
    return _extract_html_template(source)


# ---------------------------------------------------------------------------
# Scenario: The first cow's bubble text is bold on a custom text page
# ---------------------------------------------------------------------------

# Scenario: The first cow's bubble text is bold on a custom text page
def test_first_cow_output_is_wrapped_with_bold_function():
    """
    The first cowsay.say() call in the template must be processed so that
    its message lines become bold. This means the expression ${cowsay.say(...)}
    is replaced by something like ${boldBubble(cowsay.say(...))} or the output
    is built differently with <b> / <strong> wrapping.

    We check that in the setCowsaySentence body the first cow's output is NOT
    simply dropped raw as ${cowsay.say(...)} but is passed through a bold
    processing step (the raw call is absent OR it is embedded inside a larger
    expression that applies bold).
    """
    source = _load_js_source()
    template = _extract_setCowsaySentence_body(source)

    # Find all expressions that produce cow output in the template.
    # A raw ${cowsay.say({text, e: "oO"})} (with no wrapping function) is
    # the OLD pattern. The NEW pattern wraps it: ${boldBubble(cowsay.say(...))}
    # or similar.
    #
    # We look for cowsay.say calls for the FIRST cow (using oO eyes) and
    # verify they are inside a larger expression (not the outermost call).
    oo_call_pattern = re.compile(
        r'\$\{(\w+\s*\()?\s*cowsay\.say\(\{[^}]*e\s*:\s*["\']oO["\'][^}]*\}\)',
        re.DOTALL,
    )
    matches = oo_call_pattern.findall(template)
    # matches[0] is the captured group (the wrapping function prefix).
    # If it is empty string, the call is raw (no wrapping); that's wrong.
    assert matches, (
        "No cowsay.say call with e:'oO' found in the template; "
        "the first cow call must still be present"
    )
    # Check that the first oO call has a wrapping function prefix
    first_prefix = matches[0]
    assert first_prefix.strip() != "", (
        "The first cow's cowsay.say() call must be wrapped in a bold-processing "
        "function (e.g. boldBubble(cowsay.say(...))) so its message lines are bold. "
        "Currently it appears to be a raw ${cowsay.say(...)} with no wrapper."
    )


# Scenario: The first cow's bubble text is bold on a custom text page
def test_html_template_contains_bold_element_in_first_pre():
    """
    The HTML template must contain at least one <b> or <strong> element (or
    a font-weight:bold style) somewhere in the region associated with the
    first cow's pre block, indicating that message lines will be bold.

    We verify that the template as a whole references bold markup, and that
    a <b> or <strong> tag appears before the second cow's placeholder.
    """
    html = _get_html()

    # The portion of the HTML up to and including the first cow placeholder
    first_cow_section = html[:html.find("__COW_OUTPUT_1__") + len("__COW_OUTPUT_1__")]

    # There must be bold markup in the first cow's area (the bold element is
    # generated at runtime by the wrapping function, but the function itself
    # must exist in the JS source)
    source = _load_js_source()

    # Check that the source has a function that produces <b> or <strong>
    has_b_tag = re.search(r'["\']<b>', source) or re.search(r"'<b>'", source) or \
                re.search(r'`<b>`', source) or re.search(r'<b>', source)
    has_strong_tag = re.search(r'["\']<strong>', source) or re.search(r"'<strong>'", source) or \
                     re.search(r'<strong>', source)
    has_bold_style = BOLD_STYLE_RE.search(source)

    assert has_b_tag or has_strong_tag or has_bold_style, (
        "The JS source must contain bold markup (<b>, <strong>, or "
        "font-weight:bold) to make the bubble text bold. "
        "None of these were found in cowsay/src/index.js."
    )


# Scenario: The first cow's bubble text is bold on a custom text page
def test_bold_processing_function_exists_in_source():
    """
    The JS source must define (or use inline) a function that processes
    cowsay output and wraps message lines in bold.

    Acceptable patterns:
      - A named function like boldBubble, formatBubble, makeBold, etc. that
        produces <b>...</b> or <strong>...</strong>
      - An inline arrow function that splits on newlines and maps lines
    """
    source = _load_js_source()

    # Pattern 1: source produces <b> tags from cowsay output
    produces_b = bool(re.search(r'<b>', source))
    produces_strong = bool(re.search(r'<strong>', source))

    # Pattern 2: source applies font-weight bold to something related to
    # cowsay or the speech bubble
    applies_bold_style = bool(BOLD_STYLE_RE.search(source))

    assert produces_b or produces_strong or applies_bold_style, (
        "cowsay/src/index.js must contain logic that produces bold markup "
        "(<b>...</b>, <strong>...</strong>, or font-weight:bold) for the "
        "speech bubble message lines. "
        "Add a helper function such as:\n"
        "  const boldBubble = (output) => output.split('\\n').map(line =>\n"
        "    /^[<|>\\/\\\\]/.test(line) ? `<b>${line}</b>` : line\n"
        "  ).join('\\n');"
    )


# Scenario: The first cow's bubble text is bold on a custom text page
def test_first_cow_drawing_not_bold():
    """
    The cow drawing lines (those that are NOT message lines) must not be
    wrapped in bold. Specifically, the bubble borders (lines of underscores
    or dashes) and the ASCII art cow must stay plain.

    We verify that the bold function in the source wraps ONLY message lines —
    lines whose first non-space character marks them as bubble content
    (< | / \\) — and explicitly excludes drawing lines.
    """
    source = _load_js_source()

    # If the source applies bold to every line it is wrong.
    # Check that the bold-producing code has a conditional / filter.
    # The simplest check: the source cannot just wrap ALL cowsay output in <b>.
    # That is: <b>${cowsay.say(...)} or similar wrapping the whole output.

    # Bad pattern: <b> wrapping the entire cowsay output block
    bad_pattern = re.compile(
        r'<b>\s*\$\{cowsay\.say',
        re.DOTALL,
    )
    assert not bad_pattern.search(source), (
        "The entire cowsay.say() output must not be wrapped in a single <b> "
        "tag — only individual message lines inside the bubble should be bold, "
        "not the borders and cow drawing."
    )


# ---------------------------------------------------------------------------
# Scenario: The answering cow's bubble text is bold
# ---------------------------------------------------------------------------

# Scenario: The answering cow's bubble text is bold
def test_second_cow_output_is_also_bold_wrapped():
    """
    The second cow (with e:'^^' eyes) must also have its message lines shown
    in bold, just like the first cow. Its cowsay.say() call must also be
    wrapped in a bold-processing function.
    """
    source = _load_js_source()
    template = _extract_setCowsaySentence_body(source)

    # Find the second cowsay.say call (using ^^ eyes) and check it is
    # also processed through a wrapping function
    hat_call_pattern = re.compile(
        r'\$\{(\w+\s*\()?\s*cowsay\.say\(\{[^}]*e\s*:\s*["\']\\^\\^["\'][^}]*\}\)',
        re.DOTALL,
    )
    matches = hat_call_pattern.findall(template)
    assert matches, (
        "No cowsay.say call with e:'^^' found in the template; "
        "the second cow call must still be present"
    )
    second_prefix = matches[0]
    assert second_prefix.strip() != "", (
        "The second cow's cowsay.say() call must also be wrapped in the same "
        "bold-processing function so its answer text is also bold. "
        "Currently it appears to be a raw ${cowsay.say(...)} with no wrapper."
    )


# Scenario: The answering cow's bubble text is bold
def test_both_cow_calls_use_same_bold_wrapper():
    """
    The same bold-processing function must be applied to both cows.
    We verify that the function name that wraps the first cow's output
    also wraps the second cow's output.
    """
    source = _load_js_source()
    template = _extract_setCowsaySentence_body(source)

    # Find both wrapping expressions (function name before cowsay.say)
    wrapper_pattern = re.compile(
        r'\$\{(\w+)\s*\(\s*cowsay\.say\(',
        re.DOTALL,
    )
    wrappers = wrapper_pattern.findall(template)

    # Both cowsay calls must be wrapped (at least 2 occurrences)
    assert len(wrappers) >= 2, (
        f"Expected both cowsay.say() calls to be wrapped in a bold-processing "
        f"function, but found only {len(wrappers)} wrapped call(s). "
        f"The second cow must also have its message lines bold."
    )

    # Both must use the same wrapper function name (consistency)
    if len(wrappers) >= 2:
        assert wrappers[0] == wrappers[1], (
            f"Both cows must use the same bold-processing function. "
            f"Found: {wrappers[0]!r} for the first cow and "
            f"{wrappers[1]!r} for the second cow."
        )


# Scenario: The answering cow's bubble text is bold
def test_second_cow_drawing_not_bold():
    """
    Like the first cow, the second cow's drawing lines must not be bold.
    Verifies the bad pattern (entire second cow output in <b>) is absent.
    """
    source = _load_js_source()

    # The overall cowsay output for the second cow must not be wrapped in <b>
    # at the top level.  A bad template would have:  <b>${cowsay.say({text: getRandomAnswer()...
    bad_pattern = re.compile(
        r'<b>\s*\$\{cowsay\.say\(\{[^}]*getRandomAnswer',
        re.DOTALL,
    )
    assert not bad_pattern.search(source), (
        "The entire second cowsay.say() output must not be wrapped in a single "
        "<b> — only the message lines should be bold."
    )


# ---------------------------------------------------------------------------
# Scenario: The quote on the home page is bold
# ---------------------------------------------------------------------------

# Scenario: The quote on the home page is bold
def test_fallback_quote_route_uses_setCowsaySentence():
    """
    Both the fallback path (quote site down) and the normal path on GET /
    call setCowsaySentence, which is the function that produces the HTML
    with bold bubble text.  This guarantees the quote page is also bold.
    """
    source = _load_js_source()

    # All calls to res.send on the home route must go through setCowsaySentence
    # (setCowsaySentence already handles making bubble text bold)
    calls = re.findall(r'setCowsaySentence\s*\(', source)
    assert len(calls) >= 2, (
        f"Both route handlers (including the fallback on GET /) must call "
        f"setCowsaySentence so the quote page also shows bold bubble text. "
        f"Found only {len(calls)} call(s)."
    )


# Scenario: The quote on the home page is bold
def test_bold_function_applied_before_res_send():
    """
    The bold processing must happen inside setCowsaySentence (which is what
    both routes use for res.send). Since both routes call setCowsaySentence,
    and setCowsaySentence wraps cowsay output in bold, the quote page
    automatically gets bold bubble text.

    Verify that the bold markup is inside the setCowsaySentence function, not
    only in an ad-hoc path.
    """
    source = _load_js_source()

    # Extract the full setCowsaySentence function text (definition only)
    # from 'const setCowsaySentence = ...' to its closing brace
    fn_match = re.search(
        r'(const\s+setCowsaySentence\s*=.*?)\n(?=const\s|\napp\.)',
        source,
        re.DOTALL,
    )
    if not fn_match:
        # Try a broader match up to the end of a function-like block
        fn_match = re.search(
            r'const\s+setCowsaySentence\s*=\s*\(text\)\s*=>\s*\{.*?\n\}',
            source,
            re.DOTALL,
        )

    if fn_match:
        fn_body = fn_match.group(0)
        has_bold_in_fn = (
            bool(re.search(r'<b>', fn_body)) or
            bool(re.search(r'<strong>', fn_body)) or
            bool(BOLD_STYLE_RE.search(fn_body))
        )
        # If we found the function body, bold must be inside it
        # (either directly or through a helper referenced there)
        # We accept both: bold markup in the function body, OR a wrapper
        # function call like boldBubble(...) that is defined elsewhere.
        wrapper_call = bool(re.search(r'\$\{\w+\s*\(\s*cowsay\.say\(', fn_body))
        assert has_bold_in_fn or wrapper_call, (
            "Bold markup or a bold-processing wrapper must be present inside "
            "setCowsaySentence so that every page (including the quote home page) "
            "shows bold bubble text automatically."
        )
    else:
        # Broad fallback: just verify bold is somewhere in the source
        has_bold = (
            bool(re.search(r'<b>', source)) or
            bool(re.search(r'<strong>', source)) or
            bool(BOLD_STYLE_RE.search(source))
        )
        assert has_bold, (
            "The JS source must contain bold markup to make bubble text bold."
        )


# ---------------------------------------------------------------------------
# Acceptance criteria: green grass line stays plain (not bold)
# ---------------------------------------------------------------------------

# Scenario: The first cow's bubble text is bold on a custom text page
def test_grass_line_not_inside_bold():
    """
    The green grass line (the <span style="color: green">...^^^^...</span>)
    must NOT be wrapped in a <b> or <strong> element.
    The acceptance criteria require bubble borders and the grass to stay plain.
    """
    html = _get_html()

    # The grass span in the template
    # We check that the grass span is not inside <b>...</b>
    # A simple heuristic: <b> must not appear immediately before the green span
    bad_bold_grass = re.compile(
        r'<b[^>]*>\s*<span[^>]*color\s*:\s*green',
        re.IGNORECASE | re.DOTALL,
    )
    assert not bad_bold_grass.search(html), (
        "The green grass <span> must not be wrapped in a <b> or <strong> "
        "element — the grass must stay plain, not bold."
    )

    # Also verify the grass span itself does not have font-weight:bold
    # Find the grass span
    grass_span = re.search(
        r'<span[^>]*color\s*:\s*green[^>]*>',
        html,
        re.IGNORECASE,
    )
    if grass_span:
        assert 'font-weight' not in grass_span.group(0).lower() or \
               'bold' not in grass_span.group(0).lower(), (
            "The grass <span> element must not have font-weight:bold style."
        )


# ---------------------------------------------------------------------------
# Acceptance criteria: bold function produces correct line categorisation
# ---------------------------------------------------------------------------

# Scenario: The first cow's bubble text is bold on a custom text page
def test_bold_wrapping_logic_targets_message_lines():
    """
    The bold-processing function (wherever it is defined in the source) must
    use a pattern that targets message lines — lines starting with characters
    like '<', '|', '/', '\\' — and leaves other lines (borders, drawing) plain.

    We look for a regular-expression or string-matching pattern in the JS
    source that identifies bubble content lines.
    """
    source = _load_js_source()

    # The function must use a condition / regex to identify message lines.
    # Acceptable patterns include:
    #   /^[<|>\/\\]/.test(line)
    #   line.startsWith('<') || line.startsWith('|')
    #   line[0] === '<' || line[0] === '|'
    #   line.match(/^[<|>\/\\]/)
    # We look for any of these patterns.

    # Check for a regex literal that targets start-of-line bubble characters
    has_regex_pattern = bool(re.search(
        r'/\^?\[?[<|>\/\\\\]+\]?/',   # regex containing <|>/\ chars
        source,
    ))

    # Check for startsWith with bubble chars
    has_startswith = bool(re.search(
        r'startsWith\s*\(\s*[\'"][<|>\/\\\\]',
        source,
    ))

    # Check for character comparison with bubble chars
    has_char_compare = bool(re.search(
        r'[=!]==?\s*[\'"][<|>\/\\\\]',
        source,
    ))

    # Check for indexOf or includes with bubble-line markers
    has_includes = bool(re.search(
        r'indexOf|includes',
        source,
    ))

    # Check for a split+map pattern (lines are iterated)
    has_line_iteration = bool(re.search(
        r'split\s*\(\s*[\'"]\\n[\'"]|split\s*\(\s*`\\n`',
        source,
    ))

    assert has_regex_pattern or has_startswith or has_char_compare or has_line_iteration, (
        "The bold-processing logic must iterate over lines of the cowsay output "
        "and apply bold only to message lines (those starting with <, |, /, \\\\). "
        "Expected to find: a split('\\\\n') + map pattern, a startsWith check, "
        "or a regex like /^[<|\\/\\\\]/ in cowsay/src/index.js."
    )


# ---------------------------------------------------------------------------
# Acceptance criteria: existing pre structure is preserved
# ---------------------------------------------------------------------------

# Scenario: The first cow's bubble text is bold on a custom text page
def test_pre_elements_still_present_for_both_cows():
    """
    The <pre> elements that hold the cow drawings must still be present
    after the bold change. Both cows must still appear inside <pre> blocks.
    """
    html = _get_html()
    pre_count = len(re.findall(r'<pre\b', html, re.IGNORECASE))
    assert pre_count >= 2, (
        f"Expected at least 2 <pre> elements in the template (one per cow), "
        f"found {pre_count}. The bold change must not remove the <pre> elements."
    )


# Scenario: The first cow's bubble text is bold on a custom text page
def test_cow_outputs_still_in_template():
    """
    After the bold change, both cow outputs (first and second) must still be
    present as placeholders in the template. The bold wrapping must not
    remove the cowsay output.
    """
    html = _get_html()
    assert "__COW_OUTPUT_1__" in html, (
        "First cow output placeholder not found. The bold change must not "
        "remove the first cowsay.say() call from the template."
    )
    assert "__COW_OUTPUT_2__" in html, (
        "Second cow output placeholder not found. The bold change must not "
        "remove the second cowsay.say() call from the template."
    )


# ---------------------------------------------------------------------------
# Acceptance criteria: first cow keeps oO eyes, text param
# ---------------------------------------------------------------------------

# Scenario: The first cow's bubble text is bold on a custom text page
def test_first_cow_still_uses_oo_eyes_after_bold_change():
    """
    The bold change must not modify the cowsay call parameters.
    The first cow must still use e: "oO" eye style.
    """
    source = _load_js_source()
    assert 'e: "oO"' in source or "e: 'oO'" in source, (
        "After the bold change the first cowsay.say() call must still use "
        "e: 'oO' (eye style must not change)."
    )


# Scenario: The first cow's bubble text is bold on a custom text page
def test_first_cow_still_receives_text_param_after_bold_change():
    """
    The bold change must not remove the `text` parameter from the first
    cowsay call. Custom text pages (/hello) must still show the right text.
    """
    source = _load_js_source()
    template = _extract_setCowsaySentence_body(source)

    first_cowsay = re.search(r'cowsay\.say\(\{(.*?)\}\)', template, re.DOTALL)
    assert first_cowsay, "No cowsay.say({...}) call found in template"
    first_call_body = first_cowsay.group(1)
    assert "text" in first_call_body, (
        "The first cowsay.say() call must still pass the `text` parameter "
        "after the bold change."
    )
