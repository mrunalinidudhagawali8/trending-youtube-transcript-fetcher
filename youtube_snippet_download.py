import yt_dlp
import subprocess
import os

def download_youtube_snippet(video_url, start_time, end_time, output_filename="snippet.mp4"):
    """
    Downloads a YouTube video and extracts a specific snippet.

    :param video_url: URL of the YouTube video
    :param start_time: Start time in format "hh:mm:ss"
    :param end_time: End time in format "hh:mm:ss"
    :param output_filename: Name of the output file
    """

    # Set yt-dlp options to download the best format
    ydl_opts = {
        'format': 'bv+ba/best',
        'outtmpl': 'temp_video.%(ext)s',
        'merge_output_format': 'mp4'  # Ensures the final output is an MP4 file
    }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info_dict = ydl.extract_info(video_url, download=True)
        video_ext = info_dict.get('ext', 'mp4')
        temp_video_filename = f"temp_video.{video_ext}"

    # Trim the video using FFmpeg
    trimmed_output = output_filename
    ffmpeg_cmd = [
        "ffmpeg", "-i", temp_video_filename, "-ss", start_time, "-to", end_time,
        "-c:v", "libx264", "-c:a", "aac", "-strict", "experimental",
        trimmed_output
    ]

    subprocess.run(ffmpeg_cmd, check=True)

    # Remove the full downloaded video to save space
    os.remove(temp_video_filename)

    print(f"Snippet saved as {trimmed_output}")

# Example usage
video_url = "https://www.youtube.com/watch?v=6C4ZV4TW86g"
start_time = "00:00:25"  # Start time (hh:mm:ss)
end_time = "00:00:37"  # End time (hh:mm:ss)

download_youtube_snippet(video_url, start_time, end_time)

# # Example usage
# video_url = "https://www.youtube.com/watch?v=LyBims8OkSY"
# start_time = "00:02:05"  # Start time (hh:mm:ss)

# end_time = "00:02:12"  # End time (hh:mm:ss)
# download_youtube_snippet(video_url, start_time, end_time)
