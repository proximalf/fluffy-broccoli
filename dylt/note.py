from datetime import datetime
from pathlib import Path
from typing import Optional
import logging

logger = logging.getLogger(__package__)


def zettel_format(format: str = "%y%m_%d%H%M") -> str:
    """Returns a string of datetime now in format `%y%m_%d%H%M`"""
    return datetime.now().strftime(format)


def source_note(
    filename: Path,
    url: str,
    clip: Optional[str] = None,
    yaml: Optional[str] = None,
    comment: Optional[str] = None,
) -> None:
    """
    Creates a note that references the link of a downloaded video, stores clip information.

    Parameters
    ----------
    filename: Path
        Path to save note under.
    url: str
        URL of downloaded video.
    clip: Optional[str]
        Clip if used is appended to note.
    yaml: Optional[str]
        yaml is appended to beginning of note.
    comment: Optional[str]
        Comment is added to end of note.
    """

    note = filename.with_suffix(".md")

    with note.open("w") as file:
        if yaml is not None:
            file.writelines(["---\n"] + [i + "\n" for i in yaml] + ["---\n"])

        file.writelines(
            [
                f"# {note.stem}\n",
                f"[Source]({url})\n",
                "Video downloaded from YouTube\n",
            ]
        )

        if clip is not None:
            file.write(f"Clipped: {clip}\n")

        if comment is not None:
            file.write(f"\n\n{comment}")

    logger.debug(f"Source note saved: {note}")
