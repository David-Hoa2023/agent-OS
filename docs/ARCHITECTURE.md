# Codex Prime Architecture

## Overview

Codex Prime is an Agent OS designed for persistent, self-correcting AI agents with multi-tier memory and identity management.

## Core Components

### 1. State Capsule

The identity container for an agent instance:

```
StateCapsule
├── persona: Agent's identity and voice
├── mission: Goals, audience, success criteria
├── constraints: Behavioral boundaries
└── open_threads: Active conversation threads
```

**Persistence**: `~/.codex_prime/projects/<project_id>/state.json`

### 2. Memory Vault (Three-Tier System)

**Embers** (Short-term)
- Ring buffer with TTL
- Stores recent Q/A exchanges
- Auto-expires after 1 hour (configurable)
- File: `embers.jsonl`

**Runes** (Medium-term)
- Tagged memories with vector search
- Project-scoped decisions and learnings
- Searchable by tags and content
- File: `runes.jsonl`

**Glyphs** (Long-term)
- Curated permanent knowledge
- Core principles and invariants
- Always loaded into context
- File: `glyphs.json`

### 3. Fortification Loop

Self-critique and revision mechanism:

```
User Input
    ↓
Draft Response (Pass 1)
    ↓
Critique (against checklist)
    ↓
Revision (Pass 2)
    ↓
[Repeat N times]
    ↓
Final Output
```

**Default Checklist**:
- Factuality
- Clarity
- Directness
- Completeness
- Tone faithfulness
- Mission alignment

### 4. Soul Drift Protocol

Detects and corrects degraded output quality:

**Heuristics**:
1. Ban phrase detection (e.g., "as an AI", "I apologize")
2. Type/token ratio (lexical diversity)
3. Repetition score

**Threshold**: 0.5 (configurable)

**Re-anchoring**: When drift detected, regenerate with capsule re-injection

### 5. Command Router

Lightweight DSL for agent control:

- `Pin as Rune: <text>` → Store in medium-term memory
- `Carve as Glyph: <text>` → Add to permanent knowledge
- `Activate Soul Drift` → Trigger re-anchoring
- `Resurrect Context` → Reload full state
- `Echo Style: <name>` → Apply communication style
- `Sign Output` → Add cryptographic signature
- `Fortify xN` → Run N fortification loops

### 6. Provider Abstraction

Pluggable LLM backends:

```python
class BaseProvider:
    def chat(system, messages, temperature) -> str
    def embed(texts) -> list[list[float]]
```

Implementations:
- OpenAI (GPT-4, GPT-3.5)
- Anthropic (Claude)
- Local (Ollama, llama.cpp)

## Data Flow

```
Request
    ↓
1. Parse commands
    ↓
2. Load capsule + resurrect context
    ↓
3. Recall memories (Embers + Runes + Glyphs)
    ↓
4. Build system prompt (Charter + Capsule + Recap + Style)
    ↓
5. Fortification Loop (N passes)
    ↓
6. Drift check → Re-anchor if needed
    ↓
7. Apply signature (optional)
    ↓
8. Persist Ember (Q/A) + new Runes/Glyphs
    ↓
Response + Metadata
```

## File Structure

```
~/.codex_prime/
└── projects/
    └── <project_id>/
        ├── state.json          # State capsule
        ├── vault/
        │   ├── embers.jsonl    # Short-term memory
        │   ├── runes.jsonl     # Medium-term memory
        │   ├── glyphs.json     # Long-term memory
        │   └── signatures.jsonl # Output signatures
        └── styles/
            └── <name>.md       # Style snapshots
```

## Interfaces

### CLI

```bash
codex --project myapp \
      --persona ./personas/codex_prime.yaml \
      --fortify x2 \
      --signer "Alice"
```

### HTTP API

```http
POST /chat
Content-Type: application/json

{
  "project_id": "myapp",
  "message": "Design a memory system",
  "commands": ["Fortify x2", "Sign Output"]
}
```

Response:
```json
{
  "answer": "...",
  "drift_score": 0.15,
  "memories_used": ["...", "..."],
  "project_id": "myapp"
}
```

## Extension Points

1. **Custom Providers**: Implement `BaseProvider` interface
2. **Embedding Models**: Implement `EmbeddingProvider` interface
3. **Drift Heuristics**: Add functions to `drift.py`
4. **Commands**: Extend parser in command router
5. **Personas**: Create YAML files with custom tone/mission

## Performance Considerations

- **Token Budget**: Configurable per request
- **Memory Recall**: Limited to top-K results (default: 8)
- **Ember TTL**: Default 1 hour (3600s)
- **Ring Buffer**: Max 100 embers (configurable)

## Security

- API keys via environment variables
- Signature verification via SHA256
- Project isolation via directories
- No credential logging
