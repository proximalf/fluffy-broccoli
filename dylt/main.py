from pathlib import Path
import sys
from pytube import YouTube
from pytube.exceptions import PytubeError
from typing import Optional
from moviepy.editor import AudioFileClip, VideoFileClip, CompositeVideoClip
import click
import logging
import os
import subprocess

from .config import Config

logger = logging.getLogger(__name__)


def mux_audio_video(video_title: str, output_dir: Path, temp_audio: Path, temp_video: Path, stdout: Path, stderr: Path) -> None:
    """
    Mux audio and video using ffmpeg.
    """
    logger.debug("Merging using FFMPEG")

    stdout = stdout.open("w")
    stderr = stderr.open("w")

    muxed_file = output_dir / video_title
    click.secho(f"Muxing w/ ffmpeg!\nSave Location: {muxed_file}", fg="green")

    cmd = f"ffmpeg -y -i '{temp_audio}' -i '{temp_video}' -shortest '{muxed_file}.mkv'"
    subprocess.call(cmd, shell=True, stdout=stdout, stderr=stderr)

def clip_audio_video(temp_audio: Path, temp_video: Path, clip_start: str, clip_end: str, minimum_duration: int = 1) -> None:
    """
    This function clips and merges the file.
    """
    if clip_start < minimum_duration:
        logger.error(f"Duration too short: {clip_start} < {minimum_duration}")
    
    logger.debug(f"Clipping - a:{temp_audio}, v:{temp_video}")
    audio_file = AudioFileClip(str(temp_audio))
    audio_clip = audio_file.subclip(clip_start, clip_end)

    video_file = VideoFileClip(str(temp_video))
    video_clip = video_file.subclip(clip_start, clip_end)
    
    video_clip.audio = audio_clip
    logger.debug("Merging and saving clip...")    
    
    return video_clip


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
@click.argument("url")
@click.option("resolution", "-r", default=Config.resolution_default, type=str)
@click.option("clip", "-c", default=None, type=str)
@click.option("sysout_logging", "-d", "--debug", default = False, is_flag=True)
def cli(url: str, resolution: str = Config.resolution_default, clip: Optional[str] = None, sysout_logging: bool = False) -> None:
    """
    CLI script to download youtube video in highest quality avalible.
    Video and Audio downloaded seperately, and merged using FFMPEG.
    Clipping is accepted in the format xx,yy in seconds (start, end).
    """
    logger.setLevel(logging.DEBUG)
    if sysout_logging:
        log_stream = logging.StreamHandler(sys.stdout)
        logger.addHandler(log_stream)
    
    log_fh = logging.FileHandler(Path.home() / ".log-dylt.log", mode="w")
    logger.addHandler(log_fh)
    logger.debug(f"URL: {url}")
    logger.debug(f"ouput directory: {Config.output_dir}")
    
    retry_attempts = Config.retry_attempts
    for i in range(retry_attempts):
        try:
            yt = YouTube(url)
            click.secho(f"Downloading: {yt.title}", fg="green")
            break
        except PytubeError as ex:
            click.echo(f"Failed to grab URL, retrying - {retry_attempts - i} ")
            logger.debug(f"Exception: {ex}")
        if i == retry_attempts:
            click.echo("Cannot fetch url...")
            return 1


    output = str(Config.output_dir)

    logger.debug("Downloading video component")
    
    for stream in yt.streams:
        logger.debug(f"yt.streams: {stream}")
    stream = yt.streams.filter(file_extension="mp4", res=resolution)[-1]
    stream.download(output, Config.temp_video.name)

    logger.debug("Downloading audio component")
    stream = yt.streams.filter(file_extension="mp4", mime_type="audio/mp4")[-1]
    stream.download(output, Config.temp_audio.name)

    click.secho("Download complete!", fg="green")

    if clip is not None:
        clip_start, clip_end = [int(i) for i in clip.split(",")]
        click.secho(f"Clipping... {clip_start} - {clip_end}")
        video_clip = clip_audio_video(
            Config.temp_audio,
            Config.temp_video,
            clip_start, clip_end
        )
        save_clipped_video(
            video_clip,
            Config.output_dir / f"{yt.title}.mp4",
        )
    else:
        mux_audio_video(
            yt.title,
            Config.output_dir,
            Config.temp_audio,
            Config.temp_video,
            Config.stdout,
            Config.stdout,
            )
    
    clean_up_temp_files(
        Config.temp_audio,
        Config.temp_video
        )
    
    click.secho("Complete!", fg="green")