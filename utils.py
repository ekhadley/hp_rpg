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

def listStoryNames() -> list[str]:
    return os.listdir("./stories")

def makeNewStoryDir(story_name: str):
    os.mkdir(f"./stories/{story_name}")

def getFullInstructionMessage() -> str:
    with open("instructions.md", 'r') as file:
        content = file.read()
    return content

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