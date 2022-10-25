# Minimal makefile for Sphinx documentation
#

# You can set these variables from the command line, and also
# from the environment for the first two.
SPHINXOPTS    ?=
SPHINXBUILD   ?= sphinx-build
SOURCEDIR     = .
BUILDDIR      = build

# Put it first so that "make" without argument is like "make help".
help:
	@$(SPHINXBUILD) -M help "$(SOURCEDIR)" "$(BUILDDIR)" $(SPHINXOPTS) $(O)

.PHONY: help Makefile

# Catch-all target: route all unknown targets to Sphinx using the new
# "make mode" option.  $(O) is meant as a shortcut for $(SPHINXOPTS).
%: api gen Makefile
	@$(SPHINXBUILD) -M $@ "$(SOURCEDIR)" "$(BUILDDIR)" $(SPHINXOPTS) $(O)


api:
	sphinx-apidoc --output-dir api .. ../gitws/cli ../docs ../tests $(wildcard ../*.py) --separate --force --module-first --maxdepth 2
.PHONY: api

gen:
	rm -f static/git-ws.toml
	git-ws --help > static/cli.txt
	git-ws add --help > static/cli.add.txt
	git-ws checkout --help > static/cli.checkout.txt
	git-ws clone --help > static/cli.clone.txt
	git-ws commit --help > static/cli.commit.txt
	git-ws config --help > static/cli.config.txt
	git-ws config --help > static/cli.config.txt
	git-ws deinit --help > static/cli.deinit.txt
	git-ws fetch --help > static/cli.fetch.txt
	git-ws foreach --help > static/cli.foreach.txt
	git-ws git --help > static/cli.git.txt
	git-ws info --help > static/cli.info.txt
	git-ws info dep-tree --help > static/cli.info.dep-tree.txt
	git-ws init --help > static/cli.init.txt
	git-ws manifest --help > static/cli.manifest.txt
	git-ws manifest create --help > static/cli.manifest.create.txt
	git-ws manifest create -M static/git-ws.toml
	git-ws manifest upgrade --help > static/cli.manifest.upgrade.txt
	git-ws pull --help > static/cli.pull.txt
	git-ws push --help > static/cli.push.txt
	git-ws rebase --help > static/cli.rebase.txt
	git-ws reset --help > static/cli.reset.txt
	git-ws rm --help > static/cli.rm.txt
	git-ws status --help > static/cli.status.txt
	git-ws update --help > static/cli.update.txt
