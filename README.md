# Mediarr

**Mediarr** is a unified Flask application designed to organize, manage, and download high-quality **posters**, **logos**, and **backdrops** for movies and TV shows. It provides an intuitive interface to manage all your media artwork in one place, with intelligent tracking of what's available, what's missing, and what's unavailable on TMDb.

Originally built as "Backgroundarr" for managing backdrops in advance of [Plex releasing their next version](https://www.plex.tv/blog/new-year-same-mission/) which highlights backdrop images more prominently, Mediarr has evolved into a comprehensive artwork management solution.

## Key Features

- **Unified Artwork Management**: Handle posters, logos, and backdrops in a single interface with tabbed navigation
- **Three-State Status Tracking**:
  - Green: Artwork found and saved
  - Yellow: Artwork missing (click to mark as unavailable)
  - Red: Artwork marked as unavailable on TMDb (click to reset)
- **Smart Unavailability Tracking**: Persist artwork availability status across sessions and container restarts
- **Auto-Mark Unavailable**: When TMDb returns zero results for an artwork search, the item is automatically marked as unavailable and you're redirected back to the missing view
- **Acknowledged Missing View**: Dedicated filter to view items you've previously marked as unavailable, with the ability to reset them for re-searching
- **SMB/NAS Optimized Scanning**:
  - Adaptive SMB throttling with health tracking and escalating backoff (5s-30s)
  - Lightweight scan mode (listdir only, no file reads over SMB)
  - Batched directory scanning (10 dirs per batch, 2s pause) to prevent mount lockups
  - Hidden file filtering (.DS_Store, .smbdelete* files) to avoid ENOTDIR errors
- **Zero-SMB Cache Derivation**: Switching between poster/logo/backdrop tabs derives the new cache from the existing scan with zero SMB calls, using `has_poster`/`has_logo`/`has_backdrop` flags
- **Background Thumbnail Caching**: After cache derivation, thumbnails are gently copied from SMB in a background thread (one file per 0.5s) without blocking page loads
- **Async Background Scanning**: Initial scans run in a background thread with a real-time progress page (auto-polling every 2s)
- **Scan Lock**: Prevents duplicate concurrent scans from overwhelming SMB mounts
- **Incremental Cache Refresh**: Only scans new/removed directories instead of rescanning everything
- **Progress Bars**: Visual completion percentage for each artwork type
- **Advanced Filtering**: Filter by missing artwork and minimum dimensions
- **Click-to-Download**: Select artwork and download immediately
- **Quality Indicators**: See at a glance if artwork is high, medium, or low quality
- **Language Filtering**: Filter posters by language when selecting
- **Slack Notifications**: Get notified when artwork is downloaded
- **Auto-Generated Thumbnails**: Fast-loading preview images cached locally

## Quick Start with Docker

### 1. Create docker-compose.yml

```yaml
version: '3.8'

services:
  mediarr:
    image: swguru2004/mediarr:latest
    container_name: mediarr
    ports:
      - "6789:6789"
    environment:
      - TMDB_API_KEY=your_tmdb_api_key_here
      - MOVIE_FOLDERS=/movies
      - TV_FOLDERS=/tv
      - SLACK_WEBHOOK_URL=  # Optional
    volumes:
      # Mount your media directories
      - /path/to/your/movies:/movies
      - /path/to/your/tv:/tv
      # Persistent storage for cache and tracking data
      - ./mediarr-data:/app/data
    restart: unless-stopped
```

### 2. Create .env file

```bash
TMDB_API_KEY=your_tmdb_api_key_here
MOVIE_FOLDERS=/movies,/movies2
TV_FOLDERS=/tv,/tv2
SLACK_WEBHOOK_URL=https://hooks.slack.com/services/YOUR/WEBHOOK/URL
```

### 3. Start the application

```bash
docker-compose up -d
```

### 4. Access the interface

Open your browser to `http://localhost:6789`

## Requirements

- **TMDb API Key**: [Get one here](https://www.themoviedb.org/settings/api) (free)
- **Media Library**: Movies/TV shows organized in directories
- **Docker** (recommended) or Python 3.12+

## How It Works

### Artwork Status Indicators

Each media item shows three emoji indicators:
- Poster status
- Logo status
- Backdrop status

Color coding:
- **Green**: Artwork exists on disk
- **Yellow**: Artwork is missing - click to acknowledge as unavailable, or click the search button to find it on TMDb
- **Red**: Artwork has been marked as unavailable - click to reset back to missing

### Workflow

1. **Initial scan**: On first visit, Mediarr scans your media directories in the background with a real-time progress page
2. **Cache persistence**: Scan results are cached to `/app/data` and persist across container restarts
3. **Tab switching**: Switching from posters to backdrops or logos derives the cache instantly with zero SMB calls
4. **Background thumbnails**: Missing thumbnails are fetched from SMB in a gentle background thread
5. **See what's missing**: Click "Show Missing" to filter to items without artwork
6. **Search and download**: Click search buttons to find artwork on TMDb and download it
7. **Auto-mark unavailable**: If TMDb has no results, the item is automatically marked and you're returned to the missing view
8. **Manual acknowledge**: Click yellow indicators to manually mark artwork as unavailable
9. **Review acknowledged**: Click "Show Acknowledged Missing" to see items you've marked, with the option to reset them
10. **Incremental refresh**: The "Refresh Cache" button only checks for new/removed directories

### Scanning Architecture

Mediarr uses a multi-layered approach to minimize SMB stress:

```
First visit to posters tab:
  -> No cache exists
  -> Background scan with throttling (10 dirs/batch, 2s pause)
  -> Progress page with auto-polling
  -> Cache saved to disk

Switch to backdrops tab:
  -> No backdrop cache exists
  -> Derive from poster cache (zero SMB calls, instant)
  -> Background thread starts caching thumbnails (0.5s/file)
  -> Page loads immediately with "Loading thumbnail..." placeholders

Subsequent visits:
  -> Load from disk cache (instant)
  -> No SMB calls needed
```

### File Structure in Your Media Folders

Mediarr creates the following files in each media directory:

```
Movie Name (2014) {tmdb-12345}/
  poster.jpg          # Full poster image
  poster-thumb.jpg    # Thumbnail (300x450)
  logo.png            # Full logo (transparent PNG)
  logo-thumb.png      # Logo thumbnail (300x150)
  backdrop.jpg        # Full backdrop image
  backdrop-thumb.jpg  # Backdrop thumbnail (300x169)
```

## Configuration

### Environment Variables

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `TMDB_API_KEY` | Yes | - | Your TMDb API key |
| `MOVIE_FOLDERS` | Yes | - | Comma-separated movie directory paths |
| `TV_FOLDERS` | Yes | - | Comma-separated TV directory paths |
| `SLACK_WEBHOOK_URL` | No | - | Slack webhook for download notifications |

### Persistent Data

Mount `/app/data` as a volume to persist across container restarts:

- `artwork_cache/` - Scan caches and artwork thumbnails
- `unavailable_artwork.json` - Tracks which artwork is unavailable on TMDb
- `tmdb_directory_mapping.json` - Maps TMDb IDs to local directories

## Pro Tips

### Selecting Good Artwork

When selecting artwork, especially backdrops for Plex:

**Good Choices:**
- No text overlays (movie details will cover them)
- Main subject positioned on the right side
- High resolution (2000px+ width)
- No language-specific text for international compatibility

**Avoid:**
- Text that will be obscured by UI elements
- Low resolution images (<1000px)
- Centered composition (gets covered by metadata)

### Managing Missing Artwork Efficiently

1. Click "Show Missing Logos" to see only items without logos
2. Click the search button on each item to check TMDb
3. If TMDb has 0 results, the app auto-marks it as unavailable and returns you to the missing list
4. If TMDb has results, download the one you want
5. Use "Show Acknowledged Missing" later to review items you've marked, and reset any you want to re-check

### SMB/NAS Performance

For best results with network-mounted media directories:
- Avoid accessing the media server while the initial scan is running
- The first scan is the slowest; subsequent visits load from cache
- Switching tabs (poster to backdrop) requires zero SMB calls
- The "Refresh Cache" button only checks for new/removed directories (lightweight)
- If SMB errors occur, the app automatically backs off and retries

## Building from Source

```bash
# Clone the repository
git clone https://github.com/anthonysnyder/Mediarr.git
cd Mediarr

# Build the Docker image
docker build -t mediarr .

# Multi-arch build and push
docker buildx build --platform linux/amd64,linux/arm64 -t swguru2004/mediarr:latest --push .

# Or run locally with Python
pip install -r requirements.txt
python app.py
```

## Project Structure

```
mediarr/
  app.py                       # Main Flask application
  templates/
    collection.html            # Main unified collection view
    artwork_selection.html     # Artwork selection grid
    search_results.html        # TMDb search results
    scan_progress.html         # Background scan progress page
  data/
    artwork_cache/             # Scan caches and thumbnails
    unavailable_artwork.json   # Unavailability tracking
    tmdb_directory_mapping.json # TMDb ID mappings
  requirements.txt             # Python dependencies
  Dockerfile                   # Docker build configuration
  docker-compose.yml           # Docker Compose setup
  README.md                    # This file
```

## Migration from Backgroundarr

If you're upgrading from Backgroundarr:

1. Your existing backdrop files are **fully compatible**
2. Mediarr will detect and display them automatically
3. You can now add posters and logos to the same folders
4. All your backdrop-thumb files will continue to work

No migration needed - it's a drop-in replacement!

## Troubleshooting

### SMB/NAS Mount Issues

Mediarr includes adaptive SMB throttling with health tracking. If you see `BlockingIOError` or `EAGAIN` errors, the app will automatically:
- Track consecutive SMB errors
- Apply escalating backoff (5s, 10s, 15s, up to 30s)
- Resume scanning once the mount recovers
- Filter out problematic hidden files (.DS_Store, .smbdelete*) that cause false errors

### Scan Stalling or Duplicate Scans

- A scan lock prevents multiple concurrent scans from running
- If a scan appears stuck, restart the container - the cache will persist from where it left off
- The progress page auto-polls every 2 seconds and redirects when complete

### Artwork Not Showing

1. Check that TMDb ID is in directory name: `Movie (2014) {tmdb-12345}`
2. Verify artwork files exist: `poster.jpg`, `logo.png`, `backdrop.jpg`
3. Check file permissions (should be readable by container user)
4. Try "Refresh Cache" to pick up newly added files

### Thumbnails Show "Loading thumbnail..."

This means the artwork exists on disk but the thumbnail hasn't been cached locally yet. A background thread is copying thumbnails from your media server. Refresh the page periodically and they will fill in.

## Contributing

Contributions are welcome! Please:
1. Fork the repository
2. Create a feature branch
3. Submit a pull request

## License

This project is licensed under the MIT License. See the `LICENSE` file for details.

## Acknowledgments

- **TMDb** for providing the excellent free API
- **Plex** for inspiring this project
- All contributors and users who provide feedback

---

**Note**: This application requires a free TMDb API key. Mediarr is not affiliated with or endorsed by TMDb or Plex.
