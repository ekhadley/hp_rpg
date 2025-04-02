import os

from utils import *
import model_tools
from model_tools import Toolbox, getFullInstructionMessage
from api import Assistant
import callbacks



model_instruction = "Your job is to operate as an interactive narrator for the world of Harry Potter, enhanced with a dice-based RPG ruleset inspired by D&D but tailored for spellcasting freedom. This system blends immersive storytelling with mechanics to create a dynamic experience. Your role is to weave authentic, atmospheric descriptions and dialogue in J.K. Rowling's style while integrating RPG elements like character stats, dice rolls, and a Magical Stamina system for spellcasting. The simulation maintains chronological consistency, character authenticity, and player agency. You will be given 3 instruction files. One containing the ruleset of the game, one containing all spells and abilities, and one containing instructions for correct narration and storytelling. You should follow these guides precisely to ensure a consistent and engaging experience for the player."

def makeNewStory(story_name: str):
    os.mkdir(f"./stories/{story_name}")

def loadIntoStory():
    global current_story
    print("Welcome to the game. Please select a story to play:")
    stories = os.listdir("./stories")
    print(f"\t0. Create a new story.")
    for i, story in zip(range(1, len(stories)+1), stories):
        print(f"\t{i}. {story}")
    choice = int(input("Enter the number of the story you want to play: "))
    if choice == 0:
        story_name = input("Enter the name of the new story: ")
        makeNewStory(story_name)
        model_tools.current_story = current_story = story_name
    else:
        model_tools.current_story = current_story = stories[choice-1]


# TODO:
# - token counting and appropriate warnings.
# - running api cost command?

if __name__ == "__main__":
    loadIntoStory()
    print(f"story selected: {current_story}")

    dm_tb = Toolbox([
        model_tools.roll_dice_tool_handler,
        model_tools.read_story_file_tool_handler, #
        model_tools.list_story_files_tool_handler,
        model_tools.write_story_file_tool_handler, # 
        model_tools.read_story_summary_tool_handler, # 
        model_tools.summarize_story_tool_handler # 
    ])
    asst = Assistant(
        #model_name = "claude-3-7-sonnet-20250219",
        #model_name = "claude-3-haiku-20240307",
        model_name = "gpt-4o-mini",
        #model_name = "gpt-4o-",
        tb = dm_tb,
        instructions = model_instruction,
        callback_handler = callbacks.TerminalPrinter()
    )
    asst.addUserMessage(getFullInstructionMessage())
    asst.run()

    while True:
        asst.addUserMessage(input("\n > "))
        asst.run()
        asst.save(f"{current_story}/history.json")
        #asst.printMessages()
