import json
import sys
from pathlib import Path

from pydantic import ValidationError


# 项目根目录：interview-answer-agent/
PROJECT_ROOT = Path(__file__).resolve().parents[1]


# 支持在 IDE 中直接运行 demo/_models.py
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from app.models.answer import AnswerRequest


def main():
    data_path = PROJECT_ROOT / "data" / "mock_request.json"

    # 1. 读取 JSON 文件
    try:
        with data_path.open("r", encoding="utf-8-sig") as file:
            data = json.load(file)
    except FileNotFoundError:
        print(f"找不到数据文件，请先创建：{data_path}")
        return 1
    except json.JSONDecodeError as error:
        print(
            f"JSON 格式错误：第 {error.lineno} 行，"
            f"第 {error.colno} 列，{error.msg}"
        )
        return 1
    except (OSError, UnicodeError) as error:
        print(f"读取文件失败：{error}")
        return 1

    # 2. 使用 Pydantic 校验数据
    try:
        request = AnswerRequest.model_validate(data)
    except ValidationError as error:
        print("数据校验失败，请检查 JSON 字段：")
        print(error)
        return 1

    # 3. 查看请求中的主要信息
    print("数据校验成功！")
    print(f"候选人：{request.candidate.name}")
    print(f"目标岗位：{request.target_job.title}")
    print(f"面试问题：{request.question}")
    print(f"输出语言：{request.language.value}")
    print(f"回答风格：{request.style.value}")
    print(f"目标时长：{request.duration_seconds} 秒")

    # 4. 查看项目经历，兼容项目列表为空的情况
    print("\n项目经历：")

    if not request.candidate.projects:
        print("暂未提供项目经历。")
    else:
        for index, project in enumerate(
            request.candidate.projects, start=1
        ):
            print(f"\n{index}. {project.name}")
            print(f"   项目背景：{project.background}")
            print(f"   个人职责：{project.role}")
            print(f"   技术栈：{'、'.join(project.tech_stack) or '未填写'}")

            print("   完成的工作：")
            for action in project.actions:
                print(f"   - {action}")

            print("   项目结果：")
            for result in project.results:
                print(f"   - {result}")

    # 5. 输出校验后的完整 JSON
    print("\n完整请求 JSON：")
    print(request.model_dump_json(indent=2))

    return 0


if __name__ == "__main__":
    sys.exit(main())