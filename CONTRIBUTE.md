# Contribute

## Testing

### Create Environment

Run these commands just the first time:

```bash
# Ensure python3 is installed
python3 -m venv .venv
source .venv/bin/activate
pip install tox "poetry>=1.4"
```

### Enter Environment

Run this command once you open a new shell:

```bash
source .venv/bin/activate
```

### Test Your Changes

```bash
# test
tox
```

### Release

```bash
# Ensure main
git checkout main
git pull

# Version Bump
poetry version minor
# OR
poetry version patch

# Commit, Tag and Push
version=$(poetry version -s)
git commit -m"version bump to ${version}" pyproject.toml
git tag "${version}" -m "Release ${version}"
git push
git push --tags

# Publishing is handled by CI
```
