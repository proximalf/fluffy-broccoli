from pathlib import Path
from typing import Optional
import click
import logging
import sys
import pyperclip

from .config import Config
from .core import fetch_from_youtube, download_from_youtube, validate_url
from .note import source_note, zettel_format
from .lib import TagList
from . import version


@click.command()
@click.option("url", "-u", "--url", default=None)
@click.option("audio_only", "-a", "--audio-only", default=False, is_flag=True)
@click.option("resolution", "-r", default=Config.resolution_default, type=str)
@click.option("clip", "-c", default=None, type=str)
@click.option("note", "-n", "--note", default=None, type=str)
@click.option("sysout_logging", "-d", "--debug", default=False, is_flag=True)
@click.option("print_version", "-v", "--version", default=False, is_flag=True)
@click.option("tags", "-t", "--tag", default=None, type=TagList())
def cli(
    url: Optional[str] = None,
    audio_only: bool = False,
    resolution: Optional[str] = Config.resolution_default,
    clip: Optional[str] = None,
    note: Optional[str] = None,
    sysout_logging: bool = False,
    print_version: bool = False,
    tags: Optional[TagList] = None,
) -> None:
    """\b
    CLI script to download youtube video in highest quality avalible.
    URl is grabbed from clipboard, alternatively, using option "-u" the url can be pasted.
    Video and Audio downloaded seperately, and merged using FFMPEG.
    Clipping is accepted in isoformat HH:MM:SS (start, end), eg `-c 4:04,5:23`.
    Add option `-a` to download audio only, saves as '.mp3'.

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
        Set a time stamp to clip from. This must inlude start&end timestamps.
    note: Optional[str]
        A comment to add to the saved accompanying source note.
    sysout_logging: bool
        Flag to set wether details are logged using sysout.
    """

    if print_version:
        click.secho(f"dylt - Version: {version.__version__}")
        return 0
    
    if tags is not None:
        click.echo(f"Tags: {tags}")

    logger = logging.getLogger(__package__)
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

    if not validate_url(url):
        click.secho(f"Provided URL is not valid.")
        return 0

    logger.debug(f"URL: {url}")
    logger.debug(f"Output directory: {Config.output_dir}")

    yt = fetch_from_youtube(url, Config.retry_attempts)

    if yt is None:
        click.secho(f"Error when fetching details from YouTube: \nURL: {url}")
        return 1

    output_filename = Config.output_dir / f"{zettel_format()} - {yt.title}"

    if audio_only:
        click.secho("Downloading Audio only!", fg="yellow")

    try:
        download_from_youtube(output_filename, yt, resolution, clip, audio_only)
    except Exception as e:
        click.secho(f"Error during download - {e}", fg="red")
        logger.exception(f"Exception during download: {e}")
        return 1

    yaml = [
        f"author: {yt.author}",
        f"title: {yt.title}",
        f"publish date: {yt.publish_date}",
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

    click.secho("Complete!", fg="green")
    return 0
