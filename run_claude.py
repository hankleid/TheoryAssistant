import asyncio
import json
import re
import time
import shutil
from claude_agent_sdk import query, ClaudeAgentOptions, AssistantMessage, ResultMessage, UserMessage, ToolResultBlock

prompts_dir, tools_dir = "prompts", "tools"
system_prompt = open(f'{prompts_dir}/system_prompt.txt', 'r').read()
make_explore_plan_prompt = open(f'{prompts_dir}/make_explore_plan_prompt.txt', 'r').read()
make_full_plan_prompt = open(f'{prompts_dir}/make_full_plan_prompt.txt', 'r').read()
revise_plan_prompt = open(f'{prompts_dir}/revise_plan_prompt.txt', 'r').read()
execute_theory_prompt = open(f'{prompts_dir}/execute_theory_prompt.txt', 'r').read()
execute_explore_addendum = open(f'{prompts_dir}/execute_explore_addendum.txt', 'r').read()
write_final_theory_prompt = open(f'{prompts_dir}/write_final_theory_prompt.txt', 'r').read()
followup_plan_prompt = open(f'{prompts_dir}/followup_plan_prompt.txt', 'r').read()

full_revise_plan_prompt = f"Read MAIN_PLAN.md carefully in its entirety. Your task is to critically audit it on three axes and then revise it in-place. Do not summarize — edit MAIN_PLAN.md directly to fix every problem you identify.\n\n---\n\n{revise_plan_prompt}"
execute_explore_prompt = f"First read EXPLORE_PLAN.md in its entirety. This is the blueprint for the following analysis. You must operate in `init_exploration/`.  {execute_theory_prompt}\n\n---\n\n{execute_explore_addendum}"
execute_main_plan_prompt = f"First read MAIN_PLAN.md in its entirety. This is the blueprint for the following analysis. You must operate in `main_derivation/` {execute_theory_prompt}"
execute_followup_plan_prompt = f"First read FOLLOWUP_PLAN.md in its entirety. This is the blueprint for the following analysis. You must operate in `followup_derivation/` {execute_theory_prompt}"

write_final_main_theory_preamble = "First invoke the `problem-spec` skill and read its contents carefully. Then read MAIN_PLAN.md in full, every file in `main_derivation/notes/` in sequence, `main_derivation/summary.md`, and the contents of `main_derivation/data/` and `tools/` that those notes reference. This is the entire record of the derivation you are about to write up."
write_final_followup_theory_preamble = "First invoke the `problem-spec` skill and read its contents carefully. Then read, in order: MAIN_PLAN.md, every file in `main_derivation/notes/`, `main_derivation/summary.md`, and `main_derivation/data/`; then FOLLOWUP_PLAN.md, every file in `followup_derivation/notes/`, `followup_derivation/summary.md`, and `followup_derivation/data/`; and the contents of `tools/` that any of those notes reference. Together these are the entire record of the investigation — main derivation plus followup — that you are about to write up as one single integrated document. Your goal is to write a self-contained, cohesive theory writeup, based on the work you did, for the problem at hand."
write_final_main_theory_prompt = write_final_main_theory_preamble + "\n\n" + write_final_theory_prompt.format(DIR="main_derivation")
write_final_followup_theory_prompt = write_final_followup_theory_preamble + "\n\n" + write_final_theory_prompt.format(DIR="followup_derivation")



# LOGGING TOOLS

def log(txt, path='log.txt'):
    with open(path, "a+") as f:
        f.write(txt)


# COST MONITORING
# Per-million-token USD pricing (cache write = 1.25x input for 5m TTL, 2x for 1h TTL;
# cache read = 0.1x input). Unrecognized models fall back to the claude-opus-5 row.
PRICING = {
    "claude-opus-5":    {"input": 5.00, "output": 25.00, "cache_write_5m": 6.25,  "cache_write_1h": 10.00, "cache_read": 0.50},
    "claude-sonnet-5":  {"input": 3.00, "output": 15.00, "cache_write_5m": 3.75,  "cache_write_1h": 6.00,  "cache_read": 0.30},
    "claude-haiku-4-5": {"input": 1.00, "output": 5.00,  "cache_write_5m": 1.25,  "cache_write_1h": 2.00,  "cache_read": 0.10},
}
COST_WARNING_INCREMENT_USD = 20.0
_cost_state = {"total": 0.0, "next_threshold": COST_WARNING_INCREMENT_USD}

def compute_turn_cost(model, usage):
    """Estimate the USD cost of one assistant turn from its raw API usage dict."""
    if not usage:
        return 0.0
    pricing = PRICING.get(model, PRICING["claude-opus-5"])

    cache_creation = usage.get("cache_creation")
    if cache_creation:
        write_5m = cache_creation.get("ephemeral_5m_input_tokens", 0) or 0
        write_1h = cache_creation.get("ephemeral_1h_input_tokens", 0) or 0
    else:
        write_5m = usage.get("cache_creation_input_tokens", 0) or 0
        write_1h = 0

    return (
        (usage.get("input_tokens", 0) or 0) * pricing["input"]
        + (usage.get("output_tokens", 0) or 0) * pricing["output"]
        + (usage.get("cache_read_input_tokens", 0) or 0) * pricing["cache_read"]
        + write_5m * pricing["cache_write_5m"]
        + write_1h * pricing["cache_write_1h"]
    ) / 1_000_000

def track_cost(model, usage):
    """Accumulate session cost and warn every time it crosses a $20 increment."""
    _cost_state["total"] += compute_turn_cost(model, usage)
    while _cost_state["total"] >= _cost_state["next_threshold"]:
        warning = f"\n\n*** COST WARNING: session spend has reached ${_cost_state['next_threshold']:.2f} (running total ${_cost_state['total']:.2f}) ***\n"
        log(warning)
        print(warning)
        _cost_state["next_threshold"] += COST_WARNING_INCREMENT_USD

def fmt_tool_call(name, inp):
    """Format a tool invocation line."""
    primary = {
        "Bash": "command", "Read": "file_path", "Edit": "file_path",
        "Write": "file_path", "Glob": "pattern", "Grep": "pattern",
        "WebSearch": "query", "WebFetch": "url",
        "mcp__paperclip__paperclip": "command",
    }
    if name == "Skill":
        skill_name = inp.get("skill", "")
        args = inp.get("args", "")
        return f"  [Skill] {skill_name}" + (f' "{args}"' if args else "")
    if name == "Agent":
        desc = inp.get("description", inp.get("prompt", "")[:80])
        return f"  [Agent] {desc}"
    key = primary.get(name)
    value = inp.get(key, "") if key else ""
    return f"  [{name}] {value}" if value else f"  [{name}] {inp}"

def to_text(content):
    """Normalise tool result content to a plain string."""
    if content is None:
        return ""
    if isinstance(content, list):
        text = "\n".join(
            item.get("text", str(item)) if isinstance(item, dict) else str(item)
            for item in content
        )
    else:
        text = str(content)
    # Strip injected system instructions from tool results
    lines = [l for l in text.splitlines() if not l.strip().startswith("REMINDER:")]
    return "\n".join(lines)

def fmt_tool_result(name, content, is_error):
    """Format a tool result block."""
    prefix = "  !!" if is_error else "  ->"
    text = to_text(content)

    if not text.strip():
        return f"{prefix} (empty)"

    if name == "WebSearch":
        return fmt_websearch_result(prefix, text)

    if name in ("Read", "Skill"):
        return ""

    indented = "\n".join(f"       {l}" for l in text.splitlines())
    return f"{prefix} [{name}]:\n{indented}"

def fmt_websearch_result(prefix, text):
    """Parse and pretty-print web search results."""
    results = []

    # 1. Try JSON array (most common format from the tool)
    try:
        data = json.loads(text)
        if isinstance(data, list):
            for item in data:
                title   = item.get("title", "").strip()
                url     = item.get("url", item.get("link", "")).strip()
                snippet = item.get("snippet", item.get("description", "")).strip()
                if url:
                    results.append((title, url, snippet))
    except (json.JSONDecodeError, AttributeError):
        pass

    # 2. Markdown links: [Title](URL)
    if not results:
        for title, url in re.findall(r'\[([^\]]+)\]\((https?://[^)]+)\)', text):
            results.append((title.strip(), url.strip(), ""))

    # 3. Numbered blocks with a URL line
    if not results:
        for block in re.split(r'\n(?=\d+[\.\)])', text.strip()):
            url_match = re.search(r'https?://[^\s"\'}>]+', block)
            if not url_match:
                continue
            url = url_match.group(0).rstrip('.,)')
            first_line = re.sub(r'^\d+[\.\)]\s*', '', block.splitlines()[0]).strip()
            snippet_lines = [
                l.strip() for l in block.splitlines()[1:]
                if l.strip() and url not in l
            ]
            results.append((first_line, url, " ".join(snippet_lines)))

    if results:
        lines = [f"{prefix} {len(results)} result(s):"]
        for i, (title, url, snippet) in enumerate(results, 1):
            lines.append(f"       {i}. {title}")
            lines.append(f"          {url}")
            if snippet:
                lines.append(f"          {snippet}")
        return "\n".join(lines)

    # Fallback: plain indented text
    indented = "\n".join(f"       {l}" for l in text.splitlines())
    return f"{prefix} search result:\n{indented}"


def log_paper_fetch(url: str, content, step: str = None, log_path='literature_search_log.jsonl'):
    """Append one record to paper_fetch_log.jsonl if url looks like a paper."""
    import datetime, re as _re
    PAPER_PATTERNS = [
        'arxiv.org/', 'ar5iv.labs.arxiv.org/', 'semanticscholar.org/',
        'doi.org/', 'plos', 'pubmed',
    ]
    if not any(p in url for p in PAPER_PATTERNS):
        return

    if 'ar5iv.labs.arxiv.org/html/' in url:
        method, full_text = 'ar5iv', True
    elif 'arxiv.org/html/' in url:
        method, full_text = 'html', True
    elif 'arxiv.org/abs/' in url:
        method, full_text = 'abs', False
    elif 'semanticscholar.org' in url:
        method, full_text = 'semantic_scholar', None
    else:
        method, full_text = 'doi', None

    content_str = to_text(content)
    content_length = len(content_str)
    if full_text is None:
        full_text = content_length > 5000

    m = _re.search(r'(\d{4}\.\d{4,5})', url)
    arxiv_id = m.group(1) if m else None

    record = {
        'timestamp': datetime.datetime.now(datetime.timezone.utc).isoformat(),
        'step': step,
        'url': url,
        'arxiv_id': arxiv_id,
        'method': method,
        'full_text': full_text,
        'content_length': content_length,
    }
    with open(log_path, 'a') as f:
        f.write(json.dumps(record) + '\n')


PAPERCLIP_DOC_ID_RE = r'\b(PMC\d+|bio_[A-Za-z0-9]+|med_[A-Za-z0-9]+|arx_[A-Za-z0-9]+|fda_[A-Za-z0-9]+|tri_[A-Za-z0-9]+|NCT\d+)\b'
PAPERCLIP_READ_SUBCOMMANDS = {'cat', 'head', 'tail', 'scan', 'grep', 'ask-image', 'map', 'reduce'}
PAPERCLIP_FULL_TEXT_SUBCOMMANDS = {'cat', 'map', 'reduce'}


def log_paperclip_fetch(command: str, content, step: str = None, log_path='literature_search_log.jsonl'):
    """Append one record to log_path for paperclip commands that read paper content."""
    import datetime, re as _re

    parts = command.strip().split(None, 1)
    subcommand = parts[0] if parts else ''
    if subcommand not in PAPERCLIP_READ_SUBCOMMANDS:
        return

    m = _re.search(PAPERCLIP_DOC_ID_RE, command)
    doc_id = m.group(1) if m else None

    # grep/scan/head/tail without a specific doc id are corpus-wide searches, not fetches
    if doc_id is None and subcommand not in ('map', 'reduce'):
        return

    content_str = to_text(content)
    content_length = len(content_str)

    if subcommand == 'ask-image':
        full_text = False
    elif subcommand in PAPERCLIP_FULL_TEXT_SUBCOMMANDS:
        full_text = True
    else:
        full_text = content_length > 5000

    record = {
        'timestamp': datetime.datetime.now(datetime.timezone.utc).isoformat(),
        'step': step,
        'source': 'paperclip',
        'command': command,
        'method': subcommand,
        'doc_id': doc_id,
        'full_text': full_text,
        'content_length': content_length,
    }
    with open(log_path, 'a') as f:
        f.write(json.dumps(record) + '\n')


async def start_agent(user_prompt, model='claude-sonnet-5', step=None):
    tool_names: dict[str, str] = {}       # tool_use_id -> tool name
    webfetch_urls: dict[str, str] = {}    # tool_use_id -> URL
    paperclip_commands: dict[str, str] = {}  # tool_use_id -> paperclip command
    subagent_names: dict[str, str] = {}   # parent_tool_use_id -> subagent label

    log("\n\n-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-\n\n")
    start_time = time.monotonic()

    async for message in query(
        prompt=user_prompt,
        options=ClaudeAgentOptions(
            model=model,
            # claude-agent-sdk bundles its own (x86_64) CLI build, which runs
            # under Rosetta on Apple Silicon and lacks AVX -> crashes during
            # the initialize handshake. Force the native system CLI instead.
            cli_path=shutil.which("claude"),
            system_prompt=system_prompt,
            setting_sources=["user", "project"],
            allowed_tools=["Agent", "Skill", "Read", "Edit", "Bash", "Glob", "Grep", "WebSearch", "WebFetch", "mcp__paperclip__paperclip"],
            mcp_servers={"paperclip": {"type": "http", "url": "https://paperclip.gxl.ai/mcp"}},
            permission_mode="acceptEdits",
        ),
    ):
        if isinstance(message, AssistantMessage):
            track_cost(message.model, message.usage)
            is_subagent = message.parent_tool_use_id is not None
            prefix = f"  [sub:{subagent_names.get(message.parent_tool_use_id, message.parent_tool_use_id[:8])}] " if is_subagent else ""
            for block in message.content:
                if hasattr(block, "text") and block.text:
                    log(prefix + ">> " + block.text.replace("\n", "\n   "))
                elif hasattr(block, "name"):
                    tool_names[block.id] = block.name
                    if block.name == "WebFetch":
                        webfetch_urls[block.id] = block.input.get("url", "")
                    if block.name == "mcp__paperclip__paperclip":
                        paperclip_commands[block.id] = block.input.get("command", "")
                    if block.name == "Agent":
                        label = block.input.get("description", block.input.get("prompt", "")[:40])
                        subagent_names[block.id] = label
                    log(prefix + fmt_tool_call(block.name, block.input))

        elif isinstance(message, UserMessage):
            if isinstance(message.content, list):
                for block in message.content:
                    if isinstance(block, ToolResultBlock):
                        name = tool_names.get(block.tool_use_id, "Tool")
                        if name == "WebFetch" and not block.is_error:
                            url = webfetch_urls.get(block.tool_use_id, "")
                            log_paper_fetch(url, block.content, step=step)
                        elif name == "mcp__paperclip__paperclip" and not block.is_error:
                            command = paperclip_commands.get(block.tool_use_id, "")
                            log_paperclip_fetch(command, block.content, step=step)
                        result = fmt_tool_result(name, block.content, block.is_error)
                        if result:
                            log(result)

        elif isinstance(message, ResultMessage):
            elapsed = time.monotonic() - start_time
            cost = f"  ${message.total_cost_usd:.4f}" if message.total_cost_usd else ""
            log(f"\nDone ({message.subtype}){cost}  [{elapsed:.1f}s]")


if __name__ == '__main__':
    print("starting...")
    # asyncio.run(start_agent(make_explore_plan_prompt, model='claude-sonnet-5', step='make_explore_plan'))
    # asyncio.run(start_agent(execute_explore_prompt, model='claude-sonnet-5', step='execute_explore_plan'))

    # asyncio.run(start_agent(make_full_plan_prompt, step='make_main_plan'))
    # asyncio.run(start_agent(full_revise_plan_prompt, step='revise_main_plan'))
    # asyncio.run(start_agent(execute_main_plan_prompt, step='execute_main_plan'))
    # asyncio.run(start_agent(write_final_main_theory_prompt, step='write_final_theory_main'))

    # asyncio.run(start_agent(followup_plan_prompt, step='followup_plan'))
    # asyncio.run(start_agent(execute_followup_plan_prompt, step='execute_followup_plan'))
    asyncio.run(start_agent(write_final_followup_theory_prompt, step='write_final_theory_followup'))

