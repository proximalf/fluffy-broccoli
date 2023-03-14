from pathlib import Path

class Config:
    # Output directory
    output_dir: Path = Path.home() / "Downloads"

    # Download resolution
    resolution_default = "1080p"

    # Temporary file locations
    temp_video: Path = output_dir / "video.mp4"
    temp_audio: Path = output_dir / "audio.mp4"
    
    # Stdout and err for ffmpeg
    stdout: Path = output_dir / "dylt-out.log"
    stderr: Path = output_dir / "dylt-err.log"