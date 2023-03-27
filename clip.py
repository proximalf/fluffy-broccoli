from pathlib import Path
import sys
from typing import Optional
from moviepy.editor import VideoFileClip
import click
import logging
import os

logger = logging.getLogger(__name__)


def save_clipped_video(video_clip: VideoFileClip, file_path: Path) -> None:
    """
    Saves a clipped video
    """

    video_clip.write_videofile(str(file_path))
    
    
def clean_up_temp_files(temp_audio: Path, temp_video: Path) -> None:
    logger.debug("Clean up.")

    os.remove(temp_video)
    os.remove(temp_audio)


@click.command()
@click.argument("filepath", type=Path)
@click.option("clip", "-c", default=None, type=str)
@click.option("sysout_logging", "-d", "--debug", default = False, is_flag=True)
def cli(filepath: Path, clip: Optional[str] = None, sysout_logging: bool = False) -> None:
    """
    CLI script to clip videos to mp4 format.
    Clipping is accepted in the format xx,yy in seconds (start, end).
    """
    logger.setLevel(logging.DEBUG)
    if sysout_logging:
        log_stream = logging.StreamHandler(sys.stdout)
        logger.addHandler(log_stream)
    
    log_fh = logging.FileHandler(Path.home() / ".log-dylt.log", mode="w")
    logger.addHandler(log_fh)
    logger.debug(f"Path: {filepath}")

    click.secho(f"Clipping file: {filepath}", fg="green")

    if clip is None:
        return 1
    
    clip_start, clip_end = [int(i) for i in clip.split(",")]
    click.secho(f"Clipping... s: {clip_start} - e: {clip_end}", fg="green")

    minimum_duration: int = 1
    if clip_start < minimum_duration:
        logger.error(f"Duration too short: {clip_start} < {minimum_duration}")

    video_file = VideoFileClip(str(filepath), audio = True)
    video_clip = video_file.subclip(clip_start, clip_end)
        
    save_clipped_video(
        video_clip,
        filepath.with_suffix(".mp4"),
    )
   
    click.secho("Complete!", fg="green")

if __name__ == "__main__":
    cli()