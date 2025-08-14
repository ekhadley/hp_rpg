import os
import json


from utils import getFullStoryInstruction, debug, yellow, endc
import model_tools
from callbacks import WebCallbackHandler
from providers import Provider, getModelProvider, model_supports_thinking
from flask_socketio import SocketIO, emit


def makeStoryToolbox(story_name: str) -> model_tools.Toolbox:
    return model_tools.Toolbox([
        model_tools.list_story_files_tool_handler,
        model_tools.write_story_file_tool_handler,
        model_tools.append_story_file_tool_handler,
        model_tools.read_story_file_tool_handler,
        model_tools.roll_dice_tool_handler,
    ], default_kwargs={"current_story": story_name})

    
class Narrator:
    def __init__(self, model_name: str, socket: SocketIO, thinking: bool, story_name: str = None):
        self.tb = makeStoryToolbox(story_name)
        self.story_system_prompt = getFullStoryInstruction(story_name)
        self.story_history_path = f"./stories/{story_name}/history.json"
        self.socket = socket
        self.provider_class = getModelProvider(model_name)

        if thinking and not model_supports_thinking(model_name):
            if debug():
                print(yellow, f"Thinking was enabled but model '{model_name}' does not support it.", endc)
            thinking = False

        self.provider: Provider = self.provider_class(
            model_name=model_name,
            system_prompt=self.story_system_prompt,
            thinking=thinking,
            toolbox=self.tb,
            callback_handler=WebCallbackHandler(socket)
        )
    
    def saveHistory(self):
        self.provider.saveHistory(self.story_history_path)
    def loadHistory(self) -> list[dict] | None:
        return self.provider.loadHistory(self.story_history_path)

    def loadStory(self):
        history = self.loadHistory()
        if history is not None:
            converted_history = self.provider.emitHistory()
            self.socket.emit('conversation_history', converted_history)
        else:
            self.provider.addUserMessage("<|begin_conversation|>")
            self.provider.run()
            self.saveHistory()
        self.socket.emit('assistant_ready')
        self.socket.emit('turn_end')
     
    def handleUserMessage(self, data):
        self.provider.addUserMessage(data['message'])
        self.provider.run()
        self.socket.emit('turn_end')
        self.saveHistory()