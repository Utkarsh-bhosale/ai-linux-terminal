from groq import Groq
import subprocess
import os
from dotenv import load_dotenv
import json
from datetime import datetime
import readline
from rich.console import Console
from rich.panel import Panel
from rich.text import Text

console = Console()

HISTORY_FILE = ".terminal_history"

try:
    readline.read_history_file(HISTORY_FILE)
except FileNotFoundError:
    pass

load_dotenv()

client = Groq(api_key=os.getenv("GROQ_API_KEY"))

# user_input = input("Enter task: ")
system_prompt = """
  You are a Linux terminal expert.

  Convert natural language instructions into Linux commands.

  Rules:
  - Return ONLY the command
  - No explanations
  - Output a single command
  """
  
# Conversation history
conversation = [
    {"role": "system", "content": system_prompt},

    {"role": "user", "content": "list files"},
    {"role": "assistant", "content": "ls"},

    {"role": "user", "content": "show disk usage"},
    {"role": "assistant", "content": "df -h"}
]

def generate_command(user_input):
    
  cwd = os.getcwd()
  user_input = f"Current directory: {cwd}\nInstruction: {user_input}"
  
  conversation.append({
      "role":"user",
      "content":user_input
  })  

  response = client.chat.completions.create(
    model="llama-3.3-70b-versatile",
    messages=conversation,
    max_tokens=50
  )

  command = response.choices[0].message.content
  
  return command

def is_safe(command):

  blocked = ["rm -rf /", "shutdown", "reboot", "mkfs"]

  for word in blocked:
      if word in command:
          return False

  return True

def execute_command(command):

    commands = command.split(";")

    full_output = ""
    full_error = ""

    for cmd in commands:
        cmd = cmd.strip()

        # handle cd separately
        if cmd.startswith("cd"):
            try:
                path = cmd.split("cd ", 1)[1]
                os.chdir(os.path.expanduser(path))
                msg = f"[bold yellow]Changed directory to:[/bold yellow] {os.getcwd()}"
                console.print(msg)
                full_output += msg + "\n"
            except Exception as e:
                err = str(e)
                console.print("[bold red]ERROR[/bold red]")
                console.print(result.stderr)
                full_error += err + "\n"
            continue

        result = subprocess.run(
            cmd,
            shell=True,
            capture_output=True,
            text=True
        )

        console.print("\n[bold green]OUTPUT[/bold green]")
        console.print(result.stdout)

        if result.stderr:
            console.print("[bold red]ERROR[/bold red]")
            console.print(result.stderr)

        full_output += result.stdout
        full_error += result.stderr

    return full_output, full_error

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
LOG_FILE = os.path.join(BASE_DIR, "logs", "command_logs.json")
os.makedirs(os.path.join(BASE_DIR, "logs"), exist_ok=True)

def log_command(user_input, command, output, error):

    log_entry = {
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "user_input": user_input,
        "command": command,
        "cwd": os.getcwd(),
        "output": output,
        "error": error
    }

    try:
        with open(LOG_FILE, "r") as f:
            logs = json.load(f)
    except:
        logs = []

    logs.append(log_entry)

    with open(LOG_FILE, "w") as f:
        json.dump(logs, f, indent=4)

def main():
    
    console.print(
    Panel.fit(
        "[bold cyan]AI Linux Terminal[/bold cyan]\n[green]Natural Language → Linux Commands[/green]",
        border_style="cyan"
        )
    )

    console.print("[yellow]Type 'exit' to quit[/yellow]\n")

    while True:

        user_input = console.input(f"[bold magenta]{os.getcwd()}[/bold magenta] >>> ")
        
        readline.add_history(user_input)

        if user_input.lower() == "exit":
            readline.write_history_file(HISTORY_FILE)
            break

        command = generate_command(user_input)

        console.print(f"\n[bold blue]Generated command:[/bold blue] {command}")

        if not is_safe(command):
            print("Blocked: potentially dangerous command")
            continue

        confirm = input("Execute? (y/n): ")

        if confirm.lower() == "y":
            output, error = execute_command(command)
            log_command(user_input, command, output, error) 

if __name__ == "__main__":
    main()