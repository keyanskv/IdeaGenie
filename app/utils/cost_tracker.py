from typing import Dict
from app.config import MODELS

class CostTracker:
    def __init__(self):
        self.total_cost = 0.0
        self.model_usage: Dict[str, float] = {}
        self.model_tokens: Dict[str, Dict[str, int]] = {}

    def track_usage(self, model_id: str, input_tokens: int, output_tokens: int):
        if model_id not in MODELS:
            # Fallback for models not in explicit config (though should be there)
            self._record_raw(model_id, input_tokens, output_tokens, 0.0)
            return

        config = MODELS[model_id]
        cost = (input_tokens / 1000 * config.cost_per_1k_tokens_input) + \
               (output_tokens / 1000 * config.cost_per_1k_tokens_output)
        
        self.total_cost += cost
        self.model_usage[model_id] = self.model_usage.get(model_id, 0.0) + cost
        self._record_raw(model_id, input_tokens, output_tokens, cost)

    def _record_raw(self, model_id: str, input_tokens: int, output_tokens: int, cost: float):
        if model_id not in self.model_tokens:
            self.model_tokens[model_id] = {"input": 0, "output": 0, "cost": 0.0}
        
        self.model_tokens[model_id]["input"] += input_tokens
        self.model_tokens[model_id]["output"] += output_tokens
        self.model_tokens[model_id]["cost"] += cost

    def get_summary(self):
        return {
            "total_cost": self.total_cost,
            "breakdown": self.model_usage
        }

    def get_detailed_stats(self):
        return {
            "total_cost": self.total_cost,
            "models": self.model_tokens
        }

cost_tracker = CostTracker()
