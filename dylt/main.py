from pathlib import Path
from typing import Optional
import click
import logging
import sys

from .config import Config
from .core import fetch_from_youtube, download_from_youtube
from .note import source_note, zettel_format

logger = logging.getLogger(__name__)

@click.command()
@click.argument("url")
@click.option("resolution", "-r", default = Config.resolution_default, type = str)
@click.option("clip", "-c", default = None, type = str)
@click.option("note", "-n", "--note", default = None, type = str)
@click.option("sysout_logging", "-d", "--debug", default = False, is_flag=True)
def cli(url: str, resolution: str = Config.resolution_default, clip: Optional[str] = None, note: Optional[str] = None, sysout_logging: bool = False) -> None:
    """
    CLI script to download youtube video in highest quality avalible.
    Video and Audio downloaded seperately, and merged using FFMPEG.
    Clipping is accepted in isoformat HH:MM:SS (start, end), eg `-c 4:04,5:23`.

    Parameters
    ----------
    url: str
        String of youtube url link.
    resolution: str 
        Using config default, but can be set.
    clip: Optional[str]
        Set a time stamp to clip from. This must inlude start&end timestamps.
    note: Optional[str]
        A comment to add to the saved accompanying source note.
    sysout_logging: bool
        Flag to set wether details are logged using sysout.
    """
    logger.setLevel(logging.DEBUG)
    if sysout_logging:
        log_stream = logging.StreamHandler(sys.stdout)
        logger.addHandler(log_stream)
    
    log_fh = logging.FileHandler(Path.home() / ".log-dylt.log", mode="w")
    logger.addHandler(log_fh)

    logger.debug(f"URL: {url}")
    logger.debug(f"ouput directory: {Config.output_dir}")
    
    yt = fetch_from_youtube(url, Config.retry_attempts)

    if yt is None:
        click.secho("Error occured fetching details from YouTube")
        return 1

    output_filename = Config.output_dir / f"{zettel_format()} - {yt.title}"

    download_from_youtube(
        output_filename, yt, resolution, clip
    )
    
    yaml = [
        f"author: {yt.author}",
        f"title: {yt.title}", 
        f"publish date: {yt.publish_date}"
    ]

    source_note(
        filename = output_filename,
        url = url,
        clip = clip,
        yaml = yaml,
        comment = note,
        )
    
    click.secho("Complete!", fg="green")