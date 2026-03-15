from groq import Groq
import subprocess
import os
from dotenv import load_dotenv

load_dotenv()

client = Groq(api_key=os.getenv("GROQ_API_KEY"))

# user_input = input("Enter task: ")

def generate_command(user_input):

  system_prompt = """
  You are a Linux terminal expert.

  Convert natural language instructions into Linux commands.

  Rules:
  - Return ONLY the command
  - No explanations
  - Output a single command
  """

  response = client.chat.completions.create(
  model="llama-3.3-70b-versatile",
  messages=[
  {"role": "system", "content": system_prompt},

  {"role": "user", "content": "list files"},
  {"role": "assistant", "content": "ls"},

  {"role": "user", "content": "show disk usage"},
  {"role": "assistant", "content": "df -h"},

  {"role": "user", "content": user_input}
  ],
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

    result = subprocess.run(
        command,
        shell=True,
        capture_output=True,
        text=True
    )

    print("\nOUTPUT:\n")
    print(result.stdout)

    if result.stderr:
        print("ERROR:\n", result.stderr)

def main():

    print("AI Linux Terminal")
    print("Type 'exit' to quit\n")

    while True:

        user_input = input(">>> ")

        if user_input.lower() == "exit":
            break

        command = generate_command(user_input)

        print("\nGenerated command:", command)

        if not is_safe(command):
            print("Blocked: potentially dangerous command")
            continue

        confirm = input("Execute? (y/n): ")

        if confirm.lower() == "y":
            execute_command(command)

if __name__ == "__main__":
    main()