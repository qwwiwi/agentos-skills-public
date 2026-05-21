# Sub-skill Auto-generation

After Phase 2 (Audit), gaps may warrant a helper skill on the fly. We lean on the global `skill-creator` at `~/.claude/skills/skill-creator/` for the heavy lifting, with a strict non-interactive brief and a venv-pinned toolchain.

## Triggers

Generate a sub-skill only if ALL:
- Task will repeat 3+ times in this pipeline (or likely in future pipelines)
- No existing skill solves it (scouted internal + external)
- No public GitHub repo with >= 2000 stars solves it directly
- Formalizable in under 100 LOC of shell/python
- Deterministic (same input -> same output)

If any condition fails -> do NOT create a sub-skill. Write a one-off script or delegate to an AI call.

## Location

```
skills/loop-coding/sub-skills/{{slug}}/
├── SKILL.md
├── scripts/
│   └── main.sh (or main.py)
└── references/ (optional, only for docs over 300 lines)
```

Sub-skills are per-pipeline-invocation but persisted in the skill dir. Promotion to standalone skill happens during post-run review.

## Path conventions (HARD RULE)

The skill-creator v2 python scripts use package-relative imports (`-m scripts.X`), which require `cwd=$SKILL_CREATOR`. Meanwhile the sub-skill we are generating lives under loop-coding. Mixing these breaks everything.

Always use absolute paths in both shell variables and arguments:

```bash
SKILL_CREATOR="$HOME/.claude/skills/skill-creator"
SC_PY="$SKILL_CREATOR/.venv/bin/python"
SUB_SKILL="~/.claude/skills/loop-coding/sub-skills/{{slug}}"
```

- `quick_validate.py` and `package_skill.py` have `__main__` blocks — invoke directly by file path (no cwd constraint):
  ```bash
  "$SC_PY" "$SKILL_CREATOR/scripts/quick_validate.py" "$SUB_SKILL"
  ```
- `run_eval.py` and `run_loop.py` import sibling `scripts.*` modules — must be invoked with `cwd=$SKILL_CREATOR`:
  ```bash
  ( cd "$SKILL_CREATOR" && "$SC_PY" -m scripts.run_eval --skill-path "$SUB_SKILL" ... )
  ```

## Creation flow

1. **Detect the gap.** `scripts/detect-skill-gaps.sh` is currently a thin grep — it extracts bullet lines from the "Missing tools" section of AUDIT.md and prints them to stdout. It does NOT score, filter, or emit JSON. Treat its output as a candidate list for manual triage by the orchestrator, not a scored plan. If candidate gating becomes a bottleneck, upgrade the script; for now, the orchestrator applies the ALL-conditions gate above by hand.

2. **Invoke skill-creator in non-interactive Create mode.** Spawn an Opus subagent with a brief that pre-answers every interview question upstream `skill-creator` would ask, so the subagent does not stall waiting for a human:

   ```
   You are creating a sub-skill for the loop-coding pipeline. Use the skill at
   ~/.claude/skills/skill-creator/ but SKIP the "Interview and Research" phase —
   all intent is pre-answered below. Proceed directly to "Write the SKILL.md".
   Do NOT ask interview questions unless a required field is blank.

   Skill name:          {{SLUG}}
   What it enables:     {{DESCRIPTION}}
   Trigger context:     invoked internally by loop-coding phases {{PHASES}}.
                        Will not appear in Claude's available_skills list (it
                        is invoked by path), so keep description terse and
                        factual. Do not apply the "pushy description"
                        advice — it is meant for user-facing skills only.
   Expected output:     {{OUTPUT_FORMAT}}
   Input format:        {{INPUT_FORMAT}}
   Success criteria:    {{ACCEPTANCE}}   (e.g. "given X produces Y matching Z")
   Test cases needed:   {{YES_IF_OBJECTIVELY_VERIFIABLE}}
   Dependencies:        {{DEPS}}         (python3.12 / bash / jq / gh / none)
   Edge cases:          {{EDGE_CASES}}
   Budget:              under 100 LOC (shell or python)
   Target location:     /absolute/path/to/loop-coding/sub-skills/{{SLUG}}/

   HARD constraints on the description field:
   - MUST NOT contain angle brackets -- use "under N" / "over N" phrasing
     (skill-creator's quick_validate rejects angle brackets)

   After writing SKILL.md + scripts/, run quick_validate and fix any issues:
     $HOME/.claude/skills/skill-creator/.venv/bin/python \
       $HOME/.claude/skills/skill-creator/scripts/quick_validate.py \
       /absolute/path/to/sub-skills/{{SLUG}}

   Return: absolute path to the new sub-skill + validation result only.
   ```

3. **Validate.** Orchestrator runs quick_validate (absolute paths):

   ```bash
   "$SC_PY" "$SKILL_CREATOR/scripts/quick_validate.py" "$SUB_SKILL"
   ```

   Exits non-zero on: missing frontmatter, bad name, description with angle brackets, compatibility field over 600 chars. Note: quick_validate does NOT check SKILL.md body length — that is a soft guideline from upstream ("under 500 lines ideal"), enforced by review, not by the validator.

4. **Security scan.** Same scanner used for rented external skills:

   ```bash
   bash "~/.claude/skills/loop-coding/scripts/skill-security-scan.sh" "$SUB_SKILL"
   ```

   Verdict must be `safe`.

5. **Register.** Append entry to RESEARCH.md under "Generated sub-skills" -- slug, phases used, LOC, verdict.

## Optional: trigger eval before committing

Use this when a sub-skill will be consulted via Claude's available_skills (not purely path-invoked) and triggering accuracy matters. `run_eval.py` is trigger-only — it measures how often Claude picks the skill for 20 eval queries. It does NOT grade output quality.

Prereqs: author `$SUB_SKILL/evals/trigger-eval.json` with 10-12 should-trigger and 8-10 near-miss queries. Format:

```json
[{"query": "...", "should_trigger": true}, ...]
```

Run (note the `cd $SKILL_CREATOR` wrapper — `-m scripts.run_eval` needs it):

```bash
( cd "$SKILL_CREATOR" && "$SC_PY" -m scripts.run_eval \
    --eval-set "$SUB_SKILL/evals/trigger-eval.json" \
    --skill-path "$SUB_SKILL" \
    --model claude-opus-4-7 \
    --runs-per-query 3 \
    --verbose )
```

Each call spawns `claude -p` as subprocess — uses Max OAuth, no API key needed. 20 queries × 3 runs takes roughly 15–25 min.

For trivial sub-skills (single deterministic script) or sub-skills invoked only by absolute path from loop-coding scripts: skip this — quick_validate + security scan is sufficient.

## Description optimization (OAuth-compatible)

The skill-creator `run_loop.py` runs a 5-iteration optimization: eval -> propose revised description via Anthropic SDK -> re-eval -> pick best on held-out test split.

**OAuth shims live next to the upstream scripts.** Upstream `run_loop.py` + `improve_description.py` instantiate `anthropic.Anthropic()` (requires `ANTHROPIC_API_KEY`). This workspace runs on Max OAuth, so use the drop-in replacements:

- `~/.claude/skills/skill-creator/scripts/run_loop_oauth.py`
- `~/.claude/skills/skill-creator/scripts/improve_description_oauth.py`

Both shell out to `claude -p --output-format json` instead of the SDK. Trade-off: no explicit extended-thinking budget control; default reasoning is sufficient for description rewrites. Split model args: `--eval-model` (trigger eval) and `--improve-model` (rewrite). Default to `sonnet` on both to preserve Opus quota.

Invocation (package-relative imports require `cwd=$SKILL_CREATOR`):

```bash
( cd "$SKILL_CREATOR" && "$SC_PY" -m scripts.run_loop_oauth \
    --eval-set "$SUB_SKILL/evals/trigger-eval.json" \
    --skill-path "$SUB_SKILL" \
    --eval-model sonnet --improve-model sonnet \
    --max-iterations 5 --holdout 0.4 --verbose )
```

Options when description tuning is actually needed:
1. **Skip.** For internal path-invoked sub-skills, triggering accuracy is moot — sub-skill is never in available_skills.
2. **Run the OAuth shim.** Command above. Plan for ~15-25 min per iteration at N=3.
3. **Manual loop.** Run `run_eval` standalone, read failures, hand-edit description, re-run. Faster than the full loop for 2-3 iterations.

When skipping, note in RESEARCH.md: "description not optimized — sub-skill is path-invoked".

**Caveat: trigger-eval measures recognizability, not behavior.** The eval writes a unique slash command to `.claude/commands/` and measures whether Claude picks it as the first tool. This is the right signal for **recognizable content skills** (narrow keyword domains: "convert pdf", "analyze csv"). It is the wrong signal for **rule-enforced implementation skills** whose trigger mechanism is a hard rule in `core/rules.md` — those compete with EnterPlanMode/Agent/Bash on complex queries regardless of how the description is phrased. Measured on loop-coding itself (20 queries, N=3): a baseline description and a hand-crafted anti-plan-mode candidate both scored 0% recall, 100% precision. Do not waste loops tuning a description for a skill triggered by rule rather than by available_skills match.

## Post-run triage

After Phase 7, for each generated sub-skill:
- Used successfully 3+ times across runs -> promote to `skills/` (standalone), keep SKILL.md as-is
- Used 1-2 times -> keep in `sub-skills/` (may be needed again)
- Used 0 times -> delete

## Guardrails

- Sub-skills inherit parent loop-coding rules -- no additional perms.
- No sub-skill may require new secrets.
- Sub-skill code MUST pass `scripts/skill-security-scan.sh` before first use.
- No recursion: sub-skills cannot generate sub-sub-skills.
- Description MUST NOT contain angle brackets (quick_validate enforces).
- SKILL.md body under 500 lines (upstream guideline, not validator-enforced) — split via references/ if longer.
