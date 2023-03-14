import os
import click
from pathlib import Path
from pytube import YouTube
import logging
import subprocess

logger = logging.getLogger(__name__)

class Config:
    home = Path.home()
    output_dir = home / "Downloads"
    stdout = output_dir / "dylt-out.log"
    stderr = output_dir / "dylt-err.log"
    temp_video = output_dir / "video.mp4"
    temp_audio = output_dir / "audio.mp4"

@click.command()
@click.argument("url")
def main(url: str) -> None:
    """
    CLI script to download youtube video in highest quality avalible.
    Video and Audio downloaded seperately, and merged using FFMPEG.
    """
    logger.debug(f"URL: {url}")
    logger.debug(f"ouput directory: {Config.output_dir}")

    output = str(Config.output_dir)

    yt = YouTube(url)

    click.secho(f"Downloading: {yt.title}", fg="green")

    logger.debug("Downloading video component")
    stream = yt.streams.filter(file_extension="mp4", res="1080p")[-1]
    stream.download(output, Config.temp_video.name)

    logger.debug("Downloading audio component")
    stream = yt.streams.filter(file_extension="mp4", mime_type="audio/mp4")[-1]
    stream.download(output, Config.temp_audio.name)

    click.secho("Download complete!", fg="green")

    logger.debug("Merging using FFMPEG")

    stdout = Config.stdout.open("w")
    stderr = Config.stderr.open("w")

    muxed_file = Config.output_dir / yt.title
    click.secho(f"Muxing w/ ffmpeg!\nSave Location: {muxed_file}", fg="red")

    cmd = f"ffmpeg -y -i '{Config.temp_audio}' -i '{Config.temp_video}' -shortest '{muxed_file}.mkv'"
    subprocess.call(cmd, shell=True, stdout=stdout, stderr=stderr)

    logger.debug("Clean up.")

    os.remove(Config.temp_video)
    os.remove(Config.temp_audio)

    click.secho("Complete!", fg="green")


if __name__ == "__main__":
    main()
