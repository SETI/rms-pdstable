# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

`rms-pdstable` (import name `pdstable`) reads PDS3 and PDS4 tables, given their labels, into
NumPy arrays with masks. Single package, `src/` layout. `PdsTable` in `__init__.py` is the
public class; `pds3table.py` and `pds4table.py` parse the two label formats into the
`PdsTableInfo` and `PdsColumnInfo` interfaces defined in `pdsxtable.py`.

## Detailed rules

`.claude/rules/*.md` hold the authoritative detailed standards (Python style, testing,
documentation, dependencies, environment, `filecache` and logging usage) and load
automatically. The standards for each kind of document build on `doc_python` and live in
`.claude/skills/`, loaded on demand: `doc-readme`, `doc-user-guide`, `doc-dev-guide`,
`doc-how-to`. So do the process standards: `git-workflow`, `pull-request`, `bug-report`. This
file records only what you would otherwise get wrong.

## Verifying changes

`scripts/run-all-checks.sh` is the single source of truth for which checks must pass — CI is
required to run exactly that set. Run it after any change.

- It requires a virtualenv at `./venv` (override with `VENV`). Create it with
  `./scripts/setup-venv.sh`, which is idempotent. Never install into system Python.
- Useful flags: `-c/--code`, `-d/--docs`, `-m/--markdown`, `-s/--sequential`, or a single check
  such as `--pytest` / `--ruff-check` / `--sphinx`.
- `ruff format`, `bandit`, and `vulture` are disabled by default in the script. Leave them
  disabled. Its mypy check runs on `tests/` only; see the mypy rule below.
- `codespell` enforces American spelling as well as typos. A word it flags that is correct here
  goes in `ignore-words-list` in `pyproject.toml` with its reason; a one-off goes on its own
  line as `codespell:ignore <word>`.
- Docs preview: `./scripts/read-docs.sh`.

## Python style

- **Ruff is the linter of record** for every rule it implements. `ruff check src tests` must
  pass; it runs in CI and in the check script.
- Ruff implements no rule in the `E121`-`E133` range, so continuation-line indentation comes
  from `flake8 --select=E12,E13 src tests`, in CI and as `--flake8-cont` in the check script.
  That makes the `per-file-ignores` in `.flake8` authoritative for those codes alone. The
  `E127` exemption for `pds3table.py` covers one signature whose keyword-only parameters are
  aligned under the first parameter rather than the parenthesis. Elsewhere, continuation lines
  of a signature align with the opening parenthesis.
- **Maximum line length 90.** Test files are exempt from E501.
- `I001` is switched off in `pyproject.toml` because its fix collapses the column-aligned
  imports. Read the comment before re-enabling it.
- Single quotes (`[tool.ruff.format] quote-style = "single"`).
- **No type annotations under `src/`, with one exception** — parameter and return types belong in
  the docstrings. The exception is a **property**, which may carry an inline return annotation
  and then keeps a one-line docstring. **Annotate all test functions**, including `-> None`.
- **Never run `mypy` on `src/`.** It is deliberately unannotated. Run mypy on `tests/` only. The
  `tests.*` override in `pyproject.toml` disables `no-untyped-call` because every call into
  `pdstable` is untyped; `tests/__init__.py` exists so that override matches.
- The `ascii` keyword of `PdsTable` shadows a builtin and carries `# noqa: A002`; it is public
  API, so do not rename it. Do not disable the `A` (builtins) or `N` (naming) rule categories.
- At most 5 positional parameters; the rest keyword-only after `*`.
- No unicode smart quotes, em-dashes, or arrows inside `.py` files (they are fine in `.rst`/`.md`).
- Make the minimal change the task requires, and match the style of the surrounding file.

## Docstrings

Every module, class, function, and method needs one: PEP 257, Google style, but using
`Parameters:` — **not** `Args:`. Wrap to 90 characters. A docstring must be detailed enough that a
black-box test can be written from it alone. Never mention backwards compatibility, change
history, user requests, or issue numbers in a docstring.

## Testing

- The suite is **pytest throughout** — module-level `test_*` functions, no `unittest.TestCase`.
  Write new tests the same way: plain `assert`, fixtures, `pytest.raises(..., match=...)`,
  `@pytest.mark.parametrize`.
- The table tests open `test_files/...` by relative path, so pytest must run from the
  repository root.
- `pytest` addopts already apply `-n auto --cov=src/pdstable --strict-markers --strict-config`,
  so every run is parallel with coverage. Tests must be order-independent.
- `markers` is an empty list plus `--strict-markers`: any unregistered `@pytest.mark.<custom>`
  fails the run. Register it in `pyproject.toml` first.
- `filterwarnings = ["error"]`: any warning a test triggers fails it. `PdsTable` warns about
  illegally formatted values, so a test that loads such a table must catch or assert on those
  warnings.
- The rules target 90% coverage; the suite is at about 86%, so `fail_under` is 85 for now. Raise
  it as tests are added. The pytest `--cov` target and `[tool.coverage.run] source` must name
  the same path.
- Assert one condition per `assert` (no `and`), on exact expected values; `pytest.approx` for
  floats.

## Documentation

Sphinx builds are warning-as-error (`-W`) and nitpicky (`-n`) in CI, in the check script, and in
`read-docs.sh`. `docs/conf.py` also sets `nitpicky = True`, so the ReadTheDocs build is nitpicky
too. The docstrings name types by short names (`Path`, `FCPath`, `Pds3Label`, `callable`);
`napoleon_type_aliases` in `docs/conf.py` maps each to a target intersphinx can resolve, so a new
short name needs an entry there. Never add a `nitpick_ignore_regex` entry for a symbol this
project owns, or for a third-party class that intersphinx can resolve. Narrative docs are `.rst`;
Markdown is only for README/CONTRIBUTING via MyST. Every API symbol named in prose must use a
Sphinx role (`:class:`, `:meth:`, `:func:`, `:mod:`, `:attr:`, `:data:`). American spelling, one
space after a sentence-ending period, no time-anchored words ("new", "legacy", "now").

The check script and CI scan the same Markdown set — `docs/`, `.claude/`, `README.md` and
`CONTRIBUTING.md`. Keep the two in step if either changes.

## Repo etiquette

- Commit subjects: plain capitalized imperative sentence, no type prefix, no trailing period
  (e.g. `Fix crash when PdsTable is given an FCPath (#25)`). PRs are squash-merged onto `main`,
  which appends the `(#N)`.
- Branch names follow `<initials>_<YYMMDD>_<topic>`, e.g. `ms_261021_label_cache`.
- Never commit `build/`, `.coverage`, `.pytest_cache/`, or `src/rms_pdstable.egg-info/`.
- Dependencies go in `pyproject.toml` only; `requirements.txt` contains just `-e .`.
- Versions come from `setuptools_scm`; never hand-edit `src/pdstable/_version.py`.
