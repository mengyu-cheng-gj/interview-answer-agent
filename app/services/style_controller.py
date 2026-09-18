from dataclasses import dataclass

from app.models.answer import LanguageType, StyleType


@dataclass(frozen=True)
class StyleConfig:
    """一种回答风格的配置。"""

    name: str
    system_prefix: str
    speaking_tempo: str
    vocabulary_hint: str


STYLE_CONFIGS: dict[StyleType, StyleConfig] = {
    StyleType.NATURAL: StyleConfig(
        name="自然口语",
        system_prefix=(
            "请使用自然、清楚的面试口语表达。"
            "采用第一人称，以短句为主，适当使用过渡句。"
            "避免书面报告腔、堆砌术语和过多口头禅。"
        ),
        speaking_tempo="节奏自然，按照语义安排停顿",
        vocabulary_hint="使用常见词汇，保留必要的技术术语",
    ),

    StyleType.PROFESSIONAL: StyleConfig(
        name="专业正式",
        system_prefix=(
            "请使用专业、准确、逻辑清晰的面试表达。"
            "明确区分项目背景、个人职责、实施方案和结果。"
            "讨论技术时说明选择理由与取舍。"
            "只在资料提供时引用数字，不为显得专业而编造指标。"
        ),
        speaking_tempo="节奏平稳，层次清晰",
        vocabulary_hint="准确使用技术术语，避免空泛形容词",
    ),

    StyleType.CONCISE: StyleConfig(
        name="简洁直接",
        system_prefix=(
            "请直接回应问题，先给结论，再提供关键依据。"
            "删除重复信息、无关背景和客套话。"
            "优先保留个人职责、关键行动和真实结果。"
            "简洁不能以遗漏必要的限制条件为代价。"
        ),
        speaking_tempo="句子简短，信息分组清楚",
        vocabulary_hint="使用明确的动词和简短句式",
    ),
}


LANGUAGE_INSTRUCTIONS: dict[LanguageType, str] = {
    LanguageType.ZH: (
        "使用简体中文回答。"
        "采用自然的中文面试表达，必要时保留英文技术名词。"
    ),
    LanguageType.EN: (
        "Answer in natural spoken English suitable for an interview. "
        "Use clear sentences and accurate technical terms. "
        "Avoid literal translations of Chinese expressions."
    ),
    LanguageType.BOTH: (
        "分别生成简体中文和英文回答。"
        "两种语言必须保持职责、技术、数字、成果及限制条件一致。"
        "英文按自然口语重新组织，不要机械逐字翻译。"
    ),
}


class StyleController:
    @staticmethod
    def get_config(style: StyleType | str) -> StyleConfig:
        """获取风格配置；不支持的风格会抛出 ValueError。"""
        style = StyleType(style)
        return STYLE_CONFIGS[style]

    @staticmethod
    def build_instruction(
        style: StyleType | str,
        language: LanguageType | str,
    ) -> str:
        """组合风格与语言要求，供回答生成提示词使用。"""
        config = StyleController.get_config(style)
        language = LanguageType(language)

        return "\n".join([
            f"回答风格：{config.name}",
            config.system_prefix,
            f"表达节奏：{config.speaking_tempo}",
            f"用词要求：{config.vocabulary_hint}",
            f"语言要求：{LANGUAGE_INSTRUCTIONS[language]}",
            (
                "事实约束：风格调整只能改变表达方式，"
                "不得增加未经候选人资料支持的个人经历、职责或成果。"
            ),
        ])