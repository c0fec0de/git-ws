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
	sphinx-apidoc --output-dir api .. ../anyrepo/cli ../docs ../tests $(wildcard ../*.py) --separate --force --module-first
.PHONY: api

gen:
	anyrepo --help > static/cli.txt
	anyrepo clone --help > static/cli.clone.txt
	anyrepo create-manifest --help > static/cli.create-manifest.txt
	anyrepo fetch --help > static/cli.fetch.txt
	anyrepo foreach --help > static/cli.foreach.txt
	anyrepo git --help > static/cli.git.txt
	anyrepo info --help > static/cli.info.txt
	anyrepo init --help > static/cli.init.txt
	anyrepo manifest --help > static/cli.manifest.txt
	anyrepo pull --help > static/cli.pull.txt
	anyrepo rebase --help > static/cli.rebase.txt
	anyrepo status --help > static/cli.status.txt
	anyrepo update --help > static/cli.update.txt
