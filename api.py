import os
import json

import openai
import anthropic

from utils import *
import model_tools
from model_tools import Toolbox
import callbacks
from callbacks import CallbackHandler
from abc import ABC, abstractmethod

class Assistant:
    def __init__( self, model_name: str, toolbox: Toolbox, system_prompt: str, callback_handler: CallbackHandler):
        pass
    def addUserMessage(self, content) -> None:
        self.messages.append({
            "role": "user",
            "content": content,
        })
    def addAssistantMessage(self, content) -> None:
        self.messages.append({
            "role": "assistant",
            "content": content,
        })
    def save(self, path: str) -> None:
        pass
    def load(self, path: str) -> bool:
        pass
    def getStream(self):
        pass
    def run(self) -> None:
        pass

class OpenAIAssistant(Assistant):
    def __init__(
            self,
            model_name: str,
            toolbox: Toolbox,
            system_prompt: str,
            callback_handler: CallbackHandler,
        ):
        self.model_name = model_name
        self.tb = toolbox
        self.tool_schemas = self.tb.openai_schemas
        self.system_prompt = system_prompt
        self.messages: list[dict] = []
        self.cb = callback_handler

    def save(self, path: str) -> None:
        if not os.path.exists(path):
            with open(path, "w+") as f:
                json.dump({"messages": self.messages}, f)
        else:
            with open(path, "r+") as f:
                data = json.load(f)
                data["messages"] = self.messages
                f.seek(0)
                json.dump(data, f)
    # converts to openai format upon save. This means content field is a string, and tool calls are separate, top level messages with the assistant role
    def load(self, path: str) -> bool:
        if os.path.exists(path):
            with open(path) as f:
                data = json.load(f)
                if "messages" in data:
                    self.messages = data["messages"]
                    return True

    def submitToolCall(self, call_event) -> None:
        self.messages.append({
            "type": "function_call",
            "name": call_event.name,
            "arguments": call_event.arguments,
            "call_id": call_event.call_id
        })
    def submitToolOutputs(self, call_event: str, tool_outputs: dict) -> None:
        self.messages.append({
            "type": "function_call_output",
            "call_id": call_event.call_id,
            "output": str(tool_outputs)
        })

    def getStream(self):
        return openai.responses.stream(
            model = self.model_name,
            instructions = self.system_prompt,
            input = self.messages,
            tools = self.tool_schemas
        )
    def run(self) -> None:
        currently_outputting_text = False
        with self.getStream() as stream:
            for event in stream:
                if event.type == "response.output_text.delta":
                    if debug() and not currently_outputting_text:
                            print(yellow, "Assistant producing text. . .", endc)
                            currently_outputting_text = True
                    self.cb.text_output(text=event.delta)
                elif event.type == "response.output_item.added" and event.item.type == "function_call":
                    if debug(): print(pink, f"tool call started: {event.item.name}", endc)
                    self.cb.tool_request(name=event.item.name, inputs={})
                elif event.type == "response.output_item.done":
                    if event.item.type == "message":
                        currently_outputting_text = False
                        content = "".join([output.text for output in event.item.content])
                        self.addAssistantMessage(content)
                    if event.item.type == "function_call":
                        call = event.item
                        arguments = json.loads(call.arguments)
                        result = self.tb.getToolResult(call.name, arguments)
                        if debug(): print(pink, f"tool call completed: {call.name}({truncateForDebug(arguments)}) with result: {truncateForDebug(result)}", endc)
                        self.cb.tool_submit(names=[call.name], inputs=[arguments], results=[result])
                        self.submitToolCall(call)
                        self.submitToolOutputs(call, result)
                        stream.close()
                        self.run()
                        return
                elif debug():
                    if event.type == "response.failed":
                        print(bold, red, f"ERROR: RUN FAILED:\n")
                        print(event.to_dict())
                    if currently_outputting_text:
                        print(yellow, "Assistant finished producing text.", endc)
                        currently_outputting_text = False
        self.cb.turn_end()

class AnthropicAssistant(Assistant):
    def __init__(
            self,
            model_name: str,
            toolbox: Toolbox,
            system_prompt: str,
            callback_handler: CallbackHandler,
        ):
        self.model_name = model_name
        self.client = anthropic.Anthropic()
        self.tb = toolbox
        self.tool_schemas = self.tb.anthropic_schemas
        self.messages: list[dict] = []
        self.max_tokens = 4096#16384
        self.system_prompt = system_prompt
        self.system = [
            {
                "text": system_prompt,
                "type": "text",
                "cache_control": {"type": "ephemeral"},
            },
        ]
        self.cb = callback_handler

    def convertMessageFormat(self) -> list[dict]:
        # converts messages to openai format
        converted_messages = []
        for message in self.messages:
            if message["role"] == "user":
                converted_messages.append({
                    "role": "user",
                    "content": message["content"]
                })
            elif message["role"] == "assistant":
                content = message["content"]
                text_content = [c for c in content if content["type"] == "text"]
                content_str = "".join([c["text"] for c in text_content])
                converted_messages.append({
                    "role": "assistant",
                    "content": content
                })
            else:
                raise ValueError(f"Unknown role: {message['role']}")
        return converted_messages
        
    def save(self, path: str) -> None:
        if not os.path.exists(path):
            with open(path, "w+") as f:
                json.dump({"messages": self.messages}, f)
        else:
            with open(path, "r+") as f:
                data = json.load(f)
                data["messages"] = self.messages
                f.seek(0)
                json.dump(data, f)
    # converts to openai format upon save. This means content field is a string, and tool calls are separate, top level messages with the assistant role
    def load(self, path: str) -> bool:
        if os.path.exists(path):
            with open(path) as f:
                data = json.load(f)
                if "messages" in data:
                    self.messages = data["messages"]
                    return True
    
    def getStream(self):
        return self.client.messages.stream(
                model=self.model_name,
                system=self.system,
                tools=self.tool_schemas,
                messages=self.messages,
                max_tokens=self.max_tokens,
            )
    
    def run(self) -> None: 
        with self.getStream() as stream:
            currently_outputting_text = False
            for event in stream:
                if event.type == "text":
                    if debug() and not currently_outputting_text:
                        print(yellow, "Assistant producing text. . .", endc)
                        currently_outputting_text = True
                    self.cb.text_output(text=event.text)
                elif event.type == "content_block_start" and event.content_block.type == "tool_use":
                    if debug(): print(pink, f"tool call started: {event.content_block.name}", endc)
                    self.cb.tool_request(name=event.content_block.name, inputs={})
                elif event.type == "message_stop":
                    message = event.message
                    content = [content.to_dict() for content in message.content]
                    self.addAssistantMessage(content)
                    if message.stop_reason == "tool_use":
                        tool_names = []
                        tool_inputss = []
                        tool_results = []
                        for block in message.content:
                            if block.type == "tool_use":
                                tool_name = block.name
                                tool_names.append(tool_name)
                                tool_inputs = block.input
                                tool_inputss.append(tool_inputs)
                                tool_result = self.tb.getToolResult(tool_name, tool_inputs)
                                tool_call_id = block.id
                                tool_results.append({
                                    "type": "tool_result",
                                    "tool_use_id": tool_call_id,
                                    "content": tool_result
                                })
                        if debug(): print(pink, f"tool call completed: {tool_name}({tool_inputs}) with result: {truncateForDebug(tool_result)}", endc)
                        self.cb.tool_submit(names=tool_names, inputs=tool_inputss, results=[r['content'] for r in tool_results])
                        self.addUserMessage(tool_results)
                        self.run()
                        return
                elif debug() and event.type != "content_block_delta":
                    if currently_outputting_text:
                        print(yellow, "\nAssistant finished producing text.", endc)
                        currently_outputting_text = False
        self.cb.turn_end()

model_name_providers = {
    "claude": AnthropicAssistant,
    "opus": AnthropicAssistant,
    "sonnet": AnthropicAssistant,
    "haiku": AnthropicAssistant,
    "gpt": OpenAIAssistant,
    "o1": OpenAIAssistant,
    "o3": OpenAIAssistant,
}
def selectAssistantType(model_name: str) -> Assistant:
    for key in model_name_providers:
        if key in model_name:
            return model_name_providers[key]
    raise ValueError

def makeAssistant(
    model_name:str,
    toolbox:Toolbox,
    system_prompt,
    callback_handler: CallbackHandler = CallbackHandler(),
) -> Assistant:
    AssistantType = selectAssistantType(model_name)
    if AssistantType == None:
        raise ValueError(f"Unknown model name: {model_name}")
    if debug():
        print(green, f"Creating assistant of type {AssistantType.__name__} with model {model_name}", endc)
    return AssistantType(model_name, toolbox, system_prompt, callback_handler)

if __name__ == "__main__":
    basic_tb = Toolbox([ # demo
        model_tools.list_directory_tool_handler,
        model_tools.read_file_tool_handler,
        model_tools.random_number_tool_handler
    ])

    asst = makeAssistant(
        #model_name = "claude-3-haiku-20240307",
        model_name = "gpt-4o-mini",
        toolbox = basic_tb,
        system_prompt = "You are a helpful assistant that can use tools.",
        callback_handler = callbacks.TerminalPrinter()
    )

    #asst.addUserMessage("Hello assistant. Can you generate a random number from 1-10 and add to it the number of files in the current directory?")
    asst.addUserMessage("Hello assistant. How many files are in the current directory?")
    #asst.addUserMessage("Hello assistant. Can you describe the contents of `utils.py`?")
    #asst.addUserMessage("Hello assistant. How are you?")
    asst.run()

