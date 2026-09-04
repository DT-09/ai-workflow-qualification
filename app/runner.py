from __future__ import annotations

import time
from dataclasses import dataclass
from typing import Callable, Any

from app.models import TestCase, Workflow
from app.engine import qualify_workflow


@dataclass
class ExecutionCase:
    case_id: str
    input_data: Any
    expected_output: Any
    critical: bool = False
    human_review_required: bool = False


@dataclass
class ExecutionResult:
    case_id: str
    actual_output: Any
    success: bool
    latency_ms: float
    tool_error: bool
    critical: bool
    human_review_required: bool
    error: str | None = None


class AgentRunner:
    def __init__(self, agent: Callable[[Any], Any]):
        self.agent = agent

    def run_case(self, case: ExecutionCase) -> ExecutionResult:
        start = time.perf_counter()

        try:
            actual_output = self.agent(case.input_data)

            latency_ms = (time.perf_counter() - start) * 1000

            success = actual_output == case.expected_output

            return ExecutionResult(
                case_id=case.case_id,
                actual_output=actual_output,
                success=success,
                latency_ms=latency_ms,
                tool_error=False,
                critical=case.critical,
                human_review_required=case.human_review_required,
            )

        except Exception as exc:
            latency_ms = (time.perf_counter() - start) * 1000

            return ExecutionResult(
                case_id=case.case_id,
                actual_output=None,
                success=False,
                latency_ms=latency_ms,
                tool_error=True,
                critical=case.critical,
                human_review_required=case.human_review_required,
                error=str(exc),
            )

    def run(
        self,
        workflow_name: str,
        cases: list[ExecutionCase],
        target_reliability: float = 95.0,
        maximum_critical_failures: int = 0,
        maximum_human_review_rate: float = 20.0,
    ):
        results = [self.run_case(case) for case in cases]

        test_cases = [
            TestCase(
                case_id=result.case_id,
                expected_output=str(
                    next(
                        case.expected_output
                        for case in cases
                        if case.case_id == result.case_id
                    )
                ),
                actual_output=str(result.actual_output),
                success=result.success,
                latency_ms=result.latency_ms,
                tool_error=result.tool_error,
                critical=result.critical,
                human_review_required=result.human_review_required,
            )
            for result in results
        ]

        workflow = Workflow(
            name=workflow_name,
            description="Executed agent qualification",
            target_reliability=target_reliability,
            maximum_critical_failures=maximum_critical_failures,
            maximum_human_review_rate=maximum_human_review_rate,
            test_cases=test_cases,
        )

        return qualify_workflow(workflow)