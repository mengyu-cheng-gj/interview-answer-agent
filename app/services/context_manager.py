def build_context(candidate) -> dict:
    # 仅使用本次请求资料，避免不同用户之间共享个人经历。
    return candidate.model_dump()
