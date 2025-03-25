import os# import googleapiclient.discovery
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

def extract_audio_stream(youtube_url, retries=2):
    """Extracts the audio stream URL from a YouTube video."""
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
                return info.get('url', None)
        except Exception as e:
            logging.error(f"Attempt {attempt + 1} failed: {str(e)}")
            time.sleep(2)
    return None  # Return None if extraction fails

def transcribe_audio_from_url(audio_url):
    """Downloads and transcribes audio from a given URL."""
    logging.info("Downloading and transcribing audio...")
    try:
        response = requests.get(audio_url, stream=True)
        audio = AudioSegment.from_file(BytesIO(response.content), format="mp4")
        temp_audio_path = "temp_audio.wav"
        audio.export(temp_audio_path, format="wav")

        logging.info("Starting transcription...")
        segments, _ = whisper_model.transcribe(temp_audio_path)
        return " ".join(segment.text for segment in segments)
    except Exception as e:
        logging.error(f"Transcription failed: {str(e)}")
        return None  # Return None if transcription fails

def get_english_content_videos(api_key, max_results=3, search_terms=["Deep dive into song lyrics", "Music explained: meaning behind the lyrics", "Lyrical analysis of trending songs", "How [artist] writes genius lyrics", "Evolution of [genre] music", "Music production secrets of [famous artist]", "What makes [song] so unique?",
                                                                     "Intellectual debates on [topic]", "Philosophical discussions on [show]", "Greatest monologues in TV history", "How [TV show] redefined storytelling", "Most thought-provoking dialogues in TV", "Satirical analysis of [political talk show]", "The best late-night show interviews",
                                                                     "Award-winning short films with deep meaning", "Short films that make you think", "Best psychological thriller short films", "Short films with stunning cinematography", "The most artistic short films ever made", "Short films with profound storytelling", "Dialogue-heavy short films to watch",
                                                                     "Cinematic masterpieces explained", "The philosophy of [director/film]", "Symbolism in [popular film]", "Behind the scenes of [Oscar-winning movie]", "The psychology of great storytelling", "Film theory and narrative analysis", "Why [movie] is a masterpiece",
                                                                     "Geopolitical tensions explained", "Breaking down global economic trends", "The ramifications of policy changes", "Analytical breakdown of [current event]", "Unpacking international relations", "Dissecting the latest Supreme Court ruling", "How media shapes public opinion" ], categories=[10,25,30,39,43]):
    """Fetches trending YouTube videos in specified categories and retrieves transcripts."""
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
                    videoCategoryId=str(category),
                    fields="items(id/videoId,snippet(title,description))"  # Optimize fields to reduce quota usage
                )
                response = request.execute()
                time.sleep(1)  # Prevents API overload

                if 'items' in response:
                    for item in response['items']:
                        video_id = item['id']['videoId']
                        title = item['snippet']['title']
                        description = item['snippet']['description']

                        # Skip Shorts & Non-English Content Early
                        if "shorts" in title.lower() or "shorts" in description.lower():
                            continue
                        try:
                            if detect(title) != 'en':  # Only detect language when necessary
                                continue
                        except LangDetectException:
                            continue

                        # Try fetching transcript first before downloading audio
                        transcript_text = None
                        try:
                            transcript = YouTubeTranscriptApi.get_transcript(video_id, languages=['en'])
                            formatter = TextFormatter()
                            transcript_text = formatter.format_transcript(transcript)
                        except:
                            logging.info(f"No transcript available, skipping video: {video_id}")
                            continue  # Skip if no transcript found instead of using Whisper

                        all_videos.append({
                            "title": title,
                            "url": f"https://www.youtube.com/watch?v={video_id}",
                            "transcript": transcript_text,
                        })

        return all_videos
    except Exception as e:
        logging.error(f"Error: {e}")
        return None  # Return None instead of crashing

if __name__ == "__main__":
    api_key = ""
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
