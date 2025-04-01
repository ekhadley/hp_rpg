

from utils import *



def example_text_callback(text: str):
    print(f"Assistant: '{text}'")
def example_tool_request_callback(name: str, inputs: str|dict):
    print(f"Tool requested: {name}({inputs})")
def example_tool_submit_callback(names: list[str], inputs: list[str|dict], results: list[str]):
    for i in range(len(names)):
        print(f"Tool output submitted: {names[i]}({inputs[i]}) = {results[i]}")

class CallbackHandler:
    def text_output(self, text):
        pass
    def tool_request_callback(self, name:str, inputs: str|dict):
        pass
    def tool_submit_callback(self, names: list[str], inputs: list[str|dict], results: list[str]):
        pass
    def turn_end_callback(self):
        pass

class TerminalPrinter(CallbackHandler):
    def __init__(self, assistant_color=magenta, tool_color=cyan, user_color=yellow):
        self.assistant_color = assistant_color
        self.user_color = user_color
        self.tool_color = tool_color
        self.narrating = False
    
    def text_output_callback(self, text):
        if not self.narrating:
            self.narrating = True
            print(self.assistant_color, f"Narrator: ")
        print(self.assistant_color, text, sep="", end=self.user_color)
    def tool_request_callback(self, name:str, inputs: str|dict):
        self.narrating = False
        print(self.tool_color, f"Tool requested: {name}({inputs})", endc)
    def tool_submit_callback(self, names: list[str], inputs: list[str|dict], results: list[str]):
        self.narrating = False
        for i in range(len(names)):
            print(self.tool_color, f"\nTool output submitted: {names[i]}({inputs[i]}) = {results[i]}", endc)
    def turn_end_callback(self):
        self.narrating = False
