import os
import json

from utils import getSystemInstructions, debug, yellow, endc
import model_tools
from model_tools import Toolbox
from callbacks import WebCallbackHandler
from openrouter import OpenRouterProvider
from flask_socketio import SocketIO, emit

#list_story_files_tool_handler
#write_story_file_tool_handler
#append_story_file_tool_handler
#read_story_file_tool_handler
#roll_dice_tool_handler

def makeNarratorToolbox(story_name: str, system_name: str) -> model_tools.Toolbox:
    return model_tools.Toolbox([
        model_tools.list_story_files_tool_handler,
        model_tools.write_story_file_tool_handler,
        model_tools.append_story_file_tool_handler,
        model_tools.read_story_file_tool_handler,
        model_tools.roll_dice_tool_handler,
    ], default_kwargs = {
        "story_name": story_name,
        "system_name": system_name,
    })
    
class Narrator:
    def __init__(self, model_name: str, story_name: str, system_name: str, socket: SocketIO):
        self.model_name: str = model_name
        self.system_name: str = system_name
        self.tb: Toolbox = makeNarratorToolbox(story_name, system_name)
        self.socket: SocketIO = socket
        self.system_prompt = getSystemInstructions(system_name)
        self.story_history_path = f"./stories/{story_name}/history.json"
        self.thinking_effort = "high"

        self.provider = OpenRouterProvider(
            model_name=model_name,
            system_prompt=self.system_prompt,
            thinking_effort=self.thinking_effort,
            toolbox=self.tb,
            callback_handler=WebCallbackHandler(socket)
        )
    
    def saveMessages(self):
        self.provider.saveMessages(self.story_history_path, model_name=self.model_name, system_name=self.system_name)

    def loadMessages(self) -> list[dict[str, str]] | None:
        return self.provider.loadMessages(self.story_history_path)

    @staticmethod
    def initFromHistory(story_name: str, socket: SocketIO) -> "Narrator | None":
        history_path = f"./stories/{story_name}/history.json"
        if os.path.exists(history_path):
            with open(history_path) as f:
                history_data: dict[str, str] = json.load(f)
                model_name = history_data["model_name"]
                system_name = history_data["system_name"]
                return Narrator(model_name, story_name, system_name, socket)

    def loadStory(self):
        history = self.loadMessages()
        if history is not None:
            # Transform messages from OpenRouter format (role) to frontend format (type)
            frontend_messages = self._transformMessagesForFrontend(self.provider.messages)
            self.socket.emit('conversation_history', frontend_messages)
        else:
            self.provider.addUserMessage("<|begin_conversation|>")
            self.provider.run()
            self.saveMessages()
        self.socket.emit('assistant_ready')
        self.socket.emit('turn_end')
    
    def _transformMessagesForFrontend(self, messages: list[dict]) -> list[dict]:
        """Transform messages from OpenRouter format to frontend format"""
        frontend_messages = []
        
        # Special messages that should not be displayed to the user
        SKIP_MESSAGES = {"<|begin_conversation|>"}
        
        for msg in messages:
            role = msg.get("role")
            content = msg.get("content", "")
            
            # Skip system messages
            if role == "system":
                continue
            
            # Skip special internal messages
            if content in SKIP_MESSAGES:
                continue
            
            # Handle user messages
            if role == "user":
                frontend_messages.append({
                    "type": "user",
                    "content": content,
                    "timestamp": msg.get("timestamp", "")
                })
            
            # Handle assistant messages
            elif role == "assistant":
                # Check if there's thinking/reasoning
                if msg.get("reasoning") and msg.get("reasoning").strip():
                    frontend_messages.append({
                        "type": "thinking",
                        "content": msg.get("reasoning", ""),
                        "timestamp": msg.get("timestamp", "")
                    })
                
                # Check if there are tool calls
                if msg.get("tool_calls"):
                    for tool_call in msg.get("tool_calls", []):
                        frontend_messages.append({
                            "type": "tool_use",
                            "name": tool_call["function"]["name"],
                            "input": tool_call["function"]["arguments"],
                            "timestamp": msg.get("timestamp", "")
                        })
                
                # Add the text content if present
                if content and content.strip():
                    frontend_messages.append({
                        "type": "assistant",
                        "content": content,
                        "timestamp": msg.get("timestamp", "")
                    })
            
            # Handle tool result messages
            elif role == "tool":
                frontend_messages.append({
                    "type": "tool_result",
                    "content": content,
                    "timestamp": msg.get("timestamp", "")
                })
        
        return frontend_messages
     
    def handleUserMessage(self, data: dict[str, str]) -> None:
        self.provider.addUserMessage(data['message'])
        self.provider.run()
        self.socket.emit('turn_end')
        self.saveMessages()
