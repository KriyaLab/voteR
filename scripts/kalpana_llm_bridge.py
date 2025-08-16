import subprocess
import tempfile

LLAMA_BIN = "/root/llama.cpp/build/bin/llama-cli"
MODEL_PATH = "/root/llama.cpp/models/mistral-7b-instruct-v0.1.Q4_K_M.gguf"
MAX_TOKENS = "300"
DELIMITER = "\n=== RESPONSE START ===\n"

def call_llama(prompt):
    try:
        # Add unique delimiter to mark where the model should begin responding
        full_prompt = prompt.strip() + DELIMITER

        # Write full prompt to a temporary file
        with tempfile.NamedTemporaryFile(mode="w+", delete=False) as tmp:
            tmp.write(full_prompt)
            tmp_path = tmp.name

        result = subprocess.run([
            LLAMA_BIN,
            "-m", MODEL_PATH,
            "-f", tmp_path,
            "-n", MAX_TOKENS
        ], stdout=subprocess.PIPE, stderr=subprocess.PIPE)

        full_output = result.stdout.decode("utf-8")
        return extract_after_delimiter(full_output)

    except Exception as e:
        return f"[LLM ERROR] {e}"

def extract_after_delimiter(output):
    """
    Returns only the model's response after the inserted delimiter.
    Falls back to full output if delimiter is not found.
    """
    if "=== RESPONSE START ===" in output:
        return output.split("=== RESPONSE START ===", 1)[1].strip()
    else:
        return output.strip()

