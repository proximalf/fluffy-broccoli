from pathlib import Path


class Config:
    # Output directory
    output_directory: Path = Path.home() / "Downloads"

    # Download resolution, if None, highest quality is preffered.
    resolution_default = None

    # Temporary file locations
    temp_video_path: Path = output_directory / "video.mp4"
    temp_audio_path: Path = output_directory / "audio.mp4"

    # Stdout and err for ffmpeg
    stdout: Path = output_directory / "dylt-out.log"
    stderr: Path = output_directory / "dylt-err.log"

    retry_attempts: int = 3
