import os
from flask_socketio import SocketIO, emit




from api import Assistant
import model_tools



model_instruction = "Your job is to operate as an interactive narrator for the world of Harry Potter, enhanced with a dice-based RPG ruleset inspired by D&D but tailored for spellcasting freedom. This system blends immersive storytelling with mechanics to create a dynamic experience. Your role is to weave authentic, atmospheric descriptions and dialogue in J.K. Rowling's style while integrating RPG elements like character stats, dice rolls, and a Magical Stamina system for spellcasting. The simulation maintains chronological consistency, character authenticity, and player agency. You will be given 3 instruction files. One containing the ruleset of the game, one containing all spells and abilities, and one containing instructions for correct narration and storytelling. You should follow these guides precisely to ensure a consistent and engaging experience for the player."
current_story = ""

def makeNewStory(story_name: str):
    os.mkdir(f"./stories/{story_name}")
