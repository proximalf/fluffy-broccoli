# DLYT

Basic script to download yt video, uses click cli interface and `pytube`, `FFMPEG`.

Default behaviour is to take a link copied from clipboard using `pyperclip`.

## Build

Install using poetry. Need `FFMPEG` installed for clipping, not sure if it'll still run without FFMPEG installed.

## Run

Run command in terminal, takes link from clipboard.
`dylt`

```
dylt -c "0:8,5:1"

dylt -u "https://youtu.be/KenyufNno5c?si=xTuBb0cvStAIU4B7" -t jb,sax

dylt -n "New filename"

dylt --audio-only
```

## Config
Was lazy with config, edit `dylt/config.py`.


## License

This project is licensed under the terms of the MIT License.
