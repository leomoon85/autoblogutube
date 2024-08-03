import os
import requests
import json
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build

# If modifying these SCOPES, delete the file token.json.
SCOPES = ['https://www.googleapis.com/auth/youtube.readonly']

def authenticate_youtube_api():
    creds = None
    # The file token.json stores the user's access and refresh tokens, and is
    # created automatically when the authorization flow completes for the first time.
    if os.path.exists('token.json'):
        creds = Credentials.from_authorized_user_file('token.json', SCOPES)
    # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                'client_secret.json', SCOPES)
            creds = flow.run_local_server(port=0)
        # Save the credentials for the next run
        with open('token.json', 'w') as token:
            token.write(creds.to_json())
    return creds

# Get top videos until we find 10 with captions
def get_videos_with_captions(youtube, max_results=50):
    videos_with_captions = []
    next_page_token = None

    while len(videos_with_captions) < 1000000:
        request = youtube.videos().list(
            part='snippet',
            chart='mostPopular',
            maxResults=max_results,
            pageToken=next_page_token,
            regionCode='US'
        )
        response = request.execute()
        
        for video in response['items']:
            video_id = video['id']
            video_title = video['snippet']['title']
            captions = get_captions(video_id)
            if captions:
                videos_with_captions.append({
                    'id': video_id,
                    'title': video_title,
                    'captions': captions
                })
                if len(videos_with_captions) == 10:
                    break
        
        next_page_token = response.get('nextPageToken')
        if not next_page_token:
            break

    return videos_with_captions

# Get captions for a video
def get_captions(video_id):
    url = f'http://video.google.com/timedtext?lang=en&v={video_id}'
    response = requests.get(url)
    return response.text if response.status_code == 200 else None

# Main function
def main():
    creds = authenticate_youtube_api()
    youtube = build('youtube', 'v3', credentials=creds)
    
    videos = get_videos_with_captions(youtube)
    
    if not os.path.exists('captions'):
        os.makedirs('captions')
    
    for video in videos:
        video_id = video['id']
        video_title = video['title']
        captions = video['captions']
        # Sanitize the file name
        sanitized_title = ''.join(c for c in video_title if c.isalnum() or c in (' ', '_')).rstrip()
        
        with open(f'captions/{sanitized_title}.txt', 'w', encoding='utf-8') as f:
            f.write(captions)
        print(f'Captions saved for video: {video_title}')

if __name__ == "__main__":
    main()

