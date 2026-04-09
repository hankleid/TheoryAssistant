---
name: search-literature
description: "Search for and read physics papers relevant to a query using the 7-step arXiv/Semantic Scholar protocol"
argument-hint: "<search query>"
allowed-tools: WebSearch, WebFetch, Bash
---
# Search Literature

Search for and thoroughly read physics papers relevant to: **$ARGUMENTS**

## Search Protocol

**Never fetch `arxiv.org/search/` or any arXiv search page — those return no results reliably. Always use `WebSearch` (Google) to discover papers.**

Follow this priority order strictly for every paper you retrieve:

1. **Use `WebSearch` to find paper titles and arXiv IDs.** Search Google with natural language queries like `"Tavis-Cummings disorder cavity QED arXiv"`. The results will surface arXiv URLs, titles, and authors directly. Run multiple searches with varied phrasing to broaden coverage.

2. **Fetch the full paper as HTML using `arxiv.org/html/ARXIV_ID`**
   (NOT `arxiv.org/abs/` which only gives the abstract, and NOT `arxiv.org/pdf/` which returns an encoded PDF — not readable. Never fetch these URLs for paper content.)

3. **If that returns a 404, try the ar5iv mirror: `ar5iv.labs.arxiv.org/html/ARXIV_ID`**
   This renders arXiv papers as HTML when arXiv's own HTML version doesn't exist.
   If ar5iv redirects you to `arxiv.org/abs/`, that means no HTML version exists — treat this the same as a failure and move to step 4 immediately. Do NOT fetch the redirected abs/ URL.

4. **If both HTML attempts fail, go directly to Semantic Scholar**: `semanticscholar.org`
   Example query: `[paper title] site:semanticscholar.org`
   Search for the exact title. Semantic Scholar provides structured summaries that are much richer than arXiv abstract pages.
   Do this ONCE. Do not retry arxiv.org/html/ or ar5iv again after already getting a 404 or redirect from both.

5. **Also try searching for author-hosted PDFs**.
   Many researchers post papers on their lab or university pages. These are often accessible even when the journal version is paywalled.

6. Nature, APS, and similar publishers are paywalled and will return 403 or redirect errors. Do not waste a fetch call on these — go to arXiv instead.

7. **If all of the above fail, fetch `arxiv.org/abs/ARXIV_ID` as a last resort.**
   An abstract is better than nothing — it gives the key claims and results even without equations or methods. Only do this after genuinely exhausting steps 2–5.

**IMPORTANT**: A WebSearch result snippet is not the same as reading the paper. For any paper that contains equations, algorithms, or experimental details you need, you must actually fetch and read it — do not rely on the search summary.

## Outputs (mandatory - always do this first)

Return a structured summary of each paper found, including:
- Full citation (authors, title, year, arXiv ID or DOI)
- Key results relevant to the query
- Specific equations or parameter values if applicable

