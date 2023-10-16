import logging
import sys
import pyperclip
from pathlib import Path
from typing import List, Optional
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
        tags: Optional[List[str]] = None
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

    output_filename = output_directory / (
        f"{zettel_format()} - " + (f"{name}" if name is not None else f"{youtube.title}")
    )

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

@command()
@option("url", "-u", "--url", default=None)
@option("audio_only", "-a", "--audio-only", default=False, is_flag=True)
@option("resolution", "-r", default=Config.resolution_default, type=str)
@option("clip", "-c", default=None, type=str)
@option("note", "-n", "--note", default=None, type=str)
@option("sysout_logging", "-d", "--debug", default=False, is_flag=True)
@option("print_version", "-v", "--version", default=False, is_flag=True)
@option("tags", "-t", "--tag", default=None, type=TagList())
@option("name", "-e", "--name", default=None, type=str)
@option("output", "-o", "--output", default=None, type=Path)
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

    \b
    Parameters
    ----------
    url: str
        String of youtube url link.
    audio_only: bool
        Set flag to download audio only.
    resolution: str
        Using config default, but can be set.
    clip: Optional[str]
        Set a time stamp to clip from. This must inlude 'start&end' timestamps.
    note: Optional[str]
        A comment to add to the saved accompanying source note.
    sysout_logging: bool
        Flag to set wether detaildownload(url)e directory for downloads.
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
    output_directory = output.resolve() if output is not None else Config.output_directory

    error_code = download(
        url=url, 
        output_directory=output_directory, 
        name=name, 
        resolution=resolution, 
        clip=clip, 
        audio_only=audio_only, 
        note=note, 
        tags=tags
        )
    return error_code
