from flask_socketio import SocketIO
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
    def think_output(self, text):
        pass
    def think_end(self):
        pass
    def tool_request(self, name:str, inputs: dict):
        pass
    def tool_submit(self, names: list[str], inputs: list[dict], results: list[str]):
        pass
    def turn_end(self):
        pass

class TerminalPrinter(CallbackHandler): # streams text into the terminal in nice blocks.
    def __init__(self, assistant_color=brown, tool_color=cyan, user_color=white, thinking_color=gray):
        self.assistant_color = assistant_color
        self.user_color = user_color
        self.tool_color = tool_color
        self.thinking_color = thinking_color
        self.narrating = False
        self.thinking = False
    
    def text_output(self, text):
        if not self.narrating:
            self.narrating = True
            print(self.assistant_color, f"Narrator: ")
        print(self.assistant_color, text, sep="", end=self.user_color)
    def think_output(self, text):
        if not self.thinking:
            self.thinking = True
            print(self.thinking_color, f"Thinking: ", end="")
        print(self.thinking_color, text, sep="", end=self.user_color)
    def think_end(self):
        print()
        self.thinking = False
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
    def __init__(self, socket: SocketIO):
        self.socket = socket
        self.outputting_text = False
        self.thinking = False

    def think_output(self, text):
        if not self.thinking:
            self.thinking = True
            self.socket.emit('think_start')
        self.emit('think_output', text=text)
    
    def think_end(self):
        self.thinking = False
        self.socket.emit('think_end')

    def text_output(self, text):
        if not self.outputting_text:
            self.outputting_text = True
            self.socket.emit('text_start')
        self.emit('text_output', text=text)

    def tool_request(self, name:str, inputs: dict):
        self.outputting_text = False
        self.emit('tool_request', name=name, inputs=inputs)

    def tool_submit(self, names: list[str], inputs: list[dict], results: list[str]):
        self.outputting_text = False
        self.emit('tool_submit', tools=[{"name": names[i], "inputs": inputs[i], "result": results[i]} for i in range(len(names))])

    def turn_end(self):
        self.outputting_text = False
        self.emit('turn_end')

    def emit(self, event, **kwargs):
        self.socket.emit(event, kwargs)
