# Jarvis

A local, private voice assistant for Windows with a HUD-style interface.
Runs on your own PC using [Ollama](https://ollama.com) - no API key, no cloud.

- Live CPU / RAM / GPU / temperature / disk / battery / network stats
- Voice control with the wake word "Jarvis" (English and Tamil)
- Tools: open apps and websites, Google search, notes, system info, list files

## Setup
1. Install Python 3 and Ollama, then run: `ollama pull qwen2.5:7b`
2. `pip install -r requirements.txt`
3. Double-click `start_jarvis.bat` (or run `python jarvis_server.py`)

Use Edge or Chrome and allow the microphone. The server only listens on
`127.0.0.1`, so nothing is exposed to your network.

Notes: GPU stats need an NVIDIA GPU. Windows often hides CPU temperature;
it shows N/A unless the sensor is exposed.
