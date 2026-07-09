# CLAUDE.md

## Project Overview

EcomAgent is an enterprise-grade e-commerce customer service Agent system for the "云商城" platform.

- **Language**: Python 3.10+
- **Entry**: `main.py` (CLI interactive chat)
- **Model**: OpenAI-compatible API (default `gpt-4o-mini`, configurable via `.env`)

## Tech Stack

| Capability | Implementation |
|------------|---------------|
| Agent Paradigm | ReAct (Thought → Action → Observation loop) |
| Structured Output | OpenAI Structured Output / JSON fallback |
| Tool Calling | OpenAI Function Calling + local/MCP dual channel |
| MCP Integration | FastMCP Server (Streamable HTTP) + custom MCP Client |
| RAG | Markdown KB → Embedding → Vector search (Numpy / Chroma dual backend) |
| Multi-Agent | Router intent routing + presale/postsale/complaint sub-agents |
| Memory | Short-term (in-session LLM extraction) + Long-term (JSON cross-session persistence) |
| Skill System | Agent Skills open standard (progressive disclosure, SKILL.md) |
| Evaluation | Sandbox replay + process/result dual-layer metrics + LLM-as-Judge |
| Conversation Mgmt | LLM summary compression + JSON session persistence |

## Common Commands

```bash
# Install dependencies
pip install -r requirements.txt

# Configure (copy and fill in API Key)
cp .env.example .env

# Start CLI chat (single agent mode)
python main.py

# Build RAG knowledge base index
python -m app.scripts.build_kb_index              # Numpy backend (default)
python -m app.scripts.build_kb_index --backend chroma  # Chroma backend

# Start MCP Server (standalone process, default 127.0.0.1:9123)
python mcp_server/server.py

# Run tests
python -m pytest tests/ -v

# Run evaluation
python -m app.scripts.run_eval                      # Default: single agent + LLM judge
python -m app.scripts.run_eval --mode multi          # Multi-Agent mode
python -m app.scripts.run_eval --no-judge --output report.json  # Code metrics only
```

## Architecture

```
main.py                         # CLI entry, mode switch (single / multi-agent)
├── app/
│   ├── config/settings.py      # Unified config (.env → Pydantic Settings)
│   ├── prompts/                # System prompt templates
│   ├── schemas/response.py     # CustomerServiceResponse structured output
│   ├── agent/                  # Core Agent implementation
│   │   ├── chat.py             # EcomAgent: ReAct loop + tools + memory + skills
│   │   ├── summarizer.py       # LLM summary compression
│   │   ├── storage.py          # Session JSON persistence
│   │   ├── tools/              # Tools (order/product/logistics/refund/knowledge/memory/skill)
│   │   ├── rag/                # RAG (chunker/embedder/retriever/backends)
│   │   ├── memory/             # MemoryManager: STM + LTM
│   │   └── skills/             # SkillManager: SKILL.md scanning and loading
│   ├── multi_agent/            # Multi-Agent (Router + SubAgent + Orchestrator)
│   ├── mcp_client/             # MCP client (background thread + schema conversion)
│   ├── evaluation/             # Evaluation framework (sandbox/metrics/scoring/golden dataset)
│   └── scripts/                # Offline scripts (build index / run eval)
├── mcp_server/server.py        # MCP Server (FastMCP, exposes e-commerce tools)
└── tests/                      # Tests organized by technical topic
```

## Core Design Patterns

### ReAct Loop (`app/agent/chat.py:_react_loop`)

Max `max_react_steps` (default 5) rounds: LLM returns tool_calls → execute tools → observe results → continue loop until LLM returns plain text. Tool call messages are preserved in `raw_messages`.

### Dual Mode Operation

Switch via `MULTI_AGENT_ENABLED=true` environment variable:
- **Single Agent mode** (default): `EcomAgent` handles all intents directly
- **Multi-Agent mode**: `MultiAgentOrchestrator` → Router classifies intent → dispatches to presale/postsale/complaint sub-agents

Both modes share the same interface (`chat()`, `reset()`, `save()`, `close()`).

### Tool Management (`app/agent/tools/manager.py`)

`ToolManager` unifies local tools and MCP remote tools. Exposes `tool_definitions` in OpenAI Function Calling format. Supports `allowed_tools` filtering for sub-agent tool isolation in Multi-Agent mode.

### Memory System (`app/agent/memory/`)

- **Short-Term Memory (STM)**: After each turn, LLM extracts facts from recent messages (preferences, needs, context)
- **Long-Term Memory (LTM)**: At session close, merges STM → JSON file (`app/sessions/memory/{user_id}.json`), injected into system prompt on next session
- `memory` command views current memory; `recall_user_memory` tool for Agent active query

### Skill System (`app/agent/skills/`)

Follows the Agent Skills open standard: each skill is a `SKILL.md` with `---name` and `---description` frontmatter. `SkillManager` scans on startup, injects catalog into system prompt via progressive disclosure. `load_skill` tool loads full instructions on demand.

### Session Management

- Auto-restores last conversation from `app/sessions/session.json`
- Triggers LLM summary compression when messages exceed `history_threshold` (default 10 turns)
- Compression: keeps recent `keep_recent` (default 3) raw messages, tool messages are never split mid-pair
- `app/sessions/` is git-ignored

### RAG Dual Backend

- **NumpyBackend**: Cosine similarity + JSON index, zero external dependencies, full algorithm transparency
- **ChromaBackend**: Embedded Chroma vector database with HNSW indexing

Switch via `RAG_BACKEND=chroma` environment variable.

## Environment Variables (`.env`)

Copy `.env.example` and fill in (do not commit `.env`):

| Variable | Description | Default |
|----------|-------------|---------|
| `OPENAI_API_KEY` | **Required** | - |
| `OPENAI_BASE_URL` | API endpoint | `https://api.openai.com/v1` |
| `MODEL_NAME` | Model | `gpt-4o-mini` |
| `MCP_ENABLED` | Enable MCP | `false` |
| `MULTI_AGENT_ENABLED` | Enable Multi-Agent | `false` |
| `MEMORY_ENABLED` | Enable memory | `true` |
| `SKILLS_ENABLED` | Enable skills | `true` |
| `RAG_BACKEND` | Vector backend | `numpy` |

## Tests

Tests are organized by technical topic:

| File | Coverage |
|------|----------|
| `test_agent.py` | Structured output + multi-turn + reset |
| `test_conversation_management.py` | Conversation management |
| `test_react_agent.py` | ReAct + Function Calling |
| `test_mcp.py` | MCP integration |
| `test_rag.py` | RAG knowledge base retrieval |
| `test_multi_agent.py` | Multi-Agent collaboration |
| `test_memory.py` | Short/long-term memory |
| `test_skills.py` | Skill module |
| `test_evaluation.py` | Agent evaluation framework |

## Notes

- `.claude/` is git-ignored, contains Claude Code configuration
- Mock data is in `app/agent/tools/mock_data.py`, no real database dependency
- MCP Server is a standalone process, must be started before using MCP features
- Default RAG backend uses Numpy for zero-dependency cosine similarity; switch to Chroma for production-scale workloads
