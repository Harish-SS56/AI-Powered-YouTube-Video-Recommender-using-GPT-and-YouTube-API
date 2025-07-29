# IMPORTANT: Store your API keys in a `.env` file or your system environment variables:
# OPENAI_API_KEY=your_openai_key_here
# YOUTUBE_API_KEY=your_youtube_api_key_here


import openai
import os
import datetime
import requests
import speech_recognition as sr
from googleapiclient.discovery import build
from pydub import AudioSegment

# Set your own API keys
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
YOUTUBE_API_KEY = os.getenv("YOUTUBE_API_KEY")
openai.api_key = OPENAI_API_KEY

# Initialize YouTube API
youtube = build("youtube", "v3", developerKey=YOUTUBE_API_KEY)

def get_query():
    choice = input(" Voice or  Text input? (v/t): ").strip().lower()
    if choice == "v":
        recognizer = sr.Recognizer()
        with sr.Microphone() as source:
            print("Speak your query...")
            audio = recognizer.listen(source)
        try:
            return recognizer.recognize_google(audio, language="en-IN")
        except:
            return input("Couldn't understand. Enter your query in text: ")
    else:
        return input(" Enter your search query: ")

def search_youtube_videos(query):
    published_after = (datetime.datetime.now() - datetime.timedelta(days=14)).isoformat("T") + "Z"
    search_response = youtube.search().list(
        q=query,
        type="video",
        part="id,snippet",
        maxResults=25,
        publishedAfter=published_after
    ).execute()

    results = []
    for item in search_response["items"]:
        video_id = item["id"]["videoId"]
        video_title = item["snippet"]["title"]
        publish_time = item["snippet"]["publishedAt"]

        video_response = youtube.videos().list(
            part="contentDetails",
            id=video_id
        ).execute()
        duration_iso = video_response["items"][0]["contentDetails"]["duration"]

        import isodate
        duration = isodate.parse_duration(duration_iso).total_seconds() / 60.0

        if 4 <= duration <= 20:
            results.append({
                "title": video_title,
                "url": f"https://www.youtube.com/watch?v={video_id}",
                "duration": round(duration, 2),
                "publish_time": publish_time
            })

        if len(results) == 20:
            break

    return results

def analyze_titles_with_gpt(titles):
    prompt = f"""You are a smart assistant that ranks YouTube video titles by quality and relevance. 
Below are titles of videos. Recommend the best one:

{chr(10).join([f"{i+1}. {t}" for i, t in enumerate(titles)])}

Return the number of the best one and a short reason.
"""

    response = openai.chat.completions.create(
        model="gpt-4o",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.3
    )

    return response.choices[0].message.content.strip()


def main():
    query = get_query()
    print(f"\n Searching for: {query}\n")
    videos = search_youtube_videos(query)

    if not videos:
        print("No relevant videos found.")
        return

    for idx, vid in enumerate(videos, start=1):
        print(f"{idx}. {vid['title']} ({vid['duration']} mins) – {vid['url']}")

    print("\n Analyzing with GPT...\n")
    titles = [v["title"] for v in videos]
    analysis = analyze_titles_with_gpt(titles)
    print("GPT's Recommendation:\n", analysis)

if __name__ == "__main__":
    main()
