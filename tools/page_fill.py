"""Print how full each page of a PDF of music is: the number of staves on the page.

Use: uv run python tools/page_fill.py FILE.pdf [FILE.pdf ...]

A page of a part with few staves has much empty space. A page with more than
12 staves is too full. The build uses the same count to select the page on
which the music of a part starts (see `src/stmatthew/notation/pages.py`).
"""

import sys
from pathlib import Path

from stmatthew.notation.pages import staves_on_pages

for name in sys.argv[1:]:
    found = staves_on_pages(Path(name))
    print(f"{Path(name).name}: {len(found)} pages, staves on each page: {found}")
