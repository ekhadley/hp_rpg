import os
from model_tools import Toolbox, roll_dice_tool_handler, read_file_tool_handler, list_directory_tool_handler
from api import Assistant, example_text_callback, example_tool_request_callback, example_tool_submit_callback


global current_story




model_instruction = "Your job is to operate as an interactive narrator for the world of Harry Potter, enhanced with a dice-based RPG ruleset inspired by D&D but tailored for spellcasting freedom. This system blends immersive storytelling with mechanics to create a dynamic experience. Your role is to weave authentic, atmospheric descriptions and dialogue in J.K. Rowling's style while integrating RPG elements like character stats, dice rolls, and a Magical Stamina system for spellcasting. The simulation maintains chronological consistency, character authenticity, and player agency. You will be given 3 instruction files. One containing the ruleset of the game, one containing all spells and abilities, and one containing instructions for correct narration and storytelling. You should follow these guides precisely to ensure a consistent and engaging experience for the player."
def getFullInstructionMessage() -> str:
    with open("narration_guide.md", "r") as file:
        narration_guide = file.read()
    with open("ruleset.md", "r") as file:
        ruleset = file.read()
    with open("spellbook.md", "r") as file:
        spells = file.read()
    current_story_files = str(os.listdir(f"./stories/{current_story}"))
    full = f"```\n{ruleset}```\n\n```\n{spells}```\n\n```\n{narration_guide}"
    return full

if __name__ == "__main__":
    dm_tb = Toolbox([roll_dice_tool_handler, read_file_tool_handler, list_directory_tool_handler])
    asst = Assistant(
        instructions=model_instruction,
        text_output_callback = example_text_callback,
        tool_request_callback = example_tool_request_callback,
        tool_submit_callback = example_tool_submit_callback
    )
    asst.addUserMessage(getFullInstructionMessage())
    asst.run()
    asst.printMessages()