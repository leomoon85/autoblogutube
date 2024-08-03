import os
import json
import requests
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
import google.generativeai as genai

# If modifying these SCOPES, delete the file token.json.
SCOPES = ['https://www.googleapis.com/auth/youtube.readonly']
PLAYLIST_ID = 'PLefHOXeb70TKiVBztN7cOQt6PuOkOxeCx'  # Playlist ID

# Generative AI OAuth details
GENAI_CLIENT_SECRETS_FILE = "genai_client_secret.json"  # Path to your Generative AI client secret file

def authenticate_youtube_api():
    creds = None
    if os.path.exists('token.json'):
        creds = Credentials.from_authorized_user_file('token.json', SCOPES)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                'client_secret.json', SCOPES)
            creds = flow.run_local_server(port=0)
        with open('token.json', 'w') as token:
            token.write(creds.to_json())
    return creds

def authenticate_genai_api():
    creds = None
    if os.path.exists('genai_token.json'):
        creds = Credentials.from_authorized_user_file('genai_token.json')
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                GENAI_CLIENT_SECRETS_FILE, scopes=["https://www.googleapis.com/auth/cloud-platform","https://www.googleapis.com/auth/generative-language.retriever"])
            creds = flow.run_local_server(port=0)
        with open('genai_token.json', 'w') as token:
            token.write(creds.to_json())
    genai.credentials = creds

def get_videos_with_descriptions(youtube, playlist_id, max_results=50):
    videos_with_descriptions = []
    next_page_token = None

    while len(videos_with_descriptions) < 10:
        request = youtube.playlistItems().list(
            part='snippet',
            playlistId=playlist_id,
            maxResults=max_results,
            pageToken=next_page_token
        )
        response = request.execute()
        
        for item in response['items']:
            video_id = item['snippet']['resourceId']['videoId']
            video_title = item['snippet']['title']
            video_description = get_description(youtube, video_id)
            if video_description:
                videos_with_descriptions.append({
                    'id': video_id,
                    'title': video_title,
                    'description': video_description
                })
                if len(videos_with_descriptions) == 10:
                    break
        
        next_page_token = response.get('nextPageToken')
        if not next_page_token:
            break

    return videos_with_descriptions

def get_description(youtube, video_id):
    request = youtube.videos().list(
        part='snippet',
        id=video_id
    )
    response = request.execute()
    if response['items']:
        return response['items'][0]['snippet']['description']
    return None

def create_blog_from_description(description):
    response = genai.generate_text(
        model="models/text-davinci-002",
        prompt=f"Write a blog post based on the following description: {description}"
    )
    return response["choices"][0]["text"]

def main():
    creds = authenticate_youtube_api()
    youtube = build('youtube', 'v3', credentials=creds)
    
    authenticate_genai_api()
    
    videos = get_videos_with_descriptions(youtube, PLAYLIST_ID)
    
    if not os.path.exists('blog'):
        os.makedirs('blog')
    
    for video in videos:
        video_title = video['title']
        video_description = video['description']
        blog_content = create_blog_from_description(video_description)
        sanitized_title = ''.join(c for c in video_title if c.isalnum() or c in (' ', '_')).rstrip()
        
        with open(f'blog/{sanitized_title}.txt', 'w', encoding='utf-8') as f:
            f.write(blog_content)
        print(f'Blog post saved for video: {video_title}')

if __name__ == "__main__":
    main()

