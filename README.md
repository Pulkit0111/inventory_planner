# Inventory Chat Assistant

A simple natural language interface to query your SQLite inventory database using OpenAI's GPT model.

## Setup

1. Create a virtual environment and activate it:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Create a `.env` file in the project root with your OpenAI API key:
```
OPENAI_API_KEY=your_api_key_here
```

4. Place your SQLite database file at `data/retailware.db`

## Usage

Run the application:
```bash
python main.py
```

You can now ask questions about your inventory in natural language. For example:
- "How many products are in the database?"
- "What are the top 5 most expensive products?"
- "Show me all products with stock less than 10"

Type 'exit', 'quit', 'bye', or 'stop' to end the session.

## Requirements

- Python 3.8+
- OpenAI API key
- SQLite database file
