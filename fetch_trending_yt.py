
import os  # For interacting with the operating system (e.g., environment variables)
import googleapiclient.discovery  # For interacting with the YouTube Data API
import yt_dlp  # For downloading YouTube audio
import requests  # For making HTTP requests (e.g., downloading audio)
import logging  # For logging messages (useful for debugging)
import time  # For adding delays (e.g., retrying downloads)
from io import BytesIO  # For working with in-memory byte streams
from pydub import AudioSegment  # For audio format conversion
from faster_whisper import WhisperModel  # For transcribing audio using Whisper
from langdetect import detect, LangDetectException  # For detecting the language of text

# Configure Logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

# Load Whisper Model (Do this only once to save time)
logging.info("Loading Whisper model...")
##TODO : check if CPU force is needed/else can we rely completely on GPU/is it faster
whisper_model = WhisperModel("small", device="cpu")  # Load the Whisper model, force CPU usage
logging.info("Whisper model loaded successfully!")


# Function to extract the audio stream URL from a YouTube video
def extract_audio_stream(youtube_url, retries=3):
    logging.info(f"Extracting audio stream from: {youtube_url}")
    ydl_opts = {  # Options for yt-dlp
        'format': 'bestaudio[ext=m4a]/bestaudio/best',  # Get the best audio in m4a format
        'quiet': True,  # Don't print yt-dlp messages
        'no_warnings': True,  # Don't print warnings
        'outtmpl': '-',  # Output to stdout (not to a file)
    }
    for attempt in range(retries):  # Retry download if it fails
        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(youtube_url, download=False)  # Get video info without downloading
                audio_url = info['url']  # Extract the audio URL
                logging.info(f"Audio URL extracted: {audio_url}")
                return audio_url
        except Exception as e:  # Handle exceptions (e.g., network errors)
            logging.error(f"Attempt {attempt + 1} failed: {str(e)}")
            if attempt == retries - 1:  # If all retries failed, raise the exception
                raise e
            time.sleep(2)  # Wait for 2 seconds before retrying


# Function to transcribe audio from a URL using Whisper
def transcribe_audio_from_url(audio_url):
    logging.info(f"Downloading and transcribing audio from URL: {audio_url}")
    try:
        response = requests.get(audio_url, stream=True)  # Download the audio
        audio = AudioSegment.from_file(BytesIO(response.content), format="mp4")  # Convert to WAV
        temp_audio_path = "temp_audio.wav"  # Temporary file path
        audio.export(temp_audio_path, format="wav")  # Export to WAV
        logging.info("Audio converted to WAV format.")
        logging.info("Starting transcription...")
        segments, _ = whisper_model.transcribe(temp_audio_path)  # Transcribe the audio
        transcript = " ".join(segment.text for segment in segments)  # Concatenate segments
        return transcript
    except Exception as e:  # Handle exceptions
        logging.error(f"Failed to transcribe audio: {str(e)}")
        raise e


# Function to get English-language video information from YouTube
def get_english_content_videos(api_key, max_results=5, search_terms=["interview english", "movie clip english", "play scene english"]):
    try:
        youtube = googleapiclient.discovery.build("youtube", "v3", developerKey=api_key)  # Build YouTube API client
        all_videos = []  # List to store video information
        for search_term in search_terms:  # Iterate over search terms
            request = youtube.search().list(  # Search for videos
                part="snippet",
                maxResults=max_results,
                q=search_term,
                type="video",
                #TODO : category can also be trending right? eg. politics
                videoCategoryId="24"  # Entertainment category
            )
            response = request.execute()  # Execute the request
            #TODO : the items can also be shorts right?
            if 'items' in response:  # Check if videos were found
                for item in response['items']:  # Iterate over videos
                    video_id = item['id']['videoId']  # Get video ID
                    video_url = f"https://www.youtube.com/watch?v={video_id}"  # Construct video URL
                    video_details_request = youtube.videos().list(  # Get video details
                        part="snippet",
                        id=video_id
                    )
                    video_details_response = video_details_request.execute()
                    if 'items' in video_details_response:
                        title = video_details_response['items'][0]['snippet']['title']  # Get video title
                        try:
                            if detect(title) != 'en':  # Check if the title is in English
                                continue  # Skip non-English videos
                        except LangDetectException:  # Handle language detection errors
                            continue
                        try:
                            #TODO: first check if subtitles/transcript is already present - if yes then use it and if not then use AI
                            audio_url = extract_audio_stream(video_url)  # Extract audio URL
                            transcript = transcribe_audio_from_url(audio_url)  # Transcribe audio
                            all_videos.append({  # Append video info to the list
                                "title": title,
                                "url": video_url,
                                "transcript": transcript,
                            })
                        except Exception as e:  # Handle video processing errors
                            logging.error(f"Failed to process video {video_id}: {e}")
        return all_videos
    except Exception as e:  # Handle API errors
        logging.error(f"Error: {e}")
        return None


# Main execution block
if __name__ == "__main__":
    api_key = "AIzaSyAxlX_hYE-4sAHz7NDZu1-G6jZgOUyYZcQ"
    if not api_key:
        print("Please set the YOUTUBE_API_KEY environment variable.")
    else:
        english_videos = get_english_content_videos(api_key)  # Get English videos
        if english_videos:  # If videos were found
            for video in english_videos:  # Iterate over videos
                print(f"Title: {video['title']}")  # Print video title
                print(f"URL: {video['url']}")  # Print video URL
                print(f"Transcript:\n{video['transcript']}\n")  # Print transcript
                print("-" * 20)  # Print separator
        else:
            print("Failed to retrieve English content videos.")