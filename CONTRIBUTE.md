# Contribute

## Testing

### Prepare

```bash
# Ensure python3 is installed
python3 -m venv .venv
source .venv/bin/activate
pip install tox poetry
```

### Test Your Changes

```bash
# test
tox
```

### Release

```bash
poetry version minor
# OR
poetry version patch

git commit -m"version bump"

poetry publish --build
```

