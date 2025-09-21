import json
import requests

from utils import *
import model_tools
from model_tools import Toolbox
import callbacks
from callbacks import CallbackHandler



class OpenRouterStream:
    """
    Streams responses from OpenRouter. Iteration over the object yields only valid json. Uses the alpha 'Responses' endpoint.
    """
    def __init__(
        self,
        model_name: str,
        messages: list[dict],
        system_prompt: str,
        tools: list[dict],
        thinking_enabled: bool,
        thinking_effort: str,
        key: str
    ):
        self.response_stream = requests.post(
            url = "https://openrouter.ai/api/alpha/responses",
            headers = {
                "Authorization": f"Bearer {key}",
                "Content-Type": "application/json"
            },
            json = {
                "model": model_name,
                "input": messages,
                "system": system_prompt,
                "tools": tools,
                "reasoning": {
                    #"enabled": thinking_enabled,
                    #"effort": thinking_effort if thinking_enabled else None,
                    #"exclude": False,
                },
                "stream": True
            },
            stream = True
        )
        if self.response_stream.status_code != 200:
            error_msg = self.response_stream.text.replace("\\n ", "\n ").replace("\\\"", "\"")
            with open("error.json", "w+") as f: f.write(error_msg)
            assert self.response_stream.status_code == 200, f"Error response from OpenRouter: {self.response_stream.status_code}"
        self.response_iter = self.response_stream.iter_content(chunk_size=1024, decode_unicode=True)
        
        self.content_stream_finished = False
        self.buffer = ""
        self.decode_error_count = 0

    def __iter__(self):
        return self

    def __next__(self) -> dict:
        while True:
            #print(len(self.buffer), repr(self.buffer[:min(100, len(self.buffer))]))
            #print(len(self.buffer), repr(self.buffer))
            if not self.content_stream_finished:
                try:
                    next_chunk = self.response_iter.__next__()
                    self.buffer += next_chunk
                except StopIteration:
                    self.content_stream_finished = True
            elif self.buffer == "" or self.buffer.strip() == "data: [DONE]":
                raise StopIteration
            
            delta_end = self.buffer.find("\n\n")
            delta_str = self.buffer[:delta_end]
            while delta_str.startswith(": "):
                delta_end = self.buffer.find("\n\n")
                delta_str = self.buffer[:delta_end]
                self.buffer = self.buffer[delta_end+2:]

            try:
                delta_clipped = delta_str.lstrip("data: ")
                delta = json.loads(delta_clipped)
                self.buffer = self.buffer[delta_end+2:]
                return delta
            except json.JSONDecodeError as e:
                self.decode_error_count += 1
                if self.decode_error_count > 300:
                    if debug():
                        print(f"{bold+red}({self.decode_error_count}) [{self.content_stream_finished}] Error decoding delta: {repr(delta_clipped)} {endc}")
                        print(f"{bold+orange}{repr(self.buffer)} {endc}")
                    raise e
                pass
    
    def close(self):
        self.response_stream.close()
    
    def __del__(self):
        self.close()

class OpenRouterProvider():
    def __init__(
            self,
            model_name: str,
            toolbox: Toolbox,
            system_prompt: str,
            callback_handler: CallbackHandler,
            thinking_effort: str = "high",
            key: str|None = os.getenv("OPENROUTER_API_KEY"),
        ):
        self.key = key
        self.model_name = model_name
        self.tb = toolbox
        self.tool_schemas = self.tb.getToolSchemas()
        self.system_prompt = system_prompt
        self.messages: list[dict] = []
        self.cb = callback_handler
        self.thinking_enabled = thinking_effort != "none"
        self.thinking_effort = thinking_effort
        

    def addUserMessage(self, content: str) -> None:
        self.messages.append({
            "type": "message",
            "role": "user",
            "content": [{
                "type": "input_text",
                "text": content,
            }],
        })
    def addAssistantMessage(self, content) -> None:
        self.messages.append({
            "type": "message",
            "role": "assistant",
            "content": [{
                "type": "output_text",
                "text": content,
            }],
        })
    def saveMessages(self, path: str) -> None:
        with open(path, "w+") as f:
            json.dump({
                "model_name": self.model_name,
                "messages": self.messages,
            }, f, indent=4)
    def loadMessages(self, path: str) -> list[dict] | None:
        if os.path.exists(path):
            with open(path) as f:
                data = json.load(f)
                if "messages" in data:
                    messages = data["messages"]
                    self.messages = messages
                    if debug(): print(cyan, "Messages loaded successfully.", endc)
                    return messages
        if debug(): print(cyan, "No messages found.", endc)
        return None

    def getStream(self) -> OpenRouterStream:
        return OpenRouterStream(
            model_name = self.model_name,
            messages = self.messages,
            system_prompt = self.system_prompt,
            tools = self.tool_schemas,
            thinking_enabled = self.thinking_enabled,
            thinking_effort = self.thinking_effort,
            key = self.key
        )

    def run(self) -> None:
        currently_outputting_text = False
        currently_thinking = False
        currently_calling_tools = False
        current_reasoning_summary = None
        stream = self.getStream()
        if debug(): print(orange, json.dumps(self.messages, indent=4), endc)
        for event in stream:
            if debug(): print(gray, json.dumps(event, indent=4), endc)
            event_type = event["type"]
            print(gray, event_type, endc)

            if event_type == "response.output_text.delta":
                delta_content = event["delta"]
                if delta_content != "":
                    if debug() and not currently_outputting_text:
                        print(yellow, "Assistant started producing text. . .", endc)
                        currently_outputting_text = True
                    self.cb.text_output(text=delta_content)

            elif event_type == "response.reasoning_summary_text.delta":
                if debug() and not currently_thinking:
                    print(cyan, "Assistant thinking...", endc)
                    currently_thinking = True
                self.cb.think_output(text=event["delta"])

            elif event_type == "response.output_item.added":
                event_item = event["item"]
                event_item_type = event_item["type"]
                print(pink, event_item_type, endc)
                if event_item_type == "function_call":
                    tool_name = event_item["name"]
                    if not currently_calling_tools:
                        currently_calling_tools = True
                        self.cb.tool_request(name=tool_name, inputs={})
                        if debug(): print(cyan, f"tool call started: {tool_name}", endc)

                elif event_item_type == "reasoning":
                    if debug(): print(cyan, "Assistant is thinking...", endc)

                elif event_item_type == "summary_text":
                    currently_thinking = False
                    self.cb.think_end()
                    current_reasoning_summary = event_item["summary"]
                    if debug(): print(cyan, f"Assistant reasoning summary: {event_item["text"]}", endc)

                elif event_item_type == "reasoning":
                    currently_thinking = False
                    self.cb.think_end()
                    if current_reasoning_summary is not None: event_item["summary"] = current_reasoning_summary
                    current_reasoning_summary = None
                    self.messages.append(event_item)

            elif event_type == "response.completed":
                response = event["response"]
                response_output = response["output"]

                for item in response_output:
                    item_type = item["type"]
                    print(purple, item_type, endc)
                    if item_type == "function_call":
                        tool_name, tool_call_id, tool_arguments  = item["name"], item["call_id"], item["arguments"]
                        print(cyan, f"tool call arguments: {repr(tool_arguments)}", endc)
                        result = self.tb.getToolResult(tool_name, tool_arguments)
                        if debug(): print(pink, f"tool call completed: {tool_name}({truncateForDebug(tool_arguments)}) with result: {truncateForDebug(result)}", endc)
                        
                        self.submitToolCall(tool_name, tool_arguments, tool_call_id)
                        self.cb.tool_submit(names=[tool_name], inputs=[tool_arguments], results=[result])
                        self.submitToolOutput(tool_call_id, result)

                    elif item_type == "message" and not currently_calling_tools:
                        self.messages.append(item)
                    
                    elif item_type == "reasoning":
                        print(item)
                        self.messages.append(item)

                stream.close()
                if currently_calling_tools:
                    self.run()
                if debug(): print(orange, json.dumps(self.messages, indent=4), endc)
                return
            elif debug():
                if event_type == "response.failed":
                    print(bold, red, f"ERROR: RUN FAILED:\n")
                    print(event)
                if currently_outputting_text:
                    print(yellow, "Assistant finished producing text.", endc)
                    currently_outputting_text = False
        if debug(): print(orange, json.dumps(self.messages, indent=4), endc)
        stream.close()
        self.cb.turn_end()

    def submitToolCall(self, tool_name: str, tool_arguments: dict, tool_call_id: str) -> None:
        self.messages.append({
            "type": "function_call",
            "id": tool_call_id,
            "call_id": tool_call_id,
            "name": tool_name,
            "arguments": tool_arguments,
        })
    def submitToolOutput(self, call_id: str, tool_output: dict) -> None:
        self.messages.append({
            "type": "function_call_output",
            "id": call_id,
            "call_id": call_id,
            "output": str(tool_output)
        })
    

if __name__ == "_main__":
    basic_tb = Toolbox([ # demo
        model_tools.list_directory_tool_handler,
        model_tools.read_file_tool_handler,
        model_tools.random_number_tool_handler
    ])

    asst = OpenRouterProvider(
        model_name = "openai/o4-mini",
        #model_name = "openai/gpt-4o-mini",
        #model_name = "anthropic/claude-3-haiku",
        #model_name = "anthropic/claude-sonnet-4",
        system_prompt = "You are a helpful assistant that can use tools.",
        thinking_effort = "low",
        toolbox = basic_tb,
        callback_handler = callbacks.TerminalPrinter(),
    )

    #asst.addUserMessage("Hello assistant. Can you generate a random number from 1-10 and add to it the number of files in the current directory? Use your reasoning.")
    #asst.addUserMessage("Hello assistant. Can you generate 2 random numbers from 1-10 and add them together?")
    asst.addUserMessage("Hello assistant. What is the surface area of Mars in hectares?")
    #asst.addUserMessage("Hello assistant. Can you generate a random number from 1-10?")
    #asst.addUserMessage("Hello assistant. How many files are in the current directory?")
    #asst.addUserMessage("Hello assistant. How are you?")
    asst.run()
    
    asst.addUserMessage("Can you multiply the number by 2?")
    asst.run()


if __name__ == "__main__":
    response_stream = requests.post(
        url = "https://openrouter.ai/api/alpha/responses",
        headers = {
            "Authorization": f"Bearer {os.getenv('OPENROUTER_API_KEY')}",
            "Content-Type": "application/json"
        },
        json = {
            "model": "openai/o4-mini",
            "input": [
                {
                    "type": "message",
                    "role": "user",
                    "content": "Hello assistant. Can you generate a random number from 1-10?"
                }
            ],
            "system": "You are a helpful assistant that can use tools.",
            "reasoning": {
                #"enabled": thinking_enabled,
                "effort": "high",
                #"exclude": False,
            },
            "stream": True
        },
        stream = True
    )
    response_iter = response_stream.iter_content(chunk_size=1024, decode_unicode=True)

    for chunk in response_iter:
        print()
        print()
        print(chunk)