import os
from flask_socketio import SocketIO, emit
from flask import Flask, render_template

from utils import *
from api import makeAssistant
import model_tools
from callbacks import WebCallbackHandler

app = Flask(__name__, template_folder="app/templates", static_folder="app/static")
app.secret_key = os.urandom(24)
socket = SocketIO(app, cors_allowed_origins="*")

story_name = None
story_history_path = None
asst = None

@socket.on('select_story')
def select_story(data):
    global story_history_path, asst, story_name

    if debug(): print(cyan, f"selected story: '{data}', endc")
    story_name = data['selected_story']
    story_history_path = f"./stories/{story_name}/history.json"
    story_tb = model_tools.Toolbox([ # for actually playing the game
        model_tools.list_story_files_tool_handler,
        model_tools.write_story_file_tool_handler,
        model_tools.append_story_file_tool_handler,
        model_tools.read_story_file_tool_handler,
        model_tools.roll_dice_tool_handler,
    ], default_kwargs={"current_story": story_name})

    asst = makeAssistant(
        #model_name = "claude-3-7-sonnet-20250219",
        #model_name = "claude-opus-4-20250514",
        #model_name = "claude-sonnet-4-20250514",
        #model_name = "claude-3-haiku-20240307",
        #model_name = "gpt-4o-mini",
        #model_name = "gpt-4o",
        model_name = "gpt-4.1-2025-04-14",
        toolbox = story_tb,
        callback_handler = WebCallbackHandler(socket),
        system_prompt = getFullStoryInstruction(story_name)
    )

    history = asst.load(story_history_path)
    if history is not None:
        if debug(): print(cyan, "History loaded successfully.", endc)
        socket.emit('conversation_history', history)
    else:
        if debug(): print(cyan, "No history found, initializing new history file.", endc)
        asst.addUserMessage("<|begin_conversation|>")
        asst.run()
        asst.save(story_history_path)
    socket.emit('assistant_ready')
    socket.emit('turn_end')

@socket.on('user_message')
def user_message(data):
    asst.addUserMessage(data['message'])
    asst.run()
    emit('turn_end')
    asst.save(story_history_path)


@socket.on('create_story')
def create_story(data):
    new_story_name = data['story_name'].strip()
    if new_story_name:
        makeNewStoryDir(new_story_name)

@app.route('/')
def index():
    return render_template('index.html', stories=listStoryNames())

if __name__ == "__main__":
    socket.run(app, port=5001)
