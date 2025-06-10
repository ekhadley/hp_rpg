import os
import random
import json
import inspect
from collections.abc import Callable

from utils import *

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
    def __init__(self, handler: Callable, default_kwargs: dict = {}):
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

        self.kwargs = default_kwargs

    def getResult(self, parameters: dict) -> str:
        try:
            if debug(): print(pink, f"calling tool '{self.name}' with parameters {parameters}", endc)
            tool_result = str(self.handler(**parameters, **self.kwargs))
            if debug(): print(pink, f"tool returned: '{tool_result}'", endc)
            return tool_result
        except Exception as e:
            if debug(): print(bold, red, f"error in tool {self.name}: {str(e)}", endc)
            return f"error in tool {self.name}: {str(e)}"
    
    
class Toolbox:
    def __init__(self, handlers: list[Callable], default_kwargs: dict = {}):
        self.tools = [Tool(handler, default_kwargs) for handler in handlers]
        self.kwargs = default_kwargs
        self.tool_map = {tool.name: tool for tool in self.tools}
        self.openai_schemas = [tool.openai_schema for tool in self.tools]
        self.anthropic_schemas = [tool.anthropic_schema for tool in self.tools]
    
    def getToolResult(self, tool_name: str, parameters: dict) -> str:
        if tool_name in self.tool_map:
            return self.tool_map[tool_name].getResult(parameters)
        else:
            if debug(): print(bold, red, f"attempt to call nonexistant tool", endc)
            return f"error: Tool {tool_name} not found."

    def updateDefaultKwargs(self, kwargs: dict):
        self.kwargs = kwargs
        for tool in self.tools:
            tool.kwargs = kwargs

# Tool handlers
# descriptions and argument properties are parsed automatically from the docstring.
# They have to be formatted exactly like this.
# We handle errors inside these functions just to give nicer error messages to the model. You don't have to handle them here.
# Toolboxes can be given default values as kwargs which will get passed to every function call.
def random_number_tool_handler(max: int, **kwargs) -> int:
    """random_number: Generate a random number from 1 to max inclusive.
    max (integer): The maximum value of the random number.
    """
    if max < 1: raise ValueError("max argument must be greater than 0")
    random_number = random.randint(1, max)
    return random_number

def list_directory_tool_handler(**kwargs) -> list[str]:
    """list_files: List the files in the local directory.
    """
    files = os.listdir(f"./")
    return files

def read_file_tool_handler(file_name: str, **kwargs) -> str:
    """read_file: Read the contents of a file in the local directory.
    file_name (string): Name of the file to be read.
    """
    with open(f"./{file_name}", 'r') as file:
        content = file.read()
    return content

############## story tools ################

def list_story_files_tool_handler(**kwargs) -> list[str]:
    """list_files: Lists all files in the current story directory.
    """
    files = [f for f in os.listdir(f"./stories/{kwargs['current_story']}") if ".md" in f]
    return files

def read_story_file_tool_handler(file_name: str, **kwargs) -> str:
    """read_file: Read the contents of a file in the current story directory.
    file_name (string): Name of the file to be read. Should include the file extension, and not include any parent folders or subfolders.
    """
    with open(f"./stories/{kwargs['current_story']}/{file_name}", 'r') as file:
        content = file.read()
    return content

def write_story_file_tool_handler(file_name: str, contents: str, **kwargs) -> str:
    """write_file: Create or overwrite a file in the current story directory with the given name and contents. The contents of the file, if it exists, will be deleted permanently. If editing a file, you should read the file first, then write the edited or extended version after.
    file_name (string): Name of the file to save to. Should be a markdown file, ending in '.md'. Should not be a part of any subfolder.
    contents (string): The contents to write to the file. Do not include backticks around the contents to be saved.
    """
    if not file_name.endswith(".md"):
        file_name += ".md"
    exists = os.path.exists(f"./stories/{kwargs['current_story']}/{file_name}")
    with open(f"./stories/{kwargs['current_story']}/{file_name}", 'w') as file:
        file.write(contents)
    if exists: return "File edited successfully."
    else: return "File saved successfully."

def append_story_file_tool_handler(file_name: str, contents: str, **kwargs) -> str:
    """append_file: Append contents to the end of an existing file in the current story directory. If the file doesn't exist, it will be created.
    file_name (string): Name of the file to append to. Should be a markdown file, ending in '.md'. Should not be a part of any subfolder.
    contents (string): The contents to append to the file. Do not include backticks around the contents to be appended.
    """
    if not file_name.endswith(".md"):
        file_name += ".md"
    exists = os.path.exists(f"./stories/{kwargs['current_story']}/{file_name}")
    with open(f"./stories/{kwargs['current_story']}/{file_name}", 'a') as file:
        file.write(contents)
    if exists: return "Contents appended to file successfully."
    else: return "File created and contents added successfully."

def _summarize_story_tool_handler(contents: str, **kwargs) -> str:
    """summarize_story: This will overwrite the contents of the story_summary.md file with the contents provided. 
    contents (string): The contents to write to the story summary file. Do not include backticks around the contents to be saved.
    """
    with open(f"./stories/{kwargs['current_story']}/story_summary.md", 'w') as file:
        file.write(contents)
    return "Story summary saved successfully."

def read_story_summary_tool_handler(**kwargs) -> str:
    """read_story_summary: Read the story summary file (story_summary.md) in the current story directory.
    """
    with open(f"./stories/{kwargs['current_story']}/story_summary.md", 'r') as file:
        content = file.read()
    return content

def read_story_plan_tool_handler(**kwargs) -> str:
    """read_story_plan: Read the story plan file, laying out the behind-the-scenes architecture of the current story.
    """
    with open(f"./stories/{kwargs['current_story']}/story_plan.md", 'r') as file:
        content = file.read()
    return content

def read_story_planning_guide(**kwargs) -> str:
    """read_story_planning_guide: Read the story planning guide, instructing you how to create a story plan. Only use this if story_plan.md does not alredy exist.
    """
    with open(f"./planning_guide.md", 'r') as file:
        content = file.read()
    return content

def roll_dice_tool_handler(dice: str, **kwargs) -> int:
    """roll_dice: Roll a set of dice with the given number of sides and return the sum of the rolls.
    dice (string): A string describing the set of dice to roll, of the form 'dX' or 'XdY'.
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