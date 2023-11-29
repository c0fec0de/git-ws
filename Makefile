.DEFAULT_GOAL := help
source = gitws

.make.pdm:
	@pdm -V 2> /dev/null || pipx install pdm || echo 'Please install PDM: https://pdm.fming.dev/latest/#installation'

.make.pre-commit:
	@pre-commit -V 2> /dev/null || pipx install pre-commit || echo 'Please install pre-commit: https://pre-commit.com/'

.git/hooks/pre-commit:
	pre-commit install --install-hooks
	@touch .git/hooks/pre-commit

.make.lock: pyproject.toml
	pdm info
	pdm lock
	pdm install --group :all
	@touch .make.lock

.PHONY: setup  ## Prepare environment for local development
setup: .make.pdm .make.pre-commit .git/hooks/pre-commit .make.lock

.PHONY: checks  ## Run formatter, linter and all other checks (aka pre-commit)
checks: .make.pre-commit
	pre-commit run --all-files

.PHONY: test  ## Run tests
test: .make.lock
	LANGUAGE=en_US && pdm run pytest -vv -n auto

.PHONY: mypy  ## Run mypy
mypy: .make.lock
	pdm run mypy $(source)

.PHONY: doc  ## Build Documentation
doc: .make.lock
	pdm run make html -C docs

.PHONY: doc-quick  ## Build Documentation - without updating help pages
doc-quick: .make.lock
	pdm run make quick-html -C docs

.PHONY: all  ## Run all steps
all: checks test mypy doc

.PHONY: clean  ## Clear all files list by .gitignore
clean:
	@git clean -Xdf

.PHONY: help  ## Display this message
help:
	@grep -E \
		'^.PHONY: .*?## .*$$' $(MAKEFILE_LIST) | \
		sort | \
		awk 'BEGIN {FS = ".PHONY: |## "}; {printf "\033[36m%-11s\033[0m %s\n", $$2, $$3}'
