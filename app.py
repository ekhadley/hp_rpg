import os
import json
from flask_socketio import SocketIO, emit
from flask import Flask, render_template
from narrator import Narrator
from utils import *

app = Flask(__name__, template_folder="frontend/templates", static_folder="frontend/static")
app.secret_key = os.urandom(24)
socket = SocketIO(app, cors_allowed_origins="*")

narrator = None
models = [
    "openai/gpt-5",
    "openai/o4",
    "openai/gpt-4o-mini",
    "anthropic/claude-opus-4.1",
    "anthropic/claude-sonnet-4",
    "anthropic/claude-3.5-haiku",
    "google/gemini-2.5-pro",
    "moonshotai/kimi-k2-0905"
]

@socket.on('select_story')
def select_story(data):
    global narrator

    if debug(): print(cyan, f"selected story: '{data['selected_story']}'", endc)
    story_name = data['selected_story']
    requested_model = data.get('model_name', None)

    # Determine model to use for this story
    model_name = requested_model if requested_model else models[0]
    if storyHistoryExists(story_name):
        narrator = Narrator.initFromHistory(story_name, socket)
    else:
        narrator = Narrator(
            model_name = model_name,
            socket = socket,
            thinking_effort = "high",
            story_name = story_name
        )
    if debug(): print(cyan, f"narrator initialized for story: '{story_name}'", endc)
    narrator.loadStory()
    emit('model_locked', {"model_name": model_name})


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

    return render_template('index.html', stories=listStoryNames(), models=models)

if __name__ == "__main__":
    socket.run(app, port=5001)
