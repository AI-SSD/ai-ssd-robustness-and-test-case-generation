import requests
import json
from enum import Enum

class OllamaQuerier:
    class OperationMode(Enum):
        QUERY = "api/generate"
        CHAT = "api/chat"

    system_prompt = "You are a helpful assistant. Be concise and technical."

    def __init__(self, ollama_url, ollama_model):
        # Initialize the OllamaQuerier with the Ollama URL, model, and operation mode (query or chat).
        self.ollama_url = ollama_url
        self.ollama_model = ollama_model

        # Define Ollama endpoints
        self.chat_endpoint = f"{self.ollama_url}/{self.OperationMode.CHAT.value}"
        self.query_endpoint = f"{self.ollama_url}/{self.OperationMode.QUERY.value}"

        # Define the initial system prompt for chat mode
        self.conversation = [{
            "role": "system",
            "content": self.system_prompt
        }]

        # Test connection before proceeding with queries.
        # if self.test_connection() == False:
        #       raise ConnectionError(f"Failed to connect to Ollama API at {self.ollama_url} or model '{self.ollama_model}' is not available.")

    def test_connection(self):
        # Test the connection to the Ollama API by checking if the model is available
        try:
            response = requests.get(f"{self.ollama_url}/api/tags")
            response.raise_for_status()
            response = response.json()
            models = [model["name"] for model in response["models"]]
            if self.ollama_model in models:
                print(f"Successfully connected to Ollama API at {self.ollama_url}. Model '{self.ollama_model}' is available.")
                return True
            else:
                print(f"Successfully connected to Ollama API at {self.ollama_url}, but model '{self.ollama_model}' is not available.")
                return False
        except requests.exceptions.RequestException as e:
            print(f"Failed to connect to Ollama API at {self.ollama_url}. Error: {e}")
            return False

    def query(self, prompt, custom_headers=None):
        # Craft the payload for the query endpoint
        payload = {
            "model": self.ollama_model,
            "prompt": prompt,
            "stream": False
        }
        headers = {"Content-Type": "application/json"}
        if custom_headers:
            headers.update(custom_headers)

        # Query the Ollama API a single time and return the response content
        try:
            response = requests.post(self.query_endpoint, data=json.dumps(payload), headers=headers)
        except requests.exceptions.RequestException as e:
            print(f"Failed to connect to Ollama API at {self.ollama_url}. Error: {e}")
            return None
        response.raise_for_status()
        response = response.json()
        
        return response["response"]
    
    def chat(self, prompt):
        # Add user message to conversation history
        self.conversation.append({
            "role": "user",
            "content": prompt
        })

        # Craft the payload for the chat endpoint with the entire conversation history
        payload = {
            "model": self.ollama_model,
            "messages": self.conversation,
            "stream": False,
            "options": {
                "temperature": 0.2
            }
        }

        # Query the Ollama API with the conversation history + new prompt
        try:
            response = requests.post(self.chat_endpoint, json=payload)
        except requests.exceptions.RequestException as e:
            print(f"Failed to connect to Ollama API at {self.ollama_url}. Error: {e}")
            return None
        response.raise_for_status()
        response = response.json()

        assistant_reply = response["message"]["content"]

        # Add assistant reply to conversation history
        self.conversation.append({
            "role": "assistant",
            "content": assistant_reply
        })

        return assistant_reply
    
    def delete_last_exchange(self):
        # Delete the last user and assistant messages from the conversation history, but keep at least the system prompt.
        if self.conversation and len(self.conversation) > 2:
            self.conversation = self.conversation[:-2]
        else:
            print("Cannot delete exchange. Not enough messages in the conversation history.")
    
    def delete_last_message(self):
        # Delete the last message from the conversation history 
        if self.conversation and len(self.conversation) > 1:
            self.conversation.pop()

    def delete_last_messages(self, nbr_messages):
        # Delete the last N messages from the conversation history, but keep at least the system prompt.
        size = len(self.conversation)
        if self.conversation and len(self.conversation) > 1 and size > nbr_messages:
            self.conversation = self.conversation[:size - nbr_messages]
        else:
            print("Cannot delete messages. Not enough messages in the conversation history or trying to delete too many messages.")

    def delete_first_messages(self, nbr_messages):
        # Delete the first N messages from the conversation history, but keep at least the system prompt.
        if self.conversation and len(self.conversation) > 1:
            self.conversation = [self.conversation[0]] + self.conversation[nbr_messages + 1:]

    def reset_conversation(self):
        self.conversation = [{
            "role": "system",
            "content": self.system_prompt
        }]
