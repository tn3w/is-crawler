# Contributing

Contributions welcome — bug reports, feature requests, and pull requests all appreciated.

## Issues

[Open an issue](https://github.com/tn3w/is-crawler/issues) for:

- Bug reports (include UA string, expected vs actual result)
- Feature requests
- Questions about behaviour

## Pull Requests

1. Fork the repo and create a branch from `master`
2. Follow the existing code style (max 90 chars/line, no comments, early returns)
3. Format before submitting:
   ```bash
   pip install black isort
   isort . && black .
   npx prtfm
   ```
4. Describe what changed and why in the PR description

## Crawler DB

The crawler DB comes from [monperrus/crawler-user-agents](https://github.com/monperrus/crawler-user-agents). To add a new crawler pattern, contribute upstream there.

## Code Style

- No comments unless the _why_ is genuinely non-obvious
- Max 90 chars per line
- Early returns over nested branches
- Self-documenting names, no abbreviations

## License

By contributing you agree your changes will be licensed under [Apache-2.0](LICENSE).
