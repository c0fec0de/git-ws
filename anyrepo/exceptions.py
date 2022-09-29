"""Collection Of All Exceptions Which Might Occur."""


class UninitializedError(RuntimeError):
    """AnyRepo Workspace has not been initialized."""

    def __init__(self):
        super().__init__("anyrepo has not been initialized yet.")


class InitializedError(RuntimeError):
    """AnyRepo Workspace has been initialized."""

    def __init__(self, path):
        super().__init__(f"anyrepo has already been initialized yet at {path!s}.")
        self.path = path


class NoGitError(RuntimeError):
    """Git Clone has not been initialized."""

    def __init__(self):
        super().__init__("git clone has not been initialized yet.")


class ManifestNotFoundError(RuntimeError):
    """Manifest File has not been found."""

    def __init__(self, path):
        super().__init__(f"Manifest has not been found at {path!s}")
        self.path = path


class ManifestExistError(RuntimeError):
    """Manifest already exists."""

    def __init__(self, path):
        super().__init__(f"Manifest exists at {path!s}.")


class OutsideWorkspaceError(RuntimeError):
    """Project is located outside of Workspace."""

    def __init__(self, path, project_path):
        super().__init__(f"Project {project_path!s} is located outside {path!s}")
        self.path = path
        self.project_path = project_path


class ManifestError(RuntimeError):
    """Manifest Error."""

    def __init__(self, path, details):
        super().__init__(f"Manifest {path} is broken: {details}")
        self.path = path
        self.details = details


class GitCloneMissingError(RuntimeError):
    """Git Clone Missing Error."""

    def __init__(self, project_path):
        super().__init__(f"Git Clone {project_path} is missing.")
        self.project_path = project_path
