# SEND Lab

Website: https://deokjaeheo.github.io/

## Editing

Content is updated manually and published by GitHub Pages when changes are committed to `main`. Google Scholar is linked from the Professor page but is **not automatically synchronized**.

- `publications-data.json`: published papers with reviewed `sci` / `other` categories; preserve DOI and author-role markers.
- `submitted-data.json`: public title, author list and submission status only. **Never add manuscript files, supplementary files or their links.**
- `patents-data.json`: patent grants and applications from the CV. International filing dates are omitted because the English/Korean CV dates differ.
- `professor.html`: appointments, education, Awards & Honors.
- `research.html`: research descriptions and representative figures.

Run `python render_publications.py`, `python -m unittest test_publications.py`, then `python prepare_pages.py` to check and stage the website. Dependencies are in `requirements.txt`.

The published site contains only the allowlisted public HTML, styles, scripts and image assets. Maintenance data and scripts remain in this public source repository, so do not store private materials anywhere in it.

`sync_scholar.py --render-only` is a compatibility alias; automatic Scholar fetching has been removed.

## Visit analytics

`analytics.js` connects the public pages to the owner's private Google Analytics 4 property. The measurement ID is public configuration, not an access credential. Never put dashboard credentials, visitor exports or access tokens in this repository.

The footer notice was removed at the site owner's request on 2026-09-25. `privacy.html` provides additional details and a per-browser opt-out when opened directly. The script respects Do Not Track / Global Privacy Control, skips previews and the privacy page, omits query strings and URL fragments, and disables Google signals and ad personalization. Analytics cookies are host-only and expire within 90 days. Enhanced measurement is disabled in the GA web stream.

Maintain one `analytics.js` reference on every public HTML page. Access to reports is managed inside Google Analytics; no report or public admin dashboard is hosted here.
