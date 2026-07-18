# kducky

DuckyScript 3 Interpreter for Raspberry Pi Pico 2 W (RP2350)

## Development

### Prerequisites
- Python 3.10+
- pip

### Setup
```bash
pip install -e ".[dev]"
```

### Run tests
```bash
pytest
```

### Lint and type-check
```bash
ruff check src/ tests/
mypy src/ tests/
```
