import sys
import uuid
import os
import time
from flask import Flask, render_template, request, session, redirect, url_for
from flask_socketio import SocketIO, emit, join_room

# Add parent directory to path to import from main project
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from callbacks import WebCallbackHandler
from api import Assistant
import model_tools
from model_tools import Toolbox, getFullInstructionMessage
from main import makeNewStory, model_instruction
from utils import *

app = Flask(__name__)
app.secret_key = os.urandom(24)
socketio = SocketIO(app, cors_allowed_origins="*")

# Store active sessions
assistant_sessions = {}
user_stories = {}  # Map user sessions to story sessions

def get_stories():
    return os.listdir("./stories")

def initialize_assistant(session_id, story_name):
    """Initialize a new assistant for the session"""
    model_tools.current_story = story_name
    
    # Create toolbox with the same tools as in main.py
    dm_tb = Toolbox([
        model_tools.roll_dice_tool_handler,
        model_tools.read_story_file_tool_handler,
        model_tools.list_story_files_tool_handler,
        model_tools.write_story_file_tool_handler,
        model_tools.read_story_summary_tool_handler,
        model_tools.summarize_story_tool_handler
    ])
    
    web_handler = WebCallbackHandler(socketio, session_id)
    asst = Assistant(
        model_name = "claude-3-7-sonnet-20250219",
        #model_name = "claude-3-haiku-20240307",
        #model_name = "gpt-4o",
        #model_name = "gpt-4o-mini",
        #model_name = "gpt-4.5-preview",
        tb=dm_tb,
        instructions=model_instruction,
        callback_handler=web_handler
    )
    
    # Store the assistant and web handler in active sessions (initialized = False)
    assistant_sessions[session_id] = {
            'assistant': asst,
            'story': story_name,
            'web_handler': web_handler,
            'initialized': False
    }

    save_path = f"./stories/{story_name}/history.json"
    if asst.load(save_path):
        last_message = asst.messages[-1]['content'][-1]['text'] # loading and saving for anthropic models only
        if debug():
            print(bold, cyan, f"Loaded existing history file for story", endc)
            print(bold, cyan, f"last message was: {last_message}", endc)
        assistant_sessions[session_id]['initialized'] = True
        socketio.emit('assistant_ready', room=session_id)
        web_handler.turn_end()
        time.sleep(0.3)
        asst.cb.text_output(last_message)
        return session_id


    if debug(): print(bold, cyan, f"Created new history file", endc)
    asst.addUserMessage(getFullInstructionMessage())
    asst.run()
    asst.save(save_path)
    
    # Call turn_end_callback manually
    web_handler.turn_end()
    
    # Mark as initialized
    assistant_sessions[session_id]['initialized'] = True
    
    # Send an event that assistant is ready
    socketio.emit('assistant_ready', room=session_id)
    
    return session_id

# Routes
@app.route('/')
def index():
    """Main route - displays the chat interface with sidebar"""
    stories = get_stories()
    return render_template('index.html', stories=stories)

@app.route('/create_story', methods=['POST'])
def create_story():
    """Handle creation of a new story"""
    story_name = request.form.get('new_story_name', '').strip()
    if not story_name:
        return redirect(url_for('index'))
    
    # Create the story directory
    makeNewStory(story_name)
    
    # Generate a session ID
    session_id = str(uuid.uuid4())
    session['session_id'] = session_id
    session['story'] = story_name
    user_stories[session_id] = story_name
    
    # Start the assistant initialization in a background thread
    from threading import Thread
    thread = Thread(target=initialize_assistant, args=(session_id, story_name))
    thread.daemon = True
    thread.start()
    
    return redirect(url_for('index'))

@app.route('/select/<story_name>')
def select_story(story_name):
    """Handle selection of an existing story"""
    if story_name not in get_stories():
        return redirect(url_for('index'))
    
    # Generate a session ID
    session_id = str(uuid.uuid4())
    session['session_id'] = session_id
    session['story'] = story_name
    user_stories[session_id] = story_name

    from threading import Thread
    thread = Thread(target=initialize_assistant, args=(session_id, story_name))
    thread.daemon = True
    thread.start()
    
    # Redirect back to the main page with the selected story right away
    return redirect(url_for('index'))

# SocketIO events
@socketio.on('connect')
def handle_connect():
    """Handle client connection"""
    if 'session_id' in session:
        session_id = session['session_id']
        join_room(session_id)
        
        # Send story selection to client
        if session_id in assistant_sessions:
            story = assistant_sessions[session_id]['story']
            emit('story_selected', {'story': story}, room=session_id)
            emit('connected', {'status': 'connected', 'story': story}, room=session_id)
            
            # Send processing indicator if the assistant is still initializing
            if session_id in assistant_sessions and not assistant_sessions[session_id].get('initialized', False):
                emit('processing_started', room=session_id)

@socketio.on('user_message')
def handle_user_message(data):
    """Handle user messages"""
    session_id = session.get('session_id')
    if not session_id or session_id not in assistant_sessions:
        return
    
    user_message = data.get('message', '').strip()
    if not user_message:
        return
    
    # Send message to assistant
    asst = assistant_sessions[session_id]['assistant']
    asst.addUserMessage(user_message)
    
    # Emit the user message to be displayed
    emit('user_message_received', {'message': user_message}, room=session_id)
    
    # Process with assistant
    asst.run()
    asst.save(f"./stories/{assistant_sessions[session_id]['story']}/history.json")
    
    # Call turn_end_callback manually
    if session_id in assistant_sessions and 'web_handler' in assistant_sessions[session_id]:
        assistant_sessions[session_id]['web_handler'].turn_end()

@socketio.on('request_stories')
def handle_request_stories():
    """Send list of available stories to client"""
    stories = get_stories()
    emit('story_list_update', {'stories': stories})

if __name__ == '__main__':
    socketio.run(app, debug=False, host='0.0.0.0', port=5000)
