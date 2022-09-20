"""Exceptions."""


class UninitializedError(RuntimeError):
    """AnyRepo Workspace has not been initialized."""

    def __init__(self):
        super().__init__("anyrepo has not been initialized yet (Try 'anyrepo init' or 'anyrepo clone').")


class NoGitError(RuntimeError):
    """Git Clone has not been initialized."""

    def __init__(self):
        super().__init__("git clone has not been initialized yet (Try 'git init' or 'git clone').")
