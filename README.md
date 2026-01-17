# Super Play

Automation framework with Playwright, pytest-bdd, and Scrapy.

## Setup

```powershell
# Create virtual environment
python -m venv .venv

# Activate (Windows)
.\.venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Install Playwright browsers
playwright install
```

## Commands

```powershell
# Check setup
python automation_cli.py doctor

# Run gen_food (snapshot mode)
python gen_food.py --url https://example.com

# Run gen_food with mode
python gen_food.py --url https://example.com --mode snapshot
```

## Project Structure

```
super_play/
├── project/
│   └── core/
│       ├── config.py      # Configuration loader
│       ├── artifacts.py   # Run ID and directory management
│       └── log.py         # Logging utilities
├── automation_cli.py      # CLI doctor command
├── gen_food.py            # Food generator stub
└── artifacts/runs/        # Generated artifacts
```
