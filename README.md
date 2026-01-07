# Mediarr

**Unified artwork management for your media library**

Mediarr is a web application that manages backdrops, logos, and posters for your movie and TV show collection from a single, beautiful interface. No more juggling three separate tools - see all your artwork status at a glance and fill in the gaps with ease.

![Mediarr Interface](https://via.placeholder.com/800x400?text=Mediarr+Screenshot)

## Features

✨ **Unified Interface** - Manage backdrops, logos, and posters in one place
🎨 **Beautiful UI** - Modern, responsive design with dark theme
🔍 **Smart Matching** - Three-tier directory matching (UI hint → cached mapping → fuzzy match)
💾 **Persistent State** - Remembers TMDb artwork availability across container restarts
🖼️ **Auto Thumbnails** - Generates optimized thumbnails for fast loading
📁 **SMB-Safe** - Handles network mounts gracefully with retry logic
📊 **Stats Dashboard** - Track your artwork collection completeness
🔔 **Slack Notifications** - Get notified when artwork is downloaded
🎯 **Filtered Views** - Quickly find items missing specific artwork types

## Screenshots

### Unified Card View
Each media item shows all three artwork types in one card:
- **Backdrop** (16:9) - Full width at top
- **Logo** (transparent PNG) - Bottom left
- **Poster** (2:3) - Bottom right

Click any section to add or change that specific artwork type!

### Filter & Search
- Filter by missing artwork type (backdrops, logos, or posters)
- Search/filter by title
- See at a glance which items need attention

## Quick Start

### Docker Compose (Recommended)

1. **Create a `.env` file**:
```env
TMDB_API_KEY=your_tmdb_api_key_here
SLACK_WEBHOOK_URL=https://hooks.slack.com/services/YOUR/WEBHOOK/URL  # Optional
SECRET_KEY=change-this-to-a-random-secret-key
PUID=1000
PGID=1000
```

2. **Edit `docker-compose.yml`** - Update volume paths to match your media folders

3. **Run**:
```bash
docker-compose up -d
```

4. **Access**: http://localhost:5000

### Docker Run

```bash
docker run -d \
  --name=mediarr \
  -p 5000:5000 \
  -e TMDB_API_KEY=your_api_key \
  -e MOVIE_FOLDERS=/movies,/kids-movies \
  -e TV_FOLDERS=/tv,/kids-tv \
  -v /path/to/movies:/movies \
  -v /path/to/tv:/tv \
  -v ./data:/app/data \
  --user 1000:1000 \
  mediarr:latest
```

## Configuration

### Environment Variables

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `TMDB_API_KEY` | ✅ Yes | - | Your TMDb API key ([get one here](https://www.themoviedb.org/settings/api)) |
| `MOVIE_FOLDERS` | No | `/movies,/kids-movies,/anime` | Comma-separated list of movie folders |
| `TV_FOLDERS` | No | `/tv,/kids-tv` | Comma-separated list of TV show folders |
| `SLACK_WEBHOOK_URL` | No | - | Slack webhook for notifications |
| `PORT` | No | `5000` | Port to run the web server on |
| `SECRET_KEY` | No | (auto-generated) | Flask secret key for sessions |
| `PUID` | No | `1000` | User ID for file permissions |
| `PGID` | No | `1000` | Group ID for file permissions |

### Volume Mounts

- **Media folders**: Mount your movie and TV directories (read/write access needed)
- **Data folder**: `./data:/app/data` - Stores TMDb ID mappings and artwork availability

### Folder Structure

Mediarr expects your media to be organized like:
```
/movies/
  ├── The Matrix (1999)/
  │   ├── movie.mkv
  │   ├── backdrop.jpg          # Downloaded by Mediarr
  │   ├── backdrop-thumb.jpg    # Auto-generated thumbnail
  │   ├── logo.png              # Downloaded by Mediarr
  │   ├── logo-thumb.png        # Auto-generated thumbnail
  │   ├── poster.jpg            # Downloaded by Mediarr
  │   └── poster-thumb.jpg      # Auto-generated thumbnail
  └── Inception (2010)/
      └── ...

/tv/
  ├── Breaking Bad/
  │   ├── Season 01/
  │   ├── backdrop.jpg
  │   ├── logo.png
  │   └── poster.jpg
  └── ...
```

## How It Works

### Three-Tier Directory Matching

Mediarr uses a smart three-tier strategy to match TMDb results to your local directories:

1. **UI Hint** (Highest Priority) - When you click a card, the directory name is passed through the entire flow
2. **Cached Mapping** - Previously saved TMDb ID → directory mappings from `/app/data/tmdb_directory_mapping.json`
3. **Fuzzy Matching** (Fallback) - Normalized title matching with 90% similarity threshold

This prevents the "backdrop overwriting" bug and ensures artwork always goes to the correct folder.

### Artwork Availability Tracking

Mediarr remembers when TMDb doesn't have a specific artwork type:

```json
{
  "movie_603": {
    "directory": "/movies/The Matrix (1999)",
    "last_checked": "2026-01-05",
    "artwork_availability": {
      "backdrop": true,
      "logo": true,
      "poster": false  // ← No posters available on TMDb
    }
  }
}
```

This prevents repeated unsuccessful searches and survives container restarts.

### SMB Mount Support

Mediarr includes retry logic with exponential backoff for:
- Directory listing (`safe_listdir`)
- File serving (`safe_send_file`)

This handles `BlockingIOError` exceptions common with SMB/NFS mounts.

## Migrating from Separate Tools

If you're currently running backgroundarr, logoarr, and postarr separately:

1. **Stop all three containers**
```bash
docker stop backgroundarr logoarr postarr
```

2. **Backup existing mappings** (optional, logoarr only)
```bash
cp /path/to/logoarr/tmdb_directory_mapping.json ~/logoarr-mapping-backup.json
```

3. **Deploy Mediarr** with the same volume mounts

4. **First run**: Mediarr will scan all existing artwork automatically

5. **Verify**: Check that all your existing artwork shows up correctly

6. **Remove old containers** once satisfied
```bash
docker rm backgroundarr logoarr postarr
```

**Note**: All your existing artwork files (`backdrop.jpg`, `logo.png`, `poster.jpg`) stay in place - no data loss!

## API Endpoints

Mediarr provides a RESTful-ish interface:

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/` | GET | Movies page with unified cards |
| `/tv` | GET | TV shows page with unified cards |
| `/dashboard` | GET | Statistics dashboard |
| `/search_movie?query=...&artwork_type=...` | GET | Search TMDb for movies |
| `/search_tv?query=...&artwork_type=...` | GET | Search TMDb for TV shows |
| `/select/<media_type>/<tmdb_id>?artwork_type=...` | GET | View available artwork |
| `/download_artwork` | POST | Download and save artwork |
| `/artwork/<path>` | GET | Serve artwork files |
| `/recheck/<media_type>/<tmdb_id>/<artwork_type>` | GET | Force recheck TMDb availability |

## Development

### Local Development

```bash
# Clone the repo
git clone https://github.com/anthonysnyder/Mediarr.git
cd Mediarr

# Create virtual environment
python -m venv venv
source venv/bin/activate  # or `venv\Scripts\activate` on Windows

# Install dependencies
pip install -r requirements.txt

# Set environment variables
export TMDB_API_KEY=your_key_here
export MOVIE_FOLDERS=/path/to/movies
export TV_FOLDERS=/path/to/tv

# Run
python app.py
```

### Project Structure

```
mediarr/
├── app.py                 # Main Flask application
├── requirements.txt
├── Dockerfile
├── docker-compose.yml
│
├── services/              # Business logic
│   ├── artwork_service.py    # Artwork operations
│   ├── tmdb_service.py       # TMDb API client
│   └── slack_service.py      # Slack notifications
│
├── utils/                 # Utilities
│   ├── file_utils.py         # SMB-safe file operations
│   ├── image_utils.py        # Thumbnail generation
│   └── mapping_utils.py      # TMDb ID mappings
│
├── templates/             # Jinja2 templates
│   ├── base.html
│   ├── index.html            # Movies page
│   ├── tv.html               # TV shows page
│   ├── dashboard.html
│   ├── search_results.html
│   ├── artwork_selection.html
│   └── error.html
│
├── static/
│   └── css/
│       └── style.css         # Main stylesheet
│
└── data/
    └── tmdb_directory_mapping.json  # Persistent mappings
```

## Troubleshooting

### Artwork not downloading

1. **Check logs**: `docker logs mediarr`
2. **Verify TMDb API key**: Make sure it's valid and has permissions
3. **Check permissions**: Ensure PUID/PGID have write access to media folders
4. **Network issues**: Test TMDb connectivity from container

### Directory matching issues

1. **Check directory names**: Must match TMDb titles reasonably well
2. **Use UI hint**: Click the card directly instead of searching
3. **Manual selection**: If fuzzy matching fails, you'll see a directory picker
4. **Check mapping file**: `cat data/tmdb_directory_mapping.json`

### SMB mount issues

1. **Increase retries**: Mediarr retries 8 times with exponential backoff
2. **Check mount health**: `ls -la /path/to/mount` from container
3. **Review logs**: Look for `BlockingIOError` messages

## Credits

- **TMDb**: Artwork metadata from [The Movie Database](https://www.themoviedb.org/)
- **Flask**: Python web framework
- **Pillow**: Image processing
- **Bootstrap**: UI framework

## License

MIT License - See LICENSE file for details

## Support

- **Issues**: [GitHub Issues](https://github.com/anthonysnyder/Mediarr/issues)
- **Discussions**: [GitHub Discussions](https://github.com/anthonysnyder/Mediarr/discussions)

---

Made with ❤️ for the *arr community
