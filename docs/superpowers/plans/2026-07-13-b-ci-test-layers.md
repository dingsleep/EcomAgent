# B：CI 与测试分层实施计划

**目标：** 为 GitHub 仓库建立稳定的无密钥 CI 测试层，并明确真实模型与评测命令的运行边界。

**方案：** 用 `pytest` 的 `unit` 标记限定快速、确定性的本地测试；GitHub Actions 在 push/PR 只执行该层和 Python 编译检查。真实模型、MCP、RAG 端到端和 Judge 评测不进入默认 CI。

### 任务 1：标记稳定的单元测试

**文件：**
- 创建：`pytest.ini`
- 修改：`tests/test_fast_path.py`
- 修改：`tests/test_tool_safety.py`

1. 为 `unit`、`integration`、`live`、`evaluation` 声明 pytest 标记。
2. 给 `test_fast_path.py` 和 `test_tool_safety.py` 添加模块级 `pytestmark = pytest.mark.unit`。
3. 运行 `python -m pytest -m unit -q`，确认只收集并通过这两个无外部依赖的测试模块。

### 任务 2：新增默认 CI

**文件：**
- 创建：`.github/workflows/ci.yml`

1. 触发条件为 `push` 和 `pull_request`。
2. 使用 Python 3.11、pip 缓存和 `requirements-dev.txt` 安装。
3. 运行 `python -m compileall app mcp_server` 与 `python -m pytest -m unit -q`。

### 任务 3：记录运行分层

**文件：**
- 修改：`README.md`

1. 说明 CI 的 unit 命令不需要 API Key。
2. 列出真实模型回归和 Judge 评测命令，明确它们不在默认 CI 中执行。

### 验证

```powershell
D:\software\ana\envs\tx_agent\python.exe -m compileall app mcp_server
D:\software\ana\envs\tx_agent\python.exe -m pytest -m unit -q
```

检查 `.github/workflows/ci.yml` 包含上述两个命令，且不引用任何密钥。
