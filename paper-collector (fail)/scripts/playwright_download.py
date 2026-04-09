"""
playwright_download.py — process outputs/playwright_queue.jsonl

Opens a visible Chromium browser, pauses for institutional SSO login,
then downloads each queued PDF automatically.

Usage:
  source .venv/bin/activate
  python scripts/playwright_download.py

Optional flags:
  --start N     skip the first N entries (resume after interruption)
  --delay N     seconds to wait between papers (default: 8)
"""

import argparse, json, time, random, sys
from pathlib import Path
from playwright.sync_api import sync_playwright

QUEUE   = Path('outputs/playwright_queue.jsonl')
LOG     = Path('outputs/playwright_log.json')
PDF_DIR = Path('outputs/pdfs')


def load_queue():
    if not QUEUE.exists():
        print('No queue file found at outputs/playwright_queue.jsonl')
        sys.exit(1)
    entries = []
    for line in QUEUE.read_text().splitlines():
        line = line.strip()
        if line:
            entries.append(json.loads(line))
    return entries


def load_log():
    if LOG.exists():
        return json.loads(LOG.read_text())
    return {'ok': [], 'failed': [], 'skipped': []}


def save_log(log):
    LOG.write_text(json.dumps(log, indent=2))


def try_download(page, doi, dest: Path) -> bool:
    """
    Navigate to the SAGE article page and download the PDF.
    Returns True on success.
    """
    url = f'https://journals.sagepub.com/doi/abs/{doi}'
    try:
        page.goto(url, wait_until='domcontentloaded', timeout=30000)
        page.wait_for_timeout(2000)

        # Look for PDF download link on the article page
        pdf_link = None
        for selector in [
            'a[href*="/doi/pdf/"]',
            'a[href*="/doi/epdf/"]',
            'a.btn--pdf',
            'a:has-text("PDF")',
            'a:has-text("Download PDF")',
            'a:has-text("Full Text PDF")',
        ]:
            el = page.query_selector(selector)
            if el:
                pdf_link = el.get_attribute('href')
                break

        if not pdf_link:
            # Fallback: try direct PDF URL
            pdf_link = f'https://journals.sagepub.com/doi/pdf/{doi}'

        if not pdf_link.startswith('http'):
            pdf_link = 'https://journals.sagepub.com' + pdf_link

        # Download the PDF via a new page (captures the file response)
        with page.context.expect_page() as new_page_info:
            # Use fetch API in page context to get the PDF as bytes
            pass

        # Use requests-style download within the authenticated browser context
        pdf_bytes = page.evaluate(f"""
            async () => {{
                const resp = await fetch('{pdf_link}', {{credentials: 'include'}});
                if (!resp.ok) return null;
                const ct = resp.headers.get('content-type') || '';
                if (!ct.includes('pdf')) return null;
                const buf = await resp.arrayBuffer();
                return Array.from(new Uint8Array(buf));
            }}
        """)

        if not pdf_bytes or len(pdf_bytes) < 10000:
            return False

        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_bytes(bytes(pdf_bytes))
        return True

    except Exception as e:
        print(f'    Error: {e}')
        return False


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--start', type=int, default=0,
                        help='Skip first N entries (resume)')
    parser.add_argument('--delay', type=int, default=8,
                        help='Base seconds to wait between papers')
    args = parser.parse_args()

    queue = load_queue()
    log   = load_log()
    done  = set(log['ok'] + log['failed'] + log['skipped'])

    print(f'Queue: {len(queue)} papers total')
    print(f'Already processed: {len(done)}')
    print()

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False, slow_mo=100)
        context = browser.new_context(
            viewport={'width': 1280, 'height': 900},
            accept_downloads=True,
        )
        page = context.new_page()

        # ── Login step ────────────────────────────────────────────────────────
        print('Opening SAGE Journals...')
        page.goto('https://journals.sagepub.com', wait_until='domcontentloaded')
        print()
        print('=' * 60)
        print('Please log in through your institution\'s SSO in the browser.')
        print('Once you can see full-text access (e.g. a PDF button on any')
        print('article), come back here and press ENTER to start downloading.')
        print('=' * 60)
        input()

        # ── Download loop ─────────────────────────────────────────────────────
        ok_count = failed_count = skipped_count = 0

        for i, entry in enumerate(queue):
            if i < args.start:
                continue

            doi   = entry['doi']
            title = entry['title']
            dest  = Path(entry['dest'])

            # Skip if already done or file exists
            if doi in done:
                skipped_count += 1
                continue
            if dest.exists() and dest.stat().st_size > 10000:
                print(f'[{i+1}/{len(queue)}] Already on disk — skipping: {title[:60]}')
                log['skipped'].append(doi)
                save_log(log)
                skipped_count += 1
                continue

            print(f'[{i+1}/{len(queue)}] {title[:65]}')

            success = try_download(page, doi, dest)

            if success:
                print(f'    ✓ saved → {dest.name}')
                log['ok'].append(doi)
                ok_count += 1
            else:
                print(f'    ✗ failed (no access or no PDF found)')
                log['failed'].append(doi)
                failed_count += 1

            save_log(log)

            # Polite delay with jitter
            delay = args.delay + random.uniform(0, 4)
            time.sleep(delay)

        browser.close()

    # ── Summary ───────────────────────────────────────────────────────────────
    print()
    print('=' * 60)
    print(f'Done.')
    print(f'  ✓ Downloaded : {ok_count}')
    print(f'  ✗ Failed     : {failed_count}')
    print(f'  → Skipped    : {skipped_count} (already done)')
    print()
    if log['failed']:
        print('Failed DOIs:')
        for doi in log['failed']:
            print(f'  https://doi.org/{doi}')
    print('=' * 60)


if __name__ == '__main__':
    main()
