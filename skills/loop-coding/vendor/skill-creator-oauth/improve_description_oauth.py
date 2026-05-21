#!/usr/bin/env python3
"""OAuth-compatible drop-in replacement for improve_description.py.

Uses `claude -p` subprocess instead of anthropic.Anthropic() SDK, so it works
with an Anthropic Max subscription (no API key required).

Trade-off: loses explicit extended-thinking budget control. Model default
reasoning is sufficient for description-rewrite tasks.
"""

import json
import os
import re
import subprocess
import sys
from pathlib import Path


_ENV_ALLOWLIST = {
    "PATH", "HOME", "USER", "LOGNAME", "SHELL", "TERM",
    "LANG", "LC_ALL", "LC_CTYPE", "TMPDIR",
    # claude itself reads config from $HOME — no extra CLAUDE_* vars needed
}


def _minimal_env() -> dict:
    """Allowlist env for subprocess to avoid leaking secrets or tripping
    Claude Code's nested-session guards (CLAUDECODE, CLAUDECODE_ENTRYPOINT,
    CLAUDE_CODE_SSE_PORT, etc.)."""
    return {k: v for k, v in os.environ.items() if k in _ENV_ALLOWLIST}


def _run_claude(prompt: str, model: str, timeout: int = 180) -> str:
    """Call `claude -p` and return the assistant final text."""
    cmd = ["claude", "-p", "--output-format", "json", "--model", model]
    try:
        proc = subprocess.run(
            cmd,
            input=prompt,
            capture_output=True,
            text=True,
            env=_minimal_env(),
            timeout=timeout,
        )
    except FileNotFoundError as e:
        raise RuntimeError("claude binary not on PATH — check $PATH in allowlist") from e
    except subprocess.TimeoutExpired as e:
        raise RuntimeError(f"claude -p timed out after {timeout}s") from e
    if proc.returncode != 0:
        raise RuntimeError(
            f"claude -p failed (exit {proc.returncode}): {proc.stderr[:500]}"
        )
    try:
        response = json.loads(proc.stdout)
    except json.JSONDecodeError as e:
        raise RuntimeError(f"claude -p returned non-JSON: {proc.stdout[:500]}") from e
    text = response.get("result", "")
    if not text:
        raise RuntimeError(f"claude -p returned empty result: {response}")
    return text


def _build_prompt(
    skill_name: str,
    skill_content: str,
    current_description: str,
    eval_results: dict,
    history: list,
    test_results: dict | None,
) -> str:
    """Build the same prompt upstream improve_description.py uses."""
    failed_triggers = [
        r for r in eval_results["results"]
        if r["should_trigger"] and not r["pass"]
    ]
    false_triggers = [
        r for r in eval_results["results"]
        if not r["should_trigger"] and not r["pass"]
    ]

    train_score = f"{eval_results['summary']['passed']}/{eval_results['summary']['total']}"
    if test_results:
        test_score = f"{test_results['summary']['passed']}/{test_results['summary']['total']}"
        scores_summary = f"Train: {train_score}, Test: {test_score}"
    else:
        scores_summary = f"Train: {train_score}"

    prompt = f"""You are optimizing a skill description for a Claude Code skill called "{skill_name}". A "skill" is sort of like a prompt, but with progressive disclosure -- there is a title and description that Claude sees when deciding whether to use the skill, and then if it does use the skill, it reads the .md file which has lots more details and potentially links to other resources in the skill folder like helper files and scripts and additional documentation or examples.

The description appears in Claude available_skills list. When a user sends a query, Claude decides whether to invoke the skill based solely on the title and on this description. Your goal is to write a description that triggers for relevant queries, and does not trigger for irrelevant ones.

Here is the current description:
<current_description>
"{current_description}"
</current_description>

Current scores ({scores_summary}):
<scores_summary>
"""
    if failed_triggers:
        prompt += "FAILED TO TRIGGER (should have triggered but did not):\n"
        for r in failed_triggers:
            prompt += f'  - "{r["query"]}" (triggered {r["triggers"]}/{r["runs"]} times)\n'
        prompt += "\n"

    if false_triggers:
        prompt += "FALSE TRIGGERS (triggered but should not have):\n"
        for r in false_triggers:
            prompt += f'  - "{r["query"]}" (triggered {r["triggers"]}/{r["runs"]} times)\n'
        prompt += "\n"

    if history:
        prompt += "PREVIOUS ATTEMPTS (do NOT repeat these -- try something structurally different):\n\n"
        for h in history:
            train_s = f"{h.get('train_passed', h.get('passed', 0))}/{h.get('train_total', h.get('total', 0))}"
            test_s = f"{h.get('test_passed', '?')}/{h.get('test_total', '?')}" if h.get("test_passed") is not None else None
            score_str = f"train={train_s}" + (f", test={test_s}" if test_s else "")
            prompt += f'<attempt {score_str}>\n'
            prompt += f'Description: "{h["description"]}"\n'
            if "results" in h:
                prompt += "Train results:\n"
                for r in h["results"]:
                    status = "PASS" if r["pass"] else "FAIL"
                    prompt += f'  [{status}] "{r["query"][:80]}" (triggered {r["triggers"]}/{r["runs"]})\n'
            if h.get("note"):
                prompt += f'Note: {h["note"]}\n'
            prompt += "</attempt>\n\n"

    prompt += f"""</scores_summary>

Skill content (for context on what the skill does):
<skill_content>
{skill_content}
</skill_content>

Based on the failures, write a new and improved description that is more likely to trigger correctly. When I say "based on the failures", it is a bit of a tricky line to walk because we do not want to overfit to the specific cases you are seeing. So what I DO NOT want you to do is produce an ever-expanding list of specific queries that this skill should or should not trigger for. Instead, try to generalize from the failures to broader categories of user intent and situations where this skill would be useful or not useful. The reason for this is twofold:

1. Avoid overfitting
2. The list might get loooong and it is injected into ALL queries and there might be a lot of skills, so we do not want to blow too much space on any given description.

Concretely, your description should not be more than about 100-200 words, even if that comes at the cost of accuracy.

Here are some tips that we have found to work well in writing these descriptions:
- The skill should be phrased in the imperative -- "Use this skill for" rather than "this skill does"
- The skill description should focus on the user intent, what they are trying to achieve, vs. the implementation details of how the skill works.
- The description competes with other skills for Claude attention -- make it distinctive and immediately recognizable.
- If you are getting lots of failures after repeated attempts, change things up. Try different sentence structures or wordings.

I would encourage you to be creative and mix up the style in different iterations since you will have multiple opportunities to try different approaches and we will just grab the highest-scoring one at the end.

Please respond with only the new description text in <new_description> tags, nothing else."""
    return prompt


def improve_description_oauth(
    skill_name: str,
    skill_content: str,
    current_description: str,
    eval_results: dict,
    history: list,
    model: str,
    test_results: dict | None = None,
    log_dir: Path | None = None,
    iteration: int | None = None,
) -> str:
    """Subprocess-based drop-in replacement for improve_description()."""
    prompt = _build_prompt(
        skill_name=skill_name,
        skill_content=skill_content,
        current_description=current_description,
        eval_results=eval_results,
        history=history,
        test_results=test_results,
    )

    text = _run_claude(prompt, model)

    match = re.search(r"<new_description>(.*?)</new_description>", text, re.DOTALL)
    description = match.group(1).strip().strip('"') if match else text.strip().strip('"')

    transcript = {
        "iteration": iteration,
        "prompt": prompt,
        "response": text,
        "parsed_description": description,
        "char_count": len(description),
        "over_limit": len(description) > 1024,
    }

    if len(description) > 1024:
        shorten_prompt = (
            prompt
            + f"\n\n---\nYour previous response was:\n{text}\n\n"
            + f"That description is {len(description)} characters, which exceeds the hard "
            + "1024 character limit. Please rewrite it to be under 1024 characters while "
            + "preserving the most important trigger words and intent coverage. Respond "
            + "with only the new description in <new_description> tags."
        )
        shorten_text = _run_claude(shorten_prompt, model)
        m2 = re.search(r"<new_description>(.*?)</new_description>", shorten_text, re.DOTALL)
        shortened = m2.group(1).strip().strip('"') if m2 else shorten_text.strip().strip('"')

        transcript["rewrite_prompt"] = shorten_prompt
        transcript["rewrite_response"] = shorten_text
        transcript["rewrite_description"] = shortened
        transcript["rewrite_char_count"] = len(shortened)
        description = shortened

    transcript["final_description"] = description

    if log_dir:
        log_dir.mkdir(parents=True, exist_ok=True)
        log_file = log_dir / f"improve_iter_{iteration or 'unknown'}.json"
        log_file.write_text(json.dumps(transcript, indent=2))

    return description


def main():
    import argparse
    parser = argparse.ArgumentParser(description="OAuth-compatible improve_description")
    parser.add_argument("--eval-results", required=True)
    parser.add_argument("--skill-path", required=True)
    parser.add_argument("--history", default=None)
    parser.add_argument("--model", required=True)
    parser.add_argument("--verbose", action="store_true")
    args = parser.parse_args()

    from scripts.utils import parse_skill_md

    skill_path = Path(args.skill_path)
    eval_results = json.loads(Path(args.eval_results).read_text())
    history = json.loads(Path(args.history).read_text()) if args.history else []

    name, _, content = parse_skill_md(skill_path)
    current_description = eval_results["description"]

    if args.verbose:
        print(f"Current: {current_description}", file=sys.stderr)

    new_description = improve_description_oauth(
        skill_name=name,
        skill_content=content,
        current_description=current_description,
        eval_results=eval_results,
        history=history,
        model=args.model,
    )

    if args.verbose:
        print(f"Improved: {new_description}", file=sys.stderr)

    output = {
        "description": new_description,
        "history": history + [{
            "description": current_description,
            "passed": eval_results["summary"]["passed"],
            "failed": eval_results["summary"]["failed"],
            "total": eval_results["summary"]["total"],
            "results": eval_results["results"],
        }],
    }
    print(json.dumps(output, indent=2))


if __name__ == "__main__":
    main()
