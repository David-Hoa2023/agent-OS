# Prompt Pack - Commands & Examples

## Command Reference

### Memory Commands

#### Pin as Rune

Store important information in medium-term memory with tags.

**Syntax**: `Pin as Rune: <text>`

**Example**:
```
User: We decided to use PostgreSQL for the backend.
Pin as Rune: Database choice: PostgreSQL for backend storage
```

**Effect**: Adds to `runes.jsonl` with searchable tags

---

#### Carve as Glyph

Add to permanent curated knowledge base.

**Syntax**: `Carve as Glyph: <text>`

**Example**:
```
User: Always document public APIs before shipping.
Carve as Glyph: Core principle: Document public APIs before release
```

**Effect**: Adds to `glyphs.json`, loaded in every session

---

### Quality Commands

#### Activate Soul Drift

Trigger re-anchoring when output becomes generic or degraded.

**Syntax**: `Activate Soul Drift`

**Example**:
```
User: Activate Soul Drift

[System detects previous response had low lexical diversity]
[Re-anchors to capsule identity and regenerates response]
```

**Effect**: Runs drift detection and re-generates if threshold exceeded

---

#### Fortify xN

Run N rounds of self-critique and revision.

**Syntax**: `Fortify x<N>` (e.g., `Fortify x2`, `Fortify x3`)

**Example**:
```
User: Explain microservices. Fortify x2

[Draft] → [Critique against checklist] → [Revision] → [Final]
```

**Default Checklist**:
- Factuality
- Clarity
- Directness
- Completeness
- Tone faithfulness
- Mission alignment

---

### Context Commands

#### Resurrect Context

Reload full state, memories, and recap from previous session.

**Syntax**: `Resurrect Context`

**Example**:
```
User: Resurrect Context

[Loads state.json]
[Retrieves top 10 Embers]
[Retrieves mission-tagged Runes]
[Loads all Glyphs]
[Generates recap of decisions and plan]
```

**Effect**: Full context restoration across process restarts

---

#### Echo Style

Capture and replay a specific communication style.

**Syntax**: `Echo Style: <name>`

**Example**:
```
User: Explain APIs in a beginner-friendly way.
[Response in simple terms]
Echo Style: beginner

[Later...]
User: Echo Style: beginner
Explain databases.
[Response uses same beginner-friendly style]
```

**Effect**: Saves response to `styles/<name>.md`, includes as style guide in future prompts

---

### Output Commands

#### Sign Output

Add cryptographic signature with hash and metadata.

**Syntax**: `Sign Output`

**Example**:
```
User: Design a REST API. Sign Output

[Response]
---
Signed by: Alice
Hash: a3f5b8c9d2e1f0a7
Timestamp: 2025-01-15 14:30:00 UTC
Project: myapp
License: Flame Vault - Attribution Required
```

**Effect**: Appends signature footer, logs to `signatures.jsonl`

---

## Usage Patterns

### Starting a New Project

```
User: --project myapp --persona ./personas/codex_prime.yaml

Design a multi-tier memory system for an AI agent.

Carve as Glyph: Project goal: Build agent memory system
Fortify x2
```

### Resuming Work

```
User: --project myapp --resurrect

Resurrect Context

What were we working on?
```

### High-Quality Output

```
User: Write production-ready authentication code.
Fortify x3
Sign Output
Pin as Rune: Auth implementation completed with OAuth2
```

### Style Consistency

```
# First interaction
User: Explain Docker to a beginner.
[Response in simple terms]
Echo Style: beginner_friendly

# Later
User: Echo Style: beginner_friendly
Explain Kubernetes.
[Response matches previous style]
```

### Quality Recovery

```
User: [Previous response was generic]
Activate Soul Drift

[System re-anchors to capsule and regenerates]
```

---

## Command Combinations

Commands can be combined in a single message:

```
User: Design a caching strategy.
Fortify x2
Pin as Rune: Caching design for high-traffic API
Sign Output
```

**Execution Order**:
1. Parse all commands
2. Load context/memories
3. Execute fortification
4. Check drift
5. Apply signature
6. Store runes/glyphs

---

## System Behavior

### State Capsule Injection

Every request includes:

```json
[STATE CAPSULE]
{
  "persona": "Codex Prime",
  "mission": {
    "goal": "Help users design and ship AI agents",
    "audience": "devs & makers"
  },
  "constraints": ["no_vagueness", "be_direct"]
}
```

### Memory Recall

Automatic recall based on:
- User message keywords
- Mission tags
- Recency (Embers)
- Relevance score

### Drift Monitoring

Continuous monitoring with heuristics:
- Ban phrase detection
- Lexical diversity
- Repetition analysis

Threshold: 0.5 (configurable)

---

## Best Practices

1. **Use Glyphs Sparingly**: Only for core, unchanging principles
2. **Tag Runes Clearly**: Use consistent tags for better recall
3. **Fortify Important Outputs**: Use x2-x3 for production code
4. **Sign Deliverables**: Add signatures to final artifacts
5. **Resurrect Regularly**: Start sessions with context resurrection
6. **Monitor Drift**: Activate Soul Drift if responses feel generic
7. **Style Snapshots**: Create echoes for different audiences
