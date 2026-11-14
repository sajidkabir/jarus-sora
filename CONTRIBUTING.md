# Contributing

Contributions are welcome: bug reports, table checks against the
published SORA documents, worked operations that pin a calculation
down, documentation, and examples. This project aims to stay small,
readable, dependency free, and honest about what it does not yet
compute.

## Getting set up

```bash
git clone https://github.com/sajidkabir/jarus-sora.git
cd jarus-sora
python -m venv .venv
source .venv/bin/activate
pip install -e . pytest
pytest -q
```

All tests should pass before you change anything. The package is
pure standard library, so there is nothing else to install.

## Making a change

1. Fork the repository and create a branch from `main`
   (`git checkout -b feature/short-name`).
2. Keep the change focused. One table, one calculation, or one fix
   per pull request.
3. Add or update tests. A new calculation needs a check against
   the published table or a hand-computed case, and the test should
   say which table pins the behavior down.
4. Never change a table value without citing the source document,
   edition, and table number in the commit message.

## Regulatory honesty

This package computes the JARUS SORA 2.5 tables. It is not an
authorisation, and it is not legal advice. Do not present its
output as an approved assessment: only the competent authority
decides. If a table value disagrees with the current AMC to
Regulation (EU) 2019/947, the AMC wins; open an issue with the
citation.
