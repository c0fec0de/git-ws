.DEFAULT_GOAL := help
SOURCE = gitws
DOC_REQUIREMENTS =
DOC_REQUIREMENTS += "sphinx-rtd-theme<2.0.0,>=1.0.0"
DOC_REQUIREMENTS += "sphinx<6.0.0,>=5.1.1"
DOC_REQUIREMENTS += "sphinxemoji>=0.2.0"

.make.pdm:
	@pdm -V 2> /dev/null || \
	(pipx install pdm && pdm self add pdm-version) || \
	echo 'Please install PDM: https://pdm.fming.dev/latest/#installation'

.make.pre-commit:
	@pre-commit -V 2> /dev/null || \
	pipx install pre-commit || \
	echo 'Please install pre-commit: https://pre-commit.com/'

.git/hooks/pre-commit:
	pre-commit install --install-hooks
	@touch .git/hooks/pre-commit

.make.lock: .make.pdm pyproject.toml
	pdm info
	pdm lock
	pdm install --group :all
	@touch .make.lock

.PHONY: lock  ## Setup PDM
lock: .make.lock

.PHONY: setup  ## Prepare environment for local development
setup: .make.pdm .make.pre-commit .git/hooks/pre-commit .make.lock

.PHONY: checks  ## Run formatter, linter and all other checks (aka pre-commit)
checks: .make.pre-commit .git/hooks/pre-commit
	pre-commit run --all-files

.PHONY: test  ## Run tests
test: .make.lock
	LANGUAGE=en_US && pdm run pytest -vv -n auto

.PHONY: mypy  ## Run mypy
mypy: .make.lock
	pdm run mypy $(SOURCE)

.make.venv-doc:
	python3 -m venv .venv-doc
	. .venv-doc/bin/activate && \
	pip install $(DOC_REQUIREMENTS) && \
	pip install -e .
	@touch .make.venv-doc

.PHONY: doc  ## Build Documentation
doc: .make.venv-doc
	. .venv-doc/bin/activate && make html -C docs

.PHONY: doc-quick  ## Build Documentation - without updating help pages
doc-quick: .make.venv-doc
	. .venv-doc/bin/activate && make quick-html -C docs

.PHONY: all  ## Run all steps
all: checks test mypy doc

.PHONY: clean  ## Clear all files list by .gitignore
clean:
	@git clean -Xdf

.PHONY: checkmod  # Hidden Modification Check for CI
checkmod:
	@git status --short
	@git status --short | wc -l | xargs test 0 -eq

.PHONY: publish  # Hidden Publish Target for CI
publish: .make.lock
	pdm publish

.PHONY: help  ## Display this message
help:
	@grep -E \
		'^.PHONY: .*?## .*$$' $(MAKEFILE_LIST) | \
		sort | \
		awk 'BEGIN {FS = ".PHONY: |## "}; {printf "\033[36m%-11s\033[0m %s\n", $$2, $$3}'
