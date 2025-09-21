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

@socket.on('select_story')
def select_story(data):
    global narrator

    if debug(): print(cyan, f"selected story: '{data}', endc")
    story_name = data['selected_story']
    requested_model = data.get('model_name', None)

    # Determine model to use for this story
    model_name = requested_model if requested_model else "gpt-5"
    history_path = f"./stories/{story_name}/history.json"
    if os.path.exists(history_path):
        try:
            with open(history_path) as f:
                history_data = json.load(f)
                saved_model = history_data.get("model_name")
                if saved_model:
                    model_name = saved_model
        except Exception:
            pass

    narrator = Narrator(
        model_name = model_name,
        socket = socket,
        thinking = True,
        story_name = story_name
    )
    narrator.loadStory()
    if debug(): print(cyan, "narrator initialized", endc)
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
    model_providers = ["anthropic/claude-3.5-haiku", "openai/o3-mini", "gpt-5"]
    return render_template('index.html', stories=listStoryNames(), models=list(model_providers.keys()))

if __name__ == "__main__":
    socket.run(app, port=5001)
