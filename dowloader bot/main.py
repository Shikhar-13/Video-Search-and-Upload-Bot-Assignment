import asyncio
import os
import logging
import instaloader
import requests
from typing import List, Optional
import hashlib

from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager


# Configure logging
logging.basicConfig(
    level=logging.INFO, 
    format='%(asctime)s - %(levelname)s: %(message)s'
)
logger = logging.getLogger(__name__)

class VideoDownloader:
    def __init__(self, social_media: str, download_path: str = 'downloads'):
        """
        Initialize video downloader with Chrome WebDriver and Instaloader
        
        :param social_media: Social media platform
        :param download_path: Directory to save downloaded videos
        """
        self.download_path = download_path
        os.makedirs(self.download_path, exist_ok=True)
        
        # Chrome WebDriver setup with advanced options
        chrome_options = Options()
        chrome_options.add_argument("--headless")
        chrome_options.add_argument("--start-maximized")
        chrome_options.add_argument("--disable-extensions")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        
        # Use WebDriverManager to automatically manage ChromeDriver
        service = Service(ChromeDriverManager().install())
        
        self.driver = webdriver.Chrome(service=service, options=chrome_options)
        
        # Initialize Instaloader
        self.L = instaloader.Instaloader(
             download_videos=True,
            download_video_thumbnails=False,
            download_geotags=False,
            download_comments=False,
            download_pictures=False,
            save_metadata=False,
            compress_json=False,
            dirname_pattern=download_path
        )
        self.L.quiet = True 

    async def find_video_links(self, keyword: str, max_videos: int = 10) -> List[str]:
        """
        Find Instagram video links using Google search
        
        :param keyword: Search keyword
        :param max_videos: Maximum number of videos to find
        :return: List of video links
        """
        try:
            self.driver.get('https://google.com')
            
            # Wait for search bar
            search_bar = WebDriverWait(self.driver, 10).until(
                EC.element_to_be_clickable((By.NAME, "q"))
            )
            
            # Construct search query
            search_query = f"site:instagram.com {keyword} reel"
            search_bar.clear()
            search_bar.send_keys(search_query)
            
            # Submit search
            search_bar.send_keys(Keys.RETURN)
            
            # Wait for search results
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_all_elements_located((By.XPATH, "//div[@class='MjjYud']//a"))
            )
            
            # Find result links
            result_links = self.driver.find_elements(By.XPATH, "//div[@class='MjjYud']//a")
            
            # Filter Instagram Reel links
            reel_links = []
            for link in result_links:
                try:
                    href = link.get_attribute('href')
                    if href and '/reel/' in href:
                        reel_links.append(href)
                        
                        # Stop if max videos reached
                        if len(reel_links) >= max_videos:
                            break
                except Exception as link_error:
                    logger.warning(f"Error processing link: {link_error}")
            
            logger.info(f"Found {len(reel_links)} Reel links")
            return reel_links
        
        except Exception as e:
            logger.error(f"Search failed: {e}")
            return []

    async def download_video(self, video_url: str, index: int) -> Optional[str]:
        """
        Download video from Instagram link using Instaloader
        
        :param video_url: URL of the Instagram video
        :param index: Index of the video for naming
        :return: Path to downloaded video or None
        """
        try:
            # Extract shortcode from URL
            shortcode = video_url.split('/')[-2] if '/reel/' in video_url else None
            
            if not shortcode:
                logger.warning(f"Invalid video URL: {video_url}")
                return None
            
            # Sanitize filename
            sanitized_filename = f"instagram_video_{index}_{shortcode}.mp4"
            full_path = os.path.join(self.download_path, sanitized_filename)
            
            # Attempt to download using Instaloader
            try:
                # Get post by shortcode
                post = instaloader.Post.from_shortcode(self.L.context, shortcode)
                
                # Download the post
                self.L.download_post(post, target=self.download_path)
                
                # Find the video file
                for filename in os.listdir(self.download_path):
                    if filename.endswith('.mp4'):
                        original_path = os.path.join(self.download_path, filename)
                        os.rename(original_path, full_path)
                        break
            except Exception as download_error:
                logger.error(f"Instaloader download failed: {download_error}")
                return None
            
            # Verify download
            if os.path.exists(full_path) and os.path.getsize(full_path) > 0:
                logger.info(f"Successfully downloaded video: {full_path}")
                return full_path
            
            return None
        
        except Exception as e:
            logger.error(f"Error downloading video {video_url}: {e}")
            return None

    async def download_videos(self, keyword: str, max_videos: int = 10) -> List[str]:
        """
        Download multiple videos for a given keyword
        
        :param keyword: Search keyword
        :param max_videos: Maximum number of videos to download
        :return: List of downloaded video paths
        """
        # Find video links
        video_links = await self.find_video_links(keyword, max_videos)
        
        # Download videos concurrently
        download_tasks = [
            self.download_video(link, index) 
            for index, link in enumerate(video_links, 1)
        ]
        
        # Wait for all downloads to complete
        downloaded_videos = await asyncio.gather(*download_tasks)
        
        # Remove None values (failed downloads)
        downloaded_videos = [v for v in downloaded_videos if v]
        
        return downloaded_videos
    
    def close(self):
        """
        Close the browser and end WebDriver session
        """
        if self.driver:
            self.driver.quit()

class VideoUploader:
    def __init__(self, flic_token: str):
        """
        Initialize VideoUploader with Flic Token
        
        :param flic_token: Authentication token for SocialVerse API
        """
        self.flic_token = flic_token
        self.base_url = "https://api.socialverseapp.com"
        
        # Configure logging
        logging.basicConfig(
            level=logging.INFO, 
            format='%(asctime)s - %(levelname)s: %(message)s'
        )
        self.logger = logging.getLogger(__name__)

    def generate_file_hash(self, file_path: str) -> str:
        """
        Generate SHA-256 hash for the file
        
        :param file_path: Path to the video file
        :return: File hash
        """
        sha256_hash = hashlib.sha256()
        with open(file_path, "rb") as f:
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)
        return sha256_hash.hexdigest()

    def get_upload_url(self, file_path: str) -> dict:
        """
        Get pre-signed upload URL from SocialVerse API
        
        :param file_path: Path to the video file to upload
        :return: Dictionary with upload URL and hash
        """
        try:
            # Generate file hash
            file_hash = self.generate_file_hash(file_path)
            file_size = os.path.getsize(file_path)  # Get the file size
            url =f"{self.base_url}/posts/generate-upload-url"
            # Prepare headers
            headers = {
                "Flic-Token": self.flic_token,
                "Content-Type": "application/json"
            }
            
            # Prepare request payload
            payload = {
                "hash": file_hash,
                "file_size": file_size
            }
            
            # Send request to get upload URL
            response = requests.get(
                url, 
                json=payload,
                headers=headers, 
                
            )
            
            # Check response
            response.raise_for_status()
            upload_data = response.json()
            print(response.json())

            
            self.logger.info(f"Upload URL generated for file: {file_path}")
            return {
                "upload_url": upload_data.get("url"),  # Corrected key
                "hash": upload_data.get("hash")
            }
        
        except requests.RequestException as e:
            self.logger.error(f"Error getting upload URL: {e}")
            if e.response:
                self.logger.error(f"Response content: {e.response.text}")  # Log response content for debugging
            raise

    def upload_video(self, file_path: str, upload_url: str) -> bool:
        """
        Upload video to pre-signed URL
        
        :param file_path: Path to the video file
        :param upload_url: Pre-signed URL for uploading
        :return: Boolean indicating upload success
        """
        try:
            with open(file_path, 'rb') as file:
                # Upload using PUT request
                response = requests.put(
                    upload_url, 
                    data=file, 
                    headers={'Content-Type': 'application/octet-stream'}
                )
            
            response.raise_for_status()
            self.logger.info(f"Successfully uploaded video: {file_path}")
            return True
        
        except requests.RequestException as e:
            self.logger.error(f"Error uploading video: {e}")
            if e.response:
                self.logger.error(f"Response content: {e.response.text}")  # Log response content for debugging
            return False

    def create_post(self, file_hash: str, title: str, category_id: int) -> dict:
        """
        Create a post on SocialVerse after video upload
        
        :param file_hash: Hash of the uploaded file
        :param title: Title of the post
        :param category_id: Category ID for the post
        :param is_public: Whether the post is visible in public feed
        :return: Post creation response
        """
        try:
            
            # Prepare headers
            url=f"{self.base_url}/posts"
            headers = {
                "Flic-Token": self.flic_token,
                "Content-Type": "application/json"
            }
            
            # Prepare payload
            payload = {
                "title": title,
                "hash": file_hash,
                "is_available_in_public_feed": False,
                "category_id": category_id
            }
            
            # Send post creation request
            response = requests.post(
                url, 
                headers=headers, 
                json=payload,
            )
            self.logger.info(f"Creating post with payload: {payload}")
            # Check response
            response.raise_for_status()
            post_data = response.json()
            
            
            self.logger.info(f"Post created successfully: {post_data.get('id')}")
            return post_data
        
        except requests.RequestException as e:
            self.logger.error(f"Error creating post: {e}")
            if e.response is not None:
                self.logger.error(f"Response content: {e.response.text}")  # Log the response content for more details
        
            raise

    async def upload_video_to_socialverse(self, file_path: str, title: str, category_id: int) -> dict:
        """
        Comprehensive method to upload video and create post
        
        :param file_path: Path to the video file
        :param title: Title of the post
        :param category_id: Category ID for the post
        :param is_public: Whether the post is visible in public feed
        :return: Post creation response
        """
        try:
            # Get upload URL
            upload_info = self.get_upload_url(file_path)
            
            # Upload video
            upload_success = self.upload_video(file_path, upload_info['upload_url'])
            
            if not upload_success:
                raise ValueError("Video upload failed")
            
            # Create post
            post_data = self.create_post(
                upload_info['hash'], 
                title, 
                category_id, 
                
            )
            
            return post_data
        
        except Exception as e:
            self.logger.error(f"Complete upload process failed: {e}")
            if e.response is not None:
                self.logger.error(f"Response content: {e.response.text}")  # Log the response content for more details
        
            raise 

async def main():
    SOCIAL_MEDIA = 'instagram.com'
    SEARCH_KEYWORD = input("Enter keyword: ")
    MAX_VIDEOS = 5  # Number of videos to download
    
    # Create downloader instance
    downloader = VideoDownloader(
        SOCIAL_MEDIA,
        download_path='instagram_videos'
    )
    
    downloaded_files = []  # Initialize an empty list to store downloaded files
    
    try:
        # Add retry mechanism
        max_retries = 3
        for attempt in range(max_retries):
            try:
                downloaded_files = await downloader.download_videos(
                    SEARCH_KEYWORD, 
                    MAX_VIDEOS
                )
                
                if downloaded_files:
                    logger.info("\nDownloaded Videos:")
                    for video in downloaded_files:
                        logger.info(video)
                    break
                else:
                    logger.warning(f"No videos downloaded on attempt {attempt + 1}")
            
            except Exception as retry_error:
                logger.error(f"Retry attempt {attempt + 1} failed: {retry_error}")
                await asyncio.sleep(3)
    
    except Exception as e:
        logger.error(f"An error occurred: {e}")
    
    finally:
        # Always close the browser
        downloader.close()

    # Ensure that downloaded_files is not empty before proceeding to upload
    if downloaded_files:
        uploader = VideoUploader(flic_token="flic_16a53d750040604a11c71ae66b138ee44b85929c51fa21abe26db4167627552b"
)
        
        try:
            # Upload each downloaded video
            for video_path in downloaded_files:
                # Upload each downloaded video
                post_response = await uploader.upload_video_to_socialverse(
                    file_path=video_path,
                    title=f"Instagram Reel: {SEARCH_KEYWORD}",
                    category_id=25,  # Replace with actual category IDcake
                )
                os.remove(video_path) 
                print(f"Video uploaded. Post ID: {post_response.get('id')}")
        
        except Exception as e:
            logger.error(f"Upload failed: {e}")
    else:
        logger.warning("No videos were downloaded, skipping upload.")

# Run the async main functionj
if __name__ == "__main__":
    asyncio.run(main())