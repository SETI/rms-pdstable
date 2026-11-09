# Minimal makefile for Sphinx documentation
#

# You can set these variables from the command line, and also
# from the environment for the first two.
#
# SPHINXBUILD points into the project virtualenv rather than relying on PATH, because a
# sphinx-build found on PATH is often an older installation. Override VENV (as
# scripts/run-all-checks.sh does) to build against another environment.
MAKEFILE_DIR  := $(dir $(lastword $(MAKEFILE_LIST)))
VENV          ?= $(MAKEFILE_DIR)../venv
SPHINXOPTS    ?=
SPHINXBUILD   ?= $(VENV)/bin/sphinx-build
SOURCEDIR     = .
BUILDDIR      = _build

# Put it first so that "make" without argument is like "make help".
help:
	@$(SPHINXBUILD) -M help "$(SOURCEDIR)" "$(BUILDDIR)" $(SPHINXOPTS) $(O)

.PHONY: help Makefile

# Catch-all target: route all unknown targets to Sphinx using the new
# "make mode" option.  $(O) is meant as a shortcut for $(SPHINXOPTS).
%: Makefile
	@$(SPHINXBUILD) -M $@ "$(SOURCEDIR)" "$(BUILDDIR)" $(SPHINXOPTS) $(O)
