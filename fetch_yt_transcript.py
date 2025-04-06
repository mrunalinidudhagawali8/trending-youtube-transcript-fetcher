import os
import yt_dlp
import requests
import logging
import time
from io import BytesIO
from pydub import AudioSegment
from faster_whisper import WhisperModel
from langdetect import detect, LangDetectException
from youtube_transcript_api import YouTubeTranscriptApi, TranscriptsDisabled
from youtube_transcript_api.formatters import TextFormatter

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def get_video_id(youtube_url):
    """Extracts video ID from a YouTube URL."""
    logging.info("Extracting video ID from URL: %s", youtube_url)
    if "youtube.com" in youtube_url:
        video_id = youtube_url.split("v=")[-1].split("&")[0]
    elif "youtu.be" in youtube_url:
        video_id = youtube_url.split("/")[-1].split("?")[0]
    else:
        video_id = None

    if video_id:
        logging.info("Extracted video ID: %s", video_id)
    else:
        logging.error("Failed to extract video ID.")
    return video_id

def fetch_transcript(video_id):
    """Fetches transcript using YouTubeTranscriptApi."""
    logging.info("Attempting to fetch transcript for video ID: %s", video_id)
    try:
        transcript = YouTubeTranscriptApi.get_transcript(video_id)
        formatter = TextFormatter()
        logging.info("Successfully fetched transcript.")
        return formatter.format_transcript(transcript)
    except TranscriptsDisabled:
        logging.warning("Transcripts are disabled for this video.")
        return None
    except Exception as e:
        logging.error("Failed to fetch transcript: %s", e)
        return None

def download_audio(youtube_url, output_filename="audio.mp3"):
    output_path = os.path.join(os.getcwd(), output_filename)  # Save in project root
    logging.info("Downloading audio to: %s", output_path)

    ydl_opts = {
        'format': 'bestaudio/best',
        'outtmpl': output_path.replace('.mp3', ''),  # Remove extra .mp3 issue
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '192',
        }]
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([youtube_url])
        logging.info("Audio downloaded successfully: %s", output_path)
    except Exception as e:
        logging.error("Failed to download audio: %s", e)

    return output_path


def transcribe_audio(audio_path, model_size="small"):
    """Transcribes audio using faster-whisper."""
    logging.info("Starting transcription for audio file: %s", audio_path)
    model = WhisperModel(model_size, device="cpu")
    segments, _ = model.transcribe(audio_path)
    transcript = " ".join(segment.text for segment in segments)
    logging.info("Transcription completed.")
    return transcript

def main(youtube_url):
    """Main function to fetch or transcribe YouTube video transcript."""
    logging.info("Processing YouTube URL: %s", youtube_url)
    video_id = get_video_id(youtube_url)
    if not video_id:
        logging.error("Invalid YouTube URL")
        return None

    transcript = fetch_transcript(video_id)
    if transcript:
        logging.info("Transcript fetched successfully!")
        return transcript

    logging.info("Fetching transcript failed. Proceeding to download audio...")
    audio_path = download_audio(youtube_url)
    logging.info("Audio downloaded. Starting transcription...")
    transcript = transcribe_audio(audio_path)
    logging.info("Transcription completed successfully.")
    return transcript

if __name__ == "__main__":
    youtube_url = input("Enter YouTube URL: ")
    result = main(youtube_url)
    print("\nTranscript:")
    print(result)
