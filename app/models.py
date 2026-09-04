from pydantic import BaseModel, Field
from typing import List, Optional


class TestCase(BaseModel):
    case_id: str
    expected_output: str
    actual_output: str

    success: bool = False

    latency_ms: float = Field(default=0, ge=0)

    tool_error: bool = False

    critical: bool = False

    human_review_required: bool = False

    estimated_cost_usd: float = Field(default=0, ge=0)


class Workflow(BaseModel):
    name: str
    description: str = ""

    target_reliability: float = Field(
        default=95,
        ge=0,
        le=100
    )

    maximum_critical_failures: int = Field(
        default=0,
        ge=0
    )

    maximum_human_review_rate: float = Field(
        default=20,
        ge=0,
        le=100
    )

    test_cases: List[TestCase]


class Failure(BaseModel):
    case_id: str
    category: str
    severity: str
    message: str


class QualificationResult(BaseModel):
    workflow_name: str

    total_cases: int
    successful_cases: int
    failed_cases: int

    reliability_score: float

    critical_failures: int
    tool_failures: int

    human_review_cases: int
    human_review_rate: float

    average_latency_ms: float

    total_estimated_cost_usd: float
    average_cost_per_case_usd: float

    target_reliability: float
    maximum_critical_failures: int
    maximum_human_review_rate: float

    verdict: str

    reasons: List[str]

    failures: List[Failure]
