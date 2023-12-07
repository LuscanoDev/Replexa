# Replexa
An attempt to recreate Alexa and other artificial intelligences using Raspberry Pi, GPT, and Python.

## Installation
# WARNING: YOU NEED A RASPBERRY PI TO RUN THIS!!
First, place your OpenAI key at the beginning of the main.py code.
To install the code libraries, run the following command:

```bash
pip install pygame gtts speechrecognition openai requests
```
After that, connect a button to port 26 to be used as the Replexa's call button and another button to port 16 to mute the voice while the assistant is speaking.

## Usage
Run the program by executing ```python main.py``` and press the Replexa call button. A sound will play to indicate that it is ready to receive commands.

## Notes
A school project from my elective, not recommended for use in real homes unless you want to get frustrated :D
