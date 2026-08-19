"""Machine-readable orchestration primitives for publication figure workflows."""

from .contracts import (
    BindingMap,
    ComponentSpec,
    ExportManifest,
    LayoutSpec,
    QAReport,
    ReferenceSet,
    RenderPlan,
    SourceSpec,
    PaletteSpec,
    StyleSpec,
    TargetSpec,
    TaskSpec,
    TypographySpec,
)
from .orchestrator import (
    GateResult,
    Orchestrator,
    StageArtifact,
    StageContext,
    StageRecord,
    WorkflowSession,
    WorkflowStage,
)

__all__ = [
    "BindingMap",
    "ComponentSpec",
    "ExportManifest",
    "GateResult",
    "LayoutSpec",
    "Orchestrator",
    "QAReport",
    "ReferenceSet",
    "RenderPlan",
    "SourceSpec",
    "PaletteSpec",
    "StageArtifact",
    "StageContext",
    "StageRecord",
    "StyleSpec",
    "TargetSpec",
    "TaskSpec",
    "TypographySpec",
    "WorkflowSession",
    "WorkflowStage",
]
