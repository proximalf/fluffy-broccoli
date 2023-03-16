from pathlib import Path
from pytube import YouTube
from typing import Optional
from moviepy.editor import AudioFileClip, VideoFileClip
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

    logger.debug("Clean up.")

    os.remove(temp_video)
    os.remove(temp_audio)

    click.secho("Complete!", fg="green")

def clip_audio_video(temp_audio: Path, temp_video: Path, clip_start: str, clip_end: str, minimum_duration: int = 1) -> None:
    # convert paths to string cause moviepy
    temp_audio, temp_video = str(temp_audio), str(temp_video)
    
    if clip_start < minimum_duration:
        logger.error(f"Duration too short: {clip_start} < {minimum_duration}")
    
    logger.debug(f"Clipping - a:{temp_audio}, v:{temp_video}")
    audio_file = AudioFileClip(temp_audio)
    audio_clip = audio_file.subclip(clip_start, clip_end)

    video_file = VideoFileClip(temp_video)
    video_clip = video_file.subclip(clip_start, clip_end)
    
    logger.debug("Saviong clips...")
    audio_clip.write_audiofile(temp_audio)
    video_clip.write_videofile(temp_video)  




@click.command()
@click.argument("url")
@click.option("resolution", "-r", default=Config.resolution_default, type=str)
@click.option("clip", "-c", default=None, type=str)
def cli(url: str, resolution: str = Config.resolution_default, clip: Optional[str] = None) -> None:
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

    if clip is not None:
        clip_start, clip_end = clip.split(",")
        click.secho(f"Clipping... {clip_start} - {clip_end}")
        clip_audio_video(
            Config.temp_audio,
            Config.temp_video,
            clip_start, clip_end
        )
    
    mux_audio_video(
        yt.title,
        Config.output_dir,
        Config.temp_audio,
        Config.temp_video,
        Config.stdout,
        Config.stdout,
        )
