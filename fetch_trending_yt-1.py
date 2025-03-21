import os
import googleapiclient.discovery
import yt_dlp
import requests
import logging
import time
from io import BytesIO
from pydub import AudioSegment
from faster_whisper import WhisperModel
from langdetect import detect, LangDetectException
from youtube_transcript_api import YouTubeTranscriptApi
from youtube_transcript_api.formatters import TextFormatter

# Configure Logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

# Load Whisper Model (Check for GPU availability)
logging.info("Loading Whisper model...")
device = "cuda" if os.environ.get("CUDA_VISIBLE_DEVICES") else "cpu"
whisper_model = WhisperModel("small", device=device)
logging.info(f"Whisper model loaded successfully on {device}!")

def extract_audio_stream(youtube_url, retries=3):
    logging.info(f"Extracting audio stream from: {youtube_url}")
    ydl_opts = {
        'format': 'bestaudio[ext=m4a]/bestaudio/best',
        'quiet': True,
        'no_warnings': True,
        'outtmpl': '-',
    }
    for attempt in range(retries):
        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(youtube_url, download=False)
                audio_url = info['url']
                logging.info(f"Audio URL extracted: {audio_url}")
                return audio_url
        except Exception as e:
            logging.error(f"Attempt {attempt + 1} failed: {str(e)}")
            if attempt == retries - 1:
                raise e
            time.sleep(2)

def transcribe_audio_from_url(audio_url):
    logging.info(f"Downloading and transcribing audio from URL: {audio_url}")
    try:
        response = requests.get(audio_url, stream=True)
        audio = AudioSegment.from_file(BytesIO(response.content), format="mp4")
        temp_audio_path = "temp_audio.wav"
        audio.export(temp_audio_path, format="wav")
        logging.info("Audio converted to WAV format.")
        logging.info("Starting transcription...")
        segments, _ = whisper_model.transcribe(temp_audio_path)
        transcript = " ".join(segment.text for segment in segments)
        return transcript
    except Exception as e:
        logging.error(f"Failed to transcribe audio: {str(e)}")
        raise e

def get_english_content_videos(api_key, max_results=3, search_terms=["What's trending now", "Top stories today", "Viral videos", "Celebrity news", "Movie trailers", "Game highlights", "Funny moments", "Latest updates", "Explained","Reaction videos"], categories=[24, 10, 22, 25, 17, 23]):
    try:
        youtube = googleapiclient.discovery.build("youtube", "v3", developerKey=api_key)
        all_videos = []
        for search_term in search_terms:
            for category in categories:
                request = youtube.search().list(
                    part="snippet",
                    maxResults=max_results,
                    q=search_term,
                    type="video",
                    videoCategoryId=str(category)
                )
                response = request.execute()
                if 'items' in response:
                    for item in response['items']:
                        video_id = item['id']['videoId']
                        video_url = f"https://www.youtube.com/watch?v={video_id}"
                        video_details_request = youtube.videos().list(
                            part="snippet",
                            id=video_id
                        )
                        video_details_response = video_details_request.execute()
                        if 'items' in video_details_response:
                            title = video_details_response['items'][0]['snippet']['title']
                            description = video_details_response['items'][0]['snippet']['description']
                            if "shorts" in title.lower() or "shorts" in description.lower():
                                continue
                            try:
                                if detect(title) != 'en':
                                    continue
                            except LangDetectException:
                                continue
                            try:
                                transcript_text = None
                                try:
                                    transcript = YouTubeTranscriptApi.get_transcript(video_id, languages=['en'])
                                    formatter = TextFormatter()
                                    transcript_text = formatter.format_transcript(transcript)
                                except:
                                    logging.info(f"Could not retrieve transcript from YouTube, attempting whisper for video: {video_id}")
                                    audio_url = extract_audio_stream(video_url)
                                    transcript_text = transcribe_audio_from_url(audio_url)
                            all_videos.append({
                                "title": title,
                                "url": video_url,
                                "transcript": transcript_text,
                            })
                        except Exception as e:
                        logging.error(f"Failed to process video {video_id}: {e}")
    return all_videos
except Exception as e:
logging.error(f"Error: {e}")
return None

if __name__ == "__main__":
    api_key = os.environ.get("YOUTUBE_API_KEY")
    if not api_key:
        print("Please set the YOUTUBE_API_KEY environment variable.")
    else:
        english_videos = get_english_content_videos(api_key)
        if english_videos:
            for video in english_videos:
                print(f"Title: {video['title']}")
                print(f"URL: {video['url']}")
                print(f"Transcript:\n{video['transcript']}\n")
                print("-" * 20)
        else:
            print("Failed to retrieve English content videos.")