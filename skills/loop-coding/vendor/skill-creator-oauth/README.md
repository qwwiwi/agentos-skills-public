# skill-creator OAuth shims

Drop-in replacements for Anthropic `skill-creator` v2 scripts that call `anthropic.Anthropic()` (requires `ANTHROPIC_API_KEY`). These wrap `claude -p --output-format json` instead, so they work on Anthropic Max OAuth.

## Files

- `improve_description_oauth.py` — replaces upstream `improve_description.py`
- `run_loop_oauth.py` — replaces upstream `run_loop.py`, imports the shim above

## Install

The scripts must live inside the plugin dir because they import sibling `scripts.*` modules:

```bash
ln -s \
  ~/.claude/skills/loop-coding/vendor/skill-creator-oauth/improve_description_oauth.py \
  $HOME/.claude/skills/skill-creator/scripts/improve_description_oauth.py

ln -s \
  ~/.claude/skills/loop-coding/vendor/skill-creator-oauth/run_loop_oauth.py \
  $HOME/.claude/skills/skill-creator/scripts/run_loop_oauth.py
```

## Run

```bash
SKILL_CREATOR="$HOME/.claude/skills/skill-creator"
SC_PY="$SKILL_CREATOR/.venv/bin/python"

( cd "$SKILL_CREATOR" && "$SC_PY" -m scripts.run_loop_oauth \
    --eval-set "/path/to/trigger-eval.json" \
    --skill-path "/path/to/skill-dir" \
    --eval-model sonnet \
    --improve-model sonnet \
    --max-iterations 5 \
    --holdout 0.4 \
    --verbose )
```

## Caveats

- No explicit extended-thinking budget (SDK-only feature). Default model reasoning is sufficient for description rewrites.
- Shortening retry is single-prompt, not multi-turn (upstream uses conversation). Behavioral drift is small in practice.
- Prompt template is duplicated verbatim from upstream. Re-verify if upstream changes.
- Env is allowlisted (PATH/HOME/USER/SHELL/TERM/LANG/LC_*/TMPDIR) to avoid leaking ambient secrets and to strip Claude Code nesting guards.
