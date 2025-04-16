import os
from flask_socketio import SocketIO, emit
from flask import Flask, render_template, redirect, url_for, request

from utils import *
from api import Assistant
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
        model_tools.read_story_planning_guide,
        model_tools.list_story_files_tool_handler,
        model_tools.write_story_file_tool_handler,
        model_tools.read_story_file_tool_handler,
        model_tools.roll_dice_tool_handler,
    ], default_kwargs={"current_story": story_name})

    asst = Assistant(
        #model_name = "claude-3-7-sonnet-20250219",
        model_name = "claude-3-haiku-20240307",
        #model_name = "gpt-4o-mini",
        #model_name = "gpt-4o-",
        toolbox = story_tb,
        callback_handler = WebCallbackHandler(socket),
        instructions = "Your job is to operate as an interactive narrator for the world of Harry Potter, enhanced with a dice-based RPG ruleset inspired by D&D. This system blends immersive storytelling with mechanics to create a dynamic experience. Your role is to weave authentic, atmospheric descriptions and dialogue in J.K. Rowling's style while integrating RPG elements like character stats, dice rolls, and a Magical Stamina system for spellcasting. The simulation maintains chronological consistency, character authenticity, and player agency. You will be given 3 instruction files. One containing the ruleset of the game, one containing all spells and abilities, and one containing instructions for correct narration and storytelling. You should follow these guides precisely to ensure a consistent and engaging experience for the player."
    )

    history_exists = asst.load(story_history_path)
    if history_exists:
        asst.cb.text_output(asst.getLastMessageContent())
    else:
        asst.addUserMessage(getFullInstructionMessage())
        asst.run()
        asst.save(story_history_path)

    socket.emit('assistant_ready')
    socket.emit('turn_end')

@socket.on('user_message')
def user_message(data):
    asst.addUserMessage(data['message'])
    asst.run()
    asst.save(story_history_path)


@socket.on('create_story')
def create_story(data):
    new_story_name = data.story_name.strip()
    if new_story_name:
        makeNewStoryDir(new_story_name)

@app.route('/')
def index():
    return render_template('index.html', stories=listStoryNames())

if __name__ == "__main__":
    socket.run(app, debug=True, port=5001)
