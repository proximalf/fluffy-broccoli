from datetime import datetime, time
from pathlib import Path
import re
from pytube import YouTube
from pytube.exceptions import PytubeError
from typing import Optional
from moviepy.editor import AudioFileClip, VideoFileClip
import click
import logging
import os
import subprocess

from .config import Config

logger = logging.getLogger(__package__)


def mux_audio_video(
    filename: Path, temp_audio: Path, temp_video: Path, stdout: Path, stderr: Path
) -> None:
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


def time2seconds(x: time) -> int:
    """
    Converts x time object into seconds, returns an int.
    """
    return int((x.minute * 60) + x.second)


def clip_audio_video(
    temp_audio: Path,
    temp_video: Path,
    clip_start: time,
    clip_end: time,
    minimum_duration: int = 1,
) -> VideoFileClip:
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
    clip_start, clip_end = time2seconds(clip_start), time2seconds(clip_end)

    if clip_start < minimum_duration:
        logger.error(f"Duration too short: {clip_start} < {minimum_duration}")

    logger.debug(f"Clipping - a:{temp_audio}, v:{temp_video}")
    audio_file = AudioFileClip(str(temp_audio))
    audio_clip = audio_file.subclip(clip_start, clip_end)

    video_file = VideoFileClip(str(temp_video))
    video_clip = video_file.subclip(clip_start, clip_end)

    # Add clipped audio
    video_clip.audio = audio_clip

    return video_clip


def clip_audio(
    temp_audio: Path, clip_start: time, clip_end: time, minimum_duration: int = 1
) -> AudioFileClip:
    """
    This function clips audio.

    Parameters
    ----------
    temp_audio: Path
        Path to downloaded audio.
    clip_start: time
        Start time as a time object of clip.
    clip_end: time
        End time as a time object of clip.
    minimum_duration: int
        Minimum duration a video can be, in seconds, default is 1.

    Returns
    ----------
    audio_clip: AudioFileClip
        Audio clip.
    """
    # Convert from time objects to seconds
    clip_start, clip_end = time2seconds(clip_start), time2seconds(clip_end)

    if clip_start < minimum_duration:
        logger.error(f"Duration too short: {clip_start} < {minimum_duration}")

    logger.debug(f"Clipping - a:{temp_audio}")
    audio_file = AudioFileClip(str(temp_audio))
    audio_clip = audio_file.subclip(clip_start, clip_end)

    return audio_clip


def save_clipped_video(video_clip: VideoFileClip, file_path: Path) -> None:
    """
    Saves a clipped video to path.
    """
    video_clip.write_videofile(str(file_path))


def save_clipped_audio(audio_clip: AudioFileClip, file_path: Path) -> None:
    """
    Saves a clipped audio to path.
    """
    audio_clip.write_audiofile(str(file_path))


def clean_up_temp_files(temp_audio: Path, temp_video: Path) -> None:
    """
    Helper function for cleaning up files.
    """
    if temp_audio.exists():
        logger.debug("Cleaning up Audio.")
        os.remove(temp_audio)
    if temp_video.exists():
        logger.debug("Cleaning up Video.")
        os.remove(temp_video)


def validate_url(url: str) -> bool:
    """
    Returns True if url is valid.

    Parameters
    ----------
    url: str
        String of URL to be checked.

    Returns
    ----------
    bool
        True if valid.
    """
    regex = re.compile(
        r"(\w+://)?"  # protocol (optional)
        r"(\w+\.)?"  # host (optional)
        r"(([\w-]+)\.(\w+))"  # domain
        r"(\.\w+)*"  # top-level domain (optional, can have > 1)
        r"([\w\-\._\~/]*)*(?<!\.)"  # path, params, anchors, etc. (optional)
    )
    valid = regex.match(url)
    if valid:
        return True
    logger.warning("Invalid URL")
    return False


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
            click.secho(
                f"Failed to grab URL, retrying - {retry_attempts - i} ", fg="red"
            )
            logger.debug(f"Exception: {ex}")
            yt = None

        if i == retry_attempts:
            click.secho("Cannot fetch url...", fg="red")
            yt = None

    return yt


def _download_from_youtube(
    output_filename: Path,
    youtube: YouTube,
    resolution: Optional[str] = None,
    clip: Optional[str] = None,
) -> None:
    """
    Downloads video from Youtube.

    Parameters
    ----------
    output_filename: Path
        Output filename.
    youtube: YouTube
        Youtube object.
    resolution: Optional[str]
        Resolution to download, optional, if not specified highest video quality will be downloaded.
    clip: Optional[str]
        If clipping a video, provide argument as "4:05,5:43", default is None.
    """
    output = str(output_filename.parent)

    stream = youtube.streams.filter(
        file_extension="mp4", mime_type="video/mp4", adaptive=True
    )

    if resolution is not None:
        stream = stream.get_by_resolution(resolution)
        if stream is None:
            logger.critical(f"Stream cannot be found with resolution: {resolution}")
            raise ValueError(f"Resolution is not valid for this stream. {resolution}")
    else:
        stream = stream.order_by("resolution")[-1]

    logger.debug(f"Downloading video component: {stream}")
    stream.download(Config.temp_video_path.parent, Config.temp_video_path.name)

    logger.debug("Downloading audio component")
    stream = youtube.streams.get_audio_only()
    stream.download(Config.temp_audio_path.parent, Config.temp_audio_path.name)

    click.secho("Download complete!", fg="green")

    if clip is not None:
        clip_start, clip_end = [
            datetime.strptime(i, "%M:%S").time() for i in clip.split(",")
        ]

        if youtube.length < time2seconds(clip_end):
            raise Exception("Video length is shorter than specified clip.")

        click.secho(f"Clipping... {clip_start} - {clip_end}")

        video_clip = clip_audio_video(
            Config.temp_audio_path, Config.temp_video_path, clip_start, clip_end
        )

        logger.debug("Merging and saving clip...")

        save_clipped_video(
            video_clip,
            output_filename.with_suffix(".mp4"),
        )
    else:
        mux_audio_video(
            output_filename,
            Config.temp_audio_path,
            Config.temp_video_path,
            Config.stdout,
            Config.stdout,
        )


def _download_audio_from_youtube(
    output_filename: Path, youtube: YouTube, clip: Optional[str] = None
) -> None:
    """
    Downloads audio only from Youtube.

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

    logger.debug("Downloading audio component")
    stream = youtube.streams.get_audio_only()
    stream.download(Config.temp_audio_path.parent, Config.temp_audio_path.name)

    click.secho("Download complete!", fg="green")

    if clip is not None:
        clip_start, clip_end = [
            datetime.strptime(i, "%M:%S").time() for i in clip.split(",")
        ]

        if youtube.length < time2seconds(clip_end):
            raise Exception("Video length is shorter than specified clip.")

        click.secho(f"Clipping... {clip_start} - {clip_end}")

        audio_clip = clip_audio(Config.temp_audio_path, clip_start, clip_end)

        logger.debug("Saving clip...")

        save_clipped_audio(
            audio_clip,
            output_filename.with_suffix(".mp3"),
        )
    else:
        # Rename temp file.
        os.rename(Config.temp_audio_path, output_filename.with_suffix(".mp3"))


def download_from_youtube(
    output_filename: Path,
    youtube: YouTube,
    resolution: Optional[str] = None,
    clip: Optional[str] = None,
    audio_only: bool = False,
) -> None:
    """
    Downloads video from Youtube.

    Parameters
    ----------
    output_filename: Path
        Output filename.
    youtube: YouTube
        Youtube object.
    resolution: Optional[str]
        Resolution to download, if None, highest quality is preffered.
    clip: Optional[str]
        If clipping a video, provide argument as "4:05,5:43", default is None.
    audio_only: bool
        Flag to download audio only.
    """
    if audio_only:
        _download_audio_from_youtube(output_filename, youtube, clip)
    else:
        _download_from_youtube(output_filename, youtube, resolution, clip)

    clean_up_temp_files(Config.temp_audio_path, Config.temp_video_path)
