# Initialize a Python virtual environment
python3 -m venv venv
source venv/bin/activate

# Install Poetry
pip install --upgrade pip
pip install poetry

# Initialize a new Poetry project
poetry init --no-interaction --dependency playwright

# Install Playwright dependencies
poetry run playwright install