# YouTube to Blogger Automated Posting

This project automates the process of fetching trending videos from YouTube, generating blog content using Google Generative AI, and posting the content to a Blogger blog. The specific video categories include Malayalam actor interviews, Bollywood interviews, fashion discussions, and music review podcasts.

## Prerequisites

1. **Python 3.6+**
2. **Required Libraries**:
   - `google-auth`
   - `google-auth-oauthlib`
   - `google-auth-httplib2`
   - `google-api-python-client`
   - `requests`
   - `google-generativeai`

   Install these libraries using pip:
   ```sh
   pip install google-auth google-auth-oauthlib google-auth-httplib2 google-api-python-client requests google-generativeai

API Keys:
YouTube API credentials (client_secret.json)
Google Generative AI credentials (genai_client_secret.json)
api_keys.txt file with the following content:
makefile
   
   ``GENAI_API_KEY=your_gen ai_api_key
   BLOGGER_BLOG_ID=your_blogger_blog_id`

## Setup
### Clone the repository:

  ``sh
  git clone https://github.com/your-repo/youtube-to-blogger.git
  cd youtube-to-blogger
###Prepare your api_keys.txt:
Ensure you have a file named api_keys.txt in the working directory with the following content:

makefile
  ``sh
  GENAI_API_KEY=your_genai_api_key
  BLOGGER_BLOG_ID=your_blogger_blog_id
###Place your API credentials:

Place client_secret.json (YouTube API credentials) in the working directory.
Place genai_client_secret.json (Google Generative AI credentials) in the working directory.
##Running the Script
Authenticate and run the script:

  ``sh
  python main.py
## The script will:

Authenticate with YouTube and Google Generative AI APIs.
Fetch trending videos based on the specified categories.
Generate blog content from the video descriptions.
Post the generated content to your Blogger blog with embedded YouTube videos using iframes.
## Script Details
API Authentication:

authenticate_youtube_api(): Authenticates with YouTube API.
authenticate_genai_api(): Authenticates with Google Generative AI API.
Fetch Videos:

get_videos_for_query(youtube, query, max_results): Fetches videos for a specific query.
get_trending_videos(youtube): Aggregates videos from specified categories.
Generate Blog Content:

create_blog_from_description(title, description, video_embed_url): Uses Generative AI to create blog content and embeds the video.
Post to Blogger:

post_to_blogger(blog_id, title, content, creds): Posts the generated content to Blogger as an HTML post.
## Contributing
Feel free to submit issues or pull requests if you have suggestions or improvements
