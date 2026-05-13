from typing import Any


EMPTY_TOKEN_USAGE = {
    "prompt_tokens": 0,
    "output_tokens": 0,
    "thoughts_tokens": 0,
    "total_tokens": 0,
}

GPT_5_4_MINI_INPUT_USD_PER_1M = 0.75
GPT_5_4_MINI_OUTPUT_USD_PER_1M = 4.50
GEMINI_2_5_FLASH_LITE_INPUT_USD_PER_1M = 0.10
GEMINI_2_5_FLASH_LITE_OUTPUT_USD_PER_1M = 0.40
USD_TO_BRL = 5.0


class TokenUsageTracker:
    def __init__(
        self,
        input_usd_per_1m: float = GPT_5_4_MINI_INPUT_USD_PER_1M,
        output_usd_per_1m: float = GPT_5_4_MINI_OUTPUT_USD_PER_1M,
        usd_to_brl: float = USD_TO_BRL,
    ):
        self.total = EMPTY_TOKEN_USAGE.copy()
        self.steps: list[dict[str, Any]] = []
        self.input_usd_per_1m = input_usd_per_1m
        self.output_usd_per_1m = output_usd_per_1m
        self.usd_to_brl = usd_to_brl

    def capture(self, step: str, agent: Any) -> None:
        usage = self._get_usage(agent)
        if usage is None:
            return

        self.add_usage(step=step, usage=usage)

    def add_usage(self, step: str, usage: dict[str, int]) -> None:
        normalized_usage = self._normalize_usage(usage)
        self.steps.append({"step": step, **normalized_usage})

        for key in self.total:
            self.total[key] += normalized_usage[key]

    def summary(self) -> dict[str, Any]:
        cost_usd = self.estimate_cost_usd(
            prompt_tokens=self.total["prompt_tokens"],
            output_tokens=self.total["output_tokens"],
        )
        return {
            **self.total,
            "estimated_cost_usd": cost_usd,
            "estimated_cost_brl": cost_usd * self.usd_to_brl,
            "pricing": {
                "input_usd_per_1m": self.input_usd_per_1m,
                "output_usd_per_1m": self.output_usd_per_1m,
                "usd_to_brl": self.usd_to_brl,
                "formula": (
                    "(prompt_tokens / 1_000_000 * input_usd_per_1m) + "
                    "(output_tokens / 1_000_000 * output_usd_per_1m)"
                ),
            },
            "steps": self.steps,
        }

    def estimate_cost_usd(self, prompt_tokens: int, output_tokens: int) -> float:
        return (prompt_tokens / 1_000_000) * self.input_usd_per_1m + (
            output_tokens / 1_000_000
        ) * self.output_usd_per_1m

    def _get_usage(self, agent: Any) -> dict[str, int] | None:
        get_token_usage = getattr(agent, "get_token_usage", None)
        if not callable(get_token_usage):
            return None

        return get_token_usage()

    def _normalize_usage(self, usage: dict[str, int]) -> dict[str, int]:
        normalized_usage = EMPTY_TOKEN_USAGE.copy()

        for key in normalized_usage:
            value = usage.get(key, 0)
            normalized_usage[key] = value if isinstance(value, int) else 0

        return normalized_usage


def openai_gpt_5_4_mini_pricing() -> dict[str, float]:
    return {
        "input_usd_per_1m": GPT_5_4_MINI_INPUT_USD_PER_1M,
        "output_usd_per_1m": GPT_5_4_MINI_OUTPUT_USD_PER_1M,
        "usd_to_brl": USD_TO_BRL,
    }


def gemini_2_5_flash_lite_pricing() -> dict[str, float]:
    return {
        "input_usd_per_1m": GEMINI_2_5_FLASH_LITE_INPUT_USD_PER_1M,
        "output_usd_per_1m": GEMINI_2_5_FLASH_LITE_OUTPUT_USD_PER_1M,
        "usd_to_brl": USD_TO_BRL,
    }
