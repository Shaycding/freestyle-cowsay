"""
Tests for the banana tree decoration feature.

These tests statically inspect:
  - cowsay/src/public/banana-tree.svg  (the SVG asset)
  - cowsay/src/index.js                (the HTML template produced by setCowsaySentence)

No running server or Node.js is required.

Scenarios covered
-----------------
- The quote page shows banana trees on the pink background
- The custom text page shows the same banana trees
- Banana trees never cover the cow card
"""

import os
import re
import html.parser
import pytest

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------

JS_PATH = "cowsay/src/index.js"
SVG_PATH = "cowsay/src/public/banana-tree.svg"


# ---------------------------------------------------------------------------
# Helpers – JS source & HTML template extraction
# (same strategy used by the existing pink-theme / second-cow tests)
# ---------------------------------------------------------------------------

def _load_js_source() -> str:
    with open(JS_PATH, encoding="utf-8") as fh:
        return fh.read()


def _extract_html_template(source: str) -> str:
    """
    Return the static HTML produced by setCowsaySentence after substituting
    all ${…} JS expressions with recognisable placeholders.
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

    # Replace cowsay.say({...}) expressions with numbered placeholders
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


class _CollectingParser(html.parser.HTMLParser):
    """Simple parser that records every start-tag and its attributes."""

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
    return _extract_html_template(_load_js_source())


def _get_parser() -> _CollectingParser:
    return _parse_html(_get_html())


# ---------------------------------------------------------------------------
# Helper: find banana-tree <img> elements
# ---------------------------------------------------------------------------

def _banana_img_tags(parser: _CollectingParser) -> list[dict]:
    """Return the attrs dicts of every <img> whose src is /banana-tree.svg."""
    return [
        attrs
        for tag, attrs in parser.tags
        if tag == "img" and attrs.get("src", "") == "/banana-tree.svg"
    ]


# ---------------------------------------------------------------------------
# Helper: normalise inline style strings into a dict
# ---------------------------------------------------------------------------

def _parse_style(style_str: str) -> dict:
    """Turn 'position: fixed; left: 0; z-index: 0' into a dict."""
    result = {}
    for declaration in style_str.split(";"):
        declaration = declaration.strip()
        if ":" not in declaration:
            continue
        prop, _, value = declaration.partition(":")
        result[prop.strip().lower()] = value.strip().lower()
    return result


# ===========================================================================
# Scenario: The quote page shows banana trees on the pink background
# ===========================================================================

# Scenario: The quote page shows banana trees on the pink background
def test_two_banana_tree_images_present():
    """
    The HTML produced by setCowsaySentence must contain exactly two
    <img src="/banana-tree.svg"> elements (one left, one right).
    """
    parser = _get_parser()
    trees = _banana_img_tags(parser)
    assert len(trees) == 2, (
        f"Expected exactly 2 <img src='/banana-tree.svg'> elements, found {len(trees)}"
    )


# Scenario: The quote page shows banana trees on the pink background
def test_banana_tree_left_side_present():
    """
    At least one banana tree image must have data-side='left'.
    """
    parser = _get_parser()
    trees = _banana_img_tags(parser)
    left_trees = [t for t in trees if t.get("data-side") == "left"]
    assert left_trees, (
        "No banana tree image with data-side='left' found"
    )


# Scenario: The quote page shows banana trees on the pink background
def test_banana_tree_right_side_present():
    """
    At least one banana tree image must have data-side='right'.
    """
    parser = _get_parser()
    trees = _banana_img_tags(parser)
    right_trees = [t for t in trees if t.get("data-side") == "right"]
    assert right_trees, (
        "No banana tree image with data-side='right' found"
    )


# Scenario: The quote page shows banana trees on the pink background
def test_background_still_soft_pink():
    """
    The body background colour must still be #fde8e4.
    """
    html = _get_html()
    assert "#fde8e4" in html, (
        "body background-color #fde8e4 must still be present in the template"
    )


# ===========================================================================
# Scenario: The custom text page shows the same banana trees
# ===========================================================================

# Scenario: The custom text page shows the same banana trees
def test_both_routes_use_setCowsaySentence_for_banana_trees():
    """
    Both GET / and GET /:text use setCowsaySentence, so both pages
    automatically render the banana tree images.  Verify setCowsaySentence
    is called by both route handlers.
    """
    source = _load_js_source()
    calls = re.findall(r'setCowsaySentence\s*\(', source)
    assert len(calls) >= 2, (
        f"setCowsaySentence must be called in both route handlers; "
        f"found only {len(calls)} call(s)"
    )


# Scenario: The custom text page shows the same banana trees
def test_banana_trees_same_on_both_pages():
    """
    Since both routes produce output via setCowsaySentence, the HTML template
    must contain both banana tree images regardless of the URL.
    (Same template → same trees.)
    """
    parser = _get_parser()
    trees = _banana_img_tags(parser)
    sides = {t.get("data-side") for t in trees}
    assert "left" in sides and "right" in sides, (
        "Template must contain banana trees for both 'left' and 'right' sides "
        "so that both the quote page and custom-text pages show the same trees"
    )


# Scenario: The custom text page shows the same banana trees
def test_first_cow_receives_text_param():
    """
    The first cow's cowsay.say() call must pass the `text` parameter so
    that GET /hello shows the word 'hello' in the first cow's bubble.
    """
    source = _load_js_source()
    m = re.search(
        r'const\s+setCowsaySentence\s*=\s*\(text\)\s*=>\s*\{[^`]*`(.*)`\s*;?\s*\}',
        source, re.DOTALL,
    )
    if not m:
        m = re.search(
            r'const\s+setCowsaySentence\s*=.*?return\s+`(.*)`',
            source, re.DOTALL,
        )
    assert m, "Could not locate the template literal in setCowsaySentence"
    template = m.group(1)
    first_call = re.search(r'cowsay\.say\(\{(.*?)\}\)', template, re.DOTALL)
    assert first_call, "No cowsay.say({...}) call found in the template"
    assert "text" in first_call.group(1), (
        "The first cowsay.say() call must pass the `text` parameter"
    )


# ===========================================================================
# Scenario: Banana trees never cover the cow card
# ===========================================================================

# Scenario: Banana trees never cover the cow card
def test_banana_trees_have_lower_z_index_than_card():
    """
    Banana tree images must have z-index: 0 (or lower) and the white card
    must have z-index: 1 (or higher), so the card is always painted above
    the trees at any viewport width.
    """
    parser = _get_parser()

    # Check tree z-index
    trees = _banana_img_tags(parser)
    assert trees, "No banana tree images found"
    for tree in trees:
        style = _parse_style(tree.get("style", ""))
        z = style.get("z-index", None)
        assert z is not None, (
            f"Banana tree img (data-side={tree.get('data-side')}) "
            "must have an explicit z-index in its inline style"
        )
        assert int(z) <= 0, (
            f"Banana tree z-index must be 0 or lower; got {z}"
        )

    # Check card z-index: the card div has background-color:#ffffff
    card_divs = [
        attrs for tag, attrs in parser.tags
        if tag == "div" and "ffffff" in attrs.get("style", "").lower()
    ]
    assert card_divs, "No white card <div> found (background-color: #ffffff)"
    for card in card_divs:
        style = _parse_style(card.get("style", ""))
        z = style.get("z-index", None)
        assert z is not None, (
            "The white card <div> must have an explicit z-index in its inline style"
        )
        assert int(z) >= 1, (
            f"White card z-index must be 1 or higher; got {z}"
        )


# Scenario: Banana trees never cover the cow card
def test_card_has_position_relative():
    """
    z-index only works on positioned elements.  The white card must have
    'position: relative' (or absolute/fixed/sticky) in its inline style.
    """
    parser = _get_parser()
    card_divs = [
        attrs for tag, attrs in parser.tags
        if tag == "div" and "ffffff" in attrs.get("style", "").lower()
    ]
    assert card_divs, "No white card <div> found"
    for card in card_divs:
        style = _parse_style(card.get("style", ""))
        pos = style.get("position", "")
        assert pos in ("relative", "absolute", "fixed", "sticky"), (
            f"White card must have position: relative (or similar); got '{pos}'"
        )


# Scenario: Banana trees never cover the cow card
def test_h1_has_position_relative_and_z_index():
    """
    The <h1> must also have position: relative and z-index >= 1 so it
    is never hidden beneath a banana tree.
    """
    parser = _get_parser()
    h1_tags = [attrs for tag, attrs in parser.tags if tag == "h1"]
    assert h1_tags, "No <h1> element found"
    for h1 in h1_tags:
        style = _parse_style(h1.get("style", ""))
        pos = style.get("position", "")
        assert pos in ("relative", "absolute", "fixed", "sticky"), (
            f"<h1> must have position: relative; got '{pos}'"
        )
        z = style.get("z-index", None)
        assert z is not None, "<h1> must have an explicit z-index"
        assert int(z) >= 1, (
            f"<h1> z-index must be >= 1 so it stays above banana trees; got {z}"
        )


# Scenario: Banana trees never cover the cow card
def test_banana_trees_use_fixed_positioning():
    """
    Banana trees are decorative overlays; they should use 'position: fixed'
    so they stay on the sides of the viewport without pushing the card content.
    """
    parser = _get_parser()
    trees = _banana_img_tags(parser)
    assert trees, "No banana tree images found"
    for tree in trees:
        style = _parse_style(tree.get("style", ""))
        pos = style.get("position", "")
        assert pos == "fixed", (
            f"Banana tree (data-side={tree.get('data-side')}) must have "
            f"position: fixed; got '{pos}'"
        )


# Scenario: Banana trees never cover the cow card
def test_banana_tree_pointer_events_none():
    """
    Banana trees must not capture mouse/touch events: pointer-events: none.
    """
    parser = _get_parser()
    trees = _banana_img_tags(parser)
    assert trees, "No banana tree images found"
    for tree in trees:
        style = _parse_style(tree.get("style", ""))
        pe = style.get("pointer-events", "")
        assert pe == "none", (
            f"Banana tree (data-side={tree.get('data-side')}) must have "
            f"pointer-events: none; got '{pe}'"
        )


# ===========================================================================
# Acceptance criteria: accessibility – banana trees are decorative
# ===========================================================================

# Scenario: The quote page shows banana trees on the pink background
def test_banana_trees_have_empty_alt():
    """
    Screen readers must ignore the banana tree images.
    Each <img src="/banana-tree.svg"> must have alt=''.
    """
    parser = _get_parser()
    trees = _banana_img_tags(parser)
    assert trees, "No banana tree images found"
    for tree in trees:
        assert tree.get("alt") == "", (
            f"Banana tree img (data-side={tree.get('data-side')}) must have alt=''; "
            f"got alt='{tree.get('alt')}'"
        )


# Scenario: The quote page shows banana trees on the pink background
def test_banana_trees_have_aria_hidden():
    """
    Screen readers must ignore the banana tree images.
    Each <img src="/banana-tree.svg"> must have aria-hidden='true'.
    """
    parser = _get_parser()
    trees = _banana_img_tags(parser)
    assert trees, "No banana tree images found"
    for tree in trees:
        assert tree.get("aria-hidden") == "true", (
            f"Banana tree img (data-side={tree.get('data-side')}) must have "
            f"aria-hidden='true'; got aria-hidden='{tree.get('aria-hidden')}'"
        )


# Scenario: The quote page shows banana trees on the pink background
def test_banana_trees_have_data_decoration():
    """
    Each banana tree img must have data-decoration='banana-tree' as per the contract.
    """
    parser = _get_parser()
    trees = _banana_img_tags(parser)
    assert trees, "No banana tree images found"
    for tree in trees:
        assert tree.get("data-decoration") == "banana-tree", (
            f"Banana tree img (data-side={tree.get('data-side')}) must have "
            f"data-decoration='banana-tree'"
        )


# ===========================================================================
# Acceptance criteria: no <style>, no external stylesheet, no <script>
# ===========================================================================

# Scenario: The quote page shows banana trees on the pink background
def test_no_style_block_in_template():
    """
    The page must have no <style> block (inline stylesheets are forbidden).
    """
    source = _load_js_source()
    # Check the JS source itself contains no '<style' string inside setCowsaySentence
    assert "<style" not in source, (
        "The JS source must not contain a '<style' element"
    )


# Scenario: The quote page shows banana trees on the pink background
def test_no_external_stylesheet_in_template():
    """
    The page must have no <link rel='stylesheet'> tag.
    """
    source = _load_js_source()
    assert 'rel="stylesheet"' not in source and "rel='stylesheet'" not in source, (
        "The page must not load an external stylesheet"
    )


# Scenario: The quote page shows banana trees on the pink background
def test_no_script_tag_in_template():
    """
    The page must have no <script> tag.
    """
    source = _load_js_source()
    assert "<script" not in source, (
        "The page must not contain a <script> element"
    )


# ===========================================================================
# Acceptance criteria: banana tree src is site-relative (not external)
# ===========================================================================

# Scenario: The quote page shows banana trees on the pink background
def test_banana_tree_src_is_site_relative():
    """
    The banana tree src attribute must be a site-relative path starting with '/',
    not an http/https URL pointing to another website.
    """
    parser = _get_parser()
    trees = _banana_img_tags(parser)
    assert trees, "No banana tree images found"
    for tree in trees:
        src = tree.get("src", "")
        assert src.startswith("/"), (
            f"Banana tree src must start with '/' (site-relative); got '{src}'"
        )
        assert not src.startswith("http"), (
            f"Banana tree src must not be an external URL; got '{src}'"
        )


# ===========================================================================
# Acceptance criteria: banana-tree.svg file itself
# ===========================================================================

# Scenario: The quote page shows banana trees on the pink background
def test_banana_tree_svg_file_exists():
    """
    The file cowsay/src/public/banana-tree.svg must exist so express.static
    can serve it at /banana-tree.svg.
    """
    assert os.path.isfile(SVG_PATH), (
        f"The file {SVG_PATH} does not exist; "
        "it must be created so the server can serve it at /banana-tree.svg"
    )


# Scenario: The quote page shows banana trees on the pink background
def test_banana_tree_svg_root_element_is_svg():
    """
    The root element of banana-tree.svg must be <svg> with a viewBox attribute.
    """
    assert os.path.isfile(SVG_PATH), f"{SVG_PATH} does not exist"
    with open(SVG_PATH, encoding="utf-8") as fh:
        content = fh.read()

    # Check <svg is the root element (ignoring XML declaration / comments)
    stripped = content.lstrip()
    # Skip <?xml ...?> processing instruction if present
    if stripped.startswith("<?"):
        stripped = stripped[stripped.index("?>") + 2:].lstrip()
    # Skip <!-- comments -->
    while stripped.startswith("<!--"):
        stripped = stripped[stripped.index("-->") + 3:].lstrip()

    assert stripped.lower().startswith("<svg"), (
        "The root element of banana-tree.svg must be <svg>"
    )
    assert "viewBox" in content or "viewbox" in content.lower(), (
        "The <svg> element must have a viewBox attribute"
    )


# Scenario: The quote page shows banana trees on the pink background
def test_banana_tree_svg_has_no_external_references():
    """
    The SVG must be self-contained: no <image>, no <script>, no <style>,
    no <foreignObject>, no href/xlink:href to external URLs, and no
    http:// / https:// references except for namespace declarations.
    """
    assert os.path.isfile(SVG_PATH), f"{SVG_PATH} does not exist"
    with open(SVG_PATH, encoding="utf-8") as fh:
        content = fh.read()

    # Forbidden elements
    assert "<image" not in content.lower(), (
        "banana-tree.svg must not contain an <image> element"
    )
    assert "<script" not in content.lower(), (
        "banana-tree.svg must not contain a <script> element"
    )
    assert "<style" not in content.lower(), (
        "banana-tree.svg must not contain a <style> element"
    )
    assert "<foreignobject" not in content.lower(), (
        "banana-tree.svg must not contain a <foreignObject> element"
    )

    # No external http/https URLs other than xmlns namespace declarations
    # Strip xmlns="..." and xmlns:xlink="..." before checking for http URLs
    content_no_xmlns = re.sub(r'xmlns[^=]*="[^"]*"', '', content)
    external_urls = re.findall(r'https?://', content_no_xmlns)
    assert not external_urls, (
        f"banana-tree.svg must not contain external URLs (found {len(external_urls)}); "
        "only SVG namespace declarations are allowed"
    )

    # No href or xlink:href pointing to external resources
    hrefs = re.findall(r'(?:xlink:)?href\s*=\s*["\']([^"\']*)["\']', content)
    for href in hrefs:
        assert not href.startswith("http"), (
            f"banana-tree.svg must not have external href: {href}"
        )


# Scenario: The quote page shows banana trees on the pink background
def test_banana_tree_svg_colours_are_inline_presentation_attrs():
    """
    Style in the SVG should be expressed as inline presentation attributes
    (fill, stroke) rather than a <style> block.
    We verify the file has no <style> element (already checked above)
    and that it does contain at least one fill or stroke attribute, confirming
    that the drawing uses inline colour presentation.
    """
    assert os.path.isfile(SVG_PATH), f"{SVG_PATH} does not exist"
    with open(SVG_PATH, encoding="utf-8") as fh:
        content = fh.read()

    has_fill = "fill=" in content or "fill =" in content
    has_stroke = "stroke=" in content or "stroke =" in content
    assert has_fill or has_stroke, (
        "banana-tree.svg must use inline presentation attributes (fill/stroke) "
        "for colouring; no <style> block is allowed"
    )


# ===========================================================================
# Acceptance criteria: existing colours unchanged
# ===========================================================================

# Scenario: The quote page shows banana trees on the pink background
def test_heading_colour_unchanged():
    """
    The h1 must still use color: #c2185b.
    """
    html = _get_html()
    assert "#c2185b" in html, (
        "The h1 heading colour #c2185b must still be present in the template"
    )


# Scenario: The quote page shows banana trees on the pink background
def test_card_colour_unchanged():
    """
    The white card div must still use background-color: #ffffff.
    """
    html = _get_html()
    assert "#ffffff" in html, (
        "The card background-color #ffffff must still be present in the template"
    )


# Scenario: The quote page shows banana trees on the pink background
def test_right_banana_tree_is_mirrored():
    """
    The right banana tree must be horizontally flipped so it mirrors the left
    tree.  Its inline style must contain 'transform' with 'scaleX(-1)'.
    """
    parser = _get_parser()
    trees = _banana_img_tags(parser)
    right_trees = [t for t in trees if t.get("data-side") == "right"]
    assert right_trees, "No right banana tree found"
    for tree in right_trees:
        style = tree.get("style", "")
        assert "scalex(-1)" in style.lower() or "scaleX(-1)" in style, (
            f"Right banana tree must have transform: scaleX(-1) in its style; "
            f"got: '{style}'"
        )


# Scenario: The quote page shows banana trees on the pink background
def test_banana_trees_appear_before_h1_in_body():
    """
    According to the contract, the banana tree <img> elements must appear
    inside <body>, before the <h1>.  We verify the order in the HTML source.
    """
    html = _get_html()
    # Find positions of left banana tree, right banana tree, and h1
    left_pos = html.find('data-side="left"')
    if left_pos == -1:
        left_pos = html.find("data-side='left'")
    right_pos = html.find('data-side="right"')
    if right_pos == -1:
        right_pos = html.find("data-side='right'")
    h1_pos = html.lower().find("<h1")

    assert left_pos != -1, "data-side='left' not found in HTML"
    assert right_pos != -1, "data-side='right' not found in HTML"
    assert h1_pos != -1, "<h1> not found in HTML"

    assert left_pos < h1_pos, (
        "The left banana tree image must appear before the <h1> in the HTML"
    )
    assert right_pos < h1_pos, (
        "The right banana tree image must appear before the <h1> in the HTML"
    )
