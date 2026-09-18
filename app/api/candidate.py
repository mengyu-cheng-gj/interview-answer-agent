from fastapi import APIRouter
from app.models.candidate import Candidate
from app.chains.candidate_chain import analyze_candidate

router = APIRouter()

@router.post("/analyze")
def analyze(request: Candidate):
    return analyze_candidate(request)
