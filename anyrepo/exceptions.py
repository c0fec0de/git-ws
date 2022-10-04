"""Collection Of All Exceptions Which Might Occur."""


class UninitializedError(RuntimeError):
    """AnyRepo Workspace has not been initialized."""

    def __init__(self):
        super().__init__("anyrepo has not been initialized yet.")


class InitializedError(RuntimeError):
    """AnyRepo Workspace has been initialized."""

    def __init__(self, path, main_path):
        super().__init__(f"anyrepo has already been initialized at {str(path)!r} with main repo at {str(main_path)!r}.")
        self.path = path
        self.main_path = main_path


class NoGitError(RuntimeError):
    """Git Clone has not been initialized."""

    def __init__(self):
        super().__init__("git clone has not been found or initialized yet.")


class ManifestNotFoundError(RuntimeError):
    """Manifest File has not been found."""

    def __init__(self, path):
        super().__init__(f"Manifest has not been found at {str(path)!r}.")
        self.path = path


class ManifestExistError(RuntimeError):
    """Manifest already exists."""

    def __init__(self, path):
        super().__init__(f"Manifest exists at {str(path)!r}.")


class OutsideWorkspaceError(RuntimeError):
    """Project is located outside of Workspace."""

    def __init__(self, path, project_path):
        super().__init__(f"Project {str(project_path)!r} is located outside {str(path)!r}.")
        self.path = path
        self.project_path = project_path


class ManifestError(RuntimeError):
    """Manifest Error."""

    def __init__(self, path, details):
        super().__init__(f"Manifest {str(path)!r} is broken: {details}")
        self.path = path
        self.details = details


class GitCloneMissingError(RuntimeError):
    """Git Clone Missing Error."""

    def __init__(self, project_path):
        super().__init__(f"Git Clone {str(project_path)!r} is missing.")
        self.project_path = project_path
