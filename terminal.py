import os

from utils import *
from callbacks import TerminalPrinter
from api import makeAssistant
import model_tools


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
        model_tools.append_story_file_tool_handler,
        model_tools.read_story_file_tool_handler,
        model_tools.roll_dice_tool_handler,
    ], default_kwargs={"current_story": story_name})

    asst = makeAssistant(
        #model_name = "claude-3-7-sonnet-20250219",
        #model_name = "claude-3-haiku-20240307",
        model_name = "gpt-4o-mini",
        #model_name = "gpt-4o-",
        toolbox = story_tb,
        callback_handler = TerminalPrinter(),
        system_prompt = getFullInstructionMessage()
    )

    history_file_path = f"./stories/{story_name}/history.json"
    history_exists = asst.load(history_file_path)
    if history_exists:
        asst.cb.text_output(asst.getLastMessageContent())
    else:
        asst.addUserMessage("Begin.")
        asst.run()

    while True:
        user_message = input(bold+"\n > "+endc)
        asst.addUserMessage(user_message)
        asst.run()
        asst.save(history_file_path)