---
name: search-literature
description: "Search for and read physics papers relevant to a query, using the Paperclip MCP server for arXiv full text with a WebSearch/Semantic Scholar fallback"
argument-hint: "<search query>"
allowed-tools: ToolSearch, WebSearch, WebFetch, Bash, mcp__paperclip__*
---
# Search Literature

Search for and thoroughly read physics papers relevant to: **$ARGUMENTS**

## Search Protocol

A `paperclip` MCP server is connected to this project (`claude mcp list` shows it as `paperclip`). It gives direct, structured access to arXiv full text as a virtual filesystem, and should be your primary retrieval path. Its tools are deferred — if they don't already appear as callable tools, run `ToolSearch` with a query like `"paperclip search"` or `"paperclip cat"` to load their schema before calling them. That single load is all the discovery you need — do not follow it with a probing call to see what the tool accepts.

### Paperclip command reference — call these directly, verbatim

There is exactly one tool, `mcp__paperclip__paperclip`, which takes a single string
argument: a command line, in the style of a shell, with one of the verbs below.
There is no `skill`/`help`/`--help` verb — calling it with `skill` (or any bare
discovery command) is not a real usage and will always fail with "Failed to fetch
skill documentation from server." This entire reference is the documentation; do not
spend a call rediscovering it.

- `search -s arxiv "<natural language query>" -n 10` — search the arXiv corpus. Returns
  up to 10 hits (title, authors, arXiv id, DOI, one-line summary) and a session id
  (e.g. `s_ae62663c`) you can reuse with `map` (below).
- `lookup arxiv <ARXIV_ID>` — direct lookup when you already know the id (e.g.
  `lookup arxiv 2602.16067`). Use this instead of `search` whenever an id is known.
- `ls /papers/arx_<id>/` — list what's available for a paper (top-level: `meta.json`,
  `content.lines`, `sections/`).
- `cat /papers/arx_<id>/content.lines` — full text, line-numbered. Add `--full` (i.e.
  `cat --full /papers/arx_<id>/content.lines`) when the plain `cat` result looks
  truncated — full papers can be long, and `--full` is what actually returns the
  complete text (a bare `cat` can come back short).
- `cat /papers/arx_<id>/sections/<Section Name>.lines` — jump straight to one section
  on long papers, e.g. `cat --full "/papers/arx_2602.16067/sections/3. Ladder
  dissipators.lines"` (quote the path when the section name has spaces).
- `grep "<pattern>" /papers/arx_<id>/content.lines` — locate a claim/equation instead
  of reading the whole file. Supports `-i` (case-insensitive), `-C <n>` (context
  lines), and `\|`-alternation for multiple terms in one pass, e.g.
  `grep -i "friger\|commutant\|attractiv" /papers/arx_0710.5385/content.lines -C 2`.
- `map --from <session_id> "<question>"` — ask a question across all results of a
  prior `search` call at once (the session id is printed after every `search`), e.g.
  `map --from s_ae62663c "which of these give an explicit convergence rate?"`.

Follow this priority order strictly for every paper you retrieve:

1. **Search Paperclip's arXiv corpus** with `search` (unknown id) or `lookup` (known id) — see the command reference above.

2. **Read the full text with `cat`** — `/papers/arx_<id>/content.lines` for the whole paper, or `/papers/arx_<id>/sections/<Name>.lines` (e.g. `Methods.lines`, `Results.lines`) to jump straight to a relevant section on long papers; `ls /papers/arx_<id>/` first if you're unsure what sections exist. This replaces fetching `arxiv.org/html` or ar5iv — it returns real full text directly.

3. **Locate specific claims or equations with `grep`** against `/papers/arx_<id>/content.lines` instead of re-reading the whole file.

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

