from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """项目配置，从 .env 文件读取"""

    openai_api_key: str = ""
    openai_base_url: str = "https://api.openai.com/v1"
    model_name: str = "gpt-4o-mini"
    temperature: float = 0.7

    # ReAct 循环
    max_react_steps: int = 5

    # MCP 配置
    mcp_enabled: bool = False
    mcp_server_url: str = "http://127.0.0.1:9123/mcp"

    # RAG 配置
    hf_endpoint: str = ""  # HuggingFace 镜像地址（如 https://hf-mirror.com），空则用默认
    embedding_provider: str = "local"  # openai / local（本地免费，无需 API Key）
    embedding_model: str = "text-embedding-3-small"  # provider=openai 时的模型
    local_embedding_model: str = "BAAI/bge-small-zh-v1.5"  # provider=local 时的模型
    kb_dir: str = "app/agent/rag/knowledge"
    # 向量后端：numpy（零依赖）/ chroma（需 pip install chromadb）
    rag_backend: str = "numpy"
    # NumpyBackend 的 JSON 索引路径
    kb_index_path: str = "app/sessions/kb_index.json"
    # ChromaBackend 的持久化目录与 collection 名
    chroma_persist_dir: str = "app/sessions/chroma"
    chroma_collection: str = "ecom_kb"

    # Multi-Agent 配置
    multi_agent_enabled: bool = False

    # Memory 配置
    memory_enabled: bool = True
    memory_dir: str = "app/sessions/memory"
    memory_user_id: str = "default"
    max_ltm_facts: int = 50

    # Skill 配置
    skills_enabled: bool = True
    skills_dir: str = "app/agent/skills/definitions"

    # Evaluation 配置
    eval_dataset_path: str = "app/evaluation/cases.json"
    eval_use_judge: bool = True  # 是否启用 LLM-as-judge（质量/幻觉/过程合理性）
    eval_pass_threshold: float = 0.6  # 单维度通过阈值（judge 归一化到 0-1 后比较）

    # 多轮对话管理
    session_path: str = "app/sessions/session.json"
    history_threshold: int = 10  # 消息压缩策略通常为上下文达到一定的token数，例如claude code通常为达到最大上下文窗口的70%左右，此处简略为原始消息条数超过10轮
    history_keep_recent: int = 3  # 压缩时保留最近 3 条原始消息

    model_config = {"env_file": ".env"}


settings = Settings()

# 将 HF_ENDPOINT 注入系统环境变量（huggingface_hub/sentence-transformers 从 os.environ 读取）
if settings.hf_endpoint:
    import os
    os.environ["HF_ENDPOINT"] = settings.hf_endpoint
