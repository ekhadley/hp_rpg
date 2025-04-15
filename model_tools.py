import os
import random
import json
import inspect
from collections.abc import Callable

from utils import *

global current_story
current_story = ""

def parse_handler_metadata(func):
    doc = inspect.getdoc(func)
    if not doc:
        raise ValueError("Tool handlers must have a docstring.")
    lines = doc.strip().splitlines()
    first_line = lines[0]
    if ':' not in first_line:
        raise ValueError("First line of docstring must be in the format 'tool_name: description'")
    
    tool_name, description = map(str.strip, first_line.split(':', 1))

    arg_properties = {}
    for line in lines[1:]:
        line = line.strip()
        if not line:
            continue
        try:
            name_type, param_desc = line.split(":", 1)
            name, type_str = name_type.strip().split("(", 1)
            name = name.strip()
            type_str = type_str.strip(") ").lower()
        except ValueError:
            raise ValueError(f"Invalid argument docstring line: '{line}'")

        arg_properties[name] = {
            "type": type_str,
            "description": param_desc.strip()
        }

    #return type("HandlerProperties", (), {"name": tool_name, "description": description, "arg_properties": arg_properties, "handler": func})()
    return {"name": tool_name, "description": description, "arg_properties": arg_properties, "handler": func}


class Tool:
    #def __init__(self, name: str, arg_properties: dict, description: str, handler):
    def __init__(self, handler: Callable):
        handler_props = parse_handler_metadata(handler)
        self.name = handler_props['name']
        self.description = handler_props['description']
        self.handler = handler
        self.arg_properties = handler_props['arg_properties']
        self.openai_schema = {
            "type": "function",
            "function": {
                "name": self.name,
                "description": self.description,
                "parameters": {
                    "type": "object",
                    "properties": self.arg_properties,
                    "required": [key for key in self.arg_properties.keys()]
                },
            }
        }
        self.anthropic_schema = {
            "name": self.name,
            "description": self.description,
            "input_schema": {
                "type": "object",
                "properties": self.arg_properties,
                # Required fields are determined by the keys in arg_properties
                "required": [key for key in self.arg_properties.keys()]
            }
        }

    def getResult(self, parameters: dict) -> str:
        try:
            if debug(): print(pink, f"calling tool '{self.name}' with parameters {parameters}", endc)
            tool_result = str(self.handler(**parameters))
            if debug(): print(pink, f"tool returned: '{tool_result}'", endc)
            return tool_result
        except Exception as e:
            return f"error in tool {self.name}: {str(e)}"
    
class Toolbox:
    def __init__(self, handlers: list[Callable]):
        self.tools = [Tool(handler) for handler in handlers]
        self.tool_map = {tool.name: tool for tool in self.tools}
        self.openai_schemas = [tool.openai_schema for tool in self.tools]
        self.anthropic_schemas = [tool.anthropic_schema for tool in self.tools]
    
    def parseToolParameters(self, parameters: str|dict) -> dict:
        if isinstance(parameters, dict):
            return parameters
        elif isinstance(parameters, str):
            try:
                return json.loads(parameters)
            except json.JSONDecodeError:
                raise ValueError("Invalid JSON format for parameters.")
        raise ValueError("Parameters should be a JSON string or a dictionary.")
    
    def getToolResult(self, tool_name: str, parameters: str|dict) -> str:
        if tool_name in self.tool_map:
            return self.tool_map[tool_name].getResult(self.parseToolParameters(parameters))
        else:
            return f"error: Tool {tool_name} not found."

# Tool handlers
# descriptions and argument properties are parsed automatically from the docstring.
# They have to be formatted exactly like this.
# We handle errors inside these functions just to give nicer error messages to the model. You don't have to handle them here.
def random_number_tool_handler(max: int) -> int:
    """random_number: Generate a random number from 1 to max inclusive.
    max (integer): The maximum value of the random number.
    """
    if max < 1: raise ValueError("max argument must be greater than 0")
    random_number = random.randint(1, max)
    return random_number

def list_directory_tool_handler() -> list[str]:
    """list_files: List the files in the local directory.
    """
    files = os.listdir(f"./")
    return files

def read_file_tool_handler(file_name: str) -> str:
    """read_file: Read the contents of a file in the local directory.
    file_path (string): Name of the file to be read.
    """
    with open(f"./{file_name}", 'r') as file:
        content = file.read()
    return content

############## story tools ################

def list_story_files_tool_handler() -> list[str]:
    """list_files: Lists all files in the current story directory.
    """
    files = [f for f in os.listdir(f"./stories/{current_story}") if ".md" in f]
    return files

def read_story_file_tool_handler(file_name: str) -> str:
    """read_file: Read the contents of a file in the current story directory.
    file_name (string): Name of the file to be read. Should include the file extension, and not include any parent folders or subfolders.
    """
    with open(f"./stories/{current_story}/{file_name}", 'r') as file:
        content = file.read()
    return content

def write_story_file_tool_handler(file_name: str, contents: str) -> str:
    """write_file: Create a file in the current story directory with the given name and contents. This tool will fail if the file already exists. Only use this tool when you have the full contents prepareed. Files cannot be edited later, only appended to.
    file_name (string): Name of the file to save to. Should be a markdown file, ending in '.md'. Should not be a part of any subfolder.
    contents (string): The contents to write to the file. Do not include backticks around the contents to be saved.
    """
    if not file_name.endswith(".md"):
        file_name += ".md"
    if os.path.exists(f"./stories/{current_story}/{file_name}"):
        raise ValueError("File already exists.")
    with open(f"./stories/{current_story}/{file_name}", 'w') as file:
        file.write(contents)
    return "File saved successfully."

def summarize_story_tool_handler(contents: str) -> str:
    """summarize_story: This will OVERWRITE the contents of the story_summary.md file with the contents provided. Any information in the file will be lost. ONLY use this tool on user request. The contents you write should contain any and every piece of information which could be necessary for continuing the story, as seamlessly as possible. Use many details. If you have not already, you should read the current story summary, so you can replace it with an edited or appended version.
    contents (string): The contents to write to the story summary file. Do not include backticks around the contents to be saved.
    """
    with open(f"./stories/{current_story}/story_summary.md", 'w') as file:
        file.write(contents)
    return "Story summary saved successfully."

def read_story_summary_tool_handler() -> str:
    """read_story_summary: Read the contents of the story summary file (story_summary.md) in the current story directory.
    """
    with open(f"./stories/{current_story}/story_summary.md", 'r') as file:
        content = file.read()
    return content

def roll_dice_tool_handler(dice: str) -> int:
    """roll_dice: Roll a set of dice with the given number of sides and return the sum of the rolls.
    dice (string): A string describing the set of dice to roll, of the form 'dX' or 'XdY'. Y is the number of sides on the dice, X is the number of times to roll. If no X is provided, it defaults to 1.
    """
    dice = dice.lower()
    num, sides = dice.strip().split('d')
    if num == '':
        num = 1
    else:
        try:
            num = int(num)
        except ValueError:
            raise ValueError("Invalid number of dice.")
    try:
        sides = int(sides)
    except ValueError:
        raise ValueError("Invalid number of sides.")
    
    if num < 1:
        raise ValueError("Number of dice must be greater than 0.")
    if sides < 1:
        raise ValueError("Number of sides must be greater than 0.")
    
    rolls = [random.randint(1, sides) for _ in range(num)]
    return sum(rolls)

def readStoryPlanningGuide() -> str:
    """read_story_planning_guide: Read the contents of the story planning guide, instructing you how to create a secret story planning document. Use this only when the user asks you to start a new story.
    """
    with open("planning_guide.md", 'r') as file:
        content = file.read()
    return content

def getFullInstructionMessage() -> str:
    with open("instructions.md", 'r') as file:
        content = file.read()
    return content