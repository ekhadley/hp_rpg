import os
from flask_socketio import SocketIO
from flask import Flask, render_template

from utils import *
from narrator import Narrator

app = Flask(__name__, template_folder="frontend/templates", static_folder="frontend/static")
app.secret_key = os.urandom(24)
socket = SocketIO(app, cors_allowed_origins="*")

narrator = None

@socket.on('select_story')
def select_story(data):
    global narrator

    if debug(): print(cyan, f"selected story: '{data}', endc")
    story_name = data['selected_story']

    narrator = Narrator(
        #model_name = "claude-opus-4-20250514",
        model_name = "claude-sonnet-4-20250514",
        #model_name = "claude-3-7-sonnet-latest",
        #model_name = "claude-3-5-haiku-latest",
        #model_name = "gpt-4.1",
        #model_name = "o3-mini",
        #model_name = "gpt-4o-mini",
        socket = socket,
        thinking = False,
        story_name = story_name
    )
    narrator.loadStory()
    if debug(): print(cyan, "narrator initialized", endc)


@socket.on('user_message')
def handle_user_message(data):
    global narrator
    narrator.handleUserMessage(data)

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
