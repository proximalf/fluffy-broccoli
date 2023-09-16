from datetime import datetime, time
from pathlib import Path
from pytube import YouTube
from pytube.exceptions import PytubeError
from typing import Optional
from moviepy.editor import AudioFileClip, VideoFileClip
import click
import logging
import os
import subprocess

from .config import Config

logger = logging.getLogger(__name__)


def mux_audio_video(filename: Path, temp_audio: Path, temp_video: Path, stdout: Path, stderr: Path) -> None:
    """
    Mux audio and video using ffmpeg.

    Parameters
    ----------
    filename: Path
        Path to save file as.
    temp_audio: Path
        Path to save temp_audi to.
    temp_video: Path
        Path to save temp_video to.
    stdout: Path
        Path to save STDOUT to.
    stderr: Path
        Path to save STDERR to.
    """
    logger.debug("Merging using FFMPEG")

    stdout = stdout.open("w")
    stderr = stderr.open("w")

    click.secho(f"Muxing w/ ffmpeg!\nSave Location: {filename}", fg="green")

    cmd = f"ffmpeg -y -i '{temp_audio}' -i '{temp_video}' -shortest '{filename}.mkv'"
    subprocess.call(cmd, shell=True, stdout=stdout, stderr=stderr)

def clip_audio_video(temp_audio: Path, temp_video: Path, clip_start: time, clip_end: time, minimum_duration: int = 1) -> VideoFileClip:
    """
    This function clips and merges the file.

    Parameters
    ----------
    temp_audio: Path
        Path to downloaded audio.
    temp_video: Path
        Path to downloaded video.
    clip_start: time
        Start time as a time object of clip.
    clip_end: time
        End time as a time object of clip.
    minimum_duration: int
        Minimum duration a video can be, in seconds, default is 1.

    Returns
    ----------
    video_clip: VideoFileClip
        Video clip with audio attached.
    """
    # Convert from time objects to seconds
    time2seconds = lambda x: int((x.minute * 60) + x.second)
    clip_start, clip_end = time2seconds(clip_start), time2seconds(clip_end)

    if clip_start< minimum_duration:
        logger.error(f"Duration too short: {clip_start} < {minimum_duration}")
    
    logger.debug(f"Clipping - a:{temp_audio}, v:{temp_video}")
    audio_file = AudioFileClip(str(temp_audio))
    audio_clip = audio_file.subclip(clip_start, clip_end)

    video_file = VideoFileClip(str(temp_video))
    video_clip = video_file.subclip(clip_start, clip_end)
    
    # Add clipped audio
    video_clip.audio = audio_clip

    return video_clip


def save_clipped_video(video_clip: VideoFileClip, file_path: Path) -> None:
    """
    Saves a clipped video
    """
    video_clip.write_videofile(str(file_path))
    
    
def clean_up_temp_files(temp_audio: Path, temp_video: Path) -> None:
    """
    Helper function for cleaning up files.
    """
    logger.debug("Clean up.")
    os.remove(temp_video)
    os.remove(temp_audio)

def fetch_from_youtube(url: str, retry_attempts: int = 3) -> Optional[YouTube]:
    """
    Fetches url from YouTube using PyTube.

    Parameters
    ----------
    url: str
        String of URL to fetch.

    Returns
    ---------
    Optional[Youtube]
        If link is fetched sucessfully, a YouTube object is returned.
    """
    yt = None
    for i in range(retry_attempts):
        
        try:
            yt = YouTube(url)
            click.secho(f"Downloading: {yt.title}", fg="green")
            break

        except PytubeError as ex:
            click.secho(f"Failed to grab URL, retrying - {retry_attempts - i} ", fg="red")
            logger.debug(f"Exception: {ex}")
            yt = None
        
        if i == retry_attempts:
            click.secho("Cannot fetch url...", fg="red")
            yt = None

    return yt

def download_from_youtube(output_filename: Path, youtube: YouTube, resolution: str, clip: Optional[str]  = None) -> None:
    """
    Downloads video from Youtube.

    Parameters
    ----------
    output_filename: Path  
        Output filename.
    youtube: YouTube
        Youtube object.
    resolution: str
        Resolution to download.
    clip: Optional[str]  
        If clipping a video, provide argument as "4:05,5:43", default is None.
    """
    output = str(output_filename.parent)

    logger.debug("Downloading video component")
    
    for stream in youtube.streams:
        logger.debug(f"youtube.streams: {stream}")

    stream = youtube.streams.filter(file_extension="mp4", res=resolution)[-1]
    stream.download(output, Config.temp_video.name)

    logger.debug("Downloading audio component")
    stream = youtube.streams.filter(file_extension="mp4", mime_type="audio/mp4")[-1]
    stream.download(output, Config.temp_audio.name)

    click.secho("Download complete!", fg="green")   

    if clip is not None:
        clip_start, clip_end = [datetime.strptime(i, "%M:%S").time() for i in clip.split(",")]
        
        click.secho(f"Clipping... {clip_start} - {clip_end}")

        video_clip = clip_audio_video(
            Config.temp_audio,
            Config.temp_video,
            clip_start, clip_end
        )

        logger.debug("Merging and saving clip...")  

        save_clipped_video(
            video_clip,
            output_filename.with_suffix(".mp4"),
        )
    else:
        mux_audio_video(
            output_filename,
            Config.temp_audio,
            Config.temp_video,
            Config.stdout,
            Config.stdout,
            )
    
    clean_up_temp_files(
        Config.temp_audio,
        Config.temp_video
        )
