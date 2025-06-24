# Auto Video Link Converter

by [zerosocialcode](https://github.com/zerosocialcode)

---

## 🚀 Features

- **Extracts direct video download links** from a single page or a batch of URLs (batch mode).
- **Supports a wide range of video websites** using [yt-dlp](https://github.com/yt-dlp/yt-dlp).
- **Mobile-friendly HTML result file** with clickable links and clear file names.
- **Batch mode:** Reads URLs from a file (`urls.txt` or any file you specify).
- **Automatically starts a local web server** for easy link clicking from your browser or phone.
- **Real-time progress bar** for extraction.
- **Smart error handling** and fallback logic for tricky sites.

---

## 🛠️ Requirements & Installation

All required packages are freely available and cross-platform.  
You can install them using pip in your favorite environment (Linux, macOS, Windows—even Termux on Android).

### Python Version

- **Python 3.7+** is required.

### Install Dependencies

Open a terminal and run:

```bash
pip install yt-dlp rich requests beautifulsoup4
```

If using **pip3** (on some Linux/macOS):

```bash
pip3 install yt-dlp rich requests beautifulsoup4
```

If you use **conda**:

```bash
conda install -c conda-forge yt-dlp rich requests beautifulsoup4
```

If you're on **Termux** (Android):

```bash
pkg install python
pip install yt-dlp rich requests beautifulsoup4
```

---

## ⚡ Usage

### Single Link Mode

Run the script:

```bash
python app.py
```

- Paste your video page link when prompted.
- Wait for extraction (progress bar will show).
- Links are shown in the terminal and saved to `video_links.html`.
- You will be asked if you want to host the file on `localhost` for easy clicking/downloading.

---

### Batch Mode

- Create a file called `urls.txt` (or any other name you prefer).
- Add one video page URL per line.
- Run the script and choose batch mode (`2`) when prompted.
- The script will process each link, extract video links, and group them by video title in `video_links.html`.

#### Example `urls.txt`

```
https://www.youtube.com/watch?v=xxxxxxx
https://vimeo.com/xxxxxxx
https://somesite.com/xxxxxxx
```

---

## 🌐 Viewing & Using Your Download Links

- After extraction, if you choose to host, the script starts a local web server (default port 8000+).
- You’ll get a link like `http://localhost:8000/video_links.html`.
- Open this in any browser (desktop, mobile, or any device on your network).
- Click the links to download the files directly.

---

## 📱 The HTML Output

- The HTML page is **responsive** and works on all devices.
- Each video section is grouped by its title.
- Only columns shown: Number, Resolution, Size, and a clickable file name (not the raw URL).

---

## 🛡️ Error Handling

- Handles invalid URLs, missing yt-dlp, missing dependencies, network errors, permission errors, and port conflicts.
- Attempts fallback extraction if yt-dlp can't extract formats.
- Prompts for authentication details/cookies if needed.

---

## 👑 Credits

- [yt-dlp](https://github.com/yt-dlp/yt-dlp) for powerful extraction
- [rich](https://github.com/Textualize/rich) for terminal UI
- [beautifulsoup4](https://www.crummy.com/software/BeautifulSoup/) for fallback scraping
- [zerosocialcode](https://github.com/zerosocialcode) for scripting and vision

---

Enjoy your new, streamlined video link extraction workflow!