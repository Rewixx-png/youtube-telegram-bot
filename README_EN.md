[Русская версия](README.md)

---
# YouTube Downloader Telegram Bot 🚀

This bot allows Telegram users to download videos from YouTube, bypassing the standard 50 MB file size limit of the Telegram Bot API. It utilizes a self-hosted Telegram Bot API server and the powerful `yt-dlp` library for maximum reliability and functionality.

## ✨ Features

- ✅ **Bypass 50 MB Limit:** Send video files up to 2 GB in size.
- ✅ **Quality Selection:** Offers all available video resolutions, including 1440p (2K) and 2160p (4K).
- ✅ **Automatic Merging:** Downloads video and audio streams separately and automatically merges them into a single MP4 file.
- ✅ **Video Thumbnails:** Displays the video thumbnail when selecting quality and attaches it to the final sent video file.
- ✅ **Interactive UI:** User-friendly inline keyboard with a two-column layout for quality selection.

---

## 🛠️ Installation and Setup

Running this bot requires setting up two components: the Python bot itself and the local Telegram Bot API server.

### Prerequisites

- A server running Linux (this guide is written for Ubuntu/Debian).
- Python 3.10 or higher.
- Git.

### Step 1: Clone the Repository

```bash
git clone https://github.com/YOUR_USERNAME/youtube-telegram-bot.git
cd youtube-telegram-bot
```

### Step 2: Set Up the Python Environment

Using a virtual environment is highly recommended.

```bash
# Create a virtual environment
python3 -m venv venv

# Activate it
source venv/bin/activate

# Install all required libraries
pip install -r requirements.txt
```

### Step 3: Configure Essential Files

In the project's root directory, create two files: `token.txt` and `cookies.txt`.

1.  **`token.txt`**:
    - Get a bot token from [@BotFather](https://t.me/BotFather) in Telegram.
    - Paste only the token string into the `token.txt` file.
    ```
    1234567890:ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghi
    ```

2.  **`cookies.txt`**:
    - This file is necessary for `yt-dlp` to bypass YouTube's "confirm you're not a bot" checks.
    - Install the [Cookie-Editor](https://chrome.google.com/webstore/detail/cookie-editor/hlkenndednhfkekhgcdicdfddnkalmdm) browser extension.
    - Go to `youtube.com` while logged into your Google account.
    - Click the extension's icon, select **Export** -> **Export as Netscape**, and copy the text.
    - Paste the copied text into the `cookies.txt` file.

### Step 4: Build the Local Telegram Bot API Server

This server is required to send files larger than 50 MB.

1.  **Install build dependencies:**
    ```bash
    sudo apt-get update && sudo apt-get install -y git cmake g++ zlib1g-dev libssl-dev gperf
    ```
2.  **Clone the server repository and build it (this may take 5-10 minutes):**
    ```bash
    git clone --recursive https://github.com/tdlib/telegram-bot-api.git
    cd telegram-bot-api
    mkdir build
    cd build
    cmake -DCMAKE_BUILD_TYPE=Release ..
    cmake --build . --target install
    ```
3.  **Obtain `api_id` and `api_hash`**:
    - Go to [my.telegram.org](https://my.telegram.org) -> "API development tools".
    - Create a new application and copy your `api_id` and `api_hash`.

---

## 🚀 Running the Bot

The system requires two processes to be running in two separate terminal windows.

### Terminal 1: Run the API Server

Navigate to the directory where you built the server and start it. **Do not close this terminal!**

```bash
# Navigate to the build directory
# Example: cd /path/to/project/telegram-bot-api/build/
cd /path/to/your/telegram-bot-api/build/

# Run the server, substituting your own api_id and api_hash
./telegram-bot-api --api-id=YOUR_API_ID --api-hash=YOUR_API_HASH --local --http-port=8081
```

### Terminal 2: Run the Bot

Navigate to the main project directory and run the Python script.

```bash
# Navigate to the bot's directory
# Example: cd /root/YT_Bot/
cd /path/to/your/youtube-telegram-bot/

# Activate the virtual environment if it's not already active
source venv/bin/activate

# Run the bot
python3 bot.py
```

Your bot is now fully operational!