import os

from utils import *
from callbacks import TerminalPrinter
from api import Assistant
import model_tools

def selectStory() -> str:
    print("Welcome to the game. Please select a story to play:")
    stories = listStoryNames()
    print(f"\t0. Create a new story.")
    for i, story in zip(range(1, len(stories)+1), stories):
        print(f"\t{i}. {story}")
    choice = int(input("Enter the number of the story you want to play: "))
    if choice == 0:
        story_name = input("Enter the name of the new story: ")
        makeNewStoryDir(story_name)
        return story_name
    return stories[choice-1]

# TODO:
# - token counting and appropriate warnings.
# - running api cost command?

if __name__ == "__main__":
    story_name = selectStory()
    if debug(): print(cyan, f"story selected: {story_name}", endc)

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
        callback_handler = TerminalPrinter(),
        instructions = "Your job is to operate as an interactive narrator for the world of Harry Potter, enhanced with a dice-based RPG ruleset inspired by D&D but tailored for spellcasting freedom. This system blends immersive storytelling with mechanics to create a dynamic experience. Your role is to weave authentic, atmospheric descriptions and dialogue in J.K. Rowling's style while integrating RPG elements like character stats, dice rolls, and a Magical Stamina system for spellcasting. The simulation maintains chronological consistency, character authenticity, and player agency. You will be given 3 instruction files. One containing the ruleset of the game, one containing all spells and abilities, and one containing instructions for correct narration and storytelling. You should follow these guides precisely to ensure a consistent and engaging experience for the player."
    )

    history_file_path = f"./stories/{story_name}/history.json"
    history_exists = asst.load(history_file_path)
    if history_exists:
        asst.cb.text_output(asst.getLastMessageContent())
    else:
        asst.addUserMessage(getFullInstructionMessage())
        asst.run()

    while True:
        user_message = input(bold+"\n > "+endc)
        asst.addUserMessage(user_message)
        asst.run()
        asst.save(history_file_path)
        
