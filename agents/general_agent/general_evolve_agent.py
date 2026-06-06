#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
General Evolve Agent Runner - Refactored to use BasePESRunner.
"""

import argparse
from typing import Any, Dict, List, Tuple, Type

from agents.general_agent.evaluator import GeneralEvaluator
from agents.general_agent.executor import GeneralExecuteAgent
from agents.general_agent.planner import GeneralPlanAgent
from agents.general_agent.summary import GeneralSummaryAgent
from loongflow.framework.pes import Worker
from loongflow.framework.pes.base_runner import BasePESRunner
from loongflow.framework.pes.context import EvolveChainConfig


class GeneralPESAgent(BasePESRunner):
    """
    General Evolve Agent runner for flexible general-purpose tasks.

    Extends BasePESRunner with:
    - General-purpose task support
    """

    def _add_custom_args(self, parser: argparse.ArgumentParser) -> None:
        """Add general-agent specific CLI arguments."""
        pass

    def _merge_custom_configs(
        self, args: argparse.Namespace, config: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Handle general-agent specific config merging."""
        return config

    def _get_process_name(self) -> str:
        return "General PES Agent"

    def _get_worker_registrations(
        self,
    ) -> Tuple[
        List[Tuple[str, Type[Worker]]],
        List[Tuple[str, Type[Worker]]],
        List[Tuple[str, Type[Worker]]],
    ]:
        """Register General agent workers."""
        planners = [("general_planner", GeneralPlanAgent)]
        executors = [("general_executor", GeneralExecuteAgent)]
        summarizers = [("general_summarizer", GeneralSummaryAgent)]
        return planners, executors, summarizers

    def _create_evaluator(self, config: EvolveChainConfig):
        return GeneralEvaluator(config.evolve.evaluator)


if __name__ == "__main__":
    runner = GeneralPESAgent()
    runner.start()
