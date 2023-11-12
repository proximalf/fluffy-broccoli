import logging
import sys
import pyperclip
from pathlib import Path
from typing import Any, Dict, List, Optional
from click import command, option, secho

from .config import Config
from .core import fetch_from_youtube, download_from_youtube, validate_url
from .note import zettel_format, create_note
from .lib import TagList
from . import version

logger = logging.getLogger(__package__)


def download(
    url: str,
    output_directory: Path,
    name: Optional[str] = None,
    resolution: Optional[str] = None,
    clip: Optional[str] = None,
    audio_only: bool = False,
    note: Optional[str] = None,
    tags: Optional[List[str]] = None,
):
    logger.debug(f"URL: {url}")
    logger.debug(f"Output directory: {output_directory}")

    if not validate_url(url):
        secho(f"Provided URL is not valid.")
        return 1

    youtube = fetch_from_youtube(url, Config.retry_attempts)

    if youtube is None:
        secho(f"Error when fetching details from YouTube: \nURL: {url}")
        return 1

    output_filename = output_directory / Config.filename(name or youtube.title)

    if audio_only:
        secho("Downloading Audio only!", fg="yellow")

    try:
        download_from_youtube(output_filename, youtube, resolution, clip, audio_only)
    except Exception as e:
        secho(f"Error during download - {e}", fg="red")
        logger.exception(f"Exception during download: {e}")
        return 1

    if tags is not None:
        secho(f"Tags: {tags}")

    create_note(
        output_filename=output_filename,
        youtube=youtube,
        url=url,
        note=note,
        tags=tags,
    )

    secho("Complete!", fg="green")
    return 0

CONTEXT_SETTINGS: Dict[str, Any] = {"help_option_names": ["-h", "--help"]}


@command(context_settings=CONTEXT_SETTINGS)
@option(
    "url", "-u", "--url", default=None, help="URL option, overrides default behaviour."
)
@option(
    "audio_only", "-a", "--audio-only", default=False, is_flag=True, help="Audio only."
)
@option(
    "resolution",
    "-r",
    default=Config.resolution_default,
    type=str,
    help="Set download resolution.",
)
@option(
    "clip",
    "-c",
    default=None,
    type=str,
    help="Clip viedo, use format '%M:%S,%M:%S' (start, end)",
)
@option("note", "-n", "--note", default=None, type=str, help="Add a note.")
@option(
    "sysout_logging", "-d", "--debug", default=False, is_flag=True, help="Debug mode"
)
@option(
    "print_version",
    "-V",
    "--version",
    default=False,
    is_flag=True,
    help="Print verison.",
)
@option(
    "tags",
    "-t",
    "--tag",
    default=None,
    type=TagList(),
    help="List of tags in format 'tag1,tag2,etc'.",
)
@option("name", "-e", "--name", default=None, type=str, help="Set filename of file.")
@option(
    "output",
    "-o",
    "--output",
    default=None,
    type=Path,
    help="Set directory to output to.",
)
def cli(
    url: Optional[str] = None,
    audio_only: bool = False,
    resolution: Optional[str] = Config.resolution_default,
    clip: Optional[str] = None,
    note: Optional[str] = None,
    sysout_logging: bool = False,
    print_version: bool = False,
    tags: Optional[TagList] = None,
    name: Optional[str] = None,
    output: Optional[Path] = None,
) -> None:
    """\b
    CLI script to download youtube video in highest quality avalible.
    URl is grabbed from clipboard, alternatively, using option "-u" the url can be pasted.
    Video and Audio downloaded seperately, and merged using FFMPEG.
    Clipping is accepted in isoformat HH:MM:SS (start, end), eg `-c 4:04,5:23`.
    Add option `-a` to download audio only, saves as '.mp3'.
    Add tags `-t` in form 'tag,etc,type'.
    Refer to config file.
    Clipping isn't smart, so if you wanna make multiple clips, download whole video and clip individually.

    \b
    Parameters
    ----------
    url: str
        String of youtube url link, wrapped in quotes.
    audio_only: bool
        Set flag to download audio only.
    resolution: str
        Using config default, but can be set.
    clip: Optional[str]
        Set a time stamp to clip from. This must inlude 'start&end' timestamps.
    note: Optional[str]
        A comment to add to the saved accompanying source note.
    sysout_logging: bool
        Log to sysout for debug.
    print_version: bool
        Prints version.
    tags: Optional[TagList]
        A list of tags, in format 'tag1,tag2,etc'
    name: Optional[str]
        Set name of file.
    output: Optional[Path]
        Set output directory for file.

    Example
    ----------
        ```
        dylt -c "0:8,5:1"

        dylt -u "https://youtu.be/KenyufNno5c?si=xTuBb0cvStAIU4B7" -t jb,sax

        dylt -n "New filename"

        dylt --audio-only
        ```

    """

    if print_version:
        secho(f"dylt - Version: {version.__version__}")
        return 0

    logger.setLevel(logging.DEBUG)

    logger.handlers = []

    if sysout_logging:
        log_stream = logging.StreamHandler(sys.stdout)
        logger.addHandler(log_stream)
        logger.info("Logging to stream.")

    log_fh = logging.FileHandler(Path.home() / ".log-dylt.log", mode="w")
    logger.addHandler(log_fh)
    logger.info("Logging to file.")

    if url is None:
        url = pyperclip.paste()

    if output is not None:
        secho(f"Default output overriden.")
        
    output_directory = (
        output.expanduser() if output is not None else Config.output_directory
    )

    error_code = download(
        url=url,
        output_directory=output_directory,
        name=name,
        resolution=resolution,
        clip=clip,
        audio_only=audio_only,
        note=note,
        tags=tags,
    )
    return error_code
