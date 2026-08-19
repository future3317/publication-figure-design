"""A small explicit state machine for figure-design tasks.

Handlers are intentionally ordinary callables.  Each handler receives a
serialisable :class:`StageContext` and returns a JSON-compatible value (or one
of the contracts).  This keeps the orchestration boundary usable by existing
scripts while making every transition inspectable and resumable.
"""

from __future__ import annotations

import hashlib
import json
import uuid
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import Any, Callable, Dict, Iterable, List, Mapping, Optional, Union

from ..contracts.models import Contract, TaskSpec


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _canonical_hash(value: Any) -> str:
    encoded = json.dumps(_jsonable(value), sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _current_index_version() -> str:
    root = Path(__file__).resolve().parents[3]
    try:
        payload = json.loads((root / "indexes" / "semantic.json").read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return "unknown"
    return str(payload.get("provenance", {}).get("index_version") or payload.get("model_version") or "unknown")


def _jsonable(value: Any) -> Any:
    if isinstance(value, Enum):
        return value.value
    if isinstance(value, Contract):
        return value.to_dict()
    if isinstance(value, Path):
        return str(value)
    if isinstance(value, Mapping):
        return {str(k): _jsonable(v) for k, v in value.items()}
    if isinstance(value, (tuple, list, set)):
        return [_jsonable(v) for v in value]
    return value


class WorkflowStage(str, Enum):
    ROUTE = "Route"
    INTAKE = "Intake"
    REFERENCE_RETRIEVAL = "Reference Retrieval"
    REFERENCE_INSPECTION = "Reference Inspection"
    DESIGN_SPEC = "Design Spec"
    BINDING = "Binding"
    RENDER = "Render"
    COMPARE = "Compare"
    CRITIQUE = "Critique"
    REPAIR = "Repair"
    QA = "QA"
    EXPORT = "Export"


STAGE_ORDER: tuple[WorkflowStage, ...] = tuple(WorkflowStage)


@dataclass
class GateResult:
    passed: bool
    reason: str = ""
    details: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return _jsonable(asdict(self))


@dataclass
class StageArtifact:
    stage: str
    payload: Any
    schema_version: str = "1.0"
    created_at: str = field(default_factory=_now)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "stage": self.stage,
            "payload": _jsonable(self.payload),
            "created_at": self.created_at,
        }

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> "StageArtifact":
        return cls(
            stage=str(data["stage"]),
            payload=data.get("payload"),
            schema_version=str(data.get("schema_version", "1.0")),
            created_at=str(data.get("created_at", _now())),
        )


@dataclass
class StageRecord:
    stage: str
    status: str
    attempt: int
    input: Dict[str, Any] = field(default_factory=dict)
    output: Any = None
    gate: Optional[Dict[str, Any]] = None
    error: str = ""
    started_at: str = field(default_factory=_now)
    finished_at: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return _jsonable(asdict(self))


@dataclass
class StageContext:
    session_id: str
    stage: str
    task: Dict[str, Any]
    contracts: Dict[str, Any]
    artifacts: Dict[str, Dict[str, Any]]
    previous_artifact: Optional[Dict[str, Any]] = None
    telemetry: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return _jsonable(asdict(self))


@dataclass
class WorkflowSession:
    session_id: str
    task: Dict[str, Any]
    contracts: Dict[str, Any] = field(default_factory=dict)
    current_stage: Optional[str] = None
    status: str = "ready"
    artifacts: Dict[str, Dict[str, Any]] = field(default_factory=dict)
    history: List[Dict[str, Any]] = field(default_factory=list)
    best_so_far: Optional[Dict[str, Any]] = None
    telemetry: Dict[str, Any] = field(default_factory=lambda: {
        "route": "",
        "reference_ids": [],
        "style_spec_version": "",
        "iterations": 0,
        "failed_gates": [],
        "final_scores": {},
    })

    def to_dict(self) -> Dict[str, Any]:
        return _jsonable(asdict(self))

    def save(self, path: Union[str, Path]) -> Path:
        target = Path(path)
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(json.dumps(self.to_dict(), indent=2, ensure_ascii=False), encoding="utf-8")
        return target

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> "WorkflowSession":
        task = dict(data.get("task", {}))
        telemetry = dict(data.get("telemetry", {}))
        telemetry.setdefault("selected_reference_ids", list(telemetry.get("reference_ids", [])))
        telemetry.setdefault("reference_index_version", str(task.get("metadata", {}).get("reference_index_version", "unknown")))
        telemetry.setdefault("input_hash", _canonical_hash(task))
        telemetry.setdefault("renderer_version", str(task.get("metadata", {}).get("renderer_version", "")))
        telemetry.setdefault("output_hash", "")
        return cls(
            session_id=str(data["session_id"]),
            task=task,
            contracts=dict(data.get("contracts", {})),
            current_stage=data.get("current_stage"),
            status=str(data.get("status", "ready")),
            artifacts=dict(data.get("artifacts", {})),
            history=list(data.get("history", [])),
            best_so_far=data.get("best_so_far"),
            telemetry=telemetry,
        )

    @classmethod
    def load(cls, path: Union[str, Path]) -> "WorkflowSession":
        return cls.from_dict(json.loads(Path(path).read_text(encoding="utf-8")))

    def is_complete(self) -> bool:
        return self.current_stage == WorkflowStage.EXPORT.value and self.status == "complete"


Handler = Callable[[StageContext], Any]
Gate = Callable[[Any], Union[GateResult, bool]]


class Orchestrator:
    """Run the fixed workflow while enforcing gates at every transition."""

    def __init__(
        self,
        handlers: Optional[Mapping[Union[WorkflowStage, str], Handler]] = None,
        gates: Optional[Mapping[Union[WorkflowStage, str], Gate]] = None,
        max_retries: int = 3,
    ) -> None:
        if max_retries < 1:
            raise ValueError("max_retries must be at least 1")
        self.handlers = {self._stage_key(key): value for key, value in (handlers or {}).items()}
        self.gates = {self._stage_key(key): value for key, value in (gates or {}).items()}
        self.max_retries = max_retries

    @staticmethod
    def _stage_key(stage: Union[WorkflowStage, str]) -> str:
        return stage.value if isinstance(stage, WorkflowStage) else str(stage)

    def start(self, task: TaskSpec, contracts: Optional[Iterable[Contract]] = None) -> WorkflowSession:
        if not isinstance(task, TaskSpec):
            raise TypeError("task must be a TaskSpec")
        contract_map = {}
        for contract in contracts or ():
            if not isinstance(contract, Contract):
                raise TypeError("initial contracts must inherit Contract")
            contract_map[contract.contract_name] = contract.to_dict()
        return WorkflowSession(
            session_id=task.task_id or uuid.uuid4().hex,
            task=task.to_dict(),
            contracts=contract_map,
            telemetry={
                "route": "",
                "reference_ids": [],
                "selected_reference_ids": [],
                "reference_index_version": str(task.metadata.get("reference_index_version") or _current_index_version()),
                "input_hash": _canonical_hash(task.to_dict()),
                "renderer_version": str(task.metadata.get("renderer_version", "")),
                "style_spec_version": str(task.metadata.get("style_spec_version", "")),
                "iterations": 0,
                "failed_gates": [],
                "final_scores": {},
                "output_hash": "",
            },
        )

    def resume(self, session: Union[WorkflowSession, Mapping[str, Any], str, Path]) -> WorkflowSession:
        if isinstance(session, WorkflowSession):
            return session
        if isinstance(session, (str, Path)):
            return WorkflowSession.load(session)
        return WorkflowSession.from_dict(session)

    def next_stage(self, session: WorkflowSession) -> Optional[WorkflowStage]:
        if session.current_stage is None:
            return STAGE_ORDER[0]
        try:
            index = [stage.value for stage in STAGE_ORDER].index(session.current_stage)
        except ValueError as exc:
            raise ValueError(f"Unknown current stage {session.current_stage!r}") from exc
        return STAGE_ORDER[index + 1] if index + 1 < len(STAGE_ORDER) else None

    def advance(self, session: WorkflowSession) -> WorkflowSession:
        if session.status in {"blocked", "error"}:
            raise RuntimeError("Session is not runnable; call retry() after fixing the failed stage")
        stage = self.next_stage(session)
        if stage is None:
            session.status = "complete"
            return session
        key = stage.value
        previous = session.artifacts.get(session.current_stage or "")
        context = StageContext(
            session_id=session.session_id,
            stage=key,
            task=session.task,
            contracts=session.contracts,
            artifacts=session.artifacts,
            previous_artifact=previous,
            telemetry=session.telemetry,
        )
        attempt = 1 + sum(
            1 for record in session.history
            if record.get("stage") == key and record.get("status") in {"completed", "gate_failed", "error"}
        )
        if attempt > self.max_retries:
            session.status = "error"
            raise RuntimeError(f"Retry limit exceeded for stage {key}")
        record = StageRecord(stage=key, status="running", attempt=attempt, input=context.to_dict())
        session.history.append(record.to_dict())
        session.telemetry["iterations"] = int(session.telemetry.get("iterations", 0)) + 1
        if not session.telemetry.get("route"):
            session.telemetry["route"] = str(session.task.get("mode", "create"))
        metadata = session.task.get("metadata") or {}
        if isinstance(metadata, Mapping):
            ids = metadata.get("reference_ids") or metadata.get("references") or []
            if isinstance(ids, str):
                ids = [ids]
            if isinstance(ids, list):
                session.telemetry["reference_ids"] = [str(value) for value in ids]
            session.telemetry["style_spec_version"] = str(metadata.get("style_spec_version", session.telemetry.get("style_spec_version", "")))
        try:
            payload = self.handlers.get(key, lambda _: {"status": "completed"})(context)
            gate = self._evaluate_gate(key, payload)
            session.history[-1]["output"] = _jsonable(payload)
            session.history[-1]["gate"] = gate.to_dict()
            session.history[-1]["finished_at"] = _now()
            if not gate.passed:
                session.history[-1]["status"] = "gate_failed"
                failed = session.telemetry.setdefault("failed_gates", [])
                failed.append({"stage": key, "reason": gate.reason})
                session.status = "blocked"
                return session
        except Exception as exc:
            session.history[-1]["status"] = "error"
            session.history[-1]["error"] = str(exc)
            session.history[-1]["finished_at"] = _now()
            session.status = "error"
            return session
        artifact = StageArtifact(stage=key, payload=payload)
        session.artifacts[key] = artifact.to_dict()
        session.current_stage = key
        session.status = "complete" if key == WorkflowStage.EXPORT.value else "ready"
        self._update_best(session, artifact)
        if isinstance(payload, Mapping):
            if key == WorkflowStage.REFERENCE_RETRIEVAL.value:
                reference_set = payload.get("reference_set")
                if isinstance(reference_set, Mapping):
                    selected: list[str] = []
                    for field in ("structure_reference", "style_reference", "annotation_reference", "palette_reference"):
                        value = reference_set.get(field)
                        if value:
                            selected.append(str(value))
                    selected.extend(str(value) for value in reference_set.get("component_references", []) if value)
                    session.telemetry["selected_reference_ids"] = sorted(set(selected))
            if key == WorkflowStage.EXPORT.value:
                output_path = payload.get("figure_path") or payload.get("output_path")
                if output_path:
                    path = Path(str(output_path))
                    if not path.is_absolute():
                        path = Path.cwd() / path
                    if path.is_file():
                        session.telemetry["output_hash"] = hashlib.sha256(path.read_bytes()).hexdigest()
            metrics = payload.get("metrics")
            if isinstance(metrics, Mapping):
                session.telemetry["final_scores"] = _jsonable(dict(metrics))
            elif isinstance(payload.get("score"), (int, float)):
                session.telemetry["final_scores"] = {"score": float(payload["score"])}
        session.history[-1]["status"] = "completed"
        return session

    def run(self, session: WorkflowSession) -> WorkflowSession:
        while session.status not in {"blocked", "error", "complete"}:
            self.advance(session)
        return session

    def retry(self, session: WorkflowSession) -> WorkflowSession:
        if session.status not in {"blocked", "error"}:
            raise RuntimeError("retry() is only valid after a blocked or errored stage")
        session.status = "ready"
        return self.advance(session)

    def rollback(self, session: WorkflowSession, target: Union[WorkflowStage, str]) -> WorkflowSession:
        target_key = self._stage_key(target)
        keys = [stage.value for stage in STAGE_ORDER]
        if target_key not in keys:
            raise ValueError(f"Unknown rollback stage {target_key!r}")
        target_index = keys.index(target_key)
        previous_stage = session.current_stage
        previous_key = keys[target_index - 1] if target_index else None
        for key in keys[target_index:]:
            session.artifacts.pop(key, None)
        session.current_stage = previous_key
        session.status = "ready"
        session.history.append({
            "stage": target_key,
            "status": "rolled_back",
            "attempt": 0,
            "input": {"from": previous_stage, "to": target_key},
            "output": None,
            "gate": None,
            "error": "",
            "started_at": _now(),
            "finished_at": _now(),
        })
        return session

    def _evaluate_gate(self, key: str, payload: Any) -> GateResult:  # type: ignore[no-redef]
        checker = self.gates.get(key)
        if checker is None:
            return GateResult(True, "no gate registered")
        result = checker(payload)
        if isinstance(result, GateResult):
            return result
        return GateResult(bool(result), "gate returned boolean")

    @staticmethod
    def _update_best(session: WorkflowSession, artifact: StageArtifact) -> None:
        payload = artifact.payload.to_dict() if isinstance(artifact.payload, Contract) else artifact.payload
        score = None
        if isinstance(payload, Mapping):
            candidate = payload.get("score")
            if isinstance(candidate, (int, float)):
                score = float(candidate)
            elif isinstance(payload.get("metrics"), Mapping):
                candidate = payload["metrics"].get("score")
                if isinstance(candidate, (int, float)):
                    score = float(candidate)
        if score is None:
            return
        current = session.best_so_far
        if current is None or score > float(current["score"]):
            session.best_so_far = {
                "stage": artifact.stage,
                "score": score,
                "artifact": artifact.to_dict(),
            }
