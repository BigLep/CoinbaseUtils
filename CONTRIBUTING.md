# Contributing

Thanks for your interest in contributing to CoinbaseUtils.

## Commit messages: use Conventional Commits

We use **[Conventional Commits](https://www.conventionalcommits.org/)** for all commit messages. This keeps history readable and enables tooling (changelogs, versioning, etc.).

### Format

```
<type>[optional scope]: <description>

[optional body]

[optional footer(s)]
```

- **type** (required): What kind of change this is.
- **scope** (optional): Area of the codebase (e.g. `lambda`, `docs`, `scripts`).
- **description** (required): Short, imperative summary (e.g. "add upload script" not "added upload script").

### Types we use

| Type       | Use for |
|-----------|---------|
| `feat`    | New feature |
| `fix`     | Bug fix |
| `docs`    | Documentation only (README, LEARNINGS, comments) |
| `style`   | Formatting, whitespace, no code change |
| `refactor`| Code change that is not a fix or a feature |
| `test`    | Adding or updating tests |
| `chore`   | Build, config, tooling, dependencies |

### Examples

```bash
feat: add S3 config upload script
fix(lambda): use SecretId for get_secret_value
docs: update LEARNINGS.md with Lambda state
chore: pin cryptography in requirements.txt
refactor(coinbase_trader): support name or id in key file
```

### Rules

- **Always** use a conventional commit message for every commit.
- Use present tense, imperative mood in the description: "add" not "added", "fix" not "fixed".
- Keep the subject line under about 72 characters; add a body if you need more detail.
