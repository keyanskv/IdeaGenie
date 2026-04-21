from typing import List, Dict, Any
from app.models.factory import get_model
from app.agents.router import ModelRouter
from app.memory.manager import ConversationMemory
from app.utils.cost_tracker import cost_tracker
from app.utils.logger import logger

class AIOrchestrator:
    def __init__(self):
        self.memory = ConversationMemory()
        self.current_model_id = "gpt-4o"

    def chat(self, user_input: str, mode: str = "auto") -> Dict[str, Any]:
        if mode == "auto":
            model_id = ModelRouter.route_query(user_input)
        elif mode == "ensemble":
            return self._ensemble_chat(user_input)
        elif mode == "reflection":
            return self._reflection_chat(user_input)
        else:
            model_id = self.current_model_id

        return self._single_model_chat(model_id, user_input)

    def _single_model_chat(self, model_id: str, prompt: str) -> Dict[str, Any]:
        model = get_model(model_id)
        response = model.generate_response(prompt, self.memory.get_history())
        
        if "error" in response:
            return response

        # Track cost
        cost_tracker.track_usage(model_id, response["input_tokens"], response["output_tokens"])
        
        # Update memory
        self.memory.add_message("user", prompt)
        self.memory.add_message("assistant", response["content"])
        
        return response

    def _ensemble_chat(self, prompt: str) -> Dict[str, Any]:
        models_to_use = ["gpt-4o", "claude-3-5-sonnet", "gemini-1.5-flash"]
        responses = []
        
        for mid in models_to_use:
            logger.info(f"Ensemble: Querying {mid}...")
            res = get_model(mid).generate_response(prompt, self.memory.get_history())
            if "error" not in res:
                responses.append(res)
                cost_tracker.track_usage(mid, res["input_tokens"], res["output_tokens"])

        if not responses:
            return {"error": "All models in ensemble failed."}

        # Simple ranking / selection: Choose the longest one as "most detailed" or use a judge
        # For now, let's just return all and let the CLI handle display, 
        # or pick the best one via a judge model.
        best_response = self._rank_responses(prompt, responses)
        
        self.memory.add_message("user", prompt)
        self.memory.add_message("assistant", best_response["content"])
        
        return best_response

    def _rank_responses(self, prompt: str, responses: List[Dict[str, Any]]) -> Dict[str, Any]:
        logger.info("Ranking responses using GPT-4o as judge...")
        judge = get_model("gpt-4o")
        
        ranking_prompt = f"Original Prompt: {prompt}\n\n"
        for i, res in enumerate(responses):
            ranking_prompt += f"Response {i+1} (Model: {res['model']}):\n{res['content']}\n\n"
        
        ranking_prompt += "Evaluate the responses and pick the best one. Return only the index of the best response (e.g., '1')."
        
        judge_res = judge.generate_response(ranking_prompt, [])
        try:
            best_idx = int(judge_res["content"].strip()) - 1
            if 0 <= best_idx < len(responses):
                return responses[best_idx]
        except:
            pass
        
        return responses[0] # Fallback

    def _reflection_chat(self, prompt: str) -> Dict[str, Any]:
        logger.info("Starting reflection loop (Generate -> Critique -> Improve)...")
        model = get_model("gpt-4o")
        
        # 1. Generate
        initial_res = model.generate_response(prompt, self.memory.get_history())
        content = initial_res["content"]
        cost_tracker.track_usage("gpt-4o", initial_res["input_tokens"], initial_res["output_tokens"])

        # 2. Critique
        critique_prompt = f"Critique the following response for accuracy and completeness:\n\n{content}"
        critique_res = model.generate_response(critique_prompt, [])
        critique = critique_res["content"]
        cost_tracker.track_usage("gpt-4o", critique_res["input_tokens"], critique_res["output_tokens"])

        # 3. Improve
        improve_prompt = f"Original Prompt: {prompt}\n\nInitial Response: {content}\n\nCritique: {critique}\n\nProvide an improved final response."
        final_res = model.generate_response(improve_prompt, self.memory.get_history())
        cost_tracker.track_usage("gpt-4o", final_res["input_tokens"], final_res["output_tokens"])

        self.memory.add_message("user", prompt)
        self.memory.add_message("assistant", final_res["content"])
        
        return final_res
