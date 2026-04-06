"""Phase 5 Targets & Limits - Playwright Verification Test.
Tests: Card wrapper, column group headers, frozen columns, legend, color coding, pagination.
"""
import os
import sys
from playwright.sync_api import sync_playwright

BASE_URL = "http://127.0.0.1:5053"
SCREENSHOTS_DIR = os.path.join(os.path.dirname(__file__), "screenshots", "phase5")
os.makedirs(SCREENSHOTS_DIR, exist_ok=True)


def shot(page, name):
    path = os.path.join(SCREENSHOTS_DIR, f"{name}.png")
    page.screenshot(path=path, full_page=True)
    print(f"  📸 {name}.png")
    return path


def main():
    errors = []
    warnings = []
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        page = browser.new_page(viewport={"width": 1600, "height": 900})

        console_errors = []
        page.on("console", lambda msg: console_errors.append(msg.text) if msg.type == "error" else None)

        # ── Login ─────────────────────────────────────────────
        print("1. Logging in...")
        page.goto(f"{BASE_URL}/login/test-bypass")
        page.wait_for_load_state("networkidle")
        assert "/dashboard" in page.url or page.url.endswith("/"), f"Login failed, url={page.url}"
        print("   ✅ Login OK")

        # ── Navigate to Targets & Limits ──────────────────────
        print("\n2. Loading Targets & Limits page...")
        page.goto(f"{BASE_URL}/master-data/targets-limits")
        page.wait_for_load_state("networkidle")

        if "500" in page.title() or "error" in page.title().lower():
            errors.append("FAIL: Targets & Limits returned server error")
            print("   ❌ Server error!")
        else:
            print("   ✅ Page loaded")

        shot(page, "01_full_page")

        # ── Card Wrapper ──────────────────────────────────────
        print("\n3. Checking card wrapper...")
        card = page.locator(".card")
        if card.count() > 0:
            print("   ✅ Card wrapper present")

            header = page.locator(".card .card-header")
            body = page.locator(".card .card-body")
            if header.count() > 0:
                print("   ✅ card-header present")
            else:
                errors.append("FAIL: No card-header")

            if body.count() > 0:
                print("   ✅ card-body present")
            else:
                errors.append("FAIL: No card-body")
        else:
            errors.append("FAIL: No .card wrapper")

        # ── Legend ────────────────────────────────────────────
        print("\n4. Checking column group legend...")
        legend = page.locator(".tl-legend")
        if legend.count() > 0:
            print("   ✅ Legend present")

            dots = page.locator(".tl-legend-dot")
            items = page.locator(".tl-legend-item")
            if items.count() >= 10:
                print(f"   ✅ {items.count()} legend items")
            else:
                errors.append(f"FAIL: Expected 10+ legend items, got {items.count()}")

            if dots.count() >= 10:
                print(f"   ✅ {dots.count()} color dots")
            else:
                errors.append(f"FAIL: Expected 10+ legend dots, got {dots.count()}")

            # Check legend CSS
            legend_style = page.evaluate("""() => {
                const el = document.querySelector('.tl-legend');
                if (!el) return null;
                const s = getComputedStyle(el);
                return { display: s.display, flexWrap: s.flexWrap };
            }""")
            if legend_style and legend_style["display"] == "flex":
                print("   ✅ Legend uses flexbox")
            else:
                warnings.append(f"WARN: Legend display: {legend_style}")
        else:
            errors.append("FAIL: No .tl-legend found")

        shot(page, "02_legend")

        # ── Table Wrapper ─────────────────────────────────────
        print("\n5. Checking table wrapper...")
        wrap = page.locator(".tl-table-wrap")
        if wrap.count() > 0:
            print("   ✅ .tl-table-wrap present")

            wrap_style = page.evaluate("""() => {
                const el = document.querySelector('.tl-table-wrap');
                if (!el) return null;
                const s = getComputedStyle(el);
                return { overflow: s.overflow, maxHeight: s.maxHeight };
            }""")
            if wrap_style and wrap_style["maxHeight"] and wrap_style["maxHeight"] != "none":
                print(f"   ✅ max-height: {wrap_style['maxHeight']}")
            else:
                warnings.append("WARN: No max-height on table wrapper")
        else:
            errors.append("FAIL: No .tl-table-wrap found")

        # ── Group Header Row ──────────────────────────────────
        print("\n6. Checking group header row...")
        group_row = page.locator(".tl-group-row")
        if group_row.count() > 0:
            print("   ✅ Group header row present")

            group_cells = page.locator(".tl-group-row th")
            if group_cells.count() >= 10:
                print(f"   ✅ {group_cells.count()} group headers")
            else:
                errors.append(f"FAIL: Expected 10+ group headers, got {group_cells.count()}")

            # Check group headers are sticky
            sticky = page.evaluate("""() => {
                const th = document.querySelector('.tl-group-row th');
                return th ? getComputedStyle(th).position : 'none';
            }""")
            if sticky == "sticky":
                print("   ✅ Group headers are sticky")
            else:
                warnings.append(f"WARN: Group header position: {sticky}")

            # Check color backgrounds
            bg = page.evaluate("""() => {
                const th = document.querySelector('.tl-hdr-circumference');
                return th ? getComputedStyle(th).backgroundColor : 'none';
            }""")
            if bg and bg != "rgba(0, 0, 0, 0)":
                print(f"   ✅ Group header has color: {bg}")
            else:
                warnings.append(f"WARN: No color on group header: {bg}")
        else:
            errors.append("FAIL: No .tl-group-row found")

        shot(page, "03_group_headers")

        # ── Column Header Row ─────────────────────────────────
        print("\n7. Checking column header row...")
        col_row = page.locator(".tl-column-row")
        if col_row.count() > 0:
            print("   ✅ Column header row present")

            col_cells = page.locator(".tl-column-row th")
            if col_cells.count() >= 50:
                print(f"   ✅ {col_cells.count()} column headers (60+ columns)")
            else:
                errors.append(f"FAIL: Expected 50+ column headers, got {col_cells.count()}")
        else:
            errors.append("FAIL: No .tl-column-row found")

        # ── Frozen Columns ────────────────────────────────────
        print("\n8. Checking frozen columns...")
        frozen = page.locator(".tl-frozen-col")
        if frozen.count() > 0:
            print(f"   ✅ {frozen.count()} frozen column cells")

            # Check frozen idx is sticky
            idx_sticky = page.evaluate("""() => {
                const el = document.querySelector('.tl-frozen-idx');
                return el ? getComputedStyle(el).position : 'none';
            }""")
            if idx_sticky == "sticky":
                print("   ✅ Index column is sticky")
            else:
                errors.append(f"FAIL: Index column position: {idx_sticky}")

            # Check frozen fg column
            fg_sticky = page.evaluate("""() => {
                const el = document.querySelector('tbody .tl-frozen-fg');
                return el ? getComputedStyle(el).position : 'none';
            }""")
            if fg_sticky == "sticky":
                print("   ✅ FG Code column is sticky")
            else:
                errors.append(f"FAIL: FG Code column position: {fg_sticky}")

            # Check fg column has border-right
            fg_border = page.evaluate("""() => {
                const el = document.querySelector('tbody .tl-frozen-fg');
                return el ? getComputedStyle(el).borderRightWidth : 'none';
            }""")
            if fg_border and fg_border != "0px":
                print(f"   ✅ FG Code has separator border ({fg_border})")
            else:
                warnings.append("WARN: No separator border on FG Code column")
        else:
            errors.append("FAIL: No .tl-frozen-col found")

        shot(page, "04_frozen_columns")

        # ── Data Rows ─────────────────────────────────────────
        print("\n9. Checking data rows...")
        rows = page.locator(".tl-table tbody tr")
        row_count = rows.count()
        if row_count >= 1:
            print(f"   ✅ {row_count} data rows")
        else:
            warnings.append("WARN: No data rows (table may be empty)")

        # ── Column Tint Colors ────────────────────────────────
        print("\n10. Checking column tint colors...")
        nic_bg = page.evaluate("""() => {
            const el = document.querySelector('.tl-col-nic');
            return el ? getComputedStyle(el).backgroundColor : 'none';
        }""")
        if nic_bg and nic_bg != "rgba(0, 0, 0, 0)":
            print(f"   ✅ Nicotine column has tint: {nic_bg}")
        else:
            warnings.append(f"WARN: No tint on nicotine column: {nic_bg}")

        # ── Search Bar ────────────────────────────────────────
        print("\n11. Checking search bar...")
        search = page.locator(".card-header .search-bar, .card-header form")
        if search.count() > 0:
            print("   ✅ Search bar in card header")
        else:
            warnings.append("WARN: No search bar in card header")

        # ── Breadcrumbs ───────────────────────────────────────
        print("\n12. Checking breadcrumbs...")
        breadcrumb = page.locator(".breadcrumb")
        if breadcrumb.count() > 0:
            print("   ✅ Breadcrumbs present")
        else:
            warnings.append("WARN: No breadcrumbs")

        shot(page, "05_final_view")

        # ── Summary ───────────────────────────────────────────
        print("\n" + "=" * 60)
        print("PHASE 5 RESULTS")
        print("=" * 60)

        if console_errors:
            print(f"\n⚠️  Console errors ({len(console_errors)}):")
            for e in console_errors[:5]:
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
            print("\n✅ ALL PHASE 5 CHECKS PASSED!")
            browser.close()
            sys.exit(0)


if __name__ == "__main__":
    main()
