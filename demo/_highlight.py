import asyncio
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from app.chains.highlight_chain import HighlightChain
from app.models.answer import AnswerRequest


async def main():
    # 使用之前准备的模拟请求
    data_path = PROJECT_ROOT / "data" / "mock_request.json"

    # 直接读取 JSON 文本并校验
    request = AnswerRequest.model_validate_json(
        data_path.read_text(encoding="utf-8-sig")
    )

    # 创建亮点提取链
    chain = HighlightChain()

    # 提取与目标岗位有关的面试亮点
    result = await chain.extract(
        candidate=request.candidate,
        target_job=request.target_job,
    )

    print("面试亮点提取结果：")
    print(result.model_dump_json(indent=2))


if __name__ == "__main__":
    asyncio.run(main())