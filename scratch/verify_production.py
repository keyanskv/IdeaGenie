import os
import sys
import importlib

# Add current directory to path
sys.path.append(os.getcwd())

# Mock environment
os.environ["GROQ_API_KEY"] = "gsk_test_key"

from app.agents.orchestrator import AIOrchestrator
orch = AIOrchestrator()

# Mocking the model because I don't have a real key here
class MockModel:
    def generate_stream(self, prompt, history):
        yield "Hello "
        yield "this "
        yield "is "
        yield "a "
        yield "stream."

def get_mock_model(model_id, api_key):
    return MockModel()

# Patch the get_model function
import app.models.factory
app.models.factory.get_model = get_mock_model

# Test streaming
print("Testing Stream:")
for chunk in orch.chat_stream("Hi", api_keys={"groq": "gsk_test"}):
    print(f"Chunk: {chunk}")

# Test Agentic mode exists
print(f"Agentic mode method exists: {hasattr(orch, '_agentic_chat')}")
