from typing import Dict
from app.config import MODELS

class CostTracker:
    def __init__(self):
        self.total_cost = 0.0
        self.model_usage: Dict[str, float] = {}

    def track_usage(self, model_id: str, input_tokens: int, output_tokens: int):
        if model_id not in MODELS:
            return

        config = MODELS[model_id]
        cost = (input_tokens / 1000 * config.cost_per_1k_tokens_input) + \
               (output_tokens / 1000 * config.cost_per_1k_tokens_output)
        
        self.total_cost += cost
        self.model_usage[model_id] = self.model_usage.get(model_id, 0.0) + cost

    def get_summary(self):
        return {
            "total_cost": self.total_cost,
            "breakdown": self.model_usage
        }

cost_tracker = CostTracker()
