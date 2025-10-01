import os
import json

from utils import getFullStoryInstruction, debug, yellow, endc
import model_tools
from callbacks import WebCallbackHandler
from openrouter import OpenRouterProvider
from flask_socketio import SocketIO, emit


def makeStoryToolbox(story_name: str, system_name: str) -> model_tools.Toolbox:
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
    def __init__(self, model_name: str, socket: SocketIO, thinking_effort: str, story_name: str, system_name: str):
        self.tb = makeStoryToolbox(story_name, system_name)
        self.story_system_prompt = getFullStoryInstruction(system_name, story_name)
        self.story_history_path = f"./stories/{story_name}/history.json"
        self.socket = socket
        self.model_name = model_name
        self.system_name = system_name

        self.provider = OpenRouterProvider(
            model_name=model_name,
            system_prompt=self.story_system_prompt,
            thinking_effort=thinking_effort,
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
                reasoning_effort = history_data.get("reasoning_effort", "high")
                return Narrator(model_name, socket, reasoning_effort, story_name, system_name)

    def loadStory(self):
        history = self.loadMessages()
        if history is not None:
            self.socket.emit('conversation_history', self.provider.messages)
        else:
            self.provider.addUserMessage("<|begin_conversation|>")
            self.provider.run()
            self.saveMessages()
        self.socket.emit('assistant_ready')
        self.socket.emit('turn_end')
     
    def handleUserMessage(self, data: dict[str, str]) -> None:
        self.provider.addUserMessage(data['message'])
        self.provider.run()
        self.socket.emit('turn_end')
        self.saveMessages()