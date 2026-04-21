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

    def _single_model_chat(self, model_id: str, prompt: str, attempt: int = 1) -> Dict[str, Any]:
        try:
            model = get_model(model_id)
            response = model.generate_response(prompt, self.memory.get_history())
            
            if "error" in response:
                raise Exception(response["error"])

            # Track cost
            cost_tracker.track_usage(model_id, response["input_tokens"], response["output_tokens"])
            
            # Update memory
            self.memory.add_message("user", prompt)
            self.memory.add_message("assistant", response["content"])
            
            return response
        except Exception as e:
            logger.warning(f"Model {model_id} failed (attempt {attempt}): {e}")
            if attempt < 2:
                # Fallback to Gemini for cost-efficiency and reliability
                fallback_model = "gemini-1.5-flash"
                if model_id != fallback_model:
                    logger.info(f"Falling back to {fallback_model}...")
                    return self._single_model_chat(fallback_model, prompt, attempt + 1)
            return {"error": str(e)}

    def _ensemble_chat(self, prompt: str) -> Dict[str, Any]:
        # Using a mix of providers for true ensemble diversity
        models_to_use = ["gpt-4o", "claude-3-5-sonnet", "gemini-1.5-flash"]
        responses = []
        
        for mid in models_to_use:
            logger.info(f"Ensemble: Querying {mid}...")
            try:
                res = get_model(mid).generate_response(prompt, self.memory.get_history())
                if "error" not in res:
                    responses.append(res)
                    cost_tracker.track_usage(mid, res["input_tokens"], res["output_tokens"])
            except Exception as e:
                logger.error(f"Ensemble model {mid} failed: {e}")

        if not responses:
            return {"error": "All models in ensemble failed."}

        if len(responses) == 1:
            best_response = responses[0]
        else:
            best_response = self._rank_responses(prompt, responses)
        
        self.memory.add_message("user", prompt)
        self.memory.add_message("assistant", best_response["content"])
        
        return best_response

    def _rank_responses(self, prompt: str, responses: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Rank responses using a judge model (GPT-4o) based on specific criteria."""
        logger.info("Ranking responses using GPT-4o as judge...")
        try:
            judge = get_model("gpt-4o")
            
            ranking_prompt = (
                f"User Prompt: {prompt}\n\n"
                "Evaluate the following AI responses for:\n"
                "1. Accuracy\n2. Completeness\n3. Reasoning Quality\n\n"
            )
            for i, res in enumerate(responses):
                ranking_prompt += f"--- RESPONSE {i+1} (Model: {res['model']}) ---\n{res['content']}\n\n"
            
            ranking_prompt += (
                "Decide which response is the absolute best. "
                "Output ONLY the single number of the best response (e.g., '1', '2', or '3'). "
                "Do not explain your choice."
            )
            
            judge_res = judge.generate_response(ranking_prompt, [])
            best_idx_str = "".join(filter(str.isdigit, judge_res.get("content", "1")))
            best_idx = int(best_idx_str) - 1 if best_idx_str else 0
            
            if 0 <= best_idx < len(responses):
                logger.info(f"Judge selected Response {best_idx + 1}")
                return responses[best_idx]
        except Exception as e:
            logger.error(f"Ranking failed: {e}. Falling back to first valid response.")
        
        return responses[0]

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
