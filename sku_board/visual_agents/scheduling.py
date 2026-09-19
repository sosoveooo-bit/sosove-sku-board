"""Yield at durable boundaries instead of starting work in the last few seconds."""
from .contracts import digest


class PlanningYield(Exception):
    pass


def required_window(stage, runs, budget):
    floor = {'product': 90, 'strategy': 75, 'direction': 90, 'planning': 140, 'prompts': 75}[stage]
    samples = [r.get('latencyMs', 0) / 1000 for r in runs[-30:]
               if r.get('stage') == stage and r.get('status') == 'complete']
    expected = max(floor, max(samples[-5:], default=0) * 1.3 + 10)
    return min(expected, budget - 10)


def progress_key(state):
    # Ignore transient status, timestamps and failure text: only durable work counts.
    return digest({k: state.get(k) for k in ('productContentHash', 'strategy', 'direction',
                                           'feedbackReview', 'planningDraft', 'planningBatchSize', 'planning', 'prompts')})
