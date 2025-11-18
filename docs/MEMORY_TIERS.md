# Memory Tiers - Embers, Runes, and Glyphs

## Overview

Codex Prime uses a three-tier memory architecture designed for different types of information and retention needs.

## Tier 1: Embers (Short-term)

### Characteristics

- **Duration**: 1 hour TTL (configurable)
- **Capacity**: Ring buffer, max 100 items (configurable)
- **Storage**: `embers.jsonl` (JSONL format)
- **Behavior**: FIFO eviction when buffer full

### What Goes Here

- Recent Q/A exchanges
- Intermediate thoughts and reasoning
- Temporary context for current conversation
- Session-specific decisions

### Examples

```
"User asked about Python decorators at 14:30"
"Explained @property with example code"
"User preferred functional style over OOP"
```

### API

```python
vault.add_ember("Quick note about API design")
recent = vault.get_recent_embers(n=10)
```

### When to Use

- Automatic: Every user interaction
- Manual: For temporary notes you want accessible for ~1 hour

---

## Tier 2: Runes (Medium-term)

### Characteristics

- **Duration**: Persistent until deleted
- **Capacity**: Unlimited (practical limit: thousands)
- **Storage**: `runes.jsonl` (JSONL format)
- **Search**: Tag-based + keyword search
- **Scope**: Project-level

### What Goes Here

- Important decisions and rationale
- Design choices and trade-offs
- Lessons learned
- User preferences
- Architecture patterns chosen
- Failed approaches to avoid

### Examples

```
"Database choice: PostgreSQL for ACID compliance" [tags: decision, database]
"User prefers verbose error messages" [tags: preference, ux]
"Tried Redis for session store, switched to PostgreSQL for consistency" [tags: decision, architecture, redis, postgresql]
```

### API

```python
vault.add_rune(
    "API uses REST over GraphQL for simplicity",
    tags=["decision", "api", "architecture"]
)

runes = vault.get_runes_by_tags(["decision", "api"])
```

### When to Use

Use `Pin as Rune:` command for:
- Decisions that should influence future work
- Patterns to remember and reuse
- Constraints to respect
- Context that needs to survive sessions

---

## Tier 3: Glyphs (Long-term)

### Characteristics

- **Duration**: Permanent (until manually removed)
- **Capacity**: Small (~10-20 items)
- **Storage**: `glyphs.json` (JSON array)
- **Loading**: **Always loaded** in every request
- **Curated**: Manually selected invariants

### What Goes Here

- Core principles and values
- Immutable constraints
- Project-wide standards
- Team conventions
- Non-negotiable requirements

### Examples

```
"Always validate user input before database operations"
"Never commit secrets to git"
"Public APIs must have OpenAPI documentation"
"Code must pass type checking before merge"
"Prefer composition over inheritance"
```

### API

```python
vault.add_glyph("Core principle: Fail fast with clear error messages")
glyphs = vault.get_glyphs()  # Always included in context
```

### When to Use

Use `Carve as Glyph:` command for:
- Fundamental rules that never change
- Core project philosophy
- Critical constraints
- Safety requirements

**Warning**: Keep Glyphs minimal! They're always loaded, so too many will consume context budget.

---

## Decision Matrix

| If you need to remember... | Use This Tier | Command |
|----------------------------|---------------|---------|
| Last few messages in conversation | Embers | (automatic) |
| Important decision for this project | Runes | `Pin as Rune:` |
| Core principle that never changes | Glyphs | `Carve as Glyph:` |
| Temporary experiment result | Embers | (automatic) |
| User's coding style preference | Runes | `Pin as Rune:` |
| Security requirement | Glyphs | `Carve as Glyph:` |
| Database choice for current feature | Runes | `Pin as Rune:` |
| "Always X" or "Never Y" rule | Glyphs | `Carve as Glyph:` |

---

## Memory Lifecycle

### Ember → Rune Promotion

```
User: We decided PostgreSQL is the right choice because we need ACID.

[Stored as Ember automatically]

User: Pin as Rune: Database: PostgreSQL for ACID compliance

[Promoted to Rune with tags]
```

### Rune → Glyph Promotion

```
User: This PostgreSQL decision is permanent for the whole project.
Carve as Glyph: Project standard: PostgreSQL for all persistent storage

[Promoted to Glyph, always loaded]
```

---

## Recall Strategy

When processing a request, memories are recalled in this order:

1. **Glyphs**: All loaded (always)
2. **Runes**: Top-K by relevance to query + mission tags
3. **Embers**: Recent N items (default: 10)

**Total Budget**: ~8 memories per request (configurable)

**Ranking**:
- Keyword match in text
- Tag match
- Recency (for Embers)
- Relevance score (future: vector similarity)

---

## Storage Format

### Embers (JSONL)

```jsonl
{"text": "Explained decorators", "timestamp": 1705334400.0, "tier": "ember", "ttl": 3600}
{"text": "User prefers pytest", "timestamp": 1705334500.0, "tier": "ember", "ttl": 3600}
```

### Runes (JSONL)

```jsonl
{"text": "DB: PostgreSQL", "timestamp": 1705334400.0, "tags": ["decision", "db"], "tier": "rune", "scope": "project"}
{"text": "Auth: OAuth2", "timestamp": 1705334500.0, "tags": ["decision", "auth"], "tier": "rune", "scope": "project"}
```

### Glyphs (JSON)

```json
[
  {
    "text": "Always validate input",
    "timestamp": 1705334400.0,
    "tier": "glyph",
    "scope": "project"
  },
  {
    "text": "Never commit secrets",
    "timestamp": 1705334500.0,
    "tier": "glyph",
    "scope": "project"
  }
]
```

---

## Best Practices

### Embers

✅ Let them happen automatically
✅ Don't worry about cleanup (TTL handles it)
✅ Use for conversational flow

❌ Don't manually create them (automatic)
❌ Don't store important info only as ember

### Runes

✅ Use descriptive text
✅ Add 2-3 relevant tags
✅ Include rationale
✅ Keep them specific

❌ Don't use generic tags ("misc", "other")
❌ Don't store what should be in code
❌ Don't duplicate Glyphs

### Glyphs

✅ Keep list small (<20)
✅ Make them actionable
✅ Use for invariants only
✅ Review and prune periodically

❌ Don't use for project-specific decisions (use Runes)
❌ Don't add too many (context budget)
❌ Don't make them vague

---

## Example Session

```
User: Design a user authentication system.

[Agent recalls Glyphs:]
- "Never store passwords in plaintext"
- "Always use HTTPS for auth endpoints"

[Agent recalls Runes:]
- "Project uses PostgreSQL" [tags: decision, db]
- "User prefers JWT over sessions" [tags: preference, auth]

[Agent designs auth with PostgreSQL + JWT + bcrypt]

User: Great! Pin as Rune: Auth design: JWT with bcrypt hashing
[Stored as Rune]

User: This is a core security requirement.
Carve as Glyph: Security: JWT authentication with bcrypt required
[Promoted to Glyph]
```

---

## Future Enhancements

- **Vector Search**: Semantic similarity for Runes
- **Auto-Promotion**: Ember → Rune based on reference frequency
- **Cross-Project**: Share Glyphs across projects
- **Archival**: Compress old Runes to cold storage
- **Analytics**: Memory usage and recall statistics
