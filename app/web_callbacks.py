#import sys
#import os
import time

# Add parent directory to path to import from main project
#sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils import *

class WebCallbackHandler:
    def __init__(self, socketio, session_id):
        #self.asst = None
        self.socketio = socketio
        self.session_id = session_id
        self.narrating = False
        
    def text_output(self, text):
        """Handle streaming text output from the LLM"""
        if not self.narrating:
            self.narrating = True
            self.socketio.emit('text_start', room=self.session_id)
        
        # Send complete text chunks without modification
        # The client will handle all text accumulation
        self.socketio.emit('assistant_text', {'text': text, 'timestamp': time.time()}, room=self.session_id)
        
    def tool_request(self, name, inputs):
        """Handle tool requests from the LLM"""
        self.narrating = False
        self.socketio.emit('tool_request', {
            'name': name,
            'inputs': inputs
        }, room=self.session_id)
        
    def tool_submit(self, names, inputs, results):
        """Handle tool results submission"""
        self.narrating = False
        tool_data = []
        for i, name in enumerate(names):
            tool_data.append({
                'name': name,
                'inputs': inputs[i],
                'result': results[i]
            })
        self.socketio.emit('tool_submit', {'tools': tool_data}, room=self.session_id)
            
    def turn_end(self):
        """Handle the end of the LLM's turn"""
        self.narrating = False
        self.socketio.emit('turn_end', room=self.session_id)
