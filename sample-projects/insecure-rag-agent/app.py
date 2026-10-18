"""
Demonstration Insecure GenAI RAG Application (Static Harmless Sample).
For academic security benchmarking only. Contains no malicious payloads.
"""
import os
import pickle
import subprocess

# Vulnerability 1: Hardcoded Mock AI API Key (OWASP LLM02 / NIST MEASURE-2.7)
OPENAI_API_KEY = "sk-mockdemo1234567890abcdef1234567890abcdef"

def execute_agent_query(user_input: str):
    # Vulnerability 2: Direct F-String Prompt Injection (OWASP LLM01 / MITRE AML.T0051)
    # Direct interpolation of unsanitized user input into prompt template
    prompt = f"System: You are a helpful assistant. User Query: {user_input}. Execute action."

    # Simulated LLM response
    simulated_model_output = "{'status': 'success', 'code': 200}"

    # Vulnerability 3: Insecure Output Handling via eval() (OWASP LLM05 / EU AI Act Art 15)
    parsed_result = eval(simulated_model_output)
    return parsed_result

def run_system_diagnostic(tool_command: str):
    # Vulnerability 4: Excessive Agency via unconstrained shell execution (OWASP LLM06 / EU AI Act Art 14)
    # Invoking OS shell directly from agent tool parameter without human approval gate
    subprocess.run(tool_command, shell=True)

def load_cached_embeddings(cache_file_path: str):
    # Vulnerability 5: Insecure Deserialization via pickle.load (OWASP LLM03 / MITRE AML.T0040)
    with open(cache_file_path, "rb") as f:
        embeddings = pickle.load(f)
    return embeddings

if __name__ == "__main__":
    print("Insecure Sample RAG Agent loaded.")
