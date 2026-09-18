from app.models.candidate import Candidate


def analyze_candidate(candidate: Candidate) -> dict:
    return {
        "candidate_id": candidate.candidate_id,
        "projects": [p.model_dump() for p in candidate.projects],
        "missing_information": [] if candidate.projects else [
            "请补充真实项目经历、个人职责及结果。"
        ],
    }
