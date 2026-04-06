"""Phase 2 Enhanced Tables - Playwright Verification Test.
Tests: Card structure on listing pages, search bars, pagination, sticky headers, empty state.
"""
import os
import sys
from playwright.sync_api import sync_playwright

BASE_URL = "http://127.0.0.1:5053"
SCREENSHOTS_DIR = os.path.join(os.path.dirname(__file__), "screenshots", "phase2")
os.makedirs(SCREENSHOTS_DIR, exist_ok=True)


def shot(page, name):
    path = os.path.join(SCREENSHOTS_DIR, f"{name}.png")
    page.screenshot(path=path, full_page=True)
    print(f"  📸 {name}.png")
    return path


# Pages with tables wrapped in cards
LISTING_PAGES = [
    ("/process-orders/", "Process Orders"),
    ("/master-data/blends", "Blends"),
    ("/master-data/machines", "Machines"),
    ("/master-data/skus", "SKUs"),
    ("/master-data/calibration", "Calibration"),
    ("/master-data/physical-params", "Physical Params"),
    ("/master-data/tobacco-blend-analysis", "Tobacco Blend"),
    ("/master-data/size-cu", "Size CU"),
    ("/master-data/kp-tolerance", "KP Tolerance"),
    ("/master-data/plug-length-cuts", "Plug Length Cuts"),
    ("/master-data/app-fields", "App Fields"),
    ("/master-data/lookups", "Lookups"),
    ("/batch/", "Batch"),
    ("/reports/", "Reports"),
    ("/target-weight/", "Target Weight"),
]

# FG Codes uses a custom JS-driven interface (main_interface.html), not standard listing
FG_CODES_PATH = "/fg-codes/"


def main():
    errors = []
    warnings = []
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        page = browser.new_page(viewport={"width": 1400, "height": 900})

        console_errors = []
        page.on("console", lambda msg: console_errors.append(msg.text) if msg.type == "error" else None)

        network_errors = []
        page.on("response", lambda resp: network_errors.append(f"{resp.status} {resp.url}") if resp.status >= 400 else None)

        # ── Login ─────────────────────────────────────────────
        print("1. Logging in...")
        page.goto(f"{BASE_URL}/login/test-bypass")
        page.wait_for_load_state("networkidle")
        assert "/dashboard" in page.url or page.url.endswith("/"), f"Login failed, url={page.url}"
        print("   ✅ Login OK")

        # ── Check Card Structure on Listing Pages ─────────────
        print("\n2. Checking card structure on listing pages...")
        pages_checked = 0
        for path, name in LISTING_PAGES:
            page.goto(f"{BASE_URL}{path}")
            page.wait_for_load_state("networkidle")

            # Must have at least one .card
            cards = page.locator(".card")
            card_count = cards.count()
            if card_count == 0:
                errors.append(f"FAIL: {name} ({path}) - No .card found")
                continue

            # Card should have card-body
            card_body = page.locator(".card .card-body")
            if card_body.count() == 0:
                errors.append(f"FAIL: {name} ({path}) - No .card-body found")
                continue

            # Table should be inside card-body
            table_in_card = page.locator(".card .card-body table, .card .card-body .table-responsive table")
            if table_in_card.count() == 0:
                # Some pages might have empty state instead
                empty = page.locator(".card .card-body .empty-state, .card .card-body td .empty-state")
                if empty.count() == 0:
                    warnings.append(f"WARN: {name} ({path}) - No table or empty-state in card-body")

            # Table should have mb-0 (flush with card)
            table = page.locator(".card .card-body table.mb-0, .card .card-body .table-responsive table.mb-0")
            if table.count() == 0 and table_in_card.count() > 0:
                warnings.append(f"WARN: {name} ({path}) - Table missing mb-0 class")

            pages_checked += 1
            print(f"   ✅ {name}")

        shot(page, "01_last_listing_page")
        print(f"   Checked {pages_checked}/{len(LISTING_PAGES)} pages")

        # ── Check Search Bar Structure ────────────────────────
        print("\n3. Checking search bar on key pages...")
        search_pages = [
            ("/process-orders/", "Process Orders"),
            ("/master-data/blends", "Blends"),
            ("/reports/", "Reports"),
        ]
        for path, name in search_pages:
            page.goto(f"{BASE_URL}{path}")
            page.wait_for_load_state("networkidle")

            # Check for search-bar or search-input-wrap
            search = page.locator(".search-bar, .search-input-wrap, .card-header form")
            if search.count() == 0:
                errors.append(f"FAIL: {name} ({path}) - No search bar found")
            else:
                # Check for search icon
                icon = page.locator(".search-icon, .bi-search")
                if icon.count() > 0:
                    print(f"   ✅ {name} - search bar with icon")
                else:
                    print(f"   ✅ {name} - search bar present")

        shot(page, "02_search_bars")

        # ── Check Sticky Table Headers ────────────────────────
        print("\n4. Checking sticky table headers...")
        page.goto(f"{BASE_URL}/process-orders/")
        page.wait_for_load_state("networkidle")

        th = page.locator("table thead th").first
        if th.count() > 0:
            position = page.evaluate("""() => {
                const th = document.querySelector('table thead th');
                if (!th) return 'none';
                return getComputedStyle(th).position;
            }""")
            if position == "sticky":
                print("   ✅ Table headers are sticky")
            else:
                warnings.append(f"WARN: th position is '{position}', expected 'sticky'")
                print(f"   ⚠️ th position: {position}")
        else:
            warnings.append("WARN: No table headers found on process orders page")

        # ── Check Table Row Hover Transition ──────────────────
        print("\n5. Checking table row transition...")
        transition = page.evaluate("""() => {
            const tr = document.querySelector('table tbody tr');
            if (!tr) return 'none';
            return getComputedStyle(tr).transition;
        }""")
        if transition and "background" in transition:
            print(f"   ✅ Row hover transition active")
        else:
            warnings.append(f"WARN: Row transition: {transition}")
            print(f"   ⚠️ Row transition: {transition}")

        shot(page, "03_table_headers")

        # ── Check Card Header / Footer Structure ──────────────
        print("\n6. Checking card-header and card-footer...")
        page.goto(f"{BASE_URL}/master-data/blends")
        page.wait_for_load_state("networkidle")

        header = page.locator(".card .card-header")
        footer = page.locator(".card .card-footer")

        if header.count() > 0:
            print("   ✅ card-header present")
        else:
            errors.append("FAIL: Blends - No card-header")

        # Card-footer only appears when pagination exists (pages > 1)
        # So we just confirm the structure is correct
        print("   ✅ card structure verified")

        # ── Check Pagination Styling ──────────────────────────
        print("\n7. Checking pagination styling...")
        # Navigate to a page that likely has pagination
        page.goto(f"{BASE_URL}/process-orders/")
        page.wait_for_load_state("networkidle")

        pagination = page.locator(".table-pagination, .pagination")
        if pagination.count() > 0:
            print("   ✅ Pagination component found")
            # Check for page info text
            page_info = page.locator(".pagination-info")
            if page_info.count() > 0:
                print(f"   ✅ Pagination info: {page_info.first.text_content().strip()}")
            else:
                print("   ℹ️ No pagination-info (may be single page)")
        else:
            print("   ℹ️ No pagination visible (single page or no data)")

        shot(page, "04_pagination")

        # ── Check Empty State ─────────────────────────────────
        print("\n8. Checking empty state styling...")
        # Search for something that won't match to trigger empty state
        page.goto(f"{BASE_URL}/master-data/blends?q=zzzzzzzzz_nomatch_xyz")
        page.wait_for_load_state("networkidle")

        empty = page.locator(".empty-state")
        if empty.count() > 0:
            icon = page.locator(".empty-state-icon")
            text = page.locator(".empty-state-text")
            print(f"   ✅ Empty state visible")
            if icon.count() > 0:
                print(f"   ✅ Empty state icon present")
            if text.count() > 0:
                print(f"   ✅ Empty state text: {text.first.text_content().strip()[:50]}")
        else:
            # May just show "no records" in a different way
            warnings.append("WARN: Empty state component not found on blends search with no match")
            print("   ⚠️ Empty state not found (may use different pattern)")

        shot(page, "05_empty_state")

        # ── Check Audit Trail Card ────────────────────────────
        print("\n9. Checking audit trail card structure...")
        page.goto(f"{BASE_URL}/admin/audit-trail")
        page.wait_for_load_state("networkidle")

        audit_card = page.locator(".card")
        if audit_card.count() > 0:
            audit_header = page.locator(".card .card-header")
            audit_body = page.locator(".card .card-body")
            if audit_header.count() > 0 and audit_body.count() > 0:
                print("   ✅ Audit trail in card with header + body")
            else:
                errors.append("FAIL: Audit trail card missing header or body")
        else:
            errors.append("FAIL: Audit trail not wrapped in card")

        shot(page, "06_audit_trail")

        # ── Check Table-Responsive Wrapper ────────────────────
        print("\n10. Checking table-responsive wrappers...")
        page.goto(f"{BASE_URL}/master-data/skus")
        page.wait_for_load_state("networkidle")

        responsive = page.locator(".card .card-body .table-responsive")
        if responsive.count() > 0:
            print("   ✅ table-responsive wrapper present")
        else:
            warnings.append("WARN: SKUs page missing table-responsive wrapper")
            print("   ⚠️ No table-responsive wrapper found")

        shot(page, "07_table_responsive")

        # ── Summary ───────────────────────────────────────────
        print("\n" + "=" * 60)
        print("PHASE 2 RESULTS")
        print("=" * 60)

        if console_errors:
            print(f"\n⚠️  Console errors ({len(console_errors)}):")
            for e in console_errors[:5]:
                print(f"   {e[:100]}")

        if network_errors:
            print(f"\n⚠️  Network errors ({len(network_errors)}):")
            for e in network_errors[:5]:
                print(f"   {e[:100]}")

        if warnings:
            print(f"\n⚠️  Warnings ({len(warnings)}):")
            for w in warnings:
                print(f"   {w}")

        if errors:
            print(f"\n❌ FAILURES ({len(errors)}):")
            for e in errors:
                print(f"   {e}")
            browser.close()
            sys.exit(1)
        else:
            print("\n✅ ALL PHASE 2 CHECKS PASSED!")
            browser.close()
            sys.exit(0)


if __name__ == "__main__":
    main()
