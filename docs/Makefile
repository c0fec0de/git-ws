# Minimal makefile for Sphinx documentation
#

# You can set these variables from the command line, and also
# from the environment for the first two.
SPHINXOPTS    ?=
SPHINXBUILD   ?= sphinx-build
SOURCEDIR     = .
BUILDDIR      = build
APIOPTS       = --separate --force --module-first --maxdepth 2 --no-toc

# Put it first so that "make" without argument is like "make help".
help:
	@$(SPHINXBUILD) -M help "$(SOURCEDIR)" "$(BUILDDIR)" $(SPHINXOPTS) $(O)

.PHONY: help Makefile

# Catch-all target: route all unknown targets to Sphinx using the new
# "make mode" option.  $(O) is meant as a shortcut for $(SPHINXOPTS).
%: api gen Makefile
	@$(SPHINXBUILD) -M $@ "$(SOURCEDIR)" "$(BUILDDIR)" $(SPHINXOPTS) $(O)

# Quick HTML rebuild which skips generating the static files:
quick-html: Makefile
	@$(SPHINXBUILD) -M html "$(SOURCEDIR)" "$(BUILDDIR)" $(SPHINXOPTS) $(O)

api:
	sphinx-apidoc --output-dir api .. ../gitws/cli ../docs ../tests $(wildcard ../*.py) $(APIOPTS)
.PHONY: api

gen:
	rm -f static/git-ws.toml
	git-ws --help > static/cli.txt
	git-ws add --help > static/cli.add.txt
	git-ws checkout --help > static/cli.checkout.txt
	git-ws clone --help > static/cli.clone.txt
	git-ws commit --help > static/cli.commit.txt
	git-ws config --help > static/cli.config.txt
	git-ws config delete --help > static/cli.config.delete.txt
	git-ws config files --help > static/cli.config.files.txt
	git-ws config get --help > static/cli.config.get.txt
	git-ws config list --help > static/cli.config.list.txt
	git-ws config set --help > static/cli.config.set.txt
	git-ws default --help > static/cli.default.txt
	git-ws deinit --help > static/cli.deinit.txt
	git-ws dep --help > static/cli.dep.txt
	git-ws dep add --help > static/cli.dep.add.txt
	git-ws dep delete --help > static/cli.dep.delete.txt
	git-ws dep list --help > static/cli.dep.list.txt
	git-ws dep set --help > static/cli.dep.set.txt
	git-ws dep update --help > static/cli.dep.update.txt
	git-ws diff --help > static/cli.diff.txt
	git-ws fetch --help > static/cli.fetch.txt
	git-ws foreach --help > static/cli.foreach.txt
	git-ws git --help > static/cli.git.txt
	git-ws group-filters --help > static/cli.group-filters.txt
	git-ws info --help > static/cli.info.txt
	git-ws info base-path --help > static/cli.info.base-path.txt
	git-ws info dep-tree --help > static/cli.info.dep-tree.txt
	git-ws info main-path --help > static/cli.info.main-path.txt
	git-ws info project-paths --help > static/cli.info.project-paths.txt
	git-ws info workspace-path --help > static/cli.info.workspace-path.txt
	git-ws init --help > static/cli.init.txt
	git-ws manifest --help > static/cli.manifest.txt
	git-ws manifest convert --help > static/cli.manifest.convert.txt
	git-ws manifest create --help > static/cli.manifest.create.txt
	git-ws manifest create -M static/git-ws.toml
	git-ws manifest freeze --help > static/cli.manifest.freeze.txt
	git-ws manifest path --help > static/cli.manifest.path.txt
	git-ws manifest paths --help > static/cli.manifest.paths.txt
	git-ws manifest resolve --help > static/cli.manifest.resolve.txt
	git-ws manifest upgrade --help > static/cli.manifest.upgrade.txt
	git-ws manifest validate --help > static/cli.manifest.validate.txt
	git-ws pull --help > static/cli.pull.txt
	git-ws push --help > static/cli.push.txt
	git-ws rebase --help > static/cli.rebase.txt
	git-ws remote --help > static/cli.remote.txt
	git-ws remote add --help > static/cli.remote.add.txt
	git-ws remote delete --help > static/cli.remote.delete.txt
	git-ws remote list --help > static/cli.remote.list.txt
	git-ws reset --help > static/cli.reset.txt
	git-ws rm --help > static/cli.rm.txt
	git-ws status --help > static/cli.status.txt
	git-ws submodule --help > static/cli.submodule.txt
	git-ws tag --help > static/cli.tag.txt
	git-ws unshallow --help > static/cli.unshallow.txt
	git-ws update --help > static/cli.update.txt
