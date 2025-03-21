import yt_dlp
import os
import platform
import shutil  # For deleting directories


video_url = "https://www.youtube.com/shorts/Dhk_tsGDWVc"
audio_file = "test_audio.mp4"

ydl_opts = {
    'format': 'bestaudio/best',
}

with yt_dlp.YoutubeDL(ydl_opts) as ydl:
    ydl.download([video_url])

print("Download complete.")