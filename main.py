import os

from utils import *
import model_tools
from model_tools import Toolbox, roll_dice_tool_handler, read_story_file_tool_handler, list_story_files_tool_handler, read_cc_guide_tool_handler, write_story_file_tool_handler
from api import Assistant, example_text_callback, example_tool_request_callback, example_tool_submit_callback
import callbacks



model_instruction = "Your job is to operate as an interactive narrator for the world of Harry Potter, enhanced with a dice-based RPG ruleset inspired by D&D but tailored for spellcasting freedom. This system blends immersive storytelling with mechanics to create a dynamic experience. Your role is to weave authentic, atmospheric descriptions and dialogue in J.K. Rowling's style while integrating RPG elements like character stats, dice rolls, and a Magical Stamina system for spellcasting. The simulation maintains chronological consistency, character authenticity, and player agency. You will be given 3 instruction files. One containing the ruleset of the game, one containing all spells and abilities, and one containing instructions for correct narration and storytelling. You should follow these guides precisely to ensure a consistent and engaging experience for the player."
def getFullInstructionMessage() -> str:
    with open("narration_guide.md", "r") as file:
        narration_guide = file.read()
    with open("ruleset.md", "r") as file:
        ruleset = file.read()
    with open("spellbook.md", "r") as file:
        spells = file.read()
    story_files = os.listdir(f"./stories/{current_story}")
    full = f"```\n{ruleset}```\n\n```\n{spells}```\n\n```\n{narration_guide}\n - The files currently in the story directory are: {story_files}```"
    return full

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



if __name__ == "__main__":
    loadIntoStory()
    print(f"story selected: {current_story}")

    dm_tb = Toolbox([
        roll_dice_tool_handler,
        read_story_file_tool_handler,
        list_story_files_tool_handler,
        read_cc_guide_tool_handler,
        write_story_file_tool_handler
    ])
    tp = callbacks.TerminalPrinter()
    asst = Assistant(
        model_name = "claude-3-7-sonnet-20250219",
        #model_name = "gpt-4o-mini",
        tb = dm_tb,
        instructions = model_instruction,
        text_output_callback = tp.text_output_callback,
        tool_request_callback = tp.tool_request_callback,
        #tool_submit_callback = tp.tool_submit_callback
    )
    asst.addUserMessage(getFullInstructionMessage())
    asst.run()

    while True:
        asst.addUserMessage(input("\n > "))
        asst.run()