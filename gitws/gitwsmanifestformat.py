# Copyright 2022-2023 c0fec0de
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

"""
Our Own Manifest Format.
"""

from pathlib import Path
from typing import Optional

import tomlkit

from ._util import add_comment, add_info, as_dict, resolve_relative
from .datamodel import Defaults, FileRef, MainFileRef, ManifestSpec, ProjectSpec, Remote
from .exceptions import ManifestError, ManifestNotFoundError
from .manifestformat import ManifestFormat


class GitWSManifestFormat(ManifestFormat):
    """
    Our Manifest Format.
    """

    prio: int = -1

    def is_compatible(self, path: Path) -> bool:
        """Check If File At ``path`` Is Compatible."""
        return path.suffix == ".toml"

    def load(self, path: Path) -> ManifestSpec:
        """
        Load Manifest From ``path``.

        Raises:
            ManifestNotFoundError: if file is not found
            ManifestError: On Syntax Or Data Scheme Errors.
        """
        try:
            content = path.read_text()
        except FileNotFoundError:
            raise ManifestNotFoundError(resolve_relative(path)) from None
        try:
            doc = tomlkit.parse(content)
            data = dict(doc)
            return ManifestSpec(**data)
        except Exception as exc:
            raise ManifestError(resolve_relative(path), str(exc)) from None

    def dump(self, spec: ManifestSpec, path: Optional[Path] = None) -> str:
        """
        Return :any:`ManifestSpec` As String.

        Args:
            spec: Manifest Spec

        Keyword Args:
            path: Path To Possibly Existing Document.
        """
        return self._dump(spec, path=path)

    def _dump(self, spec: ManifestSpec, doc: Optional[tomlkit.TOMLDocument] = None, path: Optional[Path] = None) -> str:
        assert not doc or not path, "'doc' and 'path' are mutually exclusive."
        if doc is None:
            if path and path.exists():
                doc = tomlkit.parse(path.read_text())
            else:
                doc = self._create()
            data = {
                "version": ManifestSpec().version,
                "remotes": tomlkit.aot(),
                "group-filters": (),
                "defaults": {},
                "dependencies": tomlkit.aot(),
                "linkfiles": tomlkit.aot(),
                "copyfiles": tomlkit.aot(),
            }
        else:
            data = {}
        data.update(as_dict(spec))
        for key, value in data.items():
            doc[key] = value
        return tomlkit.dumps(doc)

    def upgrade(self, path: Path):
        """Upgrade :any:`ManifestSpec` at ``path`` To Latest Version Including Documentation."""
        # read
        content = path.read_text()
        try:
            olddoc = tomlkit.parse(content)
            olddata = dict(olddoc)
            olddata.pop("groups", None)
            obj = ManifestSpec(**olddata)
        except Exception as exc:
            raise ManifestError(resolve_relative(path), str(exc)) from None

        # merge
        newdoc = self._create()
        for key, value in olddata.items():
            newdoc[key] = value
        for key, value in as_dict(obj).items():
            newdoc[key] = value
        newdoc["version"] = "1.0"

        # write
        path.write_text(tomlkit.dumps(newdoc))

    def _create(self) -> tomlkit.TOMLDocument:
        doc = tomlkit.document()

        # Version
        doc.add("version", ManifestSpec().version)  # type: ignore
        # Intro
        add_info(
            doc,
            """
Git Workspace's Manifest. Please see the documentation at:

https://git-ws.readthedocs.io/en/stable/manual/manifest.html
""",
        )
        doc.add(tomlkit.nl())
        doc.add(tomlkit.nl())

        # Group Filtering
        example = ManifestSpec(group_filters=("-doc", "-feature@path"))
        add_comment(doc, self._dump(example, doc=tomlkit.document())[:-1])
        doc.add("group-filters", tomlkit.array())
        doc.add(tomlkit.nl())
        doc.add(tomlkit.nl())

        # Remotes
        example = ManifestSpec(remotes=[Remote(name="myremote", url_base="https://github.com/myuser")])
        add_comment(doc, self._dump(example, doc=tomlkit.document())[:-1])
        doc.add("remotes", tomlkit.aot())
        doc.add(tomlkit.nl())
        doc.add(tomlkit.nl())

        # Defaults
        doc.add("defaults", as_dict(Defaults()))
        example = ManifestSpec(
            defaults=Defaults(
                remote="myserver", revision="main", groups=("test",), with_groups=("doc",), submodules=True
            )
        )
        add_comment(doc, "\n".join(self._dump(example, doc=tomlkit.document()).split("\n")[1:-1]))
        doc.add(tomlkit.nl())
        doc.add(tomlkit.nl())

        add_info(doc, "A minimal dependency:")
        example = ManifestSpec(dependencies=[ProjectSpec(name="my", submodules=None)])
        add_comment(doc, self._dump(example, doc=tomlkit.document())[:-1])
        doc.add(tomlkit.nl())

        # Dependencies
        add_info(doc, "A full flavored dependency using a 'remote':")
        example = ManifestSpec(
            dependencies=[
                ProjectSpec(
                    name="myname",
                    remote="remote",
                    sub_url="my.git",
                    revision="main",
                    path="mydir",
                    manifest_path="git-ws.toml",
                    groups=("group",),
                    linkfiles=[
                        FileRef(src="file0-in-mydir.txt", dest="link0-in-workspace.txt"),
                        FileRef(src="file1-in-mydir.txt", dest="link1-in-workspace.txt"),
                    ],
                    copyfiles=[
                        FileRef(src="file0-in-mydir.txt", dest="file0-in-workspace.txt"),
                        FileRef(src="file1-in-mydir.txt", dest="file1-in-workspace.txt"),
                    ],
                )
            ]
        )
        add_comment(doc, self._dump(example, doc=tomlkit.document())[:-1])
        doc.add(tomlkit.nl())

        add_info(doc, "A full flavored dependency using a 'url':")
        example = ManifestSpec(
            dependencies=[
                ProjectSpec(
                    name="myname",
                    url="https://github.com/myuser/my.git",
                    revision="main",
                    path="mydir",
                    manifest_path="git-ws.toml",
                    groups=("group",),
                    linkfiles=[
                        FileRef(src="file0-in-mydir.txt", dest="link0-in-workspace.txt"),
                        FileRef(src="file1-in-mydir.txt", dest="link1-in-workspace.txt"),
                    ],
                    copyfiles=[
                        FileRef(src="file0-in-mydir.txt", dest="file0-in-workspace.txt"),
                        FileRef(src="file1-in-mydir.txt", dest="file1-in-workspace.txt"),
                    ],
                )
            ]
        )
        add_comment(doc, self._dump(example, doc=tomlkit.document())[:-1])
        doc.add(tomlkit.nl())

        doc.add("dependencies", tomlkit.aot())
        doc.add(tomlkit.nl())
        doc.add(tomlkit.nl())

        # linkfíles
        example = ManifestSpec(linkfiles=[MainFileRef(src="file-in-main-clone.txt", dest="link-in-workspace.txt")])
        add_comment(doc, self._dump(example, doc=tomlkit.document())[:-1])
        doc.add("linkfiles", tomlkit.aot())
        doc.add(tomlkit.nl())
        doc.add(tomlkit.nl())

        # copyfíles
        example = ManifestSpec(copyfiles=[MainFileRef(src="file-in-main-clone.txt", dest="file-in-workspace.txt")])
        add_comment(doc, self._dump(example, doc=tomlkit.document())[:-1])
        doc.add("copyfiles", tomlkit.aot())

        # Done
        return doc


_FORMAT = GitWSManifestFormat()
dump = _FORMAT.dump
load = _FORMAT.load
save = _FORMAT.save
upgrade = _FORMAT.upgrade
