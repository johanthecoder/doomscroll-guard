# tests/test_engine.py
import time
import pytest
from unittest.mock import MagicMock, patch
from interventions.engine import InterventionEngine, EngineState
from config import Config


def make_engine(config=None):
    if config is None:
        config = Config(grace_seconds=2, exit_grace_seconds=1, nudge_seconds=3, cooldown_seconds=2)
    nudge = MagicMock()
    aggro = MagicMock()
    engine = InterventionEngine(config, on_nudge=nudge, on_aggro=aggro)
    return engine, nudge, aggro


def test_starts_clean():
    engine, _, _ = make_engine()
    assert engine.state == EngineState.CLEAN


def test_violation_transitions_to_grace():
    engine, _, _ = make_engine()
    engine.report_violation()
    engine._tick()
    assert engine.state == EngineState.GRACE


def test_grace_to_nudge_after_grace_seconds():
    engine, nudge, _ = make_engine()
    engine.report_violation()
    engine._state_entered_at -= 3  # fast-forward past grace_seconds=2
    engine._tick()
    assert engine.state == EngineState.NUDGED
    nudge.assert_called_once()


def test_clears_to_clean_when_violation_stops():
    engine, _, _ = make_engine()
    engine.report_violation()
    engine._tick()
    assert engine.state == EngineState.GRACE
    # Simulate violation stopping and exit grace passing
    engine._last_violation_at -= 2  # past exit_grace_seconds=1
    engine._tick()
    assert engine.state == EngineState.CLEAN


def test_nudged_to_aggro_after_nudge_seconds():
    engine, nudge, aggro = make_engine()
    engine.report_violation()
    engine._state_entered_at -= 3
    engine._tick()
    assert engine.state == EngineState.NUDGED
    engine.report_violation()
    engine._state_entered_at -= 4  # past nudge_seconds=3
    engine._tick()
    assert engine.state == EngineState.AGGRO
    aggro.assert_called_once()


def test_aggro_to_cooldown_to_clean():
    engine, _, aggro = make_engine()
    engine.report_violation()
    engine._state_entered_at -= 3
    engine._tick()
    engine.report_violation()
    engine._state_entered_at -= 4
    engine._tick()
    assert engine.state == EngineState.AGGRO
    engine._tick()
    assert engine.state == EngineState.COOLDOWN
    engine._state_entered_at -= 3  # past cooldown_seconds=2
    engine._tick()
    assert engine.state == EngineState.CLEAN
