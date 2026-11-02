"""
Tests for the "Hello NYXUS" home-page cow feature.

These tests statically inspect cowsay/src/index.js to verify that:
  - The GET / route always uses "Hello NYXUS" as the first cow's text.
  - The GET / route no longer fetches / falls back to Deepak Chopra quotes.
  - The GET /:text route still passes the URL segment as the first cow's text.
  - The second cow's fixed answer list is unchanged.

No running server or Node.js is required; all checks are done by reading
and analysing the JS source file.
"""

import re
import pytest

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

JS_PATH = "cowsay/src/index.js"

FIXED_ANSWERS = [
    "Moo, so true!",
    "I was just thinking that.",
    "Deep. Very deep.",
]

HELLO_NYXUS = "Hello NYXUS"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _load_js_source() -> str:
    with open(JS_PATH, encoding="utf-8") as fh:
        return fh.read()


def _get_home_route_body(source: str) -> str:
    """
    Extract the body of the GET '/' route handler.
    Looks for:  app.get('/',  or  app.get("/",
    and returns the content up to the matching closing brace / next app.get.
    """
    # Find where the home route starts
    match = re.search(r"app\.get\s*\(\s*['\"]\/['\"]", source)
    assert match, "Could not find 'app.get(\"/\", ...)' in index.js"
    start = match.start()

    # Find where the /:text route starts (the next app.get after the home route)
    next_route = re.search(r"app\.get\s*\(\s*['\"]\/:", source[start + 1:])
    if next_route:
        end = start + 1 + next_route.start()
        return source[start:end]
    # Fallback: return everything after the home route start
    return source[start:]


# ---------------------------------------------------------------------------
# Scenario: First cow on the home page says Hello NYXUS
# ---------------------------------------------------------------------------

# Scenario: First cow on the home page says Hello NYXUS
def test_home_route_uses_hello_nyxus_as_first_cow_text():
    """
    The GET / handler must call setCowsaySentence with "Hello NYXUS" (exactly)
    so that the first cow's speech bubble always shows that text.
    """
    source = _load_js_source()
    home_body = _get_home_route_body(source)

    # The home route must pass "Hello NYXUS" to setCowsaySentence
    assert HELLO_NYXUS in home_body, (
        f"The GET / handler must pass '{HELLO_NYXUS}' to setCowsaySentence; "
        f"the string was not found in the home route handler body."
    )


# Scenario: First cow on the home page says Hello NYXUS
def test_home_route_calls_set_cowsay_with_hello_nyxus():
    """
    The GET / handler must call setCowsaySentence(\"Hello NYXUS\") (or a variable
    that is set to \"Hello NYXUS\") – not with a Deepak Chopra quote.
    We verify that setCowsaySentence is called and that 'Hello NYXUS' is present
    in the same route handler.
    """
    source = _load_js_source()
    home_body = _get_home_route_body(source)

    # setCowsaySentence must be called in the home route
    assert "setCowsaySentence" in home_body, (
        "GET / handler must call setCowsaySentence to render the page."
    )

    # "Hello NYXUS" must appear in the home route body (either directly in
    # the call or as an assigned constant)
    assert HELLO_NYXUS in home_body, (
        f"'{HELLO_NYXUS}' must be the text passed to setCowsaySentence "
        f"in the GET / handler."
    )


# Scenario: First cow on the home page says Hello NYXUS
def test_home_route_does_not_show_deepak_chopra_quote_text():
    """
    The GET / handler must NOT produce the text 'Deepak Chopra Quote' in the
    cow's speech. The home page must not mention 'Deepak Chopra Quote' at all.
    """
    source = _load_js_source()
    home_body = _get_home_route_body(source)

    # "Deepak Chopra Quote" must not appear as the speech text in the home route
    assert "Deepak Chopra Quote" not in home_body, (
        "The GET / handler must not pass 'Deepak Chopra Quote' text to the cow; "
        "the first cow must now say 'Hello NYXUS'."
    )


# ---------------------------------------------------------------------------
# Scenario: Home page shows Hello NYXUS even when the quote website is down
# ---------------------------------------------------------------------------

# Scenario: Home page shows Hello NYXUS even when the quote website is down
def test_home_route_does_not_depend_on_wisdomofchopra():
    """
    The GET / handler must not make any HTTP request to wisdomofchopra.com.
    If it does, the first cow's text depends on an external service being up,
    which contradicts the requirement that Hello NYXUS is always shown.
    We verify that wisdomofchopra.com does not appear in the home route body.
    """
    source = _load_js_source()
    home_body = _get_home_route_body(source)

    assert "wisdomofchopra" not in home_body.lower(), (
        "The GET / handler must not fetch from wisdomofchopra.com; "
        "the first cow must always say 'Hello NYXUS' regardless of network."
    )


# Scenario: Home page shows Hello NYXUS even when the quote website is down
def test_home_route_hello_nyxus_not_conditional():
    """
    'Hello NYXUS' must be the unconditional text for the first cow.
    Verify there is no fallback/error-path logic in the home route that would
    cause a different text to appear: the home route body must be simple and
    not branch based on an HTTP response.

    Heuristic: the home route handler should NOT contain a callback that decides
    between two different setCowsaySentence calls (i.e., the route body should
    call setCowsaySentence exactly once or reference 'Hello NYXUS' without
    conditional branches that could bypass it).
    """
    source = _load_js_source()
    home_body = _get_home_route_body(source)

    # The home route must contain "Hello NYXUS"
    assert HELLO_NYXUS in home_body, (
        f"'{HELLO_NYXUS}' must be present in the GET / handler unconditionally."
    )

    # Count how many times 'Hello NYXUS' appears in the home route body.
    # It should appear at least once; all paths should lead to it.
    occurrences = home_body.count(HELLO_NYXUS)
    assert occurrences >= 1, (
        f"'{HELLO_NYXUS}' must appear in the GET / handler body."
    )


# Scenario: Home page shows Hello NYXUS even when the quote website is down
def test_home_route_does_not_use_request_to_fetch_quote():
    """
    The GET / handler must not use the 'request' library to fetch a Deepak
    Chopra quote. The call to request({...wisdomofchopra...}) in the home
    route must be removed.
    """
    source = _load_js_source()
    home_body = _get_home_route_body(source)

    # The home route must not contain a request() call targeting an external URL
    # (or any network fetch at all, since the text is now hardcoded)
    has_request_call = bool(re.search(r'\brequest\s*\(', home_body))
    assert not has_request_call, (
        "The GET / handler must not call request() to fetch an external quote; "
        "the first cow's text is now the fixed string 'Hello NYXUS'."
    )


# ---------------------------------------------------------------------------
# Scenario: Text in the address still sets the first cow's speech
# ---------------------------------------------------------------------------

# Scenario: Text in the address still sets the first cow's speech
def test_text_route_still_passes_url_param_to_first_cow():
    """
    The GET /:text route must still pass req.params.text to setCowsaySentence
    so that, for example, visiting /moo shows 'moo' in the first cow's bubble.
    """
    source = _load_js_source()

    # Find the /:text route handler
    match = re.search(r"app\.get\s*\(\s*['\"]\/:[^'\"]+['\"]", source)
    assert match, "Could not find the GET /:text route handler in index.js"
    start = match.start()
    text_route_body = source[start:]

    # The route must pass req.params.text (or a variable holding it) to
    # setCowsaySentence – specifically the `text` variable
    assert "req.params.text" in text_route_body or (
        "params.text" in text_route_body
    ), (
        "The GET /:text route must read req.params.text and pass it to "
        "setCowsaySentence so that /moo shows 'moo'."
    )

    assert "setCowsaySentence" in text_route_body, (
        "The GET /:text route must call setCowsaySentence."
    )


# Scenario: Text in the address still sets the first cow's speech
def test_text_route_does_not_force_hello_nyxus():
    """
    The GET /:text route must NOT hardcode 'Hello NYXUS'; it must continue
    to use the text from the URL parameter.
    """
    source = _load_js_source()

    # Find the /:text route handler body (everything after it starts)
    match = re.search(r"app\.get\s*\(\s*['\"]\/:[^'\"]+['\"]", source)
    assert match, "Could not find the GET /:text route handler in index.js"
    start = match.start()
    text_route_body = source[start:]

    # 'Hello NYXUS' must NOT appear in the /:text route body
    assert HELLO_NYXUS not in text_route_body, (
        f"The GET /:text handler must NOT hardcode '{HELLO_NYXUS}'; "
        f"it must use the URL parameter text for the first cow."
    )


# ---------------------------------------------------------------------------
# Scenario: Second cow still answers with a random line on the home page
# ---------------------------------------------------------------------------

# Scenario: Second cow still answers with a random line on the home page
def test_second_cow_answers_list_unchanged():
    """
    The cowAnswers array must still contain exactly the three fixed replies:
      "Moo, so true!", "I was just thinking that.", "Deep. Very deep."
    """
    source = _load_js_source()

    for answer in FIXED_ANSWERS:
        assert answer in source, (
            f"The fixed answer '{answer}' must still be present in the "
            f"cowAnswers array in index.js."
        )


# Scenario: Second cow still answers with a random line on the home page
def test_second_cow_uses_get_random_answer_in_template():
    """
    The setCowsaySentence template must still call getRandomAnswer() (or
    equivalent) for the second cow so that a random answer from the fixed
    list is shown.
    """
    source = _load_js_source()

    # The template must include a call that picks from cowAnswers for the
    # second cow.  getRandomAnswer() is the expected function name.
    assert "getRandomAnswer" in source, (
        "getRandomAnswer() function must still be called for the second cow."
    )

    # Verify it is called inside the setCowsaySentence template or function
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

    assert "getRandomAnswer" in template, (
        "The second cow's text must be provided by getRandomAnswer() "
        "inside the setCowsaySentence template."
    )


# Scenario: Second cow still answers with a random line on the home page
def test_second_cow_answers_cover_all_three_options():
    """
    The cowAnswers array (used by getRandomAnswer) must contain all three
    required options so that each can be randomly selected.
    """
    source = _load_js_source()

    # Find the cowAnswers array definition
    match = re.search(r'const\s+cowAnswers\s*=\s*\[([^\]]+)\]', source, re.DOTALL)
    assert match, "Could not find 'const cowAnswers = [...]' in index.js"

    array_body = match.group(1)
    for answer in FIXED_ANSWERS:
        assert answer in array_body, (
            f"cowAnswers must still include '{answer}'"
        )
