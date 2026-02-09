from ollama_querier import OllamaQuerier

OLLAMA_URL = "http://localhost:11434"
OLLAMA_MODEL = "qwen2.5-coder:3b"

print("This is an example of how to use the OllamaQuerier class to query the Ollama API for test generation.")

# ===========================
# How to query a single time:
# ===========================
querier = OllamaQuerier(OLLAMA_URL, OLLAMA_MODEL)
print("=========== Querying Ollama API for a single response ===========")
print(f">>> Query prompt:\t What is 2 + 2?")
response = querier.query("What is 2 + 2?")
print(f"<<< Response:\t\t {response}\n")

# ===========================
# How to have a conversation:
# ===========================
print("\n=========== Starting a conversation with the Ollama API ===========")
print(f">>> Question 1:\t What is 2 + 2?")
response = querier.chat("What is 2 + 2?")
print(f"<<< Answer 1:\t {response}\n")

# Tests a follow-up question that requires context from the previous question to be answered correctly.
print(f">>> Question 2:\t What is the previous result times 2?")
response = querier.chat("What is the previous result times 2?")
print(f"<<< Answer 2:\t {response}\n")

# Test deleting the previous question and answer
print(f'>>> Question 2 (again):\t What is the previous result times 3?')
# If answering to the previous question without deleting the answer would be (2 + 2) * 2 * 3 = 24
# But if we delete the question that returns 8, the result will be (2 + 2) * 3 = 12
querier.delete_last_exchange()
response = querier.chat("What is the previous result times 3?")
print(f"<<< Answer 2 (again):\t {response}\n")

print(f">>> Question 3:\t My name is Bob. What is my name?")
response = querier.chat("My name is Bob. What is my name?")
print(f"<<< Answer 3:\t {response}\n")

# Test resetting the conversation history, which should only keep the system prompt. 
print(f">>> Question 1 (reset conversation):\t What is my name?")
querier.reset_conversation()
response = querier.chat("What is my name?")
print(f"<<< Answer 1 (reset conversation):\t {response}\n")