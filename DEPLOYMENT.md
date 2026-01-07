# Mediarr Deployment Guide

## Pre-Deployment Checklist

Before deploying Mediarr, make sure you have:

- [ ] TMDb API key ([get one here](https://www.themoviedb.org/settings/api))
- [ ] Docker and Docker Compose installed
- [ ] Media folders organized (one directory per movie/show)
- [ ] Write permissions to media folders

## Quick Deployment

### Step 1: Configure Environment

Copy the example environment file:

```bash
cp .env.example .env
```

Edit `.env` and fill in your values:

```env
TMDB_API_KEY=your_actual_api_key_here
SLACK_WEBHOOK_URL=https://hooks.slack.com/your/webhook  # Optional
SECRET_KEY=generate-a-random-secret-string
PUID=1000  # Your user ID (run `id -u`)
PGID=1000  # Your group ID (run `id -g`)
```

### Step 2: Update Volume Mounts

Edit `docker-compose.yml` and update the volume paths to match your media folders:

```yaml
volumes:
  - /your/actual/path/to/movies:/movies
  - /your/actual/path/to/kids-movies:/kids-movies
  - /your/actual/path/to/tv:/tv
  - /your/actual/path/to/kids-tv:/kids-tv
  - ./data:/app/data  # Keep this as-is
```

### Step 3: Build and Run

```bash
# Build the image
docker-compose build

# Start the container
docker-compose up -d

# Check logs
docker-compose logs -f mediarr
```

### Step 4: Access the Interface

Open your browser to: **http://localhost:5000**

You should see your movies and TV shows with their current artwork status!

## Testing the Deployment

1. **Verify Scanning**: Check that your movies/TV shows appear on the main page
2. **Test Search**: Click a card without artwork → search TMDb
3. **Download Artwork**: Select an image and download it
4. **Check Files**: Verify artwork files were created in the media directory
5. **Refresh**: Click refresh button to verify changes appear

## Common Deployment Scenarios

### Scenario 1: Unraid

1. Add Mediarr via Community Applications (once published)
2. Or use Docker Compose mode in Unraid
3. Map your media share paths
4. Set PUID/PGID to match your Unraid user

### Scenario 2: Synology NAS

```bash
# SSH into your Synology
cd /volume1/docker/mediarr
docker-compose up -d
```

**Note**: Synology uses SMB mounts internally - Mediarr's retry logic will handle this!

### Scenario 3: Standard Linux Server

```bash
sudo docker-compose up -d
```

### Scenario 4: macOS Development

```bash
# Using native Docker Desktop
docker-compose up -d

# Or run locally without Docker
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
export TMDB_API_KEY=your_key
python app.py
```

## Migrating from backgroundarr/logoarr/postarr

### Migration Steps

1. **Document current setup**:
   ```bash
   docker ps | grep -E "(background|logo|poster)arr"
   docker inspect backgroundarr | grep -A 20 Mounts
   ```

2. **Stop existing containers**:
   ```bash
   docker stop backgroundarr logoarr postarr
   ```

3. **Backup mapping file** (if using logoarr):
   ```bash
   docker cp logoarr:/app/tmdb_directory_mapping.json ~/logoarr-backup.json
   ```

4. **Deploy Mediarr** with same volume mounts as before

5. **Verify artwork** appears correctly in Mediarr

6. **Remove old containers**:
   ```bash
   docker rm backgroundarr logoarr postarr
   docker rmi backgroundarr logoarr postarr
   ```

### What Happens to Your Artwork?

**Nothing!** All your existing artwork files stay exactly where they are:
- `backdrop.jpg` / `backdrop-thumb.jpg`
- `logo.png` / `logo-thumb.png`
- `poster.jpg` / `poster-thumb.jpg`

Mediarr will detect them automatically on first scan.

## Updating Mediarr

### Update Process

```bash
# Pull latest changes
cd /path/to/mediarr
git pull

# Rebuild and restart
docker-compose down
docker-compose build
docker-compose up -d

# Check logs
docker-compose logs -f
```

### Data Preservation

The `./data` volume persists your TMDb mappings across updates:
- `tmdb_directory_mapping.json` - Remembers which TMDb IDs go to which directories

This is preserved even when you rebuild the container!

## Production Recommendations

### Security

1. **Change SECRET_KEY**: Generate a random string
   ```bash
   python -c "import secrets; print(secrets.token_hex(32))"
   ```

2. **Use HTTPS**: Put MediaArr behind a reverse proxy (nginx, Caddy, Traefik)

3. **Limit Access**: Use firewall rules or proxy authentication

### Performance

1. **Fast Storage**: Put `./data` on SSD if possible (for mapping file I/O)
2. **Network Mounts**: Mediarr handles SMB/NFS gracefully, but local is faster
3. **Memory**: 256MB RAM minimum, 512MB recommended

### Monitoring

```bash
# Check container health
docker-compose ps

# View logs
docker-compose logs -f --tail=100

# Container stats
docker stats mediarr
```

### Backups

Backup these files regularly:

```bash
# Backup mapping file
cp data/tmdb_directory_mapping.json ~/backups/mediarr-mapping-$(date +%Y%m%d).json

# Backup environment
cp .env ~/backups/mediarr-env-$(date +%Y%m%d).txt
```

## Troubleshooting

### Container won't start

```bash
# Check logs
docker-compose logs mediarr

# Common issues:
# - Missing TMDB_API_KEY
# - Invalid volume paths
# - Port 5000 already in use (change in docker-compose.yml)
```

### Can't write artwork files

```bash
# Check permissions
docker-compose exec mediarr ls -la /movies

# Fix PUID/PGID in .env
# Should match owner of media files:
ls -ln /path/to/movies | head -5
```

### Artwork not downloading

1. Check TMDb API key is valid
2. Verify internet connectivity from container
3. Check directory matching in logs
4. Try clicking the card directly (uses UI hint)

### SMB mount issues

Mediarr includes retry logic, but if issues persist:

```bash
# Test SMB mount health
docker-compose exec mediarr ls -la /movies

# Check for BlockingIOError in logs
docker-compose logs | grep BlockingIOError
```

## Support

- **Documentation**: See README.md
- **Issues**: [GitHub Issues](https://github.com/anthonysnyder/Mediarr/issues)
- **Logs**: Always include logs when reporting issues

---

Ready to deploy? Start with Step 1 above!
