.DEFAULT_GOAL = help

help: # Print this help page
	echo "TT"

all: poetry.lock # Code Formatting, Testing, Linting, Documentation Build
	tox

poetry.lock: pyproject.toml
	poetry lock