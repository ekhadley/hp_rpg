import os

purple = '\x1b[38;2;255;0;255m'
blue = '\x1b[38;2;0;0;255m'
brown = '\x1b[38;2;128;128;0m'
cyan = '\x1b[38;2;0;255;255m'
lime = '\x1b[38;2;0;255;0m'
yellow = '\x1b[38;2;255;255;0m'
red = '\x1b[38;2;255;0;0m'
pink = '\x1b[38;2;255;51;204m'
orange = '\x1b[38;2;255;51;0m'
green = '\x1b[38;2;0;0;128m'
gray = '\x1b[38;2;127;127;127m'
magenta = '\x1b[38;2;128;0;128m'
white = '\x1b[38;2;255;255;255m'
bold = '\033[1m'
underline = '\033[4m'
endc = '\033[0m'

STORIES_ROOT_DIR = "stories"
SYSTEM_PROMPTS_ROOT_DIR = "instructions"

def debug() -> bool:
    return os.environ.get("DEBUG", "0").lower() == "1"

def truncateForDebug(obj: object, max_length: int=200):
    obj_str = str(obj)
    if len(obj_str) <= max_length:
        return repr(obj_str)
    return repr(obj_str[:max_length] + "...")

def listStoryNames() -> list[str]:
    return sorted(os.listdir("./stories"))

def makeNewStoryDir(story_name: str):
    os.mkdir(f"./stories/{story_name}")

def storyHistoryExists(story_name: str) -> bool:
    return os.path.exists(f"./stories/{story_name}/history.json")

def getAllSystemInstructions(system_name: str) -> dict[str, str]:
    instructions: dict[str, str] = {}
    for file in os.listdir(f"{SYSTEM_PROMPTS_ROOT_DIR}/{system_name}"):
        with open(f"{SYSTEM_PROMPTS_ROOT_DIR}/{system_name}/{file}", 'r') as file:
            content = file.read()
            instructions[str(file)] = str(content)
    return instructions

def getFullStoryInstruction(system_name: str, story_name: str) -> str: # fetches the base instructions, as well as any of pc.md, story_plan.md, story_summary.md, if they exist.
    sys_instructions = getAllSystemInstructions(system_name)["instructions.md"]
    story_files = ["pc.md", "story_plan.md", "story_summary.md"]
    story_instructions = ""
    for file_name in story_files:
        try:
            with open(f"{STORIES_ROOT_DIR}/{story_name}/{file_name}", 'r') as file:
                content = file.read()
                story_instructions += f"\n---\n{content}"
        except FileNotFoundError:
            continue
    return sys_instructions + story_instructions