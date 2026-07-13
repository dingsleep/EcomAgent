# EcomAgent

Engineering-focused e-commerce customer service Agent demo built with a modern AI Agent stack.

## Architecture

```
main.py                      # CLI entry (single / multi-agent modes)
├── app/
│   ├── agent/               # Core Agent (ReAct loop + tools + RAG + memory + skills)
│   ├── multi_agent/         # Multi-Agent orchestration (Router + presale/postsale/complaint)
│   ├── mcp_client/          # MCP client (sync wrapper over Streamable HTTP)
│   ├── evaluation/          # Evaluation framework (sandbox + metrics + LLM-as-Judge)
│   ├── prompts/             # System prompts (agent / summarizer / evaluation)
│   ├── schemas/             # Structured output (Pydantic)
│   ├── config/              # Configuration (pydantic-settings)
│   └── scripts/             # Offline scripts (build KB index / run eval)
├── mcp_server/              # MCP Server (FastMCP, standalone process)
└── tests/                   # Test suite
```

## Features

| Capability | Implementation |
|------------|---------------|
| **Agent Paradigm** | ReAct (Thought → Action → Observation loop) |
| **Structured Output** | OpenAI Structured Output / JSON fallback |
| **Tool Calling** | OpenAI Function Calling + local/MCP dual channel |
| **MCP Integration** | FastMCP Server (Streamable HTTP) + custom MCP Client |
| **RAG** | Markdown knowledge base → Embedding → Vector search (Numpy / Chroma) |
| **Multi-Agent** | Router intent classification → presale / postsale / complaint sub-agents |
| **Memory** | Short-term (in-session LLM extraction) + Long-term (JSON cross-session) |
| **Skill System** | Agent Skills open standard (progressive disclosure, SKILL.md) |
| **Evaluation** | Sandbox replay + process/result dual-layer metrics + LLM-as-Judge |
| **Conversation Mgmt** | LLM summary compression + JSON session persistence |

## Quick Start

```bash
# Install runtime dependencies
pip install -r requirements.txt

# Configure
cp .env.example .env
# Edit .env with your API key and model settings

# Build RAG knowledge base index
python -m app.scripts.build_kb_index

# Start CLI
python main.py
```

For local development and tests, install the additional test dependency:

```bash
pip install -r requirements-dev.txt
```

## Usage

### Single Agent Mode (default)

```bash
python main.py
```

A single `EcomAgent` handles all intents with full tool access.

### Multi-Agent Mode

Set in `.env`:
```
MULTI_AGENT_ENABLED=true
```

Routes user intent to specialized sub-agents (presale / postsale / complaint) with tool-level permission isolation.

### MCP Integration

```bash
# Terminal 1: Start MCP Server
python mcp_server/server.py

# Terminal 2: Enable MCP in .env and start Agent
# MCP_ENABLED=true
python main.py
```

MCP Server exposes tools as a standardized remote service. Agent falls back to local tools on connection failure.

### Running Tests

```bash
# Deterministic tests used by GitHub Actions; no API key or MCP server required
python -m pytest -m unit -q

# Live model/MCP regression tests; requires a configured .env
python -m pytest tests/test_react_agent.py tests/test_agent.py -q

# Full local suite (may include live and optional-dependency tests)
python -m pytest tests/ -v
```

GitHub Actions runs only the `unit` layer on push and pull requests. Agent, MCP and evaluation end-to-end tests require a valid model configuration; run them locally or in a separately configured workflow because model responses can vary.

### Running Evaluation

```bash
# Full evaluation (with LLM-as-Judge)
python -m app.scripts.run_eval

# Code-rule metrics only (fast, deterministic)
python -m app.scripts.run_eval --no-judge

# Multi-Agent mode evaluation
python -m app.scripts.run_eval --mode multi
```

## Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `OPENAI_API_KEY` | **Required** | - |
| `OPENAI_BASE_URL` | API endpoint | `https://api.openai.com/v1` |
| `MODEL_NAME` | Model name | `gpt-4o-mini` |
| `MCP_ENABLED` | Enable MCP | `false` |
| `MULTI_AGENT_ENABLED` | Enable Multi-Agent | `false` |
| `MEMORY_ENABLED` | Enable memory system | `true` |
| `SKILLS_ENABLED` | Enable skill system | `true` |
| `RAG_BACKEND` | Vector backend (`numpy` / `chroma`) | `numpy` |
| `EMBEDDING_PROVIDER` | Embedding source (`openai` / `local`) | `local` |

## Key Design Decisions

- **Agentic RAG over RAG-First**: Agent decides when to search knowledge base, avoiding unnecessary retrievals
- **Tool whitelist over prompt constraints**: Sub-agents physically cannot call unauthorized tools (e.g., complaint agent has no `apply_refund`)
- **Incremental summary compression**: Old messages are summarized with previous summary as context, preserving history across compressions
- **LTM at session close**: Long-term memory extracted at session end to avoid contradictory intermediate facts
- **Skill progressive disclosure**: Only skill catalog (~100 tokens) in system prompt; full SOP loaded on demand
- **MCP graceful degradation**: Falls back to local tools when MCP Server is unreachable

## Data Boundary

Orders, products, logistics and coupons are in-memory Mock data. This project demonstrates Agent orchestration, tool contracts and evaluation design; it is not connected to a production commerce system.

## Resume Description（中文）

- 基于 ReAct、OpenAI Function Calling 与 Pydantic Structured Output 构建电商客服 Agent，覆盖订单、商品、物流和退款等工具工作流。
- 设计本地工具/MCP 双通道调度与故障降级，并通过工具白名单隔离售前、售后、投诉三个子 Agent 的权限。
- 实现双后端 RAG、会话记忆、Skill 按需加载和 Sandbox 评估框架，覆盖工具调用、Token 成本、回答质量与忠实度等指标。

## License

MIT
