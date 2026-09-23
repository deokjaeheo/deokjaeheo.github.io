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
