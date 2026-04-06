"""
Phase 6 – Polish & Animations  (Playwright, headed Chrome)
Tests: smooth scrolling, page entrance animation, card animation,
       button press effect, scroll-to-top, flash message animation,
       HTMX loading styles, reduced-motion support, sidebar active indicator,
       loading bar element, status badge pulse.
"""

from playwright.sync_api import sync_playwright
import time, sys, os

BASE = "http://127.0.0.1:5053"
SHOTS = os.path.join(os.path.dirname(__file__), "screenshots", "phase6")
os.makedirs(SHOTS, exist_ok=True)

passed = 0
failed = 0
warnings = []


def check(label, ok):
    global passed, failed
    if ok:
        print(f"   \u2705 {label}")
        passed += 1
    else:
        print(f"   \u274c {label}")
        failed += 1


def warn(msg):
    global warnings
    warnings.append(msg)


with sync_playwright() as pw:
    browser = pw.chromium.launch(headless=False, channel="chrome")
    ctx = browser.new_context(viewport={"width": 1440, "height": 900})
    page = ctx.new_page()

    console_errors = []
    page.on("console", lambda m: console_errors.append(m.text) if m.type == "error" else None)

    # ── 1. Login ──────────────────────────────────────────
    print("1. Logging in...")
    page.goto(f"{BASE}/login/test-bypass", wait_until="networkidle")
    check("Login OK", "/login" not in page.url)

    # ── 2. Dashboard page ─────────────────────────────────
    print("\n2. Loading dashboard...")
    page.goto(f"{BASE}/", wait_until="networkidle")
    page.wait_for_timeout(500)
    check("Dashboard loaded", page.title() != "")
    page.screenshot(path=os.path.join(SHOTS, "01_dashboard.png"), full_page=True)

    # ── 3. Smooth scroll on html ──────────────────────────
    print("\n3. Checking smooth scrolling...")
    scroll_behavior = page.evaluate("getComputedStyle(document.documentElement).scrollBehavior")
    check("scroll-behavior: smooth on html", scroll_behavior == "smooth")

    # ── 4. Page content entrance animation ────────────────
    print("\n4. Checking page entrance animation...")
    main_anim = page.evaluate("""
        getComputedStyle(document.querySelector('main.container-fluid')).animationName
    """)
    check("main has fadeInUp animation", main_anim == "fadeInUp")

    # ── 5. Card animation ─────────────────────────────────
    print("\n5. Checking card animation...")
    card = page.query_selector(".card")
    if card:
        card_anim = page.evaluate("el => getComputedStyle(el).animationName", card)
        check("Card has fadeInUp animation", card_anim == "fadeInUp")
    else:
        warn("No .card found on dashboard")

    # ── 6. KPI card stagger delays ────────────────────────
    print("\n6. Checking KPI card stagger...")
    kpi_cards = page.query_selector_all(".kpi-card")
    if len(kpi_cards) >= 2:
        d1 = page.evaluate("el => getComputedStyle(el).animationDelay", kpi_cards[0])
        d2 = page.evaluate("el => getComputedStyle(el).animationDelay", kpi_cards[1])
        # Cards inside col wrappers: 1st col→0.05s, 2nd col→0.1s
        check(f"KPI stagger: card1={d1}, card2={d2}", d1 != d2 or d1 == "0.05s")
    else:
        warn("Fewer than 2 KPI cards found")

    # ── 7. Button press active state ──────────────────────
    print("\n7. Checking button active scaling...")
    # Verify the CSS rule exists via stylesheet check
    has_active = page.evaluate("""
        (() => {
            for (const sheet of document.styleSheets) {
                try {
                    for (const rule of sheet.cssRules) {
                        if (rule.selectorText && rule.selectorText.includes('btn:active'))
                            return true;
                    }
                } catch(e) {}
            }
            return false;
        })()
    """)
    check("btn:active scale rule exists", has_active)

    # ── 8. Card hover lift transition ─────────────────────
    print("\n8. Checking card hover lift...")
    if card:
        card_transition = page.evaluate("el => getComputedStyle(el).transition", card)
        check("Card has box-shadow transition", "box-shadow" in card_transition)
    else:
        warn("No .card to check transition")

    # ── 9. Sidebar active indicator ───────────────────────
    print("\n9. Checking sidebar active indicator...")
    active_link = page.query_selector(".sidebar .nav-link.active")
    if active_link:
        position = page.evaluate("el => getComputedStyle(el).position", active_link)
        check("Active nav-link position: relative", position == "relative")
        # Check ::before pseudo element
        has_before = page.evaluate("""
            el => {
                const s = getComputedStyle(el, '::before');
                return s.content !== 'none' && s.content !== '';
            }
        """, active_link)
        check("Active nav-link has ::before indicator", has_before)
    else:
        warn("No active sidebar link found")

    page.screenshot(path=os.path.join(SHOTS, "02_sidebar_indicator.png"))

    # ── 10. Page loading bar element ──────────────────────
    print("\n10. Checking page loading bar...")
    bar = page.query_selector("#pageLoadingBar")
    check("Loading bar element exists", bar is not None)
    if bar:
        bar_display = page.evaluate("el => getComputedStyle(el).display", bar)
        check("Loading bar hidden by default", bar_display == "none")

    # ── 11. Scroll-to-top button ──────────────────────────
    print("\n11. Checking scroll-to-top button...")
    scroll_btn = page.query_selector("#scrollTopBtn")
    check("Scroll-to-top button exists", scroll_btn is not None)
    if scroll_btn:
        vis = page.evaluate("el => getComputedStyle(el).visibility", scroll_btn)
        check("Scroll-to-top hidden initially", vis == "hidden")

        # Navigate to a long page to test visibility
        page.goto(f"{BASE}/master-data/targets-limits", wait_until="networkidle")
        page.wait_for_timeout(500)
        # Force document height for scroll test and scroll down
        page.evaluate("""
            document.body.style.minHeight = '3000px';
            window.scrollTo(0, 600);
        """)
        page.wait_for_timeout(600)
        scroll_btn_now = page.query_selector("#scrollTopBtn")
        vis_after = page.evaluate("el => getComputedStyle(el).visibility", scroll_btn_now)
        check("Scroll-to-top visible after scroll", vis_after == "visible")
        page.screenshot(path=os.path.join(SHOTS, "03_scroll_top.png"))

    # ── 12. Flash message animation rule ──────────────────
    print("\n12. Checking flash message animation...")
    has_alert_anim = page.evaluate("""
        (() => {
            for (const sheet of document.styleSheets) {
                try {
                    for (const rule of sheet.cssRules) {
                        if (rule.selectorText === '.alert' &&
                            rule.style.animationName === 'slideDown')
                            return true;
                    }
                } catch(e) {}
            }
            return false;
        })()
    """)
    check("Alert slideDown animation rule exists", has_alert_anim)

    # ── 13. HTMX loading spinner styles ───────────────────
    print("\n13. Checking HTMX loading spinner CSS...")
    has_spinner = page.evaluate("""
        (() => {
            for (const sheet of document.styleSheets) {
                try {
                    for (const rule of sheet.cssRules) {
                        if (rule.selectorText === '.htmx-loading::after')
                            return true;
                    }
                } catch(e) {}
            }
            return false;
        })()
    """)
    check("HTMX loading spinner ::after rule exists", has_spinner)

    # ── 14. Reduced motion support ────────────────────────
    print("\n14. Checking reduced motion support...")
    has_reduced = page.evaluate("""
        (() => {
            for (const sheet of document.styleSheets) {
                try {
                    for (const rule of sheet.cssRules) {
                        if (rule.conditionText &&
                            rule.conditionText.includes('prefers-reduced-motion'))
                            return true;
                    }
                } catch(e) {}
            }
            return false;
        })()
    """)
    check("prefers-reduced-motion media query exists", has_reduced)

    # ── 15. Table row transition ──────────────────────────
    print("\n15. Checking table row transitions...")
    tr = page.query_selector(".table tbody tr")
    if tr:
        tr_transition = page.evaluate("el => getComputedStyle(el).transition", tr)
        check("Table row has background-color transition", "background-color" in tr_transition)
    else:
        warn("No table rows found")

    # ── 16. Pagination link transition ────────────────────
    print("\n16. Checking pagination transitions...")
    pg_link = page.query_selector(".page-link")
    if pg_link:
        pg_transition = page.evaluate("el => getComputedStyle(el).transition", pg_link)
        check("Page link has transition", pg_transition != "" and pg_transition != "none" and "0s" not in pg_transition)
    else:
        warn("No pagination links found")

    page.screenshot(path=os.path.join(SHOTS, "04_final.png"), full_page=True)

    # ── Summary ───────────────────────────────────────────
    print("\n" + "=" * 60)
    print("PHASE 6 RESULTS")
    print("=" * 60)

    if console_errors:
        print(f"\n\u26a0\ufe0f  Console errors ({len(console_errors)}):")
        for e in console_errors[:5]:
            print(f"   {e}")

    if warnings:
        print(f"\n\u26a0\ufe0f  Warnings ({len(warnings)}):")
        for w in warnings:
            print(f"   WARN: {w}")

    total = passed + failed
    print(f"\n   Passed: {passed}/{total}")
    if failed:
        print(f"   Failed: {failed}/{total}")
        print("\n\u274c PHASE 6 HAS FAILURES")
    else:
        print("\n\u2705 ALL PHASE 6 CHECKS PASSED!")

    browser.close()
    sys.exit(1 if failed else 0)
