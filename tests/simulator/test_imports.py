"""PR 2 smoke tests — every simulator module imports cleanly.

Later PRs add behavioural tests per module; this file guards against
accidental circular imports or syntax errors in the skeleton.
"""

import importlib

import pytest

SIMULATOR_MODULES = [
    "ml.simulator",
    "ml.simulator.config",
    "ml.simulator.cli",
    "ml.simulator.psychometrics",
    "ml.simulator.psychometrics.irt_2pl",
    "ml.simulator.psychometrics.bkt",
    "ml.simulator.psychometrics.elo",
    "ml.simulator.psychometrics.hlr",
    "ml.simulator.data",
    "ml.simulator.data.assistments_loader",
    "ml.simulator.data.eedi_misconceptions_loader",
    "ml.simulator.data.map_loader",
    "ml.simulator.data.concept_graph",
    "ml.simulator.data.item_bank",
    "ml.simulator.calibration",
    "ml.simulator.calibration.fit_2pl",
    "ml.simulator.calibration.fit_bkt",
    "ml.simulator.calibration.priors",
    "ml.simulator.student",
    "ml.simulator.student.profile",
    "ml.simulator.student.generator",
    "ml.simulator.student.dynamics",
    "ml.simulator.loop",
    "ml.simulator.loop.teach",
    "ml.simulator.loop.revise",
    "ml.simulator.loop.quiz",
    "ml.simulator.loop.runner",
    "ml.simulator.io",
    "ml.simulator.io.postgres_writer",
    "ml.simulator.io.local_writer",
]


@pytest.mark.parametrize("module_name", SIMULATOR_MODULES)
def test_module_imports(module_name: str) -> None:
    importlib.import_module(module_name)
