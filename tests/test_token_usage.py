import pytest

from backend.services.token_usage import (
    TokenUsageTracker,
    gemini_2_5_flash_lite_pricing,
)


class FakeAgent:
    def __init__(self, usages):
        self.usages = list(usages)

    def get_token_usage(self):
        return self.usages.pop(0)


def test_token_usage_tracker_accumulates_steps():
    tracker = TokenUsageTracker()
    agent = FakeAgent(
        [
            {"prompt_tokens": 10, "output_tokens": 2, "total_tokens": 12},
            {
                "prompt_tokens": 20,
                "output_tokens": 4,
                "thoughts_tokens": 1,
                "total_tokens": 25,
            },
        ]
    )

    tracker.capture("Reescrita", agent)
    tracker.capture("Resposta", agent)

    summary = tracker.summary()

    assert summary == {
        "prompt_tokens": 30,
        "output_tokens": 6,
        "thoughts_tokens": 1,
        "total_tokens": 37,
        "estimated_cost_usd": summary["estimated_cost_usd"],
        "estimated_cost_brl": summary["estimated_cost_brl"],
        "pricing": {
                "input_usd_per_1m": 0.75,
                "output_usd_per_1m": 4.50,
                "usd_to_brl": 5.0,
                "formula": "(prompt_tokens / 1_000_000 * input_usd_per_1m) + (output_tokens / 1_000_000 * output_usd_per_1m)",
            },
        "steps": [
            {
                "step": "Reescrita",
                "prompt_tokens": 10,
                "output_tokens": 2,
                "thoughts_tokens": 0,
                "total_tokens": 12,
            },
            {
                "step": "Resposta",
                "prompt_tokens": 20,
                "output_tokens": 4,
                "thoughts_tokens": 1,
                "total_tokens": 25,
            },
        ],
    }
    assert summary["estimated_cost_usd"] == pytest.approx(0.0000495)
    assert summary["estimated_cost_brl"] == pytest.approx(0.0002475)


def test_token_usage_tracker_uses_gemini_pricing_when_configured():
    tracker = TokenUsageTracker(**gemini_2_5_flash_lite_pricing())

    tracker.add_usage(
        "Gemini",
        {"prompt_tokens": 1000, "output_tokens": 500, "total_tokens": 1500},
    )

    summary = tracker.summary()

    assert summary["pricing"]["input_usd_per_1m"] == 0.10
    assert summary["pricing"]["output_usd_per_1m"] == 0.40
    assert summary["estimated_cost_usd"] == pytest.approx(0.0003)
    assert summary["estimated_cost_brl"] == pytest.approx(0.0015)


def test_token_usage_tracker_ignores_agents_without_usage():
    tracker = TokenUsageTracker()

    tracker.capture("Etapa", object())

    assert tracker.summary() == {
        "prompt_tokens": 0,
        "output_tokens": 0,
        "thoughts_tokens": 0,
        "total_tokens": 0,
        "estimated_cost_usd": 0.0,
        "estimated_cost_brl": 0.0,
        "pricing": {
            "input_usd_per_1m": 0.75,
            "output_usd_per_1m": 4.50,
            "usd_to_brl": 5.0,
            "formula": "(prompt_tokens / 1_000_000 * input_usd_per_1m) + (output_tokens / 1_000_000 * output_usd_per_1m)",
        },
        "steps": [],
    }
