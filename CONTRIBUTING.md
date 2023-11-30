# Contribute

## Development

### Create Environment

Please install [`pipx`](https://pypa.github.io/pipx/installation)

### Testing

```bash
make all
```

### Release

```bash
# Ensure main
git checkout main
git pull

version=2.x.y

# Commit, Tag and Push
pdm version ${version}
git commit -m"version bump to ${version}" pyproject.toml
git tag "${version}" -m "Release ${version}"
git push
git push --tags

# Publishing is handled by CI
```
