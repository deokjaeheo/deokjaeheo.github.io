# SEND Lab

Website: https://deokjaeheo.github.io/

Sensor / Energy / Nanotechnology Device Laboratory, led by Prof. Deokjae Heo, School of Mechanical Engineering, Kumoh National Institute of Technology.

국립금오공과대학교 기계공학부 허덕재 교수의 센서/에너지/나노기술소자연구실입니다.

## Editing and publishing

Edit the relevant HTML file in GitHub and commit to `main`. The included GitHub Actions workflow publishes the site. Pages settings must use **GitHub Actions** as the source. Hosting is free for this public repository; no continuously running personal computer is required.

- `index.html`: home
- `professor.html`: biography, appointments, honors
- `research.html`: research areas and figures
- `members.html`: members
- `teaching.html`: courses
- `contact.html`: contact and office map
- `publications-data.json`: authoritative publication list; the workflow renders `publications.html` from this file, newest first

Keep publication corrections in `publications-data.json`, not only in the generated HTML. Existing `authors_html` includes verified superscript first/co-first (†) and corresponding (*) author markers. Keep those markers when editing authors. For local rendering: `python -m pip install -r requirements.txt`, then `python sync_scholar.py --render-only`.

## Google Scholar updates

**Current status (23 September 2026):** the public-profile check succeeded locally, but its first GitHub Actions run was rejected by Google Scholar with HTTP 403. Scheduled checks are disabled; automatic Scholar-to-website synchronization is **not active**. Website publishing works independently and continues on every push. Update publications through `publications-data.json` in the meantime.

The prepared check can be run manually from **Actions → Update publications and publish website → Run workflow** with **Check Google Scholar before publishing** enabled. It is a best-effort check, not an official Google Scholar API or a real-time connection. Do not enable scheduled checks until access is confirmed working; do not bypass Google access restrictions.

The script respects Scholar's robots rules, makes no authenticated requests, and does not bypass access restrictions. It reads the latest public profile records without pagination. New publications need an unambiguous matching Crossref DOI, title, publication year and full author name before being added. Existing publications are never deleted automatically. It retains curated metadata until that field changes on Scholar.

Google Scholar does not establish co-first or corresponding-author roles. New role markers and changed author lists require review. Unmatched records are also held for review in `scholar-sync-state.json` under `review`; update the corresponding publication data manually and clear the resolved review entry. `last_successful_check` records the last completed check. Access blocks or changed page layouts fail the job while preserving the published list; inspect failed runs in Actions. No subscription or paid API is used.

## Search and public files

Page titles, descriptions, bilingual identity text, structured data, canonical URLs, `robots.txt` and `sitemap.xml` support search discovery. Search ranking and timing are controlled by search engines.

Only website assets are staged for Pages. The repository and its change history are public: include only material intended for public viewing, never credentials, private CVs or unpublished manuscripts. Research figures remain subject to their respective rights.
