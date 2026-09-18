# 中英文面试回答生成 Agent

基于 FastAPI、LangChain、Pydantic 和可选 Redis 的本地学习项目。

## 当前流程

候选人资料 + 岗位 → 亮点提取（可缓存）→ 按题型与风格生成中英文回答 → 互动修改。

主要入口：
- app/main.py：HTTP 接口和 SSE 分阶段事件。
- app/config.py：读取根目录 .env；环境变量优先。
- app/chains/：亮点、回答、互动链。
- app/services/cache_service.py：异步 Redis 缓存，失败时回退生成。
- app/models/：输入输出模型。

API：
- GET /health
- POST /api/highlight/extract
- POST /api/answer/generate
- POST /api/answer/stream
- POST /api/interaction/reply

当前 main.py 集中注册业务接口。app/api 中为早期兼容路由，不要重复注册相同路径。

## 配置

.env 已提供空配置框架（若原先存在则保留）。填写：
- LLM_MODEL：供应商模型名
- LLM_BASE_URL：兼容接口基础地址，通常以 /v1 结尾
- LLM_API_KEY：实际密钥
- CACHE_ENABLED：本地暂不使用 Redis 时设为 false

不能将完整 /chat/completions 地址作为基础地址。配置修改后需重启程序。
没有全局 mock 模式；真实生成会调用模型服务。

## 后续启动步骤（本轮未执行）

在 Anaconda Prompt 中：

```bat
conda activate rag
cd /d E:\AAAA_Mengyu_Projects\interview-answer-agent
python -m pip install -r requirements.txt
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000
```

浏览器打开 http://127.0.0.1:8000/docs 。
data/mock_request.json 是新版请求示例；旧 example_request.json 仅保留作历史参考。

## Docker（两种方案选一种）

云端 API + 本地 Redis：

```bat
docker compose up --build
```

本地 GPU 模型 + API + Redis：

```bat
docker compose -f docker-compose.local.yml up --build
```

本地模型方案需另行填写 VLLM_IMAGE、LOCAL_MODEL、LOCAL_LLM_API_KEY。
vLLM 镜像版本需结合实际 GPU、驱动和显存选择，目前未配置或验证。
Windows 使用支持 GPU 的 Docker Desktop WSL2 环境。
初次运行会下载镜像、依赖和模型，不是本轮已完成的操作。

容器内 Redis 地址为 redis://redis:6379/0；
本地模型地址为 http://vllm:8001/v1。
API 端口仅映射到本机 127.0.0.1:8000。

## 当前限制与验证状态

- 本轮按要求仅编辑文件，未安装依赖、未运行测试、未调用模型或启动 Docker。
- SSE 返回阶段状态、亮点、最终回答，不是逐 token 输出。
- 引用检查只覆盖项目 ID 与事实原文摘录，不能证明整篇回答事实正确。
- 中英文语义一致性仍依赖生成约束及人工复核。
- 尚无会话持久化、用户认证、简历文件解析或 RAG 检索。
- Redis 中的亮点缓存为明文；哈希键不等于内容加密。
- requirements.txt 使用版本范围，待统一测试后锁定环境。
- tests/test_answer.py 仍是早期 mock 接口测试，需在统一测试阶段迁移到新版接口后再执行。
