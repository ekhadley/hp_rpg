import time

import socketio

from utils import *

# each type of callback is given these exact arguments as keywords
def example_text_callback(text: str):
    print(f"Assistant: '{text}'")
def example_tool_request_callback(name: str, inputs: dict):
    print(f"Tool requested: {name}({inputs})")
def example_tool_submit_callback(names: list[str], inputs: list[dict], results: list[str]):
    for i in range(len(names)):
        print(f"Tool output submitted: {names[i]}({inputs[i]}) = {results[i]}")

class CallbackHandler:
    def text_output(self, text):
        pass
    def tool_request(self, name:str, inputs: dict):
        pass
    def tool_submit(self, names: list[str], inputs: list[dict], results: list[str]):
        pass
    def turn_end(self):
        pass

class TerminalPrinter(CallbackHandler): # streams text into the terminal in nice blocks.
    def __init__(self, assistant_color=brown, tool_color=cyan, user_color=white):
        self.assistant_color = assistant_color
        self.user_color = user_color
        self.tool_color = tool_color
        self.narrating = False
    
    def text_output(self, text):
        if not self.narrating:
            self.narrating = True
            print(self.assistant_color, f"Narrator: ")
        print(self.assistant_color, text, sep="", end=self.user_color)
    def tool_request(self, name:str, inputs: dict):
        self.narrating = False
        print(self.tool_color, f"Tool requested: {name}({inputs})", endc)
    def tool_submit(self, names: list[str], inputs: list[dict], results: list[str]):
        self.narrating = False
        for i, name in enumerate(names):
            if name not in ["summarize_story", "read_story_summary", "read_character_creation_guide", "write_file", "read_file"]:
                print(self.tool_color, f"\nTool output submitted: {name}({inputs[i]}) = {results[i]}", endc)
    def turn_end(self):
        self.narrating = False

class WebCallbackHandler(CallbackHandler):
    def __init__(self):
        pass
    def text_output(self, text):
        pass
    def tool_request(self, name:str, inputs: dict):
        pass
    def tool_submit(self, names: list[str], inputs: list[dict], results: list[str]):
        pass
    def turn_end(self):
        pass
