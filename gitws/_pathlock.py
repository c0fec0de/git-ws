# Copyright 2023 c0fec0de
#
# This file is part of Git Workspace.
#
# Git Workspace is free software: you can redistribute it and/or modify it under
# the terms of the GNU Lesser General Public License as published by the Free
# Software Foundation, either version 3 of the License, or (at your option) any
# later version.
#
# Git Workspace is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE. See the GNU General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public License along
# with Git Workspace. If not, see <https://www.gnu.org/licenses/>.

"""Locking mechanisms for file system paths."""

from contextlib import contextmanager
from datetime import timedelta
from os import rename
from pathlib import Path
from shutil import copyfile, copytree, rmtree
from threading import Semaphore, Thread
from uuid import uuid4

from flufl.lock import Lock


@contextmanager
def path_lock(path: Path):
    """
    Lock a path in the file system.

    This context manager allows to lock a path in the file system for exclusive
    use. It takes the path to a file or folder to be locked. From that, a
    lock file is derived and the function tries to lock it. Then, control
    is returned to the caller, which then can modify the resource safely.

    Consider this example:

    >>> from tempfile import TemporaryDirectory
    >>> from pathlib import Path
    >>> with TemporaryDirectory() as tmp_dir:
    ...     path = Path(tmp_dir) / "test.txt"
    ...     with path_lock(path):
    ...         # Create the clone, e.g. by calling git clone in some way or the other...
    ...         path.write_text("Hello world")
    11

    Note that this function can safely be used on NFS shares. It also takes
    care to keep the lock acquired while the caller can modify the path in
    question. For this, a separate background thread is spawned that regularly
    refreshes the lock. That also means that - in case a process dies - the
    lock will eventually expire and a new process can continue.

    Also note that this function must not be used on the same path
    simultaneously in the same process.
    """
    # Set up the lock. We construct it by appending a suffix to the path to be
    # locked, which should make it unlikely that this is used as something else:
    lock_file_path = path.with_name(f"{path.name}-gitws.lock")
    lock_file_folder_path = lock_file_path.parent
    lock_file_folder_path.mkdir(parents=True, exist_ok=True)
    lock = Lock(str(lock_file_path), lifetime=timedelta(seconds=5))

    # Try to acquire the lock
    lock.lock()

    try:
        # Set up a thread that runs in parallel and regularly refreshes the
        # lock:
        semaphore = Semaphore()
        semaphore.acquire()
        thread = Thread(target=_keep_lock, args=[lock, semaphore])
        thread.start()

        # Give control to the caller:
        yield
    finally:
        # Yield the semaphore, so the background thread terminates:
        semaphore.release()
        thread.join()

        # Release the lock:
        lock.unlock()


@contextmanager
def atomic_update_or_create_path(path: Path):
    """
    Create or update a file or folder atomically.

    This function models a context manager which makes it easy to create
    or update files or folders in an atomic way. It does so by enabling the
    following:

    - It locks the path using path_lock() to ensure only one process at
      a time tries to modify the path.
    - It calculates a temporary, intermediate path (which it yields) on
      which the caller should work.
    - If the path points to an already existing file or folder, it (recursively)
      copies it to the temporary path.
    - On success, if it exists, the path is first removed and then the temporary
      path is renamed to the original one.

    Usage is pretty simple:

    >>> from tempfile import TemporaryDirectory
    >>> from pathlib import Path
    >>> with TemporaryDirectory() as tmp_dir:
    ...     path = Path(tmp_dir) / "some_folder"
    ...     with atomic_update_or_create_path(path) as work_path:
    ...         work_path.mkdir(parents=True, exist_ok=True)
    ...         new_file = work_path / "hello.txt"
    ...         new_file.write_text("Hello World!")
    12

    Please note that the returned temporary path does only point to an existing
    file or folder, if the input path exists. In particular, if a non existing
    directory is passed in, the temporary directory must be created first.
    """
    # Lock the path:
    with path_lock(path):
        # Calculate a temporary path to work on:
        uuid = uuid4()
        tmp_path = Path(f"{path}-{uuid}")

        try:
            # If the path already exists, make a copy to work on:
            if path.exists():
                if path.is_dir():
                    copytree(path, tmp_path)
                else:
                    copyfile(path, tmp_path)

            # Yield the temporary path to the caller:
            yield tmp_path

            # On success, first remove the original path:
            if path.exists():
                if path.is_dir():
                    rmtree(path)
                else:
                    path.unlink()

            # And then rename the temporary (modified) copy to the original one.
            # Note, we have to use a rename here, to ensure an atomic update of
            # the target:
            if tmp_path.exists():
                rename(tmp_path, path)
        finally:
            # Clean up in case errors happened: Remove the temporary
            # directory:
            if tmp_path.exists():
                if tmp_path.is_dir():
                    rmtree(tmp_path)
                else:
                    tmp_path.unlink()


def _keep_lock(lock: Lock, semaphore: Semaphore):
    """
    Keep a file lock alive.

    This helper function is used to keep a lock in the file system alive.
    It waits for the given semaphore to be released and then returns. Between
    waits, it refreshes the given lock.
    """
    while not semaphore.acquire(timeout=1):
        lock.refresh(lifetime=timedelta(seconds=5))
