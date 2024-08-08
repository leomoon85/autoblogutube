import os
import json
import requests
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
import google.generativeai as genai
from requests.auth import HTTPBasicAuth
from pytrends.request import TrendReq

#TRENDING_QUERY = 'bollywood movie interviews'
TRENDING_QUERY = 'Malayalam actor interviews'
MAX_RESULTS = 10

# Load API keys from the file
def load_api_keys(file_path):
    keys = {}
    with open(file_path, 'r') as f:
        for line in f:
            name, value = line.strip().split('=')
            keys[name] = value
    return keys

keys = load_api_keys('api_keys.txt')

GENAI_API_KEY = keys['GENAI_API_KEY']
BLOGGER_BLOG_ID = keys['BLOGGER_BLOG_ID']

# If modifying these SCOPES, delete the file token.json.
SCOPES = ['https://www.googleapis.com/auth/youtube.readonly', 'https://www.googleapis.com/auth/blogger']

#SCOPES = ['https://www.googleapis.com/auth/youtube.readonly']
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
                GENAI_CLIENT_SECRETS_FILE, scopes=["https://www.googleapis.com/auth/cloud-platform", "https://www.googleapis.com/auth/generative-language.retriever"])
            creds = flow.run_local_server(port=0)
        with open('genai_token.json', 'w') as token:
            token.write(creds.to_json())
    genai.credentials = creds
    genai.configure(api_key=GENAI_API_KEY)

def get_videos_for_query(youtube, query, max_results=10):
    request = youtube.search().list(
        part='snippet',
        q=query,
        type='video',
        maxResults=max_results,
        regionCode='IN'  # India region code for Malayalam and Bollywood content
    )
    response = request.execute()
    
    videos = []
    for item in response['items']:
        video_id = item['id']['videoId']
        video_title = item['snippet']['title']
        video_description = item['snippet']['description']
        video_url = f"https://www.youtube.com/watch?v={video_id}"
        videos.append({
            'id': video_id,
            'title': video_title,
            'description': video_description,
            #'url': video_url,
            'url': f"https://www.youtube.com/embed/{video_id}"
        })
    
    return videos

def get_trending_searches_from_google():
    pytrends = TrendReq(hl='en-US', tz=360)
    trending_searches_df = pytrends.trending_searches(pn='india')
    trending_searches = trending_searches_df[0].tolist()
    return trending_searches[:5]  # Limit to top 5 trending searches

def get_trending_videos(youtube, query, max_results=10):
    video_queries = [
 #       ('Cheap used car india', 5),
        ('Malayalam interview', 1),
        ('Bollywood interview', 2),
        ('France Fashion discussions', 2),
        ('Tamil interview podcast', 1)
    ]
    all_videos = []
    for query, count in video_queries:
        videos = get_videos_for_query(youtube, query, count)
        all_videos.extend(videos)
    
    return all_videos

def get_videos_with_descriptions(youtube, playlist_id, max_results=50):
    videos_with_descriptions = []
    next_page_token = None

    while len(videos_with_descriptions) < 2:
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

def create_blog_from_description(title, description, video_url):
    model = genai.GenerativeModel('gemini-1.5-flash')
    prompt = f"Write a blog post based on the following description from a YouTube video in html format. No suggestions to user. The first line should be an overview. Text of description is:\n{description}"
    #prompt = (f"Write a blog post based on the following YouTube video description. "
   #           f"The first line should be an overview. "
    #          f"elaborate it in 2 paragraphs . details is:\n{description}\n\n" 
     #         f"Format into 2 to 3 paragraphs , if links are there format as links in seperate lines , if #keywords are there use as keywords at last in a seperate lines")
              #f"Embed the video URL {video_url} in the blog post.")
    response = model.generate_content(prompt)
    blog_content = response.text + f'\n\n<iframe width="560" height="315" src="{video_url}" frameborder="0" allowfullscreen></iframe>'
    
    
    return blog_content

def post_to_blogger(blog_id, title, content, creds):
    service = build('blogger', 'v3', credentials=creds)
    post = {
        'title': title,
        'content': content
    }
    request = service.posts().insert(blogId=blog_id, body=post)
    response = request.execute()
    return response

def post_to_wix(title, content):
    url = WIX_API_URL.format(WIXSITEID=WIX_SITE_ID)
    headers = {
        'Content-Type': 'application/json',
        'Authorization': f'Bearer {WIX_ACCESS_TOKEN}'
    }
    data = {
        'title': title,
        'content': {
            'text': content
        },
        'status': 'PUBLISHED'
    }
    response = requests.post(url, headers=headers, json=data)
    response.raise_for_status()  # Raise an error for bad status codes
    return response.json()

def post_to_wordpress(title, content):
    headers = {
        'Content-Type': 'application/json'
    }
    data = {
        'title': title,
        'content': content,
        'status': 'publish'
    }
    response = requests.post(
        WORDPRESS_URL,
        headers=headers,
        json=data,
        auth=HTTPBasicAuth(WORDPRESS_USER, WORDPRESS_APP_PASSWORD)
    )
    response.raise_for_status()  # Raise an error for bad status codes
    return response.json()

def main():
    creds = authenticate_youtube_api()
    youtube = build('youtube', 'v3', credentials=creds)
    
    authenticate_genai_api()
    
    trending_searches = get_trending_searches_from_google() 
    for query in trending_searches:
        videos = get_videos_for_query(youtube, query)
        #videos = get_videos_with_descriptions(youtube, PLAYLIST_ID)
        #videos = get_trending_videos(youtube, TRENDING_QUERY, MAX_RESULTS)
        for video in videos:
            video_title = video['title']
            video_description = video['description']
            video_url = video['url']
            blog_content = create_blog_from_description(video_title,video_description, video_url)
            post_response = post_to_blogger(BLOGGER_BLOG_ID, video_title, blog_content, creds)
            #wix post_response = post_to_wix(video_title, blog_content)
            print(f'Blog post created for video: {video_title}')
            print(f'Post URL: {post_response.get("url", "N/A")}')
        
        #print(f'Post URL: {post_response["link"]}')

if __name__ == "__main__":
    main()

