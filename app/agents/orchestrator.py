from typing import List, Dict, Any
from app.models.factory import get_model
from app.agents.router import ModelRouter
from app.memory.manager import ConversationMemory
from app.utils.cost_tracker import cost_tracker
from app.utils.logger import logger
from app.utils.search import WebSearch

class AIOrchestrator:
    def __init__(self):
        self.memory = ConversationMemory()
        self.current_model_id = "gpt-4o"
        self.search_tool = WebSearch()

    def chat(self, user_input: str, mode: str = "auto", api_keys: Dict[str, str] = None, attachment: str = None, web_search: bool = False) -> Dict[str, Any]:
        if attachment:
            user_input = f"CONTEXT FROM UPLOADED FILE:\n{attachment}\n\nUSER QUESTION: {user_input}"

        if web_search:
            return self._web_search_chat(user_input, api_keys=api_keys)

        if mode == "auto":
            model_id = ModelRouter.route_query(user_input)
        elif mode == "ensemble":
            return self._ensemble_chat(user_input, api_keys=api_keys)
        elif mode == "reflection":
            return self._reflection_chat(user_input, api_keys=api_keys)
        elif mode == "pipeline":
            return self._pipeline_chat(user_input, api_keys=api_keys)
        elif mode == "agentic":
            return self._agentic_chat(user_input, api_keys=api_keys)
        else:
            model_id = self.current_model_id

        # Pre-check: if selected model has no valid key, switch to an available one immediately
        if not self._has_key(model_id, api_keys):
            better_model = self._get_available_fallback_model(api_keys=api_keys)
            if better_model and better_model != model_id:
                logger.info(f"Model {model_id} has no valid key. Switching to available model {better_model}.")
                model_id = better_model
            elif not better_model:
                # If no models have keys at all, we'll let _single_model_chat handle the error message
                pass

        return self._single_model_chat(model_id, user_input, api_keys=api_keys)

    def _single_model_chat(self, model_id: str, prompt: str, attempt: int = 1, api_keys: Dict[str, str] = None) -> Dict[str, Any]:
        try:
            from app.models.factory import MODELS
            config = MODELS.get(model_id)
            if not config:
                return {"error": f"Model configuration for {model_id} not found."}
                
            api_key = api_keys.get(config.provider) if api_keys and config else None
            source = "session" if api_key else "config/env"
            
            if not api_key:
                # Refresh config from .env if possible
                import importlib
                import app.config
                importlib.reload(app.config)
                from app.config import API_KEYS
                api_key = API_KEYS.get(config.provider)
            
            if api_key:
                from app.utils.auth import detect_provider
                detected = detect_provider(api_key)
                masked_key = api_key[:4] + "..." + api_key[-4:] if len(api_key) > 8 else "***"
                
                if detected and detected != config.provider:
                    logger.warning(f"!!! KEY MISMATCH !!! Model expects {config.provider} but key starts with {detected} prefix. (Key: {masked_key})")
                else:
                    logger.info(f"Using key for {config.provider} from {source} (key: {masked_key})")

            if not api_key or api_key.startswith("your_"):
                # If we don't have a key, let's see if we should fall back
                if attempt < 2:
                    fallback_model = self._get_available_fallback_model(api_keys=api_keys)
                    if fallback_model and model_id != fallback_model:
                        logger.info(f"Primary model {model_id} has no API key. Falling back to {fallback_model}...")
                        return self._single_model_chat(fallback_model, prompt, attempt + 1, api_keys=api_keys)
                
                return {"error": f"API key for {config.provider} (model: {model_id}) is missing. Please add it to your .env file or provide it in the settings panel."}

            model = get_model(model_id, api_key=api_key)
            
            # Dynamically adjust history based on model limits (Groq on_demand is very tight)
            max_msgs = 8
            if "llama" in model_id or "mixtral" in model_id:
                max_msgs = 4 # Be very aggressive with Groq due to 12k TPM limit
            
            history = self.memory.get_history(max_messages=max_msgs)
            response = model.generate_response(prompt, history)
            
            if "error" in response:
                raise Exception(response["error"])

            # Track cost
            cost_tracker.track_usage(model_id, response["input_tokens"], response["output_tokens"])
            
            # Update memory
            self.memory.add_message("user", prompt)
            self.memory.add_message("assistant", response["content"])
            
            return response
        except Exception as e:
            error_str = str(e)
            logger.warning(f"Model {model_id} failed (attempt {attempt}): {error_str}")
            
            # If we hit a rate limit or "too large" error, try with less history before failing
            if attempt < 3 and ("rate_limit" in error_str.lower() or "too large" in error_str.lower() or "413" in error_str):
                logger.info(f"Retrying {model_id} with minimal history due to token limits...")
                # We'll call ourselves again but maybe we need a way to pass a flag to use less history.
                # For now, let's just try a different model if it's the first attempt, 
                # or return a specific error.
                if attempt == 1:
                    # Try with only the last 2 messages
                    try:
                        model = get_model(model_id, api_key=api_key)
                        response = model.generate_response(prompt, self.memory.get_history(max_messages=2))
                        if "error" not in response:
                            cost_tracker.track_usage(model_id, response["input_tokens"], response["output_tokens"])
                            self.memory.add_message("user", prompt)
                            self.memory.add_message("assistant", response["content"])
                            return response
                    except:
                        pass

            if attempt < 2:
                # Fallback to any model that has a valid key
                fallback_model = self._get_available_fallback_model(api_keys=api_keys)
                if fallback_model and model_id != fallback_model:
                    logger.info(f"Falling back to {fallback_model}...")
                    return self._single_model_chat(fallback_model, prompt, attempt + 1, api_keys=api_keys)
            return {"error": error_str}

    def _get_available_fallback_model(self, api_keys: Dict[str, str] = None) -> str:
        """Find a model that has an available API key."""
        from app.config import MODELS, API_KEYS as CONFIG_KEYS
        
        # Priority list of models to try as fallbacks
        priority_models = ["gemini-1.5-flash", "gpt-4o", "llama3-70b", "deepseek-chat"]
        
        # First check priority models
        for mid in priority_models:
            config = MODELS.get(mid)
            if not config: continue
            key = (api_keys.get(config.provider) if api_keys else None) or CONFIG_KEYS.get(config.provider)
            if key and not key.startswith("your_"): # Check if it's not the placeholder
                return mid
        
        # Then check any model
        for mid, config in MODELS.items():
            key = (api_keys.get(config.provider) if api_keys else None) or CONFIG_KEYS.get(config.provider)
            if key and not key.startswith("your_"):
                return mid
                
        return None

    def _ensemble_chat(self, prompt: str, api_keys: Dict[str, str] = None) -> Dict[str, Any]:
        # Using a mix of providers for true ensemble diversity
        models_to_use = ["gpt-4o", "claude-3-5-sonnet", "gemini-1.5-flash"]
        responses = []
        
        from app.models.factory import MODELS
        for mid in models_to_use:
            logger.info(f"Ensemble: Querying {mid}...")
            try:
                config = MODELS.get(mid)
                api_key = api_keys.get(config.provider) if api_keys and config else None
                res = get_model(mid, api_key=api_key).generate_response(prompt, self.memory.get_history())
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
            best_response = self._rank_responses(prompt, responses, api_keys=api_keys)
        
        self.memory.add_message("user", prompt)
        self.memory.add_message("assistant", best_response["content"])
        
        return best_response

    def _rank_responses(self, prompt: str, responses: List[Dict[str, Any]], api_keys: Dict[str, str] = None) -> Dict[str, Any]:
        """Rank responses using a judge model (GPT-4o) based on specific criteria."""
        logger.info("Ranking responses using judge model...")
        try:
            from app.config import MODELS, API_KEYS as CONFIG_KEYS
            judge_model_id = "gpt-4o"
            config = MODELS.get(judge_model_id)
            key = (api_keys.get(config.provider) if api_keys and config else None) or CONFIG_KEYS.get(config.provider)
            
            if not key or key.startswith("your_"):
                judge_model_id = self._get_available_fallback_model(api_keys=api_keys)
                if not judge_model_id:
                    raise Exception("No judge model available.")
                logger.info(f"GPT-4o unavailable. Using {judge_model_id} as judge.")
                config = MODELS.get(judge_model_id)
                key = (api_keys.get(config.provider) if api_keys and config else None) or CONFIG_KEYS.get(config.provider)

            judge = get_model(judge_model_id, api_key=key)
            
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

    def _reflection_chat(self, prompt: str, api_keys: Dict[str, str] = None) -> Dict[str, Any]:
        logger.info("Starting reflection loop (Generate -> Critique -> Improve)...")
        from app.config import MODELS, API_KEYS as CONFIG_KEYS
        model_id = "gpt-4o"
        config = MODELS.get(model_id)
        key = (api_keys.get(config.provider) if api_keys and config else None) or CONFIG_KEYS.get(config.provider)
        
        if not key or key.startswith("your_"):
            model_id = self._get_available_fallback_model(api_keys=api_keys)
            if not model_id:
                return {"error": "No models available for reflection."}
            logger.info(f"GPT-4o unavailable. Using {model_id} for reflection.")
            config = MODELS.get(model_id)
            key = (api_keys.get(config.provider) if api_keys and config else None) or CONFIG_KEYS.get(config.provider)

        model = get_model(model_id, api_key=key)
        
        # 1. Generate
        initial_res = model.generate_response(prompt, self.memory.get_history())
        content = initial_res.get("content", "")
        cost_tracker.track_usage(model_id, initial_res.get("input_tokens", 0), initial_res.get("output_tokens", 0))

        # 2. Critique
        critique_prompt = f"Critique the following response for accuracy and completeness:\n\n{content}"
        critique_res = model.generate_response(critique_prompt, [])
        critique = critique_res.get("content", "")
        cost_tracker.track_usage(model_id, critique_res.get("input_tokens", 0), critique_res.get("output_tokens", 0))

        # 3. Improve
        improve_prompt = f"Original Prompt: {prompt}\n\nInitial Response: {content}\n\nCritique: {critique}\n\nProvide an improved final response."
        final_res = model.generate_response(improve_prompt, self.memory.get_history())
        cost_tracker.track_usage(model_id, final_res.get("input_tokens", 0), final_res.get("output_tokens", 0))

        self.memory.add_message("user", prompt)
        self.memory.add_message("assistant", final_res.get("content", ""))
        
        return final_res

    def _pipeline_chat(self, prompt: str, api_keys: Dict[str, str] = None) -> Dict[str, Any]:
        logger.info("Starting Advanced Pipeline (Optimize -> Generate -> Verify)...")
        
        # 1. Optimize Prompt
        logger.info("Step 1: Optimizing prompt...")
        opt_model_id = self._get_available_fallback_model(api_keys=api_keys)
        if not opt_model_id: return {"error": "No models available for optimization."}
        
        optimizer = get_model(opt_model_id, api_key=self._get_key(opt_model_id, api_keys))
        opt_prompt = (
            f"Rewrite the following user prompt to be more descriptive, clear, and optimized for an AI assistant. "
            f"Focus on eliciting a high-quality, professional response. "
            f"Output ONLY the rewritten prompt.\n\nUser Input: {prompt}"
        )
        opt_res = optimizer.generate_response(opt_prompt, [])
        optimized_input = opt_res.get("content", prompt)
        cost_tracker.track_usage(opt_model_id, opt_res.get("input_tokens", 0), opt_res.get("output_tokens", 0))
        
        # 2. Generate Response
        logger.info(f"Step 2: Generating response with optimized prompt...")
        gen_model_id = self.current_model_id
        if not self._has_key(gen_model_id, api_keys):
            gen_model_id = self._get_available_fallback_model(api_keys=api_keys)
            
        generator = get_model(gen_model_id, api_key=self._get_key(gen_model_id, api_keys))
        gen_res = generator.generate_response(optimized_input, self.memory.get_history())
        draft_content = gen_res.get("content", "")
        cost_tracker.track_usage(gen_model_id, gen_res.get("input_tokens", 0), gen_res.get("output_tokens", 0))
        
        # 3. Verify & Critique
        logger.info("Step 3: Verifying information...")
        ver_model_id = self._get_available_fallback_model(api_keys=api_keys)
        # Try to pick a different model for verification if possible
        if ver_model_id == gen_model_id:
            from app.config import MODELS
            for mid in MODELS:
                if mid != gen_model_id and self._has_key(mid, api_keys):
                    ver_model_id = mid
                    break
        
        verifier = get_model(ver_model_id, api_key=self._get_key(ver_model_id, api_keys))
        ver_prompt = (
            f"User Prompt: {prompt}\n\n"
            f"AI Response: {draft_content}\n\n"
            f"Critique the AI response for accuracy, completeness, and clarity. "
            f"Point out any potential errors or areas for improvement. "
            f"Output ONLY the critique."
        )
        ver_res = verifier.generate_response(ver_prompt, [])
        critique = ver_res.get("content", "")
        cost_tracker.track_usage(ver_model_id, ver_res.get("input_tokens", 0), ver_res.get("output_tokens", 0))
        
        # 4. Final Refinement
        logger.info("Step 4: Refining final output...")
        final_res = generator.generate_response(
            f"Original Prompt: {prompt}\n\nInitial Response: {draft_content}\n\nCritique: {critique}\n\n"
            f"Provide a final, verified, and polished response that incorporates the feedback.",
            self.memory.get_history()
        )
        cost_tracker.track_usage(gen_model_id, final_res.get("input_tokens", 0), final_res.get("output_tokens", 0))
        
        self.memory.add_message("user", prompt)
        self.memory.add_message("assistant", final_res.get("content", ""))
        
        return final_res

    def _get_key(self, model_id: str, api_keys: Dict[str, str] = None) -> str:
        from app.config import MODELS, API_KEYS as CONFIG_KEYS
        from app.utils.auth import is_key_valid_for_provider
        
        config = MODELS.get(model_id)
        if not config: return None
        
        # Check session
        key = api_keys.get(config.provider) if api_keys else None
        if key and is_key_valid_for_provider(key, config.provider):
            return key
            
        # Check config/env
        key = CONFIG_KEYS.get(config.provider)
        if key and is_key_valid_for_provider(key, config.provider):
            return key
            
        return None

    def _has_key(self, model_id: str, api_keys: Dict[str, str] = None) -> bool:
        key = self._get_key(model_id, api_keys)
        return bool(key and not key.startswith("your_"))

    def _find_any_valid_key(self, api_keys: Dict[str, str] = None) -> tuple[str, str]:
        """Scans all sources for ANY valid key and returns (key, provider)."""
        from app.config import API_KEYS as CONFIG_KEYS
        from app.utils.auth import detect_provider
        
        # Check session keys first
        if api_keys:
            for k in api_keys.values():
                if k and not k.startswith("your_"):
                    p = detect_provider(k)
                    if p: return k, p
                    
        # Check environment keys
        for k in CONFIG_KEYS.values():
            if k and not k.startswith("your_"):
                p = detect_provider(k)
                if p: return k, p
                
        return None, None

    def _get_available_fallback_model(self, api_keys: Dict[str, str] = None) -> str:
        """Find a model that has an available API key, with provider awareness."""
        from app.config import MODELS
        
        # Try to find ANY valid key first
        _, provider = self._find_any_valid_key(api_keys)
        if provider:
            # Pick the first model from this provider
            for mid, config in MODELS.items():
                if config.provider == provider:
                    return mid
        
        return None

    def _agentic_chat(self, prompt: str, api_keys: Dict[str, str] = None) -> Dict[str, Any]:
        """An all-rounder agentic mode that uses self-correction and deep reasoning."""
        logger.info("Starting Agentic All-Rounder Loop (Think -> Generate -> Correct)...")
        
        # Step 1: Think (Internal reasoning)
        model_id = self.current_model_id
        if not self._has_key(model_id, api_keys):
            model_id = self._get_available_fallback_model(api_keys=api_keys)
        
        key = self._get_key(model_id, api_keys)
        from app.models.factory import get_model
        model = get_model(model_id, api_key=key)
        
        thought_prompt = f"Think deeply about this request and outline a perfect plan to answer it. Output ONLY your internal thoughts.\n\nUser: {prompt}"
        thought_res = model.generate_response(thought_prompt, [])
        thought = thought_res.get("content", "")
        
        # Step 2: Generate based on thought
        gen_prompt = f"Use these thoughts: {thought}\n\nTo answer the user: {prompt}"
        gen_res = model.generate_response(gen_prompt, self.memory.get_history(max_messages=6))
        content = gen_res.get("content", "")
        
        # Step 3: Self-Correct
        correct_prompt = f"Critique your own answer for logical consistency and depth. If there's an error, provide the corrected final version. If it's perfect, just output 'STET'.\n\nAnswer: {content}"
        correct_res = model.generate_response(correct_prompt, [])
        correction = correct_res.get("content", "")
        
        final_content = content if "STET" in correction.upper() else correction
        
        self.memory.add_message("user", prompt)
        self.memory.add_message("assistant", final_content)
        
        return {"content": final_content, "model": model_id, "input_tokens": 0, "output_tokens": 0}

    def _web_search_chat(self, prompt: str, api_keys: Dict[str, str] = None) -> Dict[str, Any]:
        """Performs a web search and uses results to provide an accurate answer."""
        logger.info(f"Starting Web Search reasoning for: {prompt}")
        
        # Step 1: Decision - What to search for?
        model_id = "gpt-4o"
        if not self._has_key(model_id, api_keys):
            model_id = self._get_available_fallback_model(api_keys=api_keys)
        
        key = self._get_key(model_id, api_keys)
        model = get_model(model_id, api_key=key)
        
        search_query_prompt = (
            f"Given the user prompt: '{prompt}', generate a concise Google search query to find the most accurate and up-to-date information. "
            f"Output ONLY the search query string."
        )
        query_res = model.generate_response(search_query_prompt, [])
        search_query = query_res.get("content", prompt).strip(' "')
        
        # Step 2: Search
        search_results = self.search_tool.search(search_query)
        context = self.search_tool.format_results_for_prompt(search_results)
        
        # Step 3: Answer
        final_prompt = (
            f"USE THE FOLLOWING SEARCH RESULTS TO ANSWER THE USER REQUEST ACCURATELY.\n"
            f"IF THE RESULTS ARE NOT RELEVANT, RELY ON YOUR INTERNAL KNOWLEDGE BUT MENTION THE DISCREPANCY.\n\n"
            f"{context}\n\n"
            f"USER REQUEST: {prompt}\n\n"
            f"Provide a detailed, professional response with citations to the links provided above if used."
        )
        
        response = model.generate_response(final_prompt, self.memory.get_history())
        
        if "error" not in response:
            self.memory.add_message("user", prompt)
            self.memory.add_message("assistant", response["content"])
            
        return response

    def chat_stream(self, user_input: str, mode: str = "auto", api_keys: Dict[str, str] = None, attachment: str = None, web_search: bool = False):
        """Streams the response token by token."""
        if attachment:
            user_input = f"CONTEXT FROM UPLOADED FILE:\n{attachment}\n\nUSER QUESTION: {user_input}"

        if web_search:
            # For streaming search, we first do the search synchronously then stream the synthesis
            search_res = self._web_search_chat(user_input, api_keys=api_keys)
            if "error" in search_res:
                yield f"Error: {search_res['error']}"
                return
            
            # Since we already got the full response in _web_search_chat for simplicity,
            # we simulate streaming here for consistency, OR we can refactor to stream the synthesis.
            # For now, let's just yield the content in chunks.
            content = search_res.get("content", "")
            chunk_size = 20
            for i in range(0, len(content), chunk_size):
                yield content[i:i+chunk_size]
            return

        model_id = self.current_model_id
        if mode == "auto":
            from app.agents.router import ModelRouter
            model_id = ModelRouter.route_query(user_input)
            
        if not self._has_key(model_id, api_keys):
            model_id = self._get_available_fallback_model(api_keys=api_keys)
            
        key = self._get_key(model_id, api_keys)
        from app.models.factory import get_model
        model = get_model(model_id, api_key=key)
        
        full_response = ""
        for chunk in model.generate_stream(user_input, self.memory.get_history(max_messages=8)):
            full_response += chunk
            yield chunk
            
        self.memory.add_message("user", user_input)
        self.memory.add_message("assistant", full_response)
