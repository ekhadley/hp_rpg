import os
import json
import time

import openai
import anthropic

from utils import *
import model_tools
from model_tools import Tool, Toolbox
from callbacks import example_text_callback, example_tool_request_callback, example_tool_submit_callback


class OpenAIAssistant:
    def __init__(
            self,
            model_name:str = None,
            tb:Toolbox = None,
            instructions="",
            text_output_callback: callable = None,
            tool_request_callback: callable = None,
            tool_submit_callback: callable = None,
            turn_end_callback: callable = None
        ):
        self.model_name = model_name if model_name else "gpt-4o-mini"
        self.tb = tb
        self.tool_schemas = tb.openai_schemas if tb else []
        self.assistant = openai.beta.assistants.create(
            instructions = instructions,
            model = self.model_name,
            tools = self.tool_schemas
        )
        self.assistant_id = self.assistant.id
        self.thread = openai.beta.threads.create()
        self.thread_id = self.thread.id

        self.text_output_callback = text_output_callback
        self.tool_request_callback = tool_request_callback
        self.tool_submit_callback = tool_submit_callback
        self.turn_end_callback = turn_end_callback
    
    def getMessages(self):
        return openai.beta.threads.messages.list(self.thread_id)
    
    def printMessages(self): # seems like tool calls/submissions are not visible in the history?
        messages = self.getMessages().to_dict()
        if len(messages['data']) == 0: 
            print("No messages in the history.")
            return
        for message in messages["data"]:
            role = message["role"]
            content = message["content"]
            color = magenta if role == 'assistant' else yellow
            content_str = ""
            if isinstance(content, list):
                for item in content:
                    if item['type'] == 'tool_use':
                        tool_name, tool_input = item['name'], item['input']
                        content_str += f"{blue} using tool: {tool_name}({tool_input}){endc}"
                    elif item['type'] == 'tool_result':
                        tool_result = item['content']
                        content_str += f"{blue} tool_result: {tool_name}({tool_input}) = {tool_result}{endc}"
                    else:
                        content_str += color + item['text']['value'] + endc
            else:
                content_str = content
            print(color, f"{role.capitalize()}: {content_str}")
    
    def printMessagesRaw(self) -> None:
        print(json.dumps(self.getMessages().to_dict(), indent=4))

    def addUserMessage(self, prompt:str) -> None:
        openai.beta.threads.messages.create(
            thread_id = self.thread_id,
            role = "user",
            content = prompt
        ) 

    def submitToolOutputs(self, run_id: str, outputs: list): # returns a stream on a new run, like how getStream does
        return openai.beta.threads.runs.submit_tool_outputs(
            thread_id = self.thread_id,
            run_id = run_id,
            tool_outputs = outputs,
            stream = True
        )

    def getStream(self):
        return openai.beta.threads.runs.stream(thread_id=self.thread_id, assistant_id=self.assistant_id)

    # when a tool is needed in a thread, the run ends. You submitting the tool outputs gives a new run, continuing the thread.
    def run(self) -> None:
        with self.getStream() as stream:
            self.runStream(stream)
        if self.turn_end_callback:
            self.turn_end_callback()

    def runStream(self, stream,) -> None:
        tool_submit_required = False
        for event in stream:
            if event.event == "thread.message.delta":
                tokens = "".join([block.text.value for block in event.data.delta.content])
                if debug(): print(yellow, f"Assistant: {tokens}", endc)
                if self.text_output_callback:
                    self.text_output_callback(text=tokens)
            elif event.event == "thread.run.requires_action":
                tool_submit_required = True
                required_outputs = event.data.required_action.submit_tool_outputs.tool_calls
                tool_names = []
                tool_inputss = []
                tool_outputs = []
                if debug(): print(red, green, required_outputs, endc)
                for tool_call in required_outputs:
                    tool_name = tool_call.function.name
                    tool_names.append(tool_name)
                    arguments = tool_call.function.arguments
                    tool_inputss.append(arguments)
                    tool_id = tool_call.id
                    if self.tool_request_callback:
                        self.tool_request_callback(name=tool_name, inputs=arguments)
                    result = self.tb.getToolResult(tool_name, arguments)
                    tool_outputs.append({
                        "tool_call_id": tool_id,
                        "output": result
                    })
            else:
                if debug():
                    if event.event == "thread.run.failed":
                        print(bold, red, f"ERROR: RUN FAILED:\n")
                        print(event.to_dict())
                    else:
                        print(event.event)

        stream.close()
        if tool_submit_required:
            if self.tool_submit_callback:
                self.tool_submit_callback(names=tool_names, inputs=tool_inputss, results=[r['output'] for r in tool_outputs])
            self.runStream(self.submitToolOutputs(event.data.id, tool_outputs))

class AnthropicAssistant:
    def __init__(
            self,
            model_name:str = None,
            tb:Toolbox = None,
            instructions = "",
            text_output_callback: callable = None,
            tool_request_callback: callable = None,
            tool_submit_callback: callable = None,
            turn_end_callback: callable = None
        ):
        self.model_name = model_name if model_name else "claude-3-haiku-20240307"
        self.client = anthropic.Anthropic()
        self.tb = tb
        self.tool_schemas = tb.anthropic_schemas if tb else []
        self.messages: list[dict] = []
        self.max_tokens = 4096

        self.addUserMessage(instructions)

        self.text_output_callback = text_output_callback
        self.tool_request_callback = tool_request_callback
        self.tool_submit_callback = tool_submit_callback
        self.turn_end_callback = turn_end_callback
    
    def printMessages(self) -> None:
        if not self.messages:
            print("No messages in the history.")
            return
        for message in self.messages:
            role = message["role"]
            content = message["content"]
            color = magenta if role == 'assistant' else yellow
            content_str = ""
            if isinstance(content, list):
                for item in content:
                    if item['type'] == 'tool_use':
                        tool_name, tool_input = item['name'], item['input']
                        content_str += f"{blue} using tool: {tool_name}({tool_input}){endc}"
                    elif item['type'] == 'tool_result':
                        tool_result = item['content']
                        content_str += f"{blue} tool_result: {tool_name}({tool_input}) = {tool_result}{endc}"
                    else:
                        content_str += color + item['text'] + endc
            else:
                content_str = content
            print(color, f"{role.capitalize()}: {content_str}")
            
    def printMessagesRaw(self) -> None:
        print(json.dumps(self.messages, indent=4))
    
    def addUserMessage(self, content) -> None:
        self.messages.append({"role": "user", "content": content})
    def addAssistantMessage(self, content) -> None:
        self.messages.append({"role": "assistant", "content": content})

    def getStream(self):
        return self.client.messages.stream(max_tokens=self.max_tokens, messages=self.messages, model=self.model_name, tools=self.tool_schemas)

    def run(self) -> str: 
        with self.getStream() as stream:
            for event in stream:
                if event.type == "text":
                    if debug(): print(yellow, f"Assistant: {event.text}", endc)
                    if self.text_output_callback:
                        self.text_output_callback(text=event.text)
                elif event.type == "message_stop":
                    self.addAssistantMessage([block.to_dict() for block in event.message.content])
                    if event.message.stop_reason == "tool_use":
                        if debug(): print(pink, "tool use requested: ", endc, event)
                        tool_names = []
                        tool_inputss = []
                        tool_results = []
                        for block in event.message.content:
                            if block.type == "tool_use":
                                tool_name = block.name
                                tool_names.append(tool_name)
                                tool_inputs = block.input
                                tool_inputss.append(tool_inputs)
                                if self.tool_request_callback:
                                    self.tool_request_callback(name=tool_name, inputs=tool_inputs)
                                tool_result = self.tb.getToolResult(tool_name, tool_inputs)
                                tool_call_id = block.id
                                tool_results.append({
                                    "type": "tool_result",
                                    "tool_use_id": tool_call_id,
                                    "content": tool_result
                                })
                        if self.tool_submit_callback:
                            self.tool_submit_callback(names=tool_names, inputs=tool_inputss, results=[r['content'] for r in tool_results])
                        self.addUserMessage(tool_results)
                        self.run()
                        #return
                else:
                    if debug(): print(red, "event: ", endc, event)



def Assistant(
    model_name:str,
    tb:Toolbox,
    instructions,
    text_output_callback: callable = None,
    tool_request_callback: callable = None,
    tool_submit_callback: callable = None
) -> OpenAIAssistant|AnthropicAssistant:

    is_openai_model_name = "gpt" in model_name
    if is_openai_model_name and os.getenv("PROVIDER") == "anthropic":
        raise ValueError(red, bold, "env variable PROVIDER set to anthropic, but model name is openai")
    elif is_openai_model_name:
        if debug(): print(yellow, f"creating OpenAIAssistant with model '{model_name}'", endc)
        return OpenAIAssistant(
            model_name,
            tb,
            instructions,
            text_output_callback,
            tool_request_callback,
            tool_submit_callback,
        )
    else:
        if debug(): print(yellow, f"creating AnthropicAssistant with model '{model_name}'", endc)
        return AnthropicAssistant(
            model_name,
            tb,
            instructions,
            text_output_callback,
            tool_request_callback,
            tool_submit_callback
        )

if __name__ == "__main__":
    basic_tb = Toolbox([
        model_tools.list_directory_tool_handler,
        model_tools.read_file_tool_handler,
        model_tools.random_number_tool_handler
    ])

    asst = Assistant(
        #model_name = "claude-3-7-sonnet-20250219",
        model_name = "claude-3-haiku-20240307",
        tb = basic_tb,
        instructions = "You are a helpful assistant that can use tools.",
        text_output_callback = example_text_callback,
        tool_request_callback = example_tool_request_callback,
        tool_submit_callback = example_tool_submit_callback
    )

    asst.addUserMessage("Hello, assistant. Can you generate a random number from 1-10 and add to it the number of files in the current directory?")
    asst.run()
