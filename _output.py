"""Shared output-path helper for all utility scripts.

Every script in this repo follows a convention:

    output/<script_name>/<artifact>

where *script_name* is derived from the calling module's ``__file__``
(e.g. ``md_to_docx.py`` → ``md_to_docx``), and *artifact* is the
filename of the produced file.  The ``output/`` root lives next to the
scripts themselves (i.e. in the repository root).

Usage inside a script::

    from _output import default_output

    out = default_output('result.docx')            # uses caller's module name
    out = default_output('result.docx', 'custom')  # explicit subdirectory
"""

import inspect
from pathlib import Path


_REPO_ROOT = Path(__file__).resolve().parent


def default_output(
    artifact: str,
    script_name: str | None = None,
) -> Path:
    """Return ``<repo>/output/<script_name>/<artifact>``, creating dirs.

    Args:
        artifact: Filename (not a path) for the produced file.
        script_name: Override for the subdirectory name.  When *None*,
            the name is derived from the caller's ``__file__``
            (``md_to_docx.py`` → ``md_to_docx``).

    Returns:
        Resolved :class:`~pathlib.Path` to the output location.
    """
    if script_name is None:
        frame = inspect.stack()[1]
        caller_file = frame.filename
        script_name = Path(caller_file).stem

    out_dir = _REPO_ROOT / 'output' / script_name
    out_dir.mkdir(parents=True, exist_ok=True)
    return out_dir / artifact
