---
name: search-literature
description: "Search for and read physics papers relevant to a query, using the Paperclip MCP server for arXiv full text with a WebSearch/Semantic Scholar fallback"
argument-hint: "<search query>"
allowed-tools: ToolSearch, WebSearch, WebFetch, Bash, mcp__paperclip__*
---
# Search Literature

Search for and thoroughly read physics papers relevant to: **$ARGUMENTS**

## Search Protocol

A `paperclip` MCP server is connected to this project (`claude mcp list` shows it as `paperclip`). It gives direct, structured access to arXiv full text as a virtual filesystem, and should be your primary retrieval path. Its tools are deferred — if they don't already appear as callable tools, run `ToolSearch` with a query like `"paperclip search"` or `"paperclip cat"` to load their schemas before calling them.

Follow this priority order strictly for every paper you retrieve:

1. **Search Paperclip's arXiv corpus.** Use the paperclip search tool scoped to the arXiv source (equivalent to `search -s arxiv "<query>" -n 10`) with a natural-language query. If you already know the arXiv ID, use the lookup tool instead (equivalent to `lookup arxiv <ARXIV_ID>`).

2. **Read the full text with the paperclip cat tool.** Each paper is addressed as `/papers/arx_<id>/content.lines` (full text, line-numbered) or `/papers/arx_<id>/sections/<Name>.lines` (e.g. `Methods.lines`, `Results.lines`) to jump straight to a relevant section on long papers. This replaces fetching `arxiv.org/html` or ar5iv — it returns real full text directly.

3. **Locate specific claims or equations with the paperclip grep tool**, e.g. against `/papers/arx_<id>/content.lines`, instead of re-reading the whole file.

4. **Fallback — only if step 1 finds nothing for the paper or topic** (Paperclip's arXiv corpus is large but not exhaustive), fall back to the manual chain below:
   1. **Use `WebSearch` to find paper titles and arXiv IDs.** Search Google with natural language queries like `"Tavis-Cummings disorder cavity QED arXiv"`. Run multiple searches with varied phrasing to broaden coverage.
   2. **Fetch the full paper as HTML using `arxiv.org/html/ARXIV_ID`** (NOT `arxiv.org/abs/`, which only gives the abstract, and NOT `arxiv.org/pdf/`, which returns an encoded PDF — not readable).
   3. **If that returns a 404, try the ar5iv mirror: `ar5iv.labs.arxiv.org/html/ARXIV_ID`.** If ar5iv redirects to `arxiv.org/abs/`, that means no HTML version exists — treat this as a failure and move to the next step immediately. Do NOT fetch the redirected abs/ URL.
   4. **If both HTML attempts fail, go directly to Semantic Scholar**: `semanticscholar.org`. Example query: `[paper title] site:semanticscholar.org`. Do this ONCE — do not retry arxiv.org/html or ar5iv again after a 404/redirect from both.
   5. **Also try searching for author-hosted PDFs.** Many researchers post papers on their lab or university pages, often accessible even when the journal version is paywalled.
   6. Nature, APS, and similar publishers are paywalled and will return 403 or redirect errors. Do not waste a fetch call on these — go to arXiv instead.
   7. **If all of the above fail, fetch `arxiv.org/abs/ARXIV_ID` as a last resort.** An abstract is better than nothing — it gives the key claims and results even without equations or methods. Only do this after genuinely exhausting the steps above.

**IMPORTANT**: A paperclip `search`/`lookup` result (or a WebSearch result snippet) is not the same as reading the paper. For any paper that contains equations, algorithms, or experimental details you need, you must actually `cat` the full text (or fetch/read it, in the fallback path) — do not rely on the search summary.

## Outputs (mandatory - always do this first)

Return a structured summary of each paper found, including:
- Full citation (authors, title, year, arXiv ID or DOI)
- Key results relevant to the query
- Specific equations or parameter values if applicable

