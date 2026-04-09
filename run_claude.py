import asyncio
import json
import re
import time
from claude_agent_sdk import query, ClaudeAgentOptions, AssistantMessage, ResultMessage, UserMessage, ToolResultBlock

prompts_dir, tools_dir = "prompts", "tools"
system_prompt = open(f'{prompts_dir}/system_prompt.txt', 'r').read()
make_plan_prompt = open(f'{prompts_dir}/make_plan_prompt.txt', 'r').read()
revise_plan_prompt = open(f'{prompts_dir}/revise_plan_prompt.txt', 'r').read()
gen_tools_prompt = open(f'{prompts_dir}/generate_tools_prompt.txt', 'r').read()
revise_tools_prompt = open(f'{prompts_dir}/revise_tools_prompt.txt', 'r').read()
gen_exec_checkpoints_prompt = open(f'{prompts_dir}/generate_execution_checkpoints_prompt.txt', 'r').read()
execute_phase_prompt = open(f'{prompts_dir}/execute_plan_prompt.txt').read()
interpret_results_prompt = open(f'{prompts_dir}/interpret_results_prompt.txt').read()

full_planning_prompt = f"You are measuring unknown physics in a known experimental system.\n\n{make_plan_prompt}"
full_revise_plan_prompt = f"Read PLAN.md carefully in its entirety. Your task is to critically audit it on three axes and then revise it in-place. Do not summarize — edit PLAN.md directly to fix every problem you identify.\n\n---\n\n{revise_plan_prompt}"
full_gen_tools_prompt = f"{gen_tools_prompt}\n\nSuggested Python modules: numpy, qutip, scipy.\n\nUse `conda activate 3p12` to use the right environment.\n\nAll your tools should go in LabAssistant/tools/."

def log(txt, path='log.txt'):
    with open(path, "a+") as f:
        f.write(txt)

def fmt_tool_call(name, inp):
    """Format a tool invocation line."""
    primary = {
        "Bash": "command", "Read": "file_path", "Edit": "file_path",
        "Write": "file_path", "Glob": "pattern", "Grep": "pattern",
        "WebSearch": "query", "WebFetch": "url",
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


def log_paper_fetch(url: str, content, log_path='literature_search_log.jsonl'):
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
        'url': url,
        'arxiv_id': arxiv_id,
        'method': method,
        'full_text': full_text,
        'content_length': content_length,
    }
    with open(log_path, 'a') as f:
        f.write(json.dumps(record) + '\n')


async def start_agent(user_prompt):
    tool_names: dict[str, str] = {}       # tool_use_id -> tool name
    webfetch_urls: dict[str, str] = {}    # tool_use_id -> URL
    subagent_names: dict[str, str] = {}   # parent_tool_use_id -> subagent label

    log("\n\n-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-\n\n")
    start_time = time.monotonic()

    async for message in query(
        prompt=user_prompt,
        options=ClaudeAgentOptions(
            model='claude-sonnet-4-6',
            system_prompt=system_prompt,
            setting_sources=["user", "project"],
            allowed_tools=["Agent", "Skill", "Read", "Edit", "Bash", "Glob", "Grep", "WebSearch", "WebFetch"],
            permission_mode="acceptEdits",
        ),
    ):
        if isinstance(message, AssistantMessage):
            is_subagent = message.parent_tool_use_id is not None
            prefix = f"  [sub:{subagent_names.get(message.parent_tool_use_id, message.parent_tool_use_id[:8])}] " if is_subagent else ""
            for block in message.content:
                if hasattr(block, "text") and block.text:
                    log(prefix + ">> " + block.text.replace("\n", "\n   "))
                elif hasattr(block, "name"):
                    tool_names[block.id] = block.name
                    if block.name == "WebFetch":
                        webfetch_urls[block.id] = block.input.get("url", "")
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
                            log_paper_fetch(url, block.content)
                        result = fmt_tool_result(name, block.content, block.is_error)
                        if result:
                            log(result)

        elif isinstance(message, ResultMessage):
            elapsed = time.monotonic() - start_time
            cost = f"  ${message.total_cost_usd:.4f}" if message.total_cost_usd else ""
            log(f"\nDone ({message.subtype}){cost}  [{elapsed:.1f}s]")


print("starting...")
asyncio.run(start_agent(full_planning_prompt))
# asyncio.run(start_agent(full_revise_plan_prompt))
# asyncio.run(start_agent(full_gen_tools_prompt))
# asyncio.run(start_agent(revise_tools_prompt))
# asyncio.run(start_agent(gen_exec_checkpoints_prompt))
# asyncio.run(start_agent(execute_phase_prompt))
# asyncio.run(start_agent(interpret_results_prompt))

