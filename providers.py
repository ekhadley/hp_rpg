import os
import json

import openai
import anthropic

from utils import *
import model_tools
from model_tools import Toolbox
import callbacks
from callbacks import CallbackHandler

# provider is the llm backend of a narrator
# It handles all behavior specific to a particular llm provider, such as message history formats, saving/loading, streaming events, and tool definitions.
# It provides generic responses through the callbacks while streaming for things like text/thinking start and stops, and tool uses
# message history is saved on disk and sent to the frontend using the anthropic format.
class Provider:
    def __init__( self, model_name: str, toolbox: Toolbox, system_prompt: str, callback_handler: CallbackHandler, thinking: bool):
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
    def saveMessages(self, path: str) -> None:
        converted = self.convertMessagesOut()
        if not os.path.exists(path):
            with open(path, "w+") as f:
                json.dump({"messages": converted}, f, indent=4)
        else:
            with open(path, "r+") as f:
                data = json.load(f)
                data["messages"] = converted
                f.seek(0)
                json.dump(data, f, indent=4)
    def loadMessages(self, path: str) -> list[dict] | None:
        if os.path.exists(path):
            with open(path) as f:
                data = json.load(f)
                if "messages" in data:
                    raw_messages = data["messages"]
                    self.messages = self.convertMessagesIn(raw_messages)
                    return raw_messages
        return None
    def convertMessagesIn(self, messages: list[dict]) -> list[dict]: # convert the given unified format messages into the provider's format
        pass
    def convertMessagesOut(self) -> list[dict]: # convert the current saved messages in the provider's format messages into the unified format
        pass
    def getStream(self):
        pass
    def run(self) -> None:
        pass
    def makeToolDefinitions(self) -> list[dict]:
        pass

class OpenAIProvider(Provider):
    def __init__(
            self,
            model_name: str,
            toolbox: Toolbox,
            system_prompt: str,
            callback_handler: CallbackHandler,
            thinking: bool,
            thinking_effort: str = "low",
            thinking_summary: str = "detailed"
        ):
        self.model_name = model_name
        self.tb = toolbox
        self.tool_schemas = self.makeToolDefinitions()
        self.system_prompt = system_prompt
        self.messages: list[dict] = []
        self.cb = callback_handler
        self.thinking_enabled = thinking
        self.thinking_config = {
            "effort": thinking_effort,
            "summary": thinking_summary
        } if thinking else None

    def getStream(self):
        return openai.responses.stream(
            model = self.model_name,
            instructions = self.system_prompt,
            input = self.messages,
            tools = self.tool_schemas,
            reasoning = self.thinking_config,
            store = False,
            include=["reasoning.encrypted_content"],
        )

    def run(self) -> None:
        currently_outputting_text = False
        currently_thinking = False
        current_reasoning_summary = None
        with self.getStream() as stream:
            for event in stream:
                if event.type == "response.output_text.delta":
                    if debug() and not currently_outputting_text:
                        print(yellow, "Assistant producing text. . .", endc)
                        currently_outputting_text = True
                    self.cb.text_output(text=event.delta)
                elif event.type == "response.reasoning_summary_text.delta":
                    if debug() and not currently_thinking:
                        print(cyan, "Assistant thinking...", endc)
                        currently_thinking = True
                    self.cb.think_output(text=event.delta)
                elif event.type == "response.output_item.added":
                    if event.item.type == "function_call":
                        if debug(): print(pink, f"tool call started: {event.item.name}", endc)
                        self.cb.tool_request(name=event.item.name, inputs={})
                    elif event.item.type == "reasoning":
                        if debug(): print(cyan, "Assistant is thinking...", endc)
                elif event.type == "response.output_item.done":
                    if event.item.type == "message":
                        currently_outputting_text = False
                        content = "".join([output.text for output in event.item.content])
                        self.addAssistantMessage(content)
                    elif event.item.type == "function_call":
                        call = event.item
                        arguments = json.loads(call.arguments)
                        result = self.tb.getToolResult(call.name, arguments)
                        if debug(): print(pink, f"tool call completed: {call.name}({truncateForDebug(arguments)}) with result: {truncateForDebug(result)}", endc)
                        self.cb.tool_submit(names=[call.name], inputs=[arguments], results=[result])
                        self.submitToolCall(call.name, call.arguments, call.call_id) # call args should be string, ugh
                        self.submitToolOutputs(call.call_id, result)
                        stream.close()
                        self.run()
                        return
                    elif event.item.type == "summary_text":
                        currently_thinking = False
                        self.cb.think_end()
                        current_reasoning_summary = event.item.summary
                        if debug(): print(cyan, f"Assistant reasoning summary: {event.item.text}", endc)
                    elif event.item.type == "reasoning":
                        currently_thinking = False
                        self.cb.think_end()
                        reasoning_event = event.item.to_dict()
                        if current_reasoning_summary is not None: reasoning_event["summary"] = current_reasoning_summary
                        current_reasoning_summary = None
                        self.messages.append(reasoning_event)
                elif debug():
                    if event.type == "response.failed":
                        print(bold, red, f"ERROR: RUN FAILED:\n")
                        print(event.to_dict())
                    if currently_outputting_text:
                        print(yellow, "Assistant finished producing text.", endc)
                        currently_outputting_text = False
        self.cb.turn_end()

    def submitToolCall(self, tool_name: str, arguments: dict, call_id: str) -> None:
        self.messages.append({
            "type": "function_call",
            "name": tool_name,
            "arguments": arguments,
            "call_id": call_id
        })
    def submitToolOutputs(self, call_id: str, tool_outputs: dict) -> None:
        self.messages.append({
            "type": "function_call_output",
            "call_id": call_id,
            "output": str(tool_outputs)
        })
    
    def makeToolDefinitions(self):
        return [{
            "type": "function",
            "name": tool.name,
            "description": tool.description,
            "parameters": {
                "type": "object",
                "properties": tool.arg_properties,
            },
            "required": [key for key in tool.arg_properties.keys()]
        } for tool in self.tb.tools]
    
    def convertMessagesIn(self, messages: list[dict]) -> list[dict]:
        converted = []
        for message in messages:
            role = message.get("role", None)
            if role == "user":
                content = message.get("content", None)
                if isinstance(content, str):
                    converted.append({
                        "role": "user",
                        "content": content
                    })
                elif isinstance(content, list):
                    for item in content:
                        item_type = item.get("type", None)
                        if item_type == "text":
                            converted.append({
                                "role": "user",
                                "content": item["text"]
                            })
                        elif item_type == "tool_result":
                            converted.append({
                                "type": "function_call_output",
                                "call_id": item["tool_use_id"],
                                "output": item["content"]
                            })
            elif role == "assistant":
                content = message.get("content", None)
                if isinstance(content, str):
                    converted.append({
                        "role": "assistant",
                        "content": content
                    })
                elif isinstance(content, list):
                    for item in content:
                        item_type = item.get("type", None)
                        if item_type == "text":
                            converted.append({
                                "role": "assistant",
                                "content": item["text"]
                            })
                        elif item_type == "tool_use":
                            converted.append({
                                "type": "function_call",
                                "name": item["name"],
                                "arguments": json.dumps(item["input"]),
                                "call_id": item["id"],
                            })
                        elif item_type == "thinking": # don't load reasoning traces into the provider's history. They are still sent to the frontend for displaying
                            converted.append({
                                "type": "reasoning",
                                "summary": [{
                                    "type": "summary_text",
                                    "text": item["thinking"],
                                }],
                                "encrypted_content": item["signature"],
                                "id": "rs_123",
                            })
        print(json.dumps(converted, indent=4)) # debug
        return converted
                        
    def convertMessagesOut(self) -> list[dict]: # this has to collect separate user and assistant messages/tool stuff into collated content lists, as per the anthropic format
        converted = []
        current_role = None

        def new_role(converted, current_role, new_role):
            if current_role != new_role:
                print(pink, f"changed role from {current_role} to {new_role}", endc)
                converted.append({
                    "role": new_role,
                    "content": []
                })

        for message in self.messages:
            role = message.get("role", None)
            msg_type = message.get("type", None)
            if role == "user": # user messages are always bare strings
                converted.append({
                    "role": "user",
                    "content": message["content"]
                })
            elif msg_type == "function_call_output": # potentially group multiple tool results
                new_role(converted, current_role, "user")
                current_role = "user"
                converted[-1]["content"].append({
                    "type": "tool_result",
                    "tool_use_id": message["call_id"],
                    "content": message["output"]
                })
            elif role == "assistant": # these get grouped into an assistant content chain
                new_role(converted, current_role, "assistant")
                current_role = "assistant"
                converted[-1]["content"].append({
                    "type": "text",
                    "content": message["content"]
                })
            elif msg_type == "function_call":
                new_role(converted, current_role, "assistant")
                current_role = "assistant"
                converted[-1]["content"].append({
                    "type": "tool_use",
                    "name": message["name"],
                    "input": message["arguments"],
                    "id": message["call_id"]
                })
            elif msg_type == "reasoning":
                print(red, converted, endc)
                new_role(converted, current_role, "assistant")
                print(blue, converted, endc)
                current_role = "assistant"
                summary = message.get("summary", [])
                if len(summary) > 0:
                    converted[-1]["content"].append({
                        "type": "thinking",
                        "thinking": "".join([part["text"] for part in summary]),
                        "signature": message["encrypted_content"]
                    })
                
        return converted


class AnthropicProvider(Provider):
    def __init__(
            self,
            model_name: str,
            system_prompt: str,
            callback_handler: CallbackHandler,
            toolbox: Toolbox,
            thinking: bool,
            max_tokens: int = 16384,
            thinking_budget: int = 4096
        ):
        self.model_name = model_name
        self.tb = toolbox
        self.tool_schemas = self.makeToolDefinitions()
        self.client = anthropic.Anthropic()
        self.messages: list[dict] = []
        self.max_tokens = max_tokens
        self.system_prompt = system_prompt
        self.system_message = [
            {
                "text": system_prompt,
                "type": "text",
                "cache_control": {"type": "ephemeral"},
            },
        ]
        self.cb = callback_handler
        self.thinking_config = {
            "type": "enabled",
            "budget_tokens": thinking_budget
        } if thinking else anthropic._types.NotGiven()
    
    def getStream(self):
        return self.client.messages.stream(
                model=self.model_name,
                system=self.system_message,
                tools=self.tool_schemas,
                messages=self.messages,
                max_tokens=self.max_tokens,
                thinking=self.thinking_config,
            )
        
    def run(self) -> None: 
        with self.getStream() as stream:
            currently_outputting_text = False
            for event in stream:
                #print(magenta, event.type, endc)
                if event.type == "text":
                    if debug() and not currently_outputting_text:
                        print(yellow, "Assistant producing text. . .", endc)
                        currently_outputting_text = True
                    self.cb.text_output(text=event.text)
                elif event.type == "thinking":
                    self.cb.think_output(text=event.thinking)
                elif event.type == "content_block_start":
                    if event.content_block.type == "tool_use":
                        if debug(): print(pink, f"tool call started: {event.content_block.name}", endc)
                        self.cb.tool_request(name=event.content_block.name, inputs={})
                    elif event.content_block.type == "thinking":
                        if debug(): print(cyan, "Assistant is thinking...", endc)
                elif event.type == "message_stop":
                    message = event.message
                    content = [content.to_dict() for content in message.content]
                    self.addAssistantMessage(content)
                    if message.stop_reason == "tool_use":
                        tool_names, tool_inputss, tool_results = [], [], []
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

    def makeToolDefinitions(self):
        return [{
            "name": tool.name,
            "description": tool.description,
            "input_schema": {
                "type": "object",
                "properties": tool.arg_properties,
                "required": [key for key in tool.arg_properties.keys()]
            }
        } for tool in self.tb.tools]

    def convertMessagesIn(self, messages: list[dict]) -> list[dict]: # unified format is the anthropic format.
        return messages
    def convertMessagesOut(self):
        return self.messages

if __name__ == "__main__":
    basic_tb = Toolbox([ # demo
        model_tools.list_directory_tool_handler,
        model_tools.read_file_tool_handler,
        model_tools.random_number_tool_handler
    ])

    asst = OpenAIProvider(
    #asst = AnthropicProvider(
        #model_name = "claude-3-haiku-20240307",
        #model_name = "claude-sonnet-4-20250514",
        model_name = "o3-mini-2025-01-31",
        system_prompt = "You are a helpful assistant that can use tools.",
        thinking = True,
        toolbox = basic_tb,
        callback_handler = callbacks.TerminalPrinter(),
    )

    #asst.addUserMessage("Hello assistant. Can you generate a random number from 1-10 and add to it the number of files in the current directory? Use your reasoning.")
    #asst.addUserMessage("Hello assistant. How many files are in the current directory?")
    #asst.addUserMessage("Hello assistant. How are you?")
    #asst.run()

    asst.loadMessages("./ant_history.json")
    #asst.saveMessages("./ant_history_out.json")

    asst.addUserMessage("Cool!. Can you now roll a d20?")
    asst.run()
    asst.saveMessages("./ant_history_out.json")