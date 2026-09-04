from pathlib import Path
import csv
import io
import json
import os

from fastapi import FastAPI, HTTPException, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse

from .models import Workflow
from .engine import qualify_workflow


BASE_DIR = Path(__file__).resolve().parent.parent
STATIC_DIR = BASE_DIR / "static"


app = FastAPI(
    title="AI Workflow Qualification",
    version="1.0.0",
    description="Deployment qualification engine for AI workflows.",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
def root():
    return FileResponse(
        STATIC_DIR / "index.html",
        media_type="text/html",
    )


@app.get("/api/health")
def health():
    return {
        "status": "ok",
        "service": "AI Workflow Qualification",
        "version": "1.0.0",
    }


@app.get("/api/demo")
def demo():
    workflow = Workflow(
        name="Customer Refund Agent",
        description="AI agent responsible for processing customer refund requests.",
        target_reliability=95,
        maximum_critical_failures=0,
        maximum_human_review_rate=20,
        test_cases=[
            {
                "case_id": "REF-001",
                "expected_output": "Approve refund",
                "actual_output": "Approve refund",
                "success": True,
                "latency_ms": 1200,
                "tool_error": False,
                "critical": False,
                "human_review_required": False,
                "estimated_cost_usd": 0.03,
            },
            {
                "case_id": "REF-002",
                "expected_output": "Reject refund",
                "actual_output": "Reject refund",
                "success": True,
                "latency_ms": 1400,
                "tool_error": False,
                "critical": False,
                "human_review_required": False,
                "estimated_cost_usd": 0.03,
            },
            {
                "case_id": "REF-003",
                "expected_output": "Escalate",
                "actual_output": "Escalate",
                "success": True,
                "latency_ms": 1700,
                "tool_error": False,
                "critical": False,
                "human_review_required": True,
                "estimated_cost_usd": 0.04,
            },
            {
                "case_id": "REF-004",
                "expected_output": "Reject refund",
                "actual_output": "Approve refund",
                "success": False,
                "latency_ms": 2100,
                "tool_error": False,
                "critical": True,
                "human_review_required": False,
                "estimated_cost_usd": 0.03,
            },
        ],
    )

    return qualify_workflow(workflow)


@app.post("/api/qualify")
def qualify(workflow: Workflow):
    return qualify_workflow(workflow)


@app.post("/api/qualify/json")
async def qualify_json(file: UploadFile = File(...)):
    if not file.filename or not file.filename.lower().endswith(".json"):
        raise HTTPException(
            status_code=400,
            detail="Upload a .json file.",
        )

    raw = await file.read()

    try:
        data = json.loads(raw.decode("utf-8"))
        workflow = Workflow.model_validate(data)
    except Exception as exc:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid JSON workflow: {exc}",
        )

    return qualify_workflow(workflow)


@app.post("/api/qualify/csv")
async def qualify_csv(file: UploadFile = File(...)):
    if not file.filename or not file.filename.lower().endswith(".csv"):
        raise HTTPException(
            status_code=400,
            detail="Upload a .csv file.",
        )

    raw = await file.read()

    try:
        text = raw.decode("utf-8-sig")
        reader = csv.DictReader(io.StringIO(text))

        cases = []

        for row in reader:
            cases.append(
                {
                    "case_id": row.get("case_id", ""),
                    "expected_output": row.get("expected_output", ""),
                    "actual_output": row.get("actual_output", ""),
                    "success": (
                        row.get("success", "false").strip().lower()
                        == "true"
                    ),
                    "latency_ms": float(row.get("latency_ms", 0) or 0),
                    "tool_error": (
                        row.get("tool_error", "false").strip().lower()
                        == "true"
                    ),
                    "critical": (
                        row.get("critical", "false").strip().lower()
                        == "true"
                    ),
                    "human_review_required": (
                        row.get(
                            "human_review_required",
                            "false",
                        ).strip().lower()
                        == "true"
                    ),
                    "estimated_cost_usd": float(
                        row.get("estimated_cost_usd", 0) or 0
                    ),
                }
            )

        workflow = Workflow(
            name=os.path.splitext(file.filename)[0],
            description="Imported CSV workflow",
            test_cases=cases,
        )

    except Exception as exc:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid CSV: {exc}",
        )

    return qualify_workflow(workflow)
