import os
import logging
import time
from pydub import AudioSegment
from faster_whisper import WhisperModel

def extract_audio(video_path, audio_path):
    """Extracts audio from the video file and saves it as a WAV file."""
    try:
        audio = AudioSegment.from_file(video_path)
        audio.export(audio_path, format="wav")
        print(f"Audio extracted: {audio_path}")
    except Exception as e:
        print(f"Error extracting audio: {e}")
        return None

def generate_subtitles(audio_path, subtitle_path):
    """Generates subtitles using Whisper and saves them in SRT format."""
    model = WhisperModel("small")  # Change model size if needed
    segments, _ = model.transcribe(audio_path)

    with open(subtitle_path, "w", encoding="utf-8") as srt_file:
        for i, segment in enumerate(segments):
            start = time.strftime('%H:%M:%S', time.gmtime(segment.start)) + ",000"
            end = time.strftime('%H:%M:%S', time.gmtime(segment.end)) + ",000"

            srt_file.write(f"{i+1}\n{start} --> {end}\n{segment.text}\n\n")

    print(f"Subtitles saved: {subtitle_path}")

def main(input_path):
    """Main function to process the video/audio and generate subtitles."""
    subtitle_path = "output.srt"

    if input_path.lower().endswith(('.mp4', '.mkv', '.avi', '.mov')):
        audio_path = "temp_audio.wav"
        extract_audio(input_path, audio_path)
    elif input_path.lower().endswith(('.wav', '.mp3', '.flac', '.aac', '.ogg')):
        audio_path = input_path
    else:
        print("Unsupported file format.")
        return

    generate_subtitles(audio_path, subtitle_path)

    # if input_path.lower().endswith(('.mp4', '.mkv', '.avi', '.mov')):
        # os.remove(audio_path)  # Cleanup
        # print("Temporary files removed.")

if __name__ == "__main__":
    input_file = "snippet.mp4"  # Change this to your video or audio file path
    # input_file = "mark_first_que.mp3"
    main(input_file)
