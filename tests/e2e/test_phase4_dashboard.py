"""Phase 4 Dashboard Redesign - Playwright Verification Test.
Tests: KPI cards, quick actions, status breakdown, recent orders, activity feed.
"""
import os
import sys
from playwright.sync_api import sync_playwright

BASE_URL = "http://127.0.0.1:5053"
SCREENSHOTS_DIR = os.path.join(os.path.dirname(__file__), "screenshots", "phase4")
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
        page = browser.new_page(viewport={"width": 1400, "height": 900})

        console_errors = []
        page.on("console", lambda msg: console_errors.append(msg.text) if msg.type == "error" else None)

        # ── Login ─────────────────────────────────────────────
        print("1. Logging in...")
        page.goto(f"{BASE_URL}/login/test-bypass")
        page.wait_for_load_state("networkidle")
        assert "/dashboard" in page.url or page.url.endswith("/"), f"Login failed, url={page.url}"
        print("   ✅ Login OK")

        # ── Dashboard loads without error ─────────────────────
        print("\n2. Checking dashboard loads correctly...")
        page.goto(f"{BASE_URL}/")
        page.wait_for_load_state("networkidle")

        if "500" in page.title() or "error" in page.title().lower():
            errors.append("FAIL: Dashboard returned server error")
        else:
            print("   ✅ Dashboard loaded successfully")

        shot(page, "01_dashboard_full")

        # ── KPI Cards ─────────────────────────────────────────
        print("\n3. Checking KPI cards...")
        kpi_cards = page.locator(".kpi-card")
        kpi_count = kpi_cards.count()
        if kpi_count >= 4:
            print(f"   ✅ Found {kpi_count} KPI cards")
        else:
            errors.append(f"FAIL: Expected 4+ KPI cards, got {kpi_count}")

        # Check KPI card structure
        kpi_value = page.locator(".kpi-value")
        kpi_label = page.locator(".kpi-label")
        kpi_icon = page.locator(".kpi-icon")
        if kpi_value.count() >= 4:
            print(f"   ✅ KPI values present ({kpi_value.count()})")
        else:
            errors.append(f"FAIL: Expected 4+ .kpi-value, got {kpi_value.count()}")

        if kpi_label.count() >= 4:
            print(f"   ✅ KPI labels present ({kpi_label.count()})")
        else:
            errors.append(f"FAIL: Expected 4+ .kpi-label, got {kpi_label.count()}")

        if kpi_icon.count() >= 4:
            print(f"   ✅ KPI icons present ({kpi_icon.count()})")
        else:
            errors.append(f"FAIL: Expected 4+ .kpi-icon, got {kpi_icon.count()}")

        # Check KPI card CSS
        kpi_style = page.evaluate("""() => {
            const card = document.querySelector('.kpi-card');
            if (!card) return null;
            const s = getComputedStyle(card);
            return {
                borderLeft: s.borderLeftWidth,
                borderRadius: s.borderRadius,
                background: s.backgroundColor
            };
        }""")
        if kpi_style:
            if kpi_style["borderLeft"] and int(kpi_style["borderLeft"].replace("px", "")) >= 3:
                print(f"   ✅ KPI card left border: {kpi_style['borderLeft']}")
            else:
                warnings.append(f"WARN: KPI border-left: {kpi_style['borderLeft']}")
        else:
            errors.append("FAIL: Could not read KPI card styles")

        # Check accent variants
        accent_secondary = page.locator(".accent-secondary")
        accent_warning = page.locator(".accent-warning")
        accent_danger = page.locator(".accent-danger")
        accents = accent_secondary.count() + accent_warning.count() + accent_danger.count()
        if accents >= 2:
            print(f"   ✅ Accent variants found ({accents})")
        else:
            warnings.append(f"WARN: Only {accents} accent variants (expected 2+)")

        shot(page, "02_kpi_cards")

        # ── Quick Actions ─────────────────────────────────────
        print("\n4. Checking quick actions...")
        qa_grid = page.locator(".quick-actions-grid")
        if qa_grid.count() > 0:
            print("   ✅ Quick actions grid present")

            qa_items = page.locator(".quick-action-item")
            if qa_items.count() >= 4:
                print(f"   ✅ {qa_items.count()} quick action items")
            else:
                errors.append(f"FAIL: Expected 4+ quick action items, got {qa_items.count()}")

            # Check grid CSS
            grid_style = page.evaluate("""() => {
                const grid = document.querySelector('.quick-actions-grid');
                if (!grid) return null;
                const s = getComputedStyle(grid);
                return { display: s.display };
            }""")
            if grid_style and grid_style["display"] == "grid":
                print("   ✅ Quick actions uses CSS grid")
            else:
                warnings.append(f"WARN: Quick actions display: {grid_style}")

            # Check items are links
            qa_links = page.locator(".quick-action-item[href]")
            if qa_links.count() >= 4:
                print("   ✅ Quick action items are clickable links")
            else:
                warnings.append("WARN: Some quick action items may not be links")
        else:
            errors.append("FAIL: No .quick-actions-grid found")

        shot(page, "03_quick_actions")

        # ── Status Breakdown ──────────────────────────────────
        print("\n5. Checking status breakdown...")
        status_bars = page.locator(".status-bars")
        if status_bars.count() > 0:
            print("   ✅ Status bars container present")

            rows = page.locator(".status-bar-row")
            if rows.count() >= 1:
                print(f"   ✅ {rows.count()} status bar rows")
            else:
                warnings.append("WARN: No status-bar-row elements")

            tracks = page.locator(".status-bar-track")
            fills = page.locator(".status-bar-fill")
            if tracks.count() >= 1 and fills.count() >= 1:
                print("   ✅ Status bar tracks and fills present")
            else:
                warnings.append("WARN: Missing status-bar-track or status-bar-fill")
        else:
            errors.append("FAIL: No .status-bars found")

        shot(page, "04_status_breakdown")

        # ── Recent Process Orders Table ───────────────────────
        print("\n6. Checking recent process orders...")
        # Should be a table with recent orders
        recent_table = page.locator("table")
        if recent_table.count() > 0:
            headers = page.locator("table thead th")
            if headers.count() >= 3:
                print(f"   ✅ Recent orders table with {headers.count()} columns")
            else:
                warnings.append(f"WARN: Table has only {headers.count()} headers")

            rows = page.locator("table tbody tr")
            print(f"   ✅ {rows.count()} recent order rows")
        else:
            warnings.append("WARN: No table found (may have no data)")

        shot(page, "05_recent_orders")

        # ── Activity Feed ─────────────────────────────────────
        print("\n7. Checking activity feed...")
        feed = page.locator(".activity-feed")
        if feed.count() > 0:
            print("   ✅ Activity feed present")

            items = page.locator(".activity-item")
            if items.count() >= 1:
                print(f"   ✅ {items.count()} activity items")

                icon = page.locator(".activity-icon")
                body = page.locator(".activity-body")
                if icon.count() >= 1 and body.count() >= 1:
                    print("   ✅ Activity items have icon + body")
                else:
                    warnings.append("WARN: Activity items missing icon or body")
            else:
                print("   ℹ️ No activity items (may have no data)")
        else:
            errors.append("FAIL: No .activity-feed found")

        shot(page, "06_activity_feed")

        # ── Dashboard Layout (responsive columns) ─────────────
        print("\n8. Checking dashboard layout...")
        cols = page.locator(".col-lg-5, .col-lg-7, .col-lg-8, .col-lg-4")
        if cols.count() >= 4:
            print(f"   ✅ Layout columns present ({cols.count()})")
        else:
            warnings.append(f"WARN: Expected 4+ layout columns, got {cols.count()}")

        # ── Page Header ───────────────────────────────────────
        print("\n9. Checking page header...")
        header = page.locator(".page-header, h2")
        if header.count() > 0:
            print(f"   ✅ Page header present")
        else:
            warnings.append("WARN: No page header")

        # ── Breadcrumbs ───────────────────────────────────────
        print("\n10. Checking breadcrumbs...")
        breadcrumb = page.locator(".breadcrumb")
        if breadcrumb.count() > 0:
            print("   ✅ Breadcrumbs present")
        else:
            warnings.append("WARN: No breadcrumbs on dashboard")

        shot(page, "07_final_dashboard")

        # ── Summary ───────────────────────────────────────────
        print("\n" + "=" * 60)
        print("PHASE 4 RESULTS")
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
            print("\n✅ ALL PHASE 4 CHECKS PASSED!")
            browser.close()
            sys.exit(0)


if __name__ == "__main__":
    main()
