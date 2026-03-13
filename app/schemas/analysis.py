from pydantic import BaseModel


class AnalysisResult(BaseModel):
    approach: str
    time_complexity: str
    improvement: str
    next_problem: str
    better_code: str

