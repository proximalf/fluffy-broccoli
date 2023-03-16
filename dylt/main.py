import os
from pathlib import Path
import click
import logging
import subprocess
from pytube import YouTube

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

    logger.debug("Clean up.")

    os.remove(temp_video)
    os.remove(temp_audio)

    click.secho("Complete!", fg="green")


@click.command()
@click.argument("url")
@click.option("resolution", "-r", default=Config.resolution_default)
def cli(url: str, resolution=Config.resolution_default) -> None:
    """
    CLI script to download youtube video in highest quality avalible.
    Video and Audio downloaded seperately, and merged using FFMPEG.
    """
    logger.debug(f"URL: {url}")
    logger.debug(f"ouput directory: {Config.output_dir}")

    yt = YouTube(url)

    click.secho(f"Downloading: {yt.title}", fg="green")

    output = str(Config.output_dir)

    logger.debug("Downloading video component")
    stream = yt.streams.filter(file_extension="mp4", res=resolution)[-1]
    stream.download(output, Config.temp_video.name)

    logger.debug("Downloading audio component")
    stream = yt.streams.filter(file_extension="mp4", mime_type="audio/mp4")[-1]
    stream.download(output, Config.temp_audio.name)

    click.secho("Download complete!", fg="green")

    mux_audio_video(
        yt.title,
        Config.output_dir,
        Config.temp_audio,
        Config.temp_video,
        Config.stdout,
        Config.stdout,
        )
