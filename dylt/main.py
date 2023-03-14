import os
import click
import logging
import subprocess
from pytube import YouTube

from .config import Config

logger = logging.getLogger(__name__)


@click.command()
@click.argument("url")
@click.option("resolution", "-r", default=Config.resolution_default)
def main(url: str, resolution=Config.resolution_default) -> None:
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

    logger.debug("Merging using FFMPEG")

    stdout = Config.stdout.open("w")
    stderr = Config.stderr.open("w")

    muxed_file = Config.output_dir / yt.title
    click.secho(f"Muxing w/ ffmpeg!\nSave Location: {muxed_file}", fg="green")

    cmd = f"ffmpeg -y -i '{Config.temp_audio}' -i '{Config.temp_video}' -shortest '{muxed_file}.mkv'"
    subprocess.call(cmd, shell=True, stdout=stdout, stderr=stderr)

    logger.debug("Clean up.")

    os.remove(Config.temp_video)
    os.remove(Config.temp_audio)

    click.secho("Complete!", fg="green")


if __name__ == "__main__":
    main()
