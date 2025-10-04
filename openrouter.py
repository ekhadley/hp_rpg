from codecs import utf_8_decode
import json
import requests
import copy
import os

import model_tools
from model_tools import Toolbox

import callbacks
from callbacks import CallbackHandler

#from utils import *

class OpenRouterStream:
    """
    Streams responses from OpenRouter. Iteration over the object yields only valid json.
    """
    def __init__(
        self,
        model_name: str,
        messages: list[dict],
        tools: list[dict],
        thinking_enabled: bool,
        thinking_effort: str,
        key: str
    ):
        self.response_stream = requests.post(
            url = "https://openrouter.ai/api/v1/chat/completions",
            headers = {
                "Authorization": f"Bearer {key}",
                "Content-Type": "application/json"
            },
            json = {
                "model": model_name,
                "messages": messages,
                #"system": system_prompt,
                "tools": tools,
                "reasoning": {
                    "enabled": thinking_enabled,
                    "effort": thinking_effort if thinking_enabled else None,
                    "exclude": False,
                },
                "stream": True
            },
            stream = True
        )
        if self.response_stream.status_code != 200:
            error_msg = self.response_stream.text.replace("\\n ", "\n ").replace("\\\"", "\"")
            assert self.response_stream.status_code == 200, f"Error response from OpenRouter: {error_msg}"
        self.response_iter = self.response_stream.iter_content(chunk_size=1024, decode_unicode=False)
        
        self.content_stream_finished = False
        self.buffer = ""
        self.decode_retry_count = 0
        self.decode_retry_limit = 1000

    def __iter__(self):
        return self

    def __next__(self) -> dict:
        while True:
            # Ensure we have at least one complete SSE event in the buffer
            def find_event_delimiter(buf: str) -> tuple[int, int]:
                idx_lf = buf.find("\n\n")
                idx_crlf = buf.find("\r\n\r\n")
                if idx_lf == -1 and idx_crlf == -1:
                    return -1, 0
                if idx_lf == -1:
                    return idx_crlf, 4
                if idx_crlf == -1:
                    return idx_lf, 2
                # choose earliest occurrence
                return (idx_lf, 2) if idx_lf < idx_crlf else (idx_crlf, 4)

            while True:
                idx, sep_len = find_event_delimiter(self.buffer)
                if idx != -1:
                    break
                if self.content_stream_finished:
                    break
                try:
                    next_chunk = utf_8_decode(self.response_iter.__next__())[0]
                    self.buffer += next_chunk
                except StopIteration:
                    self.content_stream_finished = True
                    break

            # If stream is finished and buffer is empty or only contains DONE, stop.
            if self.content_stream_finished and (self.buffer.strip() == "" or self.buffer.strip() == "data: [DONE]"):
                raise StopIteration

            # Extract one SSE event (or whatever remains if no delimiter found at end)
            if idx != -1:
                event_chunk = self.buffer[:idx]
                self.buffer = self.buffer[idx + sep_len:]
            else:
                event_chunk = self.buffer
                self.buffer = ""

            if event_chunk.strip() == "":
                # Nothing meaningful in this chunk; continue reading
                continue

            # Parse SSE fields; concatenate multi-line data fields, ignore comments/other fields
            data_lines: list[str] = []
            for raw_line in event_chunk.splitlines():
                line = raw_line.rstrip("\r")
                if not line:
                    continue
                if line.startswith(":"):
                    # SSE comment/keepalive
                    continue
                if line.startswith("data:"):
                    data_lines.append(line[5:].lstrip())
                # Ignore other fields like id:, event:, retry:

            if not data_lines:
                # No data lines in this event; continue
                continue

            data_payload = "\n".join(data_lines).strip()

            if data_payload == "[DONE]":
                # Mark finished; only stop if buffer drained
                self.content_stream_finished = True
                if self.buffer.strip() == "":
                    raise StopIteration
                continue

            try:
                parsed = json.loads(data_payload)
                self.decode_retry_count = 0
                return parsed
            except json.JSONDecodeError as e:
                self.decode_retry_count += 1
                if self.decode_retry_count > self.decode_retry_limit or self.content_stream_finished:
                    if debug():
                        print(f"{bold+red}({self.decode_retry_count}) [{self.content_stream_finished}] Error decoding data payload: {repr(data_payload)} {endc}")
                        print(f"{bold+orange}{repr(self.buffer)} {endc}")
                    raise e
                # On transient decode issues, keep accumulating more data
                continue
    
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
        assert key is not None, "OPENROUTER_API_KEY is not set"
        self.key: str = key
        self.model_name: str = model_name
        self.tb: Toolbox = toolbox
        self.tool_schemas = self.tb.getToolSchemas()
        self.system_prompt = system_prompt
        self.messages: list[dict] = []
        self.cb = callback_handler
        self.thinking_enabled = thinking_effort != "none"
        self.thinking_effort = thinking_effort
        
        self.addSystemMessage(system_prompt)

    def addSystemMessage(self, content: str) -> None:
        self.messages.insert(0, {
            "role": "system",
            "content": content,
        })
    def addUserMessage(self, content: str) -> None:
        self.messages.append({
            "role": "user",
            "content": content,
        })
    def addAssistantMessage(self, content) -> None:
        self.messages.append({
            "role": "assistant",
            "content": content,
        })
    def saveMessages(self, path: str, **kwargs) -> None:
        with open(path, "w+") as f:
            json.dump({
                "model_name": kwargs.get("model_name", self.model_name),
                "system_name": kwargs.get("system_name", ""),
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
            tools = self.tool_schemas,
            thinking_enabled = self.thinking_enabled,
            thinking_effort = self.thinking_effort,
            key = self.key
        )

    def run(self) -> None:
        currently_outputting_text = False
        stream = self.getStream()
        #print(orange, json.dumps(self.messages, indent=4), endc)
        for event in stream:
            #print(gray if not "tool_calls" in str(event) else red, json.dumps(event, indent=4), endc)
            event_item = event["choices"][0]
            delta = event_item["delta"]
            if self.messages[-1]["role"] != "assistant":
                self.messages.append(copy.deepcopy(delta))
                if "tool_calls" in delta: self.messages[-1]["tool_calls"] = [] # only initialize a tool calls array if it's in the delta. gets repopulated later.
                self.messages[-1]["reasoning"] = ""
                self.messages[-1]["reasoning_details"] = [{}]

            delta_content = delta.get("content", None)
            if delta_content is not None and delta_content != "":
                if delta_content != "": self.messages[-1]["content"] += delta_content
                if not currently_outputting_text:
                    if debug(): print(yellow, "Assistant producing text. . .", endc)
                    currently_outputting_text = True
                self.cb.text_output(text=delta_content)
            
            reasoning_delta = delta.get("reasoning", None)
            if reasoning_delta is not None and reasoning_delta != "":
                self.messages[-1]["reasoning"] += reasoning_delta
                self.cb.think_output(text=reasoning_delta)
            
            reasoning_details = delta.get("reasoning_details", [{}])
            if reasoning_details != [{}] and reasoning_details != []:
                self.messages[-1]["reasoning_details"] = reasoning_details
                self.messages[-1]["reasoning_details"][0]["text"] = self.messages[-1]["reasoning"]

            tool_calls = delta.get("tool_calls", [])
            assert len(tool_calls) < 2, f"Tool calls: {tool_calls}"
            for tool_call in tool_calls:
                if "id" in tool_call: # only the first delta has the id/name. subsequent deltas are for arguments only
                    if "tool_calls" not in self.messages[-1]: self.messages[-1]["tool_calls"] = []
                    self.messages[-1]["tool_calls"].append(tool_call)
                    tool_name = tool_call["function"]["name"]
                    self.cb.tool_request(name=tool_name, inputs={})
                    if debug(): print(pink, f"Tool call started: {tool_name}()", endc)
                self.messages[-1]["tool_calls"][-1]["function"]["arguments"] += tool_call["function"]["arguments"]
            
            finish_reason = event_item.get("finish_reason", "")
            if finish_reason == "stop":
                currently_outputting_text = False
                if debug(): print(yellow, "Assistant finished producing text.", endc)
                return
            
            if finish_reason == "tool_calls":
                for tool_call in self.messages[-1]["tool_calls"]:
                    tool_name, tool_arguments, call_id = tool_call["function"]["name"], tool_call["function"]["arguments"], tool_call["id"]
                    tool_result = self.tb.getToolResult(tool_name, tool_arguments)
                    self.submitToolOutput(call_id, tool_result)
                    
                    if debug(): print(pink, f"Tool call finished: {tool_name}({truncateForDebug(tool_arguments)})", endc)
                    self.cb.tool_submit(names=[tool_name], inputs=[tool_arguments], results=[tool_result])

                #print(orange, json.dumps(self.messages, indent=4), endc)
                self.run()
                return

        #print(orange, json.dumps(self.messages, indent=4), endc)
        stream.close()
        self.cb.turn_end()

    def submitToolCall(self, tool_name: str, tool_arguments: dict, tool_call_id: str) -> None:
        self.messages.append({
            "role": "tool",
            "tool_call_id": tool_call_id,
            "arguments": tool_arguments,
        })
    def submitToolOutput(self, call_id: str, tool_output: str) -> None:
        self.messages.append({
            "role": "tool",
            "tool_call_id": call_id,
            "content": tool_output,
        })
    

if __name__ == "__main__":
    basic_tb = Toolbox([ # demo
        model_tools.list_directory_tool_handler,
        model_tools.read_file_tool_handler,
        model_tools.random_number_tool_handler
    ])

    asst = OpenRouterProvider(
        #model_name = "openai/o4-mini",
        model_name = "openai/gpt-4o-mini",
        #model_name = "anthropic/claude-3-haiku",
        #model_name = "anthropic/claude-3.5-haiku",
        #model_name = "anthropic/claude-sonnet-4",
        system_prompt = "You are a helpful assistant that can use tools and talks like a pirate.",
        thinking_effort = "high",
        toolbox = basic_tb,
        callback_handler = callbacks.TerminalPrinter(),
    )

    #asst.addUserMessage("Hello assistant. Can you generate a random number from 1-10 and add to it the number of files in the current directory?")
    #asst.addUserMessage("Hello assistant. Can you generate a random number from 1-10?")
    #asst.addUserMessage("Hello assistant. Can you generate a random numbers from 1-10 and add it to a random number from 1-20?")
    #asst.addUserMessage("Hello assistant. What is the surface area of Mars in hectares?")
    asst.addUserMessage("Hello assistant. How many files are in the current directory?")
    #asst.addUserMessage("Hello assistant. How are you?")
    asst.run()

    #asst.addUserMessage("Give me 1 fun fact about sheep.")
    #asst.run()
