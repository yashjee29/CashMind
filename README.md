# CashMind — AI Content Generation & Reasoning Service

CashMind is the dedicated backend AI microservice within the CASH ecosystem, providing high-performance, structured LLM reasoning and content generation exclusively powered by Groq.

---

## 1. Capabilities

CashMind provides two specialized AI generation modules under `/api/v1/generate`:

### A. Moderation Reason Rewriter
Rewrites raw, casual, or emotionally charged incident reports into authoritative, strictly professional moderation reasons for Discord audit logs and moderation embeds:
- **Supported Actions**: `warning`, `timeout`, `kick`, `ban`.
- **Strict Writing Policy**: Preserves original meaning, enforces strict professional tone, never hallucinates allegations, never invents punishment durations, strips external URLs and emojis.
- **Auditable**: Keeps original report preserved alongside rewritten output.

### B. ICAI Announcement Generator & Rewriter
Generates and polishes motivational, student-friendly announcements for the ICAI study community (CA Foundation, Intermediate, and Final):
- **Generate Operation**: Creates structured announcements from topics and instructions.
- **Rewrite Operation**: Polishes existing drafts while preserving exam dates, deadlines, and registration steps.
- **Icon Catalog Validation**: Selects approved icons strictly from the Cash Mod catalog (resets unknown icons to `null`).
- **Resource Link Preservation**: Preserves user-provided URLs byte-for-byte; strictly prohibits LLM link invention.
- **Components V2 Ready**: Outputs structured sections and link button metadata for Discord Components V2 rendering.

---

## 2. Architecture & Separation of Concerns

```
┌─────────────────────────────────┐
│     Cash Mod (TypeScript Bot)   │
│  - Discord Interactions & Gateway│
│  - User Authorization           │
│  - Icon Catalog & Emojis        │
│  - Components V2 Rendering      │
└────────────────┬────────────────┘
                 │ HTTP API
┌────────────────▼────────────────┐
│    CashMind (Python FastAPI)    │
│  - AI Reasoning & Prompts       │
│  - Schema & Policy Validation   │
│  - Key Pool & Quota Manager     │
│  - Concurrency Scheduler        │
└────────────────┬────────────────┘
                 │ Async Groq API
┌────────────────▼────────────────┐
│         Groq Platform           │
│  - openai/gpt-oss-120b          │
│  - openai/gpt-oss-20b           │
│  - qwen/qwen3.8-27b             │
└─────────────────────────────────┘
```

- **CashMind Python**: AI generation, prompt engineering, structured validation. Never connects to Discord Gateway.
- **Cash Mod TypeScript**: Discord bot, user permissions, custom emojis, Components V2 message rendering.
- **Groq API**: Sole LLM inference provider.

---

## 3. Directory Layout

```
CashMind/
├── app/
│   ├── main.py
│   ├── core/
│   │   ├── config.py                 # Pydantic Settings & environment parsing
│   │   ├── logging.py                # Structured logging & secret masking
│   │   ├── security.py               # Internal service API key authentication
│   │   ├── exceptions.py             # Custom domain exception hierarchy
│   │   ├── responses.py              # Success & Error response envelopes
│   │   └── providers/
│   │       ├── key_pool.py           # Multi-key pooling, cooldowns & quota manager
│   │       ├── model_router.py       # Task-based routing & fallback models
│   │       ├── scheduler.py          # Concurrency limiting & retry with backoff
│   │       └── groq_provider.py      # Shared Groq provider client
│   └── modules/
│       └── generate/
│           ├── router.py             # Router aggregator & GET /health
│           ├── moderation/           # Moderation reason rewriter
│           │   ├── router.py
│           │   ├── service.py
│           │   ├── rewriter.py
│           │   ├── schemas.py
│           │   ├── prompts.py
│           │   └── validators.py
│           ├── announcements/        # ICAI announcement generator & rewriter
│           │   ├── router.py
│           │   ├── service.py
│           │   ├── generator.py
│           │   ├── rewriter.py
│           │   ├── schemas.py
│           │   ├── prompts.py
│           │   ├── icon_validator.py
│           │   └── link_validator.py
│           └── shared/               # Shared generation context & validators
├── tests/                            # 38 automated test cases
├── pyproject.toml
└── .env.example
```

---

## 4. Configuration

Copy `.env.example` to `.env`:

```bash
PORT=9102
HOST=0.0.0.0
CASHMIND_API_KEY=your_internal_service_key

# Groq API Keys (comma-separated or single)
GROQ_API_KEYS=gsk_your_key_here

# Groq Models Available on Account
GROQ_MODEL_MODERATION=openai/gpt-oss-20b
GROQ_MODEL_ANNOUNCEMENT_GEN=openai/gpt-oss-120b
GROQ_MODEL_ANNOUNCEMENT_REW=openai/gpt-oss-120b
GROQ_FALLBACK_MODEL=openai/gpt-oss-20b

GROQ_MAX_CONCURRENCY=10
GROQ_REQUEST_TIMEOUT_SECONDS=30.0
GROQ_MAX_RETRIES=3
KEY_COOLDOWN_SECONDS=60.0
```

---

## 5. Running the Service

### Development Server:
```bash
uvicorn app.main:app --host 0.0.0.0 --port 9102 --reload
```

### Running Test Suite:
```bash
pytest -v
```

---

## 6. API Reference

### Health Probe
`GET /api/v1/generate/health`
Returns module availability, Groq key pool status, and active models.

### Moderation Reason Rewrite
`POST /api/v1/generate/moderation/rewrite`

**Request:**
```json
{
  "action": "warning",
  "reason": "This guy keeps abusing people in chat and targeting them.",
  "language": "en",
  "max_length": 500
}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "action": "warning",
    "original_reason": "This guy keeps abusing people in chat and targeting them.",
    "rewritten_reason": "The user repeatedly harasses and targets other members in chat. This conduct violates community guidelines. The user is hereby warned to cease this behavior immediately.",
    "language": "en"
  },
  "metadata": {
    "model": "openai/gpt-oss-20b",
    "provider": "groq",
    "prompt_version": "1.0.0"
  }
}
```

### ICAI Announcement Generation
`POST /api/v1/generate/announcements/generate`

**Request:**
```json
{
  "operation": "generate",
  "topic": "Daily study consistency",
  "instructions": "Motivate students to complete daily study targets.",
  "links": [
    {
      "label": "Study Portal",
      "url": "https://icai.org/bos"
    }
  ],
  "available_icons": ["target", "book-open", "calendar", "trophy"]
}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "type": "icai_announcement",
    "title": "Stay on Track: Crush Your Daily Study Goals!",
    "subtitle": "For CA Foundation, Intermediate & Final Aspirants",
    "introduction": "Consistency is the backbone of success in the ICAI journey.",
    "sections": [
      {
        "heading": "Set Clear Daily Targets",
        "icon": "target",
        "content": "Define exactly what you will cover each study session.",
        "items": [
          "Write down specific topics or chapters",
          "Allocate realistic time blocks"
        ]
      }
    ],
    "links": [
      {
        "label": "Study Portal",
        "url": "https://icai.org/bos",
        "icon": null
      }
    ],
    "closing_message": "Keep the momentum alive—your future self will thank you!",
    "footer": "ICAI Study Community"
  },
  "metadata": {
    "model": "openai/gpt-oss-120b",
    "provider": "groq",
    "prompt_version": "1.0.0"
  }
}
```
