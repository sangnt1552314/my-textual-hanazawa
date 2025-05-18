# My Textual Hanazawa

A Terminal User Interface (TUI) application built with [Textual](https://textual.textualize.io/) to explore and learn the library's capabilities.

## Features

### Radio Player
- Browse and listen to radio stations from Shoutcast
- Simple terminal-based interface for streaming radio
- Real-time station information display

## Requirements

```sh
pip install -r requirements.txt
```

Key dependencies:
- textual
- python-vlc
- python-dotenv
- httpx
- requests

## Setup

1. Clone the repository
2. Copy `.env.example` to `.env`
3. Add your Shoutcast API key to `.env`:
```
SHOUTCAST_API_KEY=your_api_key_here
```

## Usage

Run the application:

```sh
python main.py
```

### Controls
- `q`: Quit application
- `r`: Switch to Radio page
- `s`: Switch to Settings page

## Development

This is a learning project for exploring the Textual library's features and capabilities. The first implementation focuses on creating a radio player interface using Shoutcast's API.

## License

MIT License - See [LICENSE](LICENSE) for details