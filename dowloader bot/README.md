Instagram Video Downloader and Uploader

Overview
This project allows you to download Instagram Reels videos based on a search keyword and upload them to the SocialVerse platform. It leverages Selenium WebDriver for browser automation, Instaloader for Instagram video download, and the SocialVerse API for video upload.

Features
Search and Download Instagram Reels Videos: Allows users to search Instagram videos based on a keyword and download them.
Upload to SocialVerse: Automatically uploads the downloaded videos to SocialVerse using an API token.
Customizable: You can modify search terms, video limits, and upload categories to fit your needs.
Prerequisites
Before you start, ensure you have the following:

Python 3.7+: Download Python
Google Chrome: Download Chrome
SocialVerse Flic Token: Obtain a valid token from the SocialVerse platform for video upload.
Installation Guide
Step 1: Clone the Repository
If you haven’t already cloned the repository, you can do so with the following command:

bash
Copy code
git clone <repository-url>
cd <repository-directory>
Step 2: Set Up a Virtual Environment
Create and activate a virtual environment to isolate your project dependencies.

On Windows:

bash
Copy code
python -m venv venv
.\venv\Scripts\activate
On macOS/Linux:

bash
Copy code
python3 -m venv venv
source venv/bin/activate
Step 3: Install Dependencies
Install the necessary Python libraries by running the following command:

bash
Copy code
pip install -r requirements.txt
If requirements.txt is unavailable, install dependencies manually:

bash
Copy code
pip install selenium instaloader requests webdriver-manager
Step 4: Install Google Chrome and WebDriver
Ensure Google Chrome is installed on your machine.

WebDriver Installation:
The script uses webdriver-manager to automatically download the correct version of Chrome WebDriver, so manual installation is not required. However, ensure that your Chrome version is up-to-date for compatibility.

Configuration
Step 1: Set Up SocialVerse Flic Token
You need a Flic Token to authenticate video uploads to SocialVerse.

Obtain your Flic Token from the SocialVerse platform or API.
Store your token securely.
You can either:

Use an environment variable:

On Windows:

bash
Copy code
set FLIC_TOKEN=your_token_here
On macOS/Linux:

bash
Copy code
export FLIC_TOKEN=your_token_here
Hardcode the token in the script (not recommended for production):

python
Copy code
uploader = VideoUploader(flic_token="your_token_here")
Usage
Step 1: Run the Script
Execute the script using Python:

bash
Copy code
python script_name.py
Step 2: Input Search Keyword
The script will prompt you to enter a search keyword for Instagram Reels.

mathematica
Copy code
Enter keyword: funny cats
Once you input the keyword, the script will:

Search for Instagram Reels based on the keyword.
Download up to 5 videos (default behavior, can be modified).
Upload the videos to the SocialVerse platform.
Customization
You can customize several parameters:

Number of Videos to Download: Modify the MAX_VIDEOS constant in the script to change how many videos are downloaded.
Upload Category: Modify the category_id to specify which category the videos are uploaded under on SocialVerse.
Video Source: Change the search source from Google if you need to download videos from another platform.
Troubleshooting
WebDriver Not Found:
Ensure Google Chrome is installed and WebDriver Manager is configured correctly.
No Videos Downloaded:
Check if the search keyword is valid and returns results with Instagram Reels links.
Upload Failures:
Verify the Flic Token has proper upload permissions.
Ensure that videos are downloaded correctly before attempting to upload them.
License
This project is licensed under the MIT License - see the LICENSE file for details.

Acknowledgements
Selenium: For automating the browser interactions.
Instaloader: For downloading Instagram content.
SocialVerse: For providing the API for video uploads.
Contact
For issues, feature requests, or contributions, please feel free to open an issue or submit a pull request.
