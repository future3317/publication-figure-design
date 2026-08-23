"""Unified ``pfd`` command line entrypoint."""

from __future__ import annotations

import argparse
import importlib.util
import json
import sys
from pathlib import Path
from typing import Any

from .contracts import TaskSpec
from .orchestrator import Orchestrator, WorkflowSession, build_runtime_orchestrator


ROOT = Path(__file__).resolve().parents[2]


def _load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _load_maintenance_module(name: str) -> Any:
    path = ROOT / "scripts" / f"{name}.py"
    spec = importlib.util.spec_from_file_location(f"publication_figure_design.maintenance.{name}", path)
    if spec is None or spec.loader is None:
        raise ImportError(f"cannot load maintenance module {name}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _run_task(args: argparse.Namespace) -> int:
    if args.resume:
        session = WorkflowSession.load(args.task_spec)
        orchestrator = build_runtime_orchestrator()
    else:
        task = TaskSpec.from_dict(_load_json(args.task_spec))
        orchestrator = build_runtime_orchestrator()
        session = orchestrator.start(task)
    orchestrator.run(session)
    output = Path(args.output or args.task_spec)
    session.save(output)
    print(json.dumps(session.to_dict(), indent=2, ensure_ascii=False))
    return 0 if session.status == "complete" else 2


def _reference_command(args: argparse.Namespace) -> int:
    library = _load_maintenance_module("reference_library").ReferenceLibrary(ROOT)
    if args.reference_action == "ingest":
        metadata = json.loads(args.metadata) if args.metadata else {}
        reference = library.ingest(Path(args.image), args.figure_type, metadata_override=metadata)
        print(json.dumps(reference.metadata, indent=2, ensure_ascii=False))
        return 0
    if args.reference_action == "analyze":
        analyze_image = _load_maintenance_module("reference_image_analysis").analyze_image

        reference = library.get(args.reference_id)
        if reference is None:
            raise SystemExit(f"Unknown reference id: {args.reference_id}")
        image = ROOT / reference.metadata["image_path"]
        output = Path(args.output or (ROOT / reference.metadata["figure_card_path"]))
        output.parent.mkdir(parents=True, exist_ok=True)
        card = analyze_image(image, output=output, figure_type=reference.metadata.get("figure_type"))
        print(json.dumps(card, indent=2, ensure_ascii=False))
        return 0
    if args.reference_action == "dna":
        dna = library.analyze_dna(args.reference_id)
        print(json.dumps(dna, indent=2, ensure_ascii=False))
        return 0
    if args.reference_action == "review":
        review = _load_json(Path(args.review_json))
        library.review(args.reference_id, float(review.pop("aesthetic_rating")), review)
        library.rebuild_registry()
        print(f"reviewed {args.reference_id}")
        return 0
    if args.reference_action == "benchmark":
        canary = _load_json(Path(args.canary_json))
        library.benchmark_reference(args.reference_id, canary)
        library.rebuild_registry()
        print(f"benchmarked {args.reference_id}")
        return 0
    if args.reference_action == "promote":
        evidence = _load_json(Path(args.evidence_json))
        library.promote_reference(args.reference_id, evidence)
        library.rebuild_registry()
        print(f"promoted {args.reference_id}")
        return 0
    raise SystemExit(f"Unknown reference action: {args.reference_action}")


def _index_command(_: argparse.Namespace) -> int:
    print(json.dumps(_load_maintenance_module("build_reference_indexes").build_indexes(ROOT), indent=2, ensure_ascii=False))
    return 0


def _eval_command(args: argparse.Namespace) -> int:
    import subprocess
    mode = args.eval_mode or "full"
    if mode == "quick":
        commands = [[sys.executable, "-m", "unittest", "discover", "-s", str(ROOT / "scripts"), "-p", "test_*.py"]]
    elif mode == "visual":
        commands = [[sys.executable, str(ROOT / "scripts" / "evaluate_benchmark.py")], [sys.executable, str(ROOT / "scripts" / "evaluate_holdout.py")]]
    elif mode in {"full", "release"}:
        commands = [[sys.executable, str(ROOT / "scripts" / "ci_gate.py")]] if mode == "release" else [[sys.executable, "-m", "unittest", "discover", "-s", str(ROOT / "scripts"), "-p", "test_*.py"], [sys.executable, str(ROOT / "scripts" / "evaluate_benchmark.py")]]
    else:
        raise SystemExit(f"Unknown eval mode: {mode}")
    return max(subprocess.run(command, cwd=ROOT).returncode for command in commands)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="pfd", description="Publication Figure Design orchestrator")
    sub = parser.add_subparsers(dest="command", required=True)

    run = sub.add_parser("run", help="run or resume a persisted task-spec/session")
    run.add_argument("task_spec", type=Path)
    run.add_argument("--output", type=Path)
    run.add_argument("--resume", action="store_true")
    run.set_defaults(handler=_run_task)

    reference = sub.add_parser("reference", help="reference-library intake and review")
    ref_sub = reference.add_subparsers(dest="reference_action", required=True)
    ingest = ref_sub.add_parser("ingest")
    ingest.add_argument("image")
    ingest.add_argument("figure_type")
    ingest.add_argument("--metadata")
    ingest.set_defaults(handler=_reference_command)
    analyze = ref_sub.add_parser("analyze")
    analyze.add_argument("reference_id")
    analyze.add_argument("--output")
    analyze.set_defaults(handler=_reference_command)
    dna = ref_sub.add_parser("dna")
    dna.add_argument("reference_id")
    dna.set_defaults(handler=_reference_command)
    review = ref_sub.add_parser("review")
    review.add_argument("reference_id")
    review.add_argument("review_json")
    review.set_defaults(handler=_reference_command)
    benchmark = ref_sub.add_parser("benchmark")
    benchmark.add_argument("reference_id")
    benchmark.add_argument("canary_json")
    benchmark.set_defaults(handler=_reference_command)
    promote = ref_sub.add_parser("promote")
    promote.add_argument("reference_id")
    promote.add_argument("evidence_json")
    promote.set_defaults(handler=_reference_command)

    index = sub.add_parser("index", help="build retrieval indexes")
    index_sub = index.add_subparsers(dest="index_action", required=True)
    build = index_sub.add_parser("build")
    build.set_defaults(handler=_index_command)

    evaluation = sub.add_parser("eval", help="run quick, full, visual, or release evaluation")
    evaluation.add_argument("eval_mode", nargs="?", choices=["quick", "full", "visual", "release"], default="full")
    evaluation.set_defaults(handler=_eval_command)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    return int(args.handler(args))


if __name__ == "__main__":
    raise SystemExit(main())
