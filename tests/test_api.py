"""Test API."""


def test_imports():
    """Test imports."""
    # pylint: disable=unused-import,too-many-locals,import-outside-toplevel
    from anyrepo import (
        AnyRepo,
        AppConfig,
        AppConfigData,
        AppConfigLocation,
        Clone,
        Defaults,
        Filter,
        Git,
        GitCloneMissingError,
        Group,
        InitializedError,
        InvalidConfigurationFileError,
        InvalidConfigurationLocationError,
        Manifest,
        ManifestError,
        ManifestExistError,
        ManifestIter,
        ManifestNotFoundError,
        ManifestSpec,
        NoGitError,
        OutsideWorkspaceError,
        Project,
        ProjectIter,
        ProjectSpec,
        Remote,
        UninitializedError,
        Workspace,
        find_workspace,
    )