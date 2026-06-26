"""Multi-agent financial intelligence pipeline (independent from solo_agent)."""

__all__ = ["build_multi_agent_pipeline", "run_multi_agent_cli"]


def build_multi_agent_pipeline(*args, **kwargs):
    from src.serving.agent.multi_agent.pipeline import build_multi_agent_pipeline as _build

    return _build(*args, **kwargs)


def run_multi_agent_cli():
    from src.serving.agent.multi_agent.runner import run_multi_agent_cli as _run

    return _run()
