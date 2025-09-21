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

def debug() -> bool:
    return os.environ.get("DEBUG", "0").lower() == "1"

def truncateForDebug(obj, max_length=200):
    obj_str = str(obj)
    if len(obj_str) <= max_length:
        return repr(obj_str)
    return repr(obj_str[:max_length] + "...")

def listStoryNames() -> list[str]:
    return sorted(os.listdir("./stories"))

def makeNewStoryDir(story_name: str):
    os.mkdir(f"./stories/{story_name}")

def getFullInstructionMessage() -> str:
    with open("instructions/instructions.md", 'r') as file:
        content = file.read()
    return content

def storyHistoryExists(story_name: str) -> bool:
    return os.path.exists(f"./stories/{story_name}/history.json")

def getFullStoryInstruction(story_name: str) -> str: # fetches the base instructions, as well as any of pc.md, story_plan.md, story_summary.md, if they exist.
    base_instructions = getFullInstructionMessage()
    story_files = ["pc.md", "story_plan.md", "story_summary.md"]
    story_instructions = ""
    for file_name in story_files:
        try:
            with open(f"./stories/{story_name}/{file_name}", 'r') as file:
                content = file.read()
                story_instructions += f"\n---\n{content}"
        except FileNotFoundError:
            continue
    return base_instructions + story_instructions

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

old_hp_system_prompt = "Your job is to operate as an interactive narrator for the world of Harry Potter, enhanced with a dice-based RPG ruleset inspired by D&D. This system blends immersive storytelling with mechanics to create a dynamic experience. Your role is to weave authentic, atmospheric descriptions and dialogue in J.K. Rowling's style while integrating RPG elements like character stats, dice rolls, and a Magical Stamina system for spellcasting. The simulation maintains chronological consistency, character authenticity, and player agency. You will be given 3 instruction files. One containing the ruleset of the game, one containing all spells and abilities, and one containing instructions for correct narration and storytelling. You should follow these guides precisely to ensure a consistent and engaging experience for the player."