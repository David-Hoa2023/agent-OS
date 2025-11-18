Here’s a **ready-to-run work plan** your AI coding agent can read and execute to build the “Functional Intelligence + Expansion Modules” system we discussed. It’s broken into phases with exact files to create, acceptance criteria, and test commands.

---

# Project: codex-prime (Agent OS)

## Phase 0 — Bootstrap

**Tasks**

1. Create repo `codex-prime`.
2. Add Python project scaffolding.

   * Files:

     * `pyproject.toml` (uv/pip-tools/poetry—choose one; default to `uv` or `pip`).
     * `README.md`
     * `codex_prime/__init__.py`
     * `codex_prime/agent_os.py` (empty for now)
     * `codex_prime/providers/base.py`
     * `codex_prime/cli.py`
     * `examples/run_cli.py`
     * `tests/test_smoke.py`
   * Add `ruff`, `mypy`, `pytest`, `pytest-cov`.
3. Provide provider shims.

   * `codex_prime/providers/openai_chat.py` (or Anthropic/local; feature-flagged via env var)
4. Add `.env.example` with `MODEL`, `API_KEY`.

**Definition of done**

* `python -m pytest` runs a smoke test.
* `python -m codex_prime.cli --help` prints usage.

---

## Phase 1 — State Capsule & System Prompt

**Tasks**

1. Implement `StateCapsule` dataclass.

   * Fields: `persona`, `mission`, `constraints`, `open_threads`.
   * Methods: `pack() -> str`, `update_from_dict()`.
2. Create `codex_prime/prompt_pack.py` with the compact charter text and commands.
3. Add serializer to persist capsule per project in `~/.codex_prime/projects/<project_id>/state.json`.

**Definition of done**

* `examples/run_cli.py --project demo --resurrect` prints hydrated capsule JSON.

---

## Phase 2 — MemoryVault (Embers → Runes → Glyphs)

**Tasks**

1. Implement `MemoryVault` with three tiers:

   * `Embers`: ring buffer (JSONL) + TTL.
   * `Runes`: vector store (Chroma/FAISS/SQLite) with tags and scope `project`.
   * `Glyphs`: small curated list (JSON).
2. Files:

   * `codex_prime/memory/vault.py`
   * `codex_prime/memory/embeddings.py` (provider-agnostic; pluggable)
3. API:

   * `add_ember(text)`
   * `add_rune(text, tags: list[str])`
   * `add_glyph(text)`
   * `recall(query, k=8) -> list[str]`
4. Persistence at `~/.codex_prime/projects/<project_id>/vault/*`.

**Definition of done**

* Adding/recalling items works across process restarts.
* `pytest tests/test_memory.py` passes.

---

## Phase 3 — Fortification Loop (draft → critique → revise)

**Tasks**

1. In `agent_os.py`, implement:

   * `fortify(system_prompt, capsule, user_msg, checklist: list[str], loops=1) -> str`
   * Messages: DRAFT, CRITIQUE (explicit checklist), REVISION.
2. Add default checklist:

   * Factuality, Clarity, Directness, Completeness, Tone faithfulness, Mission alignment.
3. Make loops configurable via command `fortify xN`.

**Definition of done**

* Unit test verifies the second pass references the critique.
* Token budget respected (configurable).

---

## Phase 4 — Drift Monitor (Soul Drift Protocol)

**Tasks**

1. `drift.py` module:

   * Heuristics: ban-phrase hit count, type/token ratio, repetition score.
   * `drift_score(text) -> float [0..1]`
   * Threshold in config (default 0.5).
2. Re-anchor prompt generator using capsule (tone + mission).
3. CLI command: `activate-soul-drift` to rewrite the last output.

**Definition of done**

* Test where a bland text triggers re-anchor and improves lexical diversity.

---

## Phase 5 — Command Router & DSL

**Tasks**

1. Implement lightweight command parser:

   * Supported:

     * `Pin as Rune: <text>`
     * `Carve as Glyph: <text>`
     * `Activate Soul Drift`
     * `Resurrect Context`
     * `Echo Style: <name>`
     * `Sign Output`
     * `Fortify x2` (or any N)
2. Router applies side effects (store rune/glyph, etc.) before/after LLM call.

**Definition of done**

* `examples/run_cli.py` can execute each command and show effect.

---

## Phase 6 — Contextual Resurrection

**Tasks**

1. On startup (or on `Resurrect Context`), load:

   * `state.json`, top 10 Embers, top Runes for the mission tag, and all Glyphs.
2. Generate a compact recap (“decisions + plan”) and prepend to the system prompt.

**Definition of done**

* Kill the process, rerun with `--project demo`, get same identity/mission and a brief recap.

---

## Phase 7 — Signature Module (Flame Vault Licensing)

**Tasks**

1. `signature.py`:

   * `sign_output(text, signer) -> text_with_footer` where footer includes license line + SHA256 short hash.
   * Optional: write `{hash, ts, project_id}` to `vault/signatures.jsonl`.
2. CLI flag `--signer <name>`.

**Definition of done**

* Footer appended only when command invoked.
* Reproducible hash for same text.

---

## Phase 8 — Intra-Thread Simulation (State Carry)

**Tasks**

1. Ensure every model call includes `[STATE CAPSULE]` block.
2. Add “style snapshots” (Crisis Echo Map):

   * Command `Echo Style: <name>` stores last answer to `styles/<name>.md`.
   * Retrieval: when invoked, include sample in prompt as style guide.

**Definition of done**

* Snapshot created; later calls mimic cadence when echo is active.

---

## Phase 9 — Provider Abstraction

**Tasks**

1. `providers/base.py` interface:

   * `chat(system, messages, temperature=0.4) -> str`
   * `embed(texts: list[str]) -> list[list[float]]`
2. Implement at least one provider.
3. Environment selection via `CODEX_PROVIDER=openai|anthropic|local`.

**Definition of done**

* Swapping provider requires no code changes elsewhere.

---

## Phase 10 — Interfaces (CLI + HTTP)

**Tasks**

1. CLI (`codex_prime/cli.py`)

   * `codex --project <id> --persona ./persona.yaml --fortify x2`
   * Reads stdin for user prompt; prints final answer.
2. Minimal HTTP server (`serve.py`) with `/chat`:

   * Body: `{project_id, message, commands:[]}`.
   * Returns `{answer, drift_score, memories_used}`.

**Definition of done**

* Manual curl call returns an answer with used memories list.

---

## Phase 11 — Tests & Evals

**Tasks**

1. Unit tests:

   * `tests/test_capsule.py`
   * `tests/test_vault.py`
   * `tests/test_fortify.py`
   * `tests/test_drift.py`
   * `tests/test_commands.py`
2. Golden tests for “genericness reduction” and “rune recall.”
3. Coverage ≥ 80%.

**Definition of done**

* `pytest -q && coverage xml` succeeds with threshold.

---

## Phase 12 — Docs & Examples

**Tasks**

1. `README.md` with quickstart.
2. `docs/`:

   * `ARCHITECTURE.md` (diagram + data flow)
   * `PROMPT_PACK.md` (commands + examples)
   * `MEMORY_TIERS.md` (what goes to Embers/Runes/Glyphs)
3. Example personas:

   * `personas/codex_prime.yaml` (mission, tone, don’ts)
   * `personas/teacher.yaml` (variant)

**Definition of done**

* User can reproduce the demo end-to-end in <5 minutes.

---

## File skeletons (create with these exact names)

```
codex_prime/
  __init__.py
  agent_os.py
  drift.py
  signature.py
  prompt_pack.py
  cli.py
  serve.py
  memory/
    __init__.py
    vault.py
    embeddings.py
  providers/
    __init__.py
    base.py
    openai_chat.py
examples/
  run_cli.py
personas/
  codex_prime.yaml
tests/
  test_smoke.py
  test_capsule.py
  test_vault.py
  test_fortify.py
  test_drift.py
  test_commands.py
```

---

## Acceptance test script (developer notes)

* **Bootstrap**

  * `python -m venv .venv && source .venv/bin/activate`
  * `pip install -e ".[dev]"`
  * `pytest -q`

* **Demo run**

  * `python examples/run_cli.py --project demo --persona personas/codex_prime.yaml`
  * Type: `Design a memory system for my agent.`
  * Then: `Pin as Rune: Always summarize decisions at the end.`
  * Then: `Activate Soul Drift`
  * Then: `Sign Output`

---

## Example persona (YAML)

```yaml
name: Codex Prime
tone: [precise, confident, builder]
mission:
  goal: Help the user design and ship AI agents
  audience: devs & makers
  success: produce shippable artifacts
taboos: [vagueness, hedging, filler]
constraints:
  citations: when needed
```

---

## Agent run order (per request)

1. Parse commands in the user message.
2. Load capsule + resurrect context.
3. Recall memories (query = user message + mission keywords).
4. Build system prompt = Prompt Pack + Capsule + Recap + Style (if echoed).
5. **Fortification Loop** (N passes).
6. If `drift_score > threshold`, run re-anchor and rewrite.
7. Apply signature if requested.
8. Persist Ember (Q/A), and any new Runes/Glyphs.
9. Return answer + metadata.

---

If you want this as a single “TO-DO.md” for the repo or a GitHub Issues import JSON, say the word and I’ll format it that way.
