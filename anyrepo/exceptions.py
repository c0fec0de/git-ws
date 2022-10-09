"""Collection Of All Exceptions Which Might Occur."""

from pathlib import Path


class UninitializedError(RuntimeError):
    """Anyrepo Workspace Has Not Been Initialized."""

    def __init__(self):
        super().__init__("anyrepo has not been initialized yet.")


class InitializedError(RuntimeError):
    """Anyrepo Workspace Has Already Been Initialized."""

    def __init__(self, path, main_path):
        super().__init__(f"anyrepo has already been initialized at {str(path)!r} with main repo at {str(main_path)!r}.")
        self.path = path
        self.main_path = main_path


class NoGitError(RuntimeError):
    """Git Clone Has Not Been Initialized."""

    def __init__(self):
        super().__init__("git clone has not been found or initialized yet.")


class ManifestNotFoundError(RuntimeError):
    """Manifest File Has Not Been Found."""

    def __init__(self, path):
        super().__init__(f"Manifest has not been found at {str(path)!r}.")
        self.path = path


class ManifestExistError(RuntimeError):
    """Manifest Already Exists."""

    def __init__(self, path):
        super().__init__(f"Manifest exists at {str(path)!r}.")


class OutsideWorkspaceError(RuntimeError):
    """Project Is Located Outside Of Workspace."""

    def __init__(self, path, project_path):
        super().__init__(f"Project {str(project_path)!r} is located outside {str(path)!r}.")
        self.path = path
        self.project_path = project_path


class ManifestError(RuntimeError):
    """The Manifest Is Invalid."""

    def __init__(self, path, details):
        super().__init__(f"Manifest {str(path)!r} is broken: {details}")
        self.path = path
        self.details = details


class InvalidConfigurationFileError(RuntimeError):
    """A Configuration File Is Invalid And Cannot Be Used."""

    def __init__(self, path: Path, details: str):
        super().__init__(f"The configuration file {path} cannot be read: {details}")
        self.path = path
        self.details = details


class InvalidConfigurationLocationError(RuntimeError):
    """An Invalid Location For Configuration Data Has Been Used."""

    def __init__(self, location: str):
        super().__init__(f"The configuration location {location} is not known")
        self.location = location


class GitCloneMissingError(RuntimeError):
    """Git Clone Is Missing."""

    def __init__(self, project_path):
        super().__init__(f"Git Clone {str(project_path)!r} is missing.")
        self.project_path = project_path


class GitCloneNotCleanError(RuntimeError):
    """Git Clone Contains Changes."""

    def __init__(self, project_path):
        super().__init__(f"Git Clone {str(project_path)!r} contains changes.")
        self.project_path = project_path
