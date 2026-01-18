# Contributing to AI Bookkeeper

Thank you for your interest in contributing to AI Bookkeeper!

## Development Setup

See the [README.md](README.md#development) for setup instructions.

## Code Style

### Python (Backend)

- **Formatter**: [Ruff](https://docs.astral.sh/ruff/) (auto-formatting)
- **Linter**: Ruff (linting rules)
- **Type Checker**: [mypy](https://mypy.readthedocs.io/) (strict mode)
- **Line Length**: 100 characters
- **Python Version**: 3.11+

Run checks before committing:

```bash
uv run ruff check src/backend tests
uv run ruff format src/backend tests
uv run mypy src/backend
```

### TypeScript/Vue (Frontend)

- **Type Checker**: vue-tsc
- **Formatter**: Prettier (via editor)

Run checks:

```bash
cd src/frontend
pnpm vue-tsc --noEmit
```

## Architecture

This project follows **Hexagonal Architecture** (Ports & Adapters) with **Domain-Driven Design** principles.

### Layer Responsibilities

| Layer | Location | Responsibility |
|-------|----------|----------------|
| **Domain** | `src/backend/domain/` | Pure business logic, entities, value objects |
| **Ports** | `src/backend/ports/` | Interfaces for input (use cases) and output (repositories, services) |
| **Application** | `src/backend/application/` | Use case implementations |
| **Adapters** | `src/backend/adapters/` | Implementations (API, persistence, external services) |

### Key Principles

1. **Domain layer has no external dependencies** — only standard library and typing
2. **Ports define contracts** — abstract interfaces, not implementations
3. **Adapters implement ports** — concrete implementations of repositories and services
4. **Dependency injection** — use cases receive their dependencies, enabling testing

## Testing

### Test Organization

```
tests/
├── domain/           # Unit tests for domain logic
├── application/      # Unit tests for use cases (with mocked ports)
├── adapters/
│   ├── api/          # API integration tests
│   ├── persistence/  # Repository integration tests
│   └── external/     # External service tests (with mocks)
└── fixtures/         # Test fixtures (sample PDFs, etc.)
```

### Coverage Targets

- **Domain Layer**: 90%+
- **Application Layer**: 85%+
- **API Layer**: 85%+
- **Repository Adapters**: 80%+

### Running Tests

```bash
# All tests with coverage
uv run pytest tests -v --cov=src/backend --cov-report=term-missing

# Specific layer
uv run pytest tests/domain -v
uv run pytest tests/adapters/api -v
```

## Commit Messages

Use clear, descriptive commit messages:

- `feat: Add invoice processing use case`
- `fix: Handle duplicate document detection`
- `docs: Update API documentation`
- `test: Add booking service tests`
- `refactor: Extract charge allocation logic`

## Pull Requests

1. Create a feature branch from `main`
2. Make your changes
3. Ensure all tests pass and linting is clean
4. Update documentation if needed
5. Submit a PR with a clear description

## Questions?

Open an issue for any questions about contributing.
