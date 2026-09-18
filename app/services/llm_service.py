"""可选的同步模型调用入口，统一读取项目配置。异步 Chain 直接使用 ChatOpenAI。"""
from langchain_openai import ChatOpenAI
from app.config import settings


class ModelServiceError(RuntimeError):
    pass


def complete(system: str, user: str) -> str:
    settings.require_llm_config()
    try:
        llm = ChatOpenAI(
            model=settings.LLM_MODEL,
            base_url=settings.LLM_BASE_URL,
            api_key=settings.LLM_API_KEY.get_secret_value(),
            timeout=60, max_retries=2,
        )
        result = llm.invoke([("system", system), ("human", user)])
        if not isinstance(result.content, str) or not result.content.strip():
            raise ValueError("模型未返回文本")
        return result.content
    except Exception as error:
        raise ModelServiceError("模型调用失败，请检查配置和网络。") from error
