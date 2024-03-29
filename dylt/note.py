from datetime import datetime
from pathlib import Path
from typing import List, Optional
from pytube import YouTube
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
    tags: Optional[List[str]] = None,
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
    tags: Optional[List[str]]
        Tags to add to note.
    """

    note = filename.with_suffix(".md")

    with note.open("w") as file:
        if yaml is not None:
            file.writelines(["---\n"] + [i + "\n" for i in yaml] + ["---\n"])

        file.writelines(
            [
                f"# {note.stem}\n",
                "Tags: #" + ", #".join(tags) + "\n" if tags is not None else "\n",
                f"[Source]({url})\n",
                "Video downloaded from YouTube\n",
                f"Clipped: {clip}\n" if clip is not None else "\n",
                f"\n\n{comment}\n" if comment is not None else "\n",
            ]
        )

    logger.debug(f"Source note saved: {note}")


def create_note(
    output_filename: Path,
    youtube: YouTube,
    url: str,
    clip: Optional[str] = None,
    note: Optional[str] = None,
    tags: Optional[List[str]] = None,
) -> None:
    """
    Create a note from a provided youtube object.

    Parameters
    ----------
    youtube: YouTube
    output_filename: Path
    tags: Optional[List[str]]
    """
    yaml = [
        f"author: {youtube.author}",
        f"title: {youtube.title}",
        f"publish date: {youtube.publish_date}",
    ]

    if tags is not None:
        yaml_tag = "tags: " + ", ".join(tags)
        yaml.append(yaml_tag)

    source_note(
        filename=output_filename,
        url=url,
        clip=clip,
        yaml=yaml,
        comment=note,
        tags=tags,
    )
