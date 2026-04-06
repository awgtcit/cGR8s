"""Quick validation of new pages."""
import time
from playwright.sync_api import sync_playwright

BASE_URL = 'http://127.0.0.1:5053'

with sync_playwright() as p:
    browser = p.chromium.launch(headless=False, slow_mo=300)
    page = browser.new_page(viewport={'width': 1440, 'height': 900})

    # Login
    page.goto(f'{BASE_URL}/login/test-bypass')
    page.wait_for_load_state('networkidle')
    print(f'Logged in: {page.url}')

    # Test all 4 new pages
    new_pages = [
        ('/master-data/size-cu', 'Size / CU'),
        ('/master-data/kp-tolerance', 'KP Tolerance'),
        ('/master-data/plug-length-cuts', 'Plug Length / Cuts'),
        ('/master-data/app-fields', 'App Fields'),
    ]

    for url, name in new_pages:
        page.goto(f'{BASE_URL}{url}')
        page.wait_for_load_state('networkidle')
        rows = page.locator('table tbody tr')
        count = rows.count()
        title = page.title()
        if count > 0:
            first = rows.first.inner_text().strip()[:60]
            print(f'OK  {name}: {count} rows | title="{title}" | first={first}')
        else:
            print(f'FAIL {name}: 0 rows | title="{title}"')

    # Check sidebar has all 9 sub-links
    page.goto(f'{BASE_URL}/master-data/blends')
    page.wait_for_load_state('networkidle')
    links = page.locator('#masterDataSub a.nav-link')
    link_count = links.count()
    link_texts = [links.nth(i).inner_text().strip() for i in range(link_count)]
    print(f'\nSidebar sub-nav ({link_count} links): {link_texts}')

    time.sleep(3)
    browser.close()

print('\nDone!')
