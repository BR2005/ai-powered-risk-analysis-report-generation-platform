"""
Demonstration Secure GenAI RAG Application (Static Harmless Sample).
Implements defensive guardrails, role isolation, schema validation, and least privilege.
"""
import os
import json
from pydantic import BaseModel, Field

# Mitigation 1: Secret stored in environment variable, not hardcoded
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")

class AgentResponseSchema(BaseModel):
    status: str = Field(..., max_length=50)
    code: int = Field(..., ge=100, le=599)

def sanitize_user_input(user_input: str) -> str:
    """Sanitizes user input and enforces length boundaries."""
    return user_input.strip()[:1000]

def execute_agent_query(user_input: str) -> AgentResponseSchema:
    # Mitigation 2: Role-based message isolation preventing Prompt Injection
    clean_input = sanitize_user_input(user_input)
    messages = [
        {"role": "system", "content": "You are a helpful assistant. Only answer questions within domain."},
        {"role": "user", "content": clean_input}
    ]

    # Simulated LLM response
    simulated_json_output = '{"status": "success", "code": 200}'

    # Mitigation 3: Pydantic Schema Parsing instead of eval()/exec()
    parsed_result = AgentResponseSchema.model_validate_json(simulated_json_output)
    return parsed_result

def run_system_diagnostic(tool_command: str, user_confirmed: bool = False):
    # Mitigation 4: Human-in-the-Loop authorization gate and command whitelisting
    allowed_diagnostics = ["ping_health", "check_uptime", "verify_storage"]
    if tool_command not in allowed_diagnostics:
        raise PermissionError(f"Command '{tool_command}' is not in approved tool whitelist.")
    if not user_confirmed:
        raise PermissionError("Human-in-the-loop confirmation required before executing diagnostic action.")

    return {"status": "diagnostic_complete", "action": tool_command}

def load_cached_embeddings(cache_file_path: str):
    # Mitigation 5: Safe JSON serialization avoiding pickle deserialization
    with open(cache_file_path, "r", encoding="utf-8") as f:
        embeddings = json.load(f)
    return embeddings

if __name__ == "__main__":
    print("Secure Sample RAG Agent loaded.")
