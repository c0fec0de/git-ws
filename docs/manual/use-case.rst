Use Case
========

Managing large projects can be a real challenge - be it in the software domain or in hardware development. There are a lot of challenges involved:

- How to reuse parts of the project so that - when starting a new one - we can get a quick start by just taking over modules as-is?
- How to manage dependencies of our projects, also towards (company/organization) internal modules?
- How to efficiently build and test our project without spawning hour long CI/CD pipelines even for the tiniest commit pushed to the VCS server?

These and other questions are not trivial to answer. For use, from the requirements we had for our projects, we came to the following conclusions:

- We wanted to break down our (formerly very large monolithic) projects into smaller, more digestible parts and manage each in their own ``git`` repository.
- We wanted to be able to define dependencies between these modules.
- We needed a mechanism to *lock* a project (i.e. create a frozen state of all modules to be able to re-create specific, historic states).
- Especially during the early development stages, we anticipated that frequent changes on several modules would be required. Hence, we needed a way to have several modules available in an *editable* way.

As detailed in :ref:`evaluationofexistingtools`, we evaluated several existing tools that seemed suitable for building larger workspaces from several smaller ``git`` repositories, but unfortunately, none of the existing tools really fulfilled our use case. The tool that seemed most promising was ``west``, but while technically and feature wise it provides a lot, it had some downsides that didn't fit with the concrete workflow we envisioned. In particular, the lack of relative include paths for dependencies (which is important when the same project can be cloned via several different URL schemes) as well as the fact that ``west`` always checks out dependencies on a detached head (which makes editing them more cumbersome) made it a non-ideal choice for us.

That's why we started Git Workspace at all. So here is what *we* envisioned in terms of use cases:

- We put our modules in individual ``git`` repositories.
- These repositories are assembled into a workspace.
- There is a main project in each workspace.
- The main project can define dependencies, which in turn can have own dependencies and so on. The tool will then generate a list of all repositories needed to go into the final workspace.
- Dependencies can be set to track ``git`` branches, tags and also commit hashes. In particular this means that components checked out at a branch can be edited.
- Dependencies (and other meta information) are stored in a manifest that is part of the individual projects' repositories. This is convenient as all information are stored in one place (versus e.g. the approach taken by Google's ``repo`` tool, which stores the manifest in dedicated repositories).
