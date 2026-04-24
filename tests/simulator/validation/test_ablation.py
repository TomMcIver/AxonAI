"""Tests for B12 ablation study."""

from __future__ import annotations

import pytest

from ml.simulator.loop.explanation_style import CONCISE_ANSWER, CONTRAST_WITH_MISCONCEPTION
from ml.simulator.validation.ablation import (
    ALL_CONDITIONS,
    CONDITION_DEFAULT_STYLE_ONLY,
    CONDITION_FULL,
    CONDITION_NO_DETECTOR,
    CONDITION_NO_SLOW_STUDENTS,
    CONDITION_NO_SUSCEPTIBILITY,
    AblationReport,
    ConditionMetrics,
    run_ablation_study,
    _build_profiles_full,
    _build_profiles_no_susceptibility,
    _build_profiles_no_slow,
)


# ---------------------------------------------------------------------------
# Profile builder tests
# ---------------------------------------------------------------------------

class TestProfileBuilders:
    def test_full_has_slow_students(self):
        profiles = _build_profiles_full(20, 2, seed=0, slow_fraction=0.20)
        slow = [p for p in profiles if p.response_time_lognorm_params[0] > 10]
        assert len(slow) >= 1

    def test_no_susceptibility_profiles_all_empty(self):
        profiles = _build_profiles_no_susceptibility(10, 2, seed=0)
        assert all(len(p.misconception_susceptibility) == 0 for p in profiles)

    def test_no_slow_all_fast(self):
        profiles = _build_profiles_no_slow(10, 2, seed=0)
        import math
        assert all(p.response_time_lognorm_params[0] < math.log(15000) for p in profiles)

    def test_profile_count_respected(self):
        profiles = _build_profiles_full(15, 2, seed=0)
        assert len(profiles) == 15


# ---------------------------------------------------------------------------
# ConditionMetrics / AblationReport tests
# ---------------------------------------------------------------------------

class TestAblationReport:
    def _make_metric(self, condition: str, cwm: float, bkt: float, cor: float) -> ConditionMetrics:
        return ConditionMetrics(
            condition=condition,
            n_attempts=100,
            style_distribution={s: 0 for s in [CONTRAST_WITH_MISCONCEPTION, CONCISE_ANSWER]},
            contrast_with_misconception_rate=cwm,
            bkt_growth=bkt,
            mean_correct_rate=cor,
        )

    def test_get_by_condition(self):
        m = self._make_metric(CONDITION_FULL, 0.3, 0.05, 0.6)
        report = AblationReport(conditions=(m,))
        assert report.get(CONDITION_FULL) is m

    def test_get_missing_returns_none(self):
        report = AblationReport(conditions=())
        assert report.get(CONDITION_FULL) is None

    def test_delta_correct(self):
        base = self._make_metric(CONDITION_FULL, 0.30, 0.05, 0.60)
        ablated = self._make_metric(CONDITION_NO_DETECTOR, 0.10, 0.04, 0.58)
        report = AblationReport(conditions=(base, ablated))
        assert report.delta(CONDITION_NO_DETECTOR, "contrast_with_misconception_rate") == pytest.approx(-0.20)
        assert report.delta(CONDITION_NO_DETECTOR, "bkt_growth") == pytest.approx(-0.01)

    def test_delta_missing_condition_returns_none(self):
        base = self._make_metric(CONDITION_FULL, 0.3, 0.05, 0.6)
        report = AblationReport(conditions=(base,))
        assert report.delta(CONDITION_NO_DETECTOR, "bkt_growth") is None

    def test_to_dict_serializable(self):
        import json
        base = self._make_metric(CONDITION_FULL, 0.3, 0.05, 0.6)
        report = AblationReport(conditions=(base,))
        json.dumps(report.to_dict())


# ---------------------------------------------------------------------------
# run_ablation_study integration tests
# ---------------------------------------------------------------------------

class TestRunAblationStudy:
    # Use minimal params to keep tests fast.
    _PARAMS = dict(n_students=20, n_sessions=4, n_concepts=2, n_items_per_concept=3, seed=0)

    def test_returns_ablation_report(self):
        report = run_ablation_study(**self._PARAMS, conditions=[CONDITION_FULL])
        assert isinstance(report, AblationReport)

    def test_all_conditions_run(self):
        report = run_ablation_study(**self._PARAMS)
        condition_names = {c.condition for c in report.conditions}
        assert condition_names == set(ALL_CONDITIONS)

    def test_full_condition_present(self):
        report = run_ablation_study(**self._PARAMS)
        assert report.get(CONDITION_FULL) is not None

    def test_no_susceptibility_has_zero_cwm_rate(self):
        # Without susceptibility, detector tagged shortcut finds no match → Rule 1 never fires.
        report = run_ablation_study(**self._PARAMS)
        no_susc = report.get(CONDITION_NO_SUSCEPTIBILITY)
        assert no_susc is not None
        assert no_susc.contrast_with_misconception_rate == pytest.approx(0.0)

    def test_no_detector_has_lower_cwm_rate_than_full(self):
        report = run_ablation_study(
            n_students=30, n_sessions=5, n_concepts=2, n_items_per_concept=4, seed=42
        )
        full = report.get(CONDITION_FULL)
        no_det = report.get(CONDITION_NO_DETECTOR)
        assert full is not None and no_det is not None
        assert no_det.contrast_with_misconception_rate <= full.contrast_with_misconception_rate

    def test_default_style_only_all_concise(self):
        report = run_ablation_study(**self._PARAMS, conditions=[CONDITION_DEFAULT_STYLE_ONLY])
        cond = report.get(CONDITION_DEFAULT_STYLE_ONLY)
        assert cond is not None
        dist = cond.style_distribution
        total = sum(dist.values())
        assert dist.get(CONCISE_ANSWER, 0) == total

    def test_no_slow_students_has_no_analogy(self):
        report = run_ablation_study(**self._PARAMS, conditions=[CONDITION_NO_SLOW_STUDENTS])
        cond = report.get(CONDITION_NO_SLOW_STUDENTS)
        assert cond is not None
        from ml.simulator.loop.explanation_style import ANALOGY
        assert cond.style_distribution.get(ANALOGY, 0) == 0

    def test_bkt_growth_positive_for_full(self):
        report = run_ablation_study(**self._PARAMS)
        full = report.get(CONDITION_FULL)
        assert full is not None
        assert full.bkt_growth > 0.0

    def test_n_attempts_positive(self):
        report = run_ablation_study(**self._PARAMS)
        for c in report.conditions:
            assert c.n_attempts > 0

    def test_subset_of_conditions(self):
        report = run_ablation_study(
            **self._PARAMS,
            conditions=[CONDITION_FULL, CONDITION_NO_DETECTOR],
        )
        assert len(report.conditions) == 2

    def test_delta_no_detector_reduces_cwm(self):
        report = run_ablation_study(
            n_students=30, n_sessions=5, n_concepts=2, n_items_per_concept=4, seed=42
        )
        delta = report.delta(CONDITION_NO_DETECTOR, "contrast_with_misconception_rate")
        assert delta is not None
        assert delta <= 0.0  # removing detector can only reduce or keep CWM rate

    def test_condition_metrics_to_dict(self):
        import json
        report = run_ablation_study(**self._PARAMS, conditions=[CONDITION_FULL])
        full = report.get(CONDITION_FULL)
        assert full is not None
        json.dumps(full.to_dict())
