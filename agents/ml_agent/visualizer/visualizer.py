#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Flask web server for ML Agent task visualizer.

Provides real-time monitoring of ML Agent tasks, including:
- Pipeline stage progress (EDA, Load Data, Splitter, Preprocess, Train, Ensemble, Workflow)
- Per-stage evaluation results (score, status, summary)
- Evocoder attempt tracking (attempt N/M per stage)
- LLM-generated source code for each stage
- Agent log streaming
"""

from __future__ import annotations

import argparse
import json
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from flask import Flask, jsonify, send_from_directory

BASE_DIR = Path(__file__).parent.parent.parent.parent

ML_STAGES = [
    {"id": "eda", "label": "EDA", "icon": "chart"},
    {"id": "load_data", "label": "Load Data", "icon": "download"},
    {"id": "get_splitter", "label": "Splitter", "icon": "scissors"},
    {"id": "preprocess", "label": "Preprocess", "icon": "filter"},
    {"id": "train_and_predict", "label": "Train & Predict", "icon": "cpu"},
    {"id": "ensemble", "label": "Ensemble", "icon": "layers"},
    {"id": "workflow", "label": "Workflow", "icon": "play"},
]

STAGE_ORDER = [s["id"] for s in ML_STAGES]
STAGE_INFO = {s["id"]: s for s in ML_STAGES}


class MLAgentService:
    """Service for loading and managing ML Agent task data."""

    def __init__(self, output_dirs, log_file=None):
        self.output_dirs = [Path(d).resolve() for d in output_dirs if Path(d).exists()]
        self.log_file = Path(log_file).resolve() if log_file else None

    def list_runs(self):
        """List all ML agent runs across output directories."""
        runs = []
        for out_dir in self.output_dirs:
            for item in out_dir.iterdir():
                if not item.is_dir():
                    continue
                iter_dirs = [d for d in item.iterdir() if d.is_dir() and d.name.isdigit()]
                if not iter_dirs:
                    continue
                run_info = self._get_run_info(item)
                if run_info:
                    runs.append(run_info)
        runs.sort(key=lambda x: x.get("started_at", ""), reverse=True)
        return runs

    def get_run_detail(self, run_id):
        run_path = self._find_run_path(run_id)
        if not run_path:
            raise ValueError(f"Run not found: {run_id}")
        iterations = self._scan_iterations(run_path)
        stages = self._scan_stages(run_path, iterations)
        logs = self._read_log_tail(200)
        return {
            "run_id": run_id,
            "run_path": str(run_path),
            "iterations": iterations,
            "stages": stages,
            "logs": logs,
        }

    def get_stage_detail(self, run_id, stage_id):
        run_path = self._find_run_path(run_id)
        if not run_path:
            raise ValueError(f"Run not found: {run_id}")
        result = {"stage_id": stage_id, "stage_label": STAGE_INFO.get(stage_id, {}).get("label", stage_id), "evals": [], "plan": None}
        for iter_dir in sorted([d for d in run_path.iterdir() if d.is_dir() and d.name.isdigit()], key=lambda d: int(d.name)):
            evocoder_dir = iter_dir / "evocoder" / stage_id
            if not evocoder_dir.exists():
                continue
            for eval_dir in sorted(evocoder_dir.iterdir()):
                if not eval_dir.is_dir() or not eval_dir.name.startswith("eval_"):
                    continue
                eval_data = self._read_eval_result(eval_dir)
                eval_data["iteration"] = int(iter_dir.name)
                eval_data["eval_id"] = eval_dir.name
                result["evals"].append(eval_data)
        plan_file = run_path / "1" / "planner" / "best_plan.txt"
        if plan_file.exists():
            try:
                plan_data = json.loads(plan_file.read_text(encoding="utf-8"))
                if stage_id in plan_data:
                    result["plan"] = plan_data[stage_id]
            except (json.JSONDecodeError, KeyError):
                pass
        return result

    def get_file_content(self, run_id, iter_num, stage_id, eval_id, filename):
        run_path = self._find_run_path(run_id)
        if not run_path:
            raise ValueError(f"Run not found: {run_id}")
        file_path = run_path / str(iter_num) / "evocoder" / stage_id / eval_id / filename
        if not file_path.exists():
            raise ValueError(f"File not found: {filename}")
        try:
            content = file_path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            content = file_path.read_text(encoding="latin-1")
        ext = file_path.suffix.lower()
        lang_map = {".py": "python", ".json": "json", ".yaml": "yaml", ".yml": "yaml", ".md": "markdown", ".txt": "text", ".log": "log", ".sh": "bash"}
        return {"filename": file_path.name, "content": content, "language": lang_map.get(ext, "text"), "path": str(file_path.relative_to(run_path))}

    def get_plan(self, run_id):
        run_path = self._find_run_path(run_id)
        if not run_path:
            raise ValueError(f"Run not found: {run_id}")
        result = {"stages": {}, "strategic_analysis": None}
        iter_dirs = sorted([d for d in run_path.iterdir() if d.is_dir() and d.name.isdigit()], key=lambda d: int(d.name), reverse=True)
        if not iter_dirs:
            return result
        latest = iter_dirs[0]
        plan_file = latest / "planner" / "best_plan.txt"
        if plan_file.exists():
            try:
                result["stages"] = json.loads(plan_file.read_text(encoding="utf-8"))
            except (json.JSONDecodeError, KeyError):
                pass
        sa_file = latest / "planner" / "strategic_analysis.txt"
        if sa_file.exists():
            result["strategic_analysis"] = sa_file.read_text(encoding="utf-8")
        return result

    def _find_run_path(self, run_id):
        for out_dir in self.output_dirs:
            candidate = out_dir / run_id
            if candidate.is_dir():
                return candidate
        return None

    def _get_run_info(self, run_path):
        iter_dirs = sorted([d for d in run_path.iterdir() if d.is_dir() and d.name.isdigit()], key=lambda d: int(d.name))
        if not iter_dirs:
            return None
        latest = iter_dirs[-1]
        current_iter = int(latest.name)
        completed_stages = []
        active_stage = None
        for stage_id in STAGE_ORDER:
            evocoder_dir = latest / "evocoder" / stage_id
            if evocoder_dir.exists():
                eval_dirs = [d for d in evocoder_dir.iterdir() if d.is_dir() and d.name.startswith("eval_")]
                successes = sum(1 for d in eval_dirs if self._read_eval_status(d) == "success")
                if successes > 0:
                    completed_stages.append(stage_id)
                elif eval_dirs:
                    active_stage = stage_id
                    break
                else:
                    active_stage = stage_id
                    break
            else:
                plan_file = latest / "planner" / "best_plan.txt"
                if plan_file.exists():
                    try:
                        plan_data = json.loads(plan_file.read_text(encoding="utf-8"))
                        if stage_id in plan_data:
                            active_stage = stage_id
                            break
                    except (json.JSONDecodeError, KeyError):
                        pass
        task_name = run_path.name
        started_at = ""
        if self.log_file and self.log_file.exists():
            with open(self.log_file, "r") as f:
                for line in f:
                    if line.startswith("["):
                        try:
                            ts_str = line.split("]")[0].lstrip("[")
                            dt = datetime.strptime(ts_str, "%Y-%m-%d %H:%M:%S,%f")
                            started_at = dt.isoformat()
                        except (ValueError, IndexError):
                            pass
                        break
        return {"run_id": run_path.name, "task_name": task_name, "current_iteration": current_iter, "completed_stages": completed_stages, "active_stage": active_stage, "started_at": started_at}

    def _scan_iterations(self, run_path):
        iterations = []
        for d in sorted([d for d in run_path.iterdir() if d.is_dir() and d.name.isdigit()], key=lambda d: int(d.name)):
            iter_num = int(d.name)
            stages_status = {}
            for stage_id in STAGE_ORDER:
                evd = d / "evocoder" / stage_id
                if evd.exists():
                    eval_dirs = [x for x in evd.iterdir() if x.is_dir() and x.name.startswith("eval_")]
                    successes = sum(1 for x in eval_dirs if self._read_eval_status(x) == "success")
                    failures = sum(1 for x in eval_dirs if self._read_eval_status(x) != "success")
                    stages_status[stage_id] = {"total_attempts": len(eval_dirs), "successes": successes, "failures": failures}
            iterations.append({"iteration": iter_num, "stages": stages_status})
        return iterations

    def _scan_stages(self, run_path, iterations):
        stages = []
        for stage_id in STAGE_ORDER:
            total_attempts = sum(it.get("stages", {}).get(stage_id, {}).get("total_attempts", 0) for it in iterations)
            total_successes = sum(it.get("stages", {}).get(stage_id, {}).get("successes", 0) for it in iterations)
            total_failures = sum(it.get("stages", {}).get(stage_id, {}).get("failures", 0) for it in iterations)
            info = STAGE_INFO[stage_id].copy()
            info.update({"total_attempts": total_attempts, "total_successes": total_successes, "total_failures": total_failures})
            if total_successes > 0:
                info["status"] = "completed"
            elif total_attempts > 0:
                info["status"] = "in_progress"
            else:
                info["status"] = "pending"
            stages.append(info)
        return stages

    def _read_eval_result(self, eval_dir):
        result_file = eval_dir / "evaluation_result.json"
        process_log = eval_dir / "evaluation_process.log"
        ret = {"score": None, "status": "unknown", "summary": "", "files": [], "details": {}}
        if result_file.exists():
            try:
                data = json.loads(result_file.read_text(encoding="utf-8"))
                ret["score"] = data.get("score")
                ret["status"] = data.get("status")
                ret["summary"] = data.get("summary", "")
            except (json.JSONDecodeError, KeyError):
                pass
        ret["files"] = [f.name for f in eval_dir.iterdir() if f.is_file() and f.suffix in (".py", ".json", ".log")]
        # Parse process_log for live details (fold AUCs, epochs, etc.)
        if process_log.exists():
            try:
                log_text = process_log.read_text(encoding="utf-8")
                folds = re.findall(r"Fold (\d+) Validation AUC:\s*([\d.]+)", log_text)
                epochs = re.findall(r"Epoch (\d+)/\d+ \| Train Loss:\s*([\d.]+) \| Val AUC:\s*([\d.]+)", log_text)
                if folds:
                    ret["details"]["folds"] = [{"fold": int(f[0]), "auc": float(f[1])} for f in folds]
                if epochs:
                    ret["details"]["epochs"] = [{"epoch": int(e[0]), "train_loss": float(e[1]), "val_auc": float(e[2])} for e in epochs]
                if "Pipeline finished" in log_text:
                    ret["details"]["pipeline_finished"] = True
                oof = re.findall(r"OOF coverage:\s*([\d.]+)", log_text)
                cv = re.findall(r"Mean CV AUC:\s*([\d.]+)", log_text)
                if oof:
                    ret["details"]["oof_coverage"] = float(oof[-1])
                if cv:
                    ret["details"]["mean_cv_auc"] = float(cv[-1])
            except Exception:
                pass
        return ret

    def _read_eval_status(self, eval_dir):
        result_file = eval_dir / "evaluation_result.json"
        if result_file.exists():
            try:
                return json.loads(result_file.read_text(encoding="utf-8")).get("status", "unknown")
            except (json.JSONDecodeError, KeyError):
                pass
        return "unknown"

    def _read_log_tail(self, lines=200):
        if not self.log_file or not self.log_file.exists():
            return []
        with open(self.log_file, "r") as f:
            all_lines = f.readlines()
        return [l.rstrip("\n") for l in all_lines[-lines:]]


app = Flask(__name__, static_folder=str(BASE_DIR / "agents/ml_agent/visualizer/static"))
service = None


@app.route("/")
def index():
    return send_from_directory(app.static_folder, "index.html")


@app.route("/api/runs")
def api_list_runs():
    try:
        runs = service.list_runs()
        return jsonify({"success": True, "runs": runs})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@app.route("/api/runs/<run_id>")
def api_get_run(run_id):
    try:
        detail = service.get_run_detail(run_id)
        return jsonify({"success": True, "run": detail})
    except ValueError as e:
        return jsonify({"success": False, "error": str(e)}), 404
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@app.route("/api/runs/<run_id>/stages/<stage_id>")
def api_get_stage(run_id, stage_id):
    try:
        detail = service.get_stage_detail(run_id, stage_id)
        return jsonify({"success": True, "stage": detail})
    except ValueError as e:
        return jsonify({"success": False, "error": str(e)}), 404
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@app.route("/api/runs/<run_id>/plan")
def api_get_plan(run_id):
    try:
        plan = service.get_plan(run_id)
        return jsonify({"success": True, "plan": plan})
    except ValueError as e:
        return jsonify({"success": False, "error": str(e)}), 404
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@app.route("/api/runs/<run_id>/iterations/<int:iter_num>/stages/<stage_id>/evals/<eval_id>/files/<path:filename>")
def api_get_file(run_id, iter_num, stage_id, eval_id, filename):
    try:
        file_data = service.get_file_content(run_id, iter_num, stage_id, eval_id, filename)
        return jsonify({"success": True, "file": file_data})
    except ValueError as e:
        return jsonify({"success": False, "error": str(e)}), 404
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


def main():
    parser = argparse.ArgumentParser(description="ML Agent Visualizer")
    parser.add_argument("--output", "-o", type=str, action="append", default=[], help="Output directory path (repeatable)")
    parser.add_argument("--log-file", "-l", type=str, default=None, help="Path to evolux.log")
    parser.add_argument("--port", "-p", type=int, default=8081, help="Server port")
    parser.add_argument("--host", type=str, default="127.0.0.1", help="Server host")
    args = parser.parse_args()
    if not args.output:
        args.output = [str(BASE_DIR / "output")]
    global service
    service = MLAgentService(args.output, args.log_file)
    print("=" * 60)
    print("ML Agent Visualizer")
    print("=" * 60)
    print(f"Output dirs: {args.output}")
    if args.log_file:
        print(f"Log file: {args.log_file}")
    print(f"Server: http://{args.host}:{args.port}")
    print("=" * 60)
    app.run(host=args.host, port=args.port, debug=False)


if __name__ == "__main__":
    main()
