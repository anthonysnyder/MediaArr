"""
Mediarr - Unified artwork management for movies and TV shows
Manages backdrops, logos, and posters from a single interface
"""

import os
import re
from urllib.parse import unquote
from flask import Flask, render_template, request, redirect, url_for, flash, jsonify

from services import TMDbService, SlackService, ArtworkService
from utils import safe_send_file
from utils.mapping_utils import (
    mark_artwork_unavailable,
    is_artwork_available,
    reset_artwork_availability,
    get_tmdb_id_by_directory
)


# Initialize Flask application
app = Flask(__name__)
app.secret_key = os.getenv('SECRET_KEY', 'mediarr-secret-key-change-in-production')

# Configuration from environment variables
TMDB_API_KEY = os.getenv('TMDB_API_KEY')
if not TMDB_API_KEY:
    raise ValueError("TMDB_API_KEY environment variable is required")

# Parse folder configuration
movie_folders_env = os.getenv('MOVIE_FOLDERS', '/movies,/kids-movies,/anime')
tv_folders_env = os.getenv('TV_FOLDERS', '/tv,/kids-tv')

movie_folders = [
    folder.strip() for folder in movie_folders_env.split(',')
    if folder.strip() and os.path.exists(folder.strip())
]
tv_folders = [
    folder.strip() for folder in tv_folders_env.split(',')
    if folder.strip() and os.path.exists(folder.strip())
]

# Log configuration
app.logger.info(f"Movie folders: {movie_folders}")
app.logger.info(f"TV folders: {tv_folders}")

# Initialize services
tmdb_service = TMDbService(TMDB_API_KEY)
slack_service = SlackService()


# ============================================================================
# JINJA2 FILTERS
# ============================================================================

@app.template_filter('remove_year')
def remove_year(value):
    """Remove year information from movie titles for cleaner display"""
    return re.sub(r'\b(19|20|21|22|23)\d{2}\b', '', value).strip()


@app.template_filter('remove_tmdb')
def remove_tmdb(value):
    """Remove TMDb ID patterns from titles"""
    return re.sub(r'\{tmdb-\d+\}', '', value).strip()


@app.template_filter('escapejs')
def escapejs(value):
    """Escape quotes for JavaScript strings"""
    return value.replace("'", "\\'").replace('"', '\\"')


# ============================================================================
# MAIN PAGES
# ============================================================================

@app.route('/')
def index():
    """Main page - redirects to posters page"""
    return redirect(url_for('posters'))


@app.route('/tv')
def tv_shows():
    """Legacy TV shows route - redirects to posters with TV filter"""
    return redirect(url_for('posters', media_filter='tv'))


@app.route('/posters')
def posters():
    """Posters page with Movies/TV filter"""
    media_filter = request.args.get('media_filter', 'all')

    # Scan both movies and TV shows
    movies, total_movies = ArtworkService.scan_media_directories(movie_folders)
    shows, total_shows = ArtworkService.scan_media_directories(tv_folders)

    # Combine and filter based on media_filter
    all_media = []
    if media_filter in ('all', 'movies'):
        for m in movies:
            m['media_type'] = 'movie'
            # Look up tmdb_id from mapping
            tmdb_info = get_tmdb_id_by_directory(m['directory_path'])
            m['tmdb_id'] = tmdb_info['tmdb_id'] if tmdb_info else None
            all_media.append(m)
    if media_filter in ('all', 'tv'):
        for s in shows:
            s['media_type'] = 'tv'
            # Look up tmdb_id from mapping
            tmdb_info = get_tmdb_id_by_directory(s['directory_path'])
            s['tmdb_id'] = tmdb_info['tmdb_id'] if tmdb_info else None
            all_media.append(s)

    # Filter for items missing posters
    missing = [m for m in all_media if not m['has_poster']]

    stats = {
        'total': len(all_media),
        'with_artwork': sum(1 for m in all_media if m['has_poster']),
        'missing_artwork': len(missing),
    }

    return render_template('artwork_page.html',
                         media_items=all_media,
                         artwork_type='poster',
                         stats=stats,
                         media_filter=media_filter)


@app.route('/logos')
def logos():
    """Logos page with Movies/TV filter"""
    media_filter = request.args.get('media_filter', 'all')

    # Scan both movies and TV shows
    movies, total_movies = ArtworkService.scan_media_directories(movie_folders)
    shows, total_shows = ArtworkService.scan_media_directories(tv_folders)

    # Combine and filter based on media_filter
    all_media = []
    if media_filter in ('all', 'movies'):
        for m in movies:
            m['media_type'] = 'movie'
            # Look up tmdb_id from mapping
            tmdb_info = get_tmdb_id_by_directory(m['directory_path'])
            m['tmdb_id'] = tmdb_info['tmdb_id'] if tmdb_info else None
            all_media.append(m)
    if media_filter in ('all', 'tv'):
        for s in shows:
            s['media_type'] = 'tv'
            # Look up tmdb_id from mapping
            tmdb_info = get_tmdb_id_by_directory(s['directory_path'])
            s['tmdb_id'] = tmdb_info['tmdb_id'] if tmdb_info else None
            all_media.append(s)

    # Filter for items missing logos
    missing = [m for m in all_media if not m['has_logo']]

    stats = {
        'total': len(all_media),
        'with_artwork': sum(1 for m in all_media if m['has_logo']),
        'missing_artwork': len(missing),
    }

    return render_template('artwork_page.html',
                         media_items=all_media,
                         artwork_type='logo',
                         stats=stats,
                         media_filter=media_filter)


@app.route('/backdrops')
def backdrops():
    """Backdrops page with Movies/TV filter"""
    media_filter = request.args.get('media_filter', 'all')

    # Scan both movies and TV shows
    movies, total_movies = ArtworkService.scan_media_directories(movie_folders)
    shows, total_shows = ArtworkService.scan_media_directories(tv_folders)

    # Combine and filter based on media_filter
    all_media = []
    if media_filter in ('all', 'movies'):
        for m in movies:
            m['media_type'] = 'movie'
            # Look up tmdb_id from mapping
            tmdb_info = get_tmdb_id_by_directory(m['directory_path'])
            m['tmdb_id'] = tmdb_info['tmdb_id'] if tmdb_info else None
            all_media.append(m)
    if media_filter in ('all', 'tv'):
        for s in shows:
            s['media_type'] = 'tv'
            # Look up tmdb_id from mapping
            tmdb_info = get_tmdb_id_by_directory(s['directory_path'])
            s['tmdb_id'] = tmdb_info['tmdb_id'] if tmdb_info else None
            all_media.append(s)

    # Filter for items missing backdrops
    missing = [m for m in all_media if not m['has_backdrop']]

    stats = {
        'total': len(all_media),
        'with_artwork': sum(1 for m in all_media if m['has_backdrop']),
        'missing_artwork': len(missing),
    }

    return render_template('artwork_page.html',
                         media_items=all_media,
                         artwork_type='backdrop',
                         stats=stats,
                         media_filter=media_filter)


@app.route('/dashboard')
def dashboard():
    """Dashboard with overall statistics and recent activity"""
    # Scan both movies and TV shows
    movies, total_movies = ArtworkService.scan_media_directories(movie_folders)
    shows, total_shows = ArtworkService.scan_media_directories(tv_folders)

    stats = {
        'movies': {
            'total': total_movies,
            'with_backdrop': sum(1 for m in movies if m['has_backdrop']),
            'with_logo': sum(1 for m in movies if m['has_logo']),
            'with_poster': sum(1 for m in movies if m['has_poster']),
        },
        'tv': {
            'total': total_shows,
            'with_backdrop': sum(1 for s in shows if s['has_backdrop']),
            'with_logo': sum(1 for s in shows if s['has_logo']),
            'with_poster': sum(1 for s in shows if s['has_poster']),
        }
    }

    return render_template('dashboard.html', stats=stats)


@app.route('/refresh')
def refresh():
    """Trigger manual refresh of media directories"""
    # Just redirect back - scanning happens on each page load
    referer = request.referrer
    if referer and '/tv' in referer:
        return redirect(url_for('tv_shows'))
    return redirect(url_for('index'))


# ============================================================================
# SEARCH ROUTES
# ============================================================================

@app.route('/search_movie')
def search_movie():
    """Search for movies on TMDb"""
    query = request.args.get('query', '')
    directory = request.args.get('directory', '')
    artwork_type = request.args.get('artwork_type', 'backdrop')  # Default to backdrop

    results = tmdb_service.search_movies(query)

    # Add clean IDs for anchors
    for result in results:
        result['clean_id'] = ArtworkService.generate_clean_id(result['title'])

    return render_template(
        'search_results.html',
        query=query,
        results=results,
        directory=directory,
        artwork_type=artwork_type,
        media_type='movie'
    )


@app.route('/search_tv')
def search_tv():
    """Search for TV shows on TMDb"""
    query = unquote(request.args.get('query', ''))
    directory = request.args.get('directory', '')
    artwork_type = request.args.get('artwork_type', 'backdrop')

    app.logger.info(f"Search TV query: {query}, Directory: {directory}, Artwork: {artwork_type}")

    results = tmdb_service.search_tv(query)

    # Add clean IDs for anchors
    for result in results:
        result['clean_id'] = ArtworkService.generate_clean_id(result['name'])

    return render_template(
        'search_results.html',
        query=query,
        results=results,
        directory=directory,
        artwork_type=artwork_type,
        media_type='tv'
    )


# ============================================================================
# ARTWORK SELECTION ROUTES
# ============================================================================

@app.route('/select/<media_type>/<int:tmdb_id>')
def select_artwork(media_type, tmdb_id):
    """
    Select artwork (backdrop/logo/poster) for a movie or TV show.

    Query params:
        - artwork_type: 'backdrop', 'logo', or 'poster'
        - directory: Directory name hint from UI
    """
    artwork_type = request.args.get('artwork_type', 'backdrop')
    directory = request.args.get('directory', '')

    # Get media details
    if media_type == 'movie':
        details = tmdb_service.get_movie_details(tmdb_id)
        media_title = details.get('title', '')
    else:
        details = tmdb_service.get_tv_details(tmdb_id)
        media_title = details.get('name', '')

    # Check if we already know this artwork is unavailable
    availability = is_artwork_available(tmdb_id, media_type, artwork_type)
    if availability is False:
        flash(f"No {artwork_type}s available on TMDb for '{media_title}'. Click 'Recheck TMDb' to try again.", "warning")
        # Still show the selection page with a recheck option

    # Get artwork from TMDb based on type
    if artwork_type == 'backdrop':
        artworks = tmdb_service.get_backdrops(tmdb_id, media_type)
    elif artwork_type == 'logo':
        artworks = tmdb_service.get_logos(tmdb_id, media_type)
    elif artwork_type == 'poster':
        artworks = tmdb_service.get_posters(tmdb_id, media_type)
    else:
        artworks = []

    # If no artwork found, mark as unavailable
    if not artworks:
        mark_artwork_unavailable(tmdb_id, media_type, artwork_type)
        flash(f"No {artwork_type}s available on TMDb for '{media_title}'", "warning")

        # Redirect back to main page
        redirect_url = url_for('tv_shows' if media_type == 'tv' else 'index')
        anchor = f"#{ArtworkService.generate_clean_id(media_title)}"
        return redirect(redirect_url + anchor)

    return render_template(
        'artwork_selection.html',
        media_title=media_title,
        media_type=media_type,
        artwork_type=artwork_type,
        artworks=artworks,
        tmdb_id=tmdb_id,
        directory=directory
    )


@app.route('/recheck/<media_type>/<int:tmdb_id>/<artwork_type>')
def recheck_artwork(media_type, tmdb_id, artwork_type):
    """Force re-checking TMDb for artwork availability"""
    directory = request.args.get('directory', '')

    # Reset the availability flag
    reset_artwork_availability(tmdb_id, media_type, artwork_type)
    flash(f"Re-checking TMDb for {artwork_type}s...", "info")

    # Redirect to selection page
    return redirect(url_for(
        'select_artwork',
        media_type=media_type,
        tmdb_id=tmdb_id,
        artwork_type=artwork_type,
        directory=directory
    ))


@app.route('/mark_unavailable/<media_type>/<int:tmdb_id>/<artwork_type>', methods=['POST'])
def mark_unavailable(media_type, tmdb_id, artwork_type):
    """Mark artwork as unavailable on TMDb"""
    try:
        mark_artwork_unavailable(tmdb_id, media_type, artwork_type)
        return jsonify({'success': True, 'message': f'{artwork_type} marked as unavailable'})
    except Exception as e:
        app.logger.exception(f"Error marking artwork as unavailable: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


# ============================================================================
# ARTWORK DOWNLOAD ROUTES
# ============================================================================

@app.route('/download_artwork', methods=['POST'])
def download_artwork():
    """Download and save selected artwork"""
    app.logger.info(f"Received form data: {request.form}")

    # Validate required form data
    required_fields = ['artwork_url', 'artwork_type', 'media_title', 'media_type']
    if not all(field in request.form for field in required_fields):
        flash("Missing required form data", "error")
        return redirect(url_for('index'))

    try:
        artwork_url = request.form['artwork_url']
        artwork_type = request.form['artwork_type']
        media_title = request.form['media_title']
        media_type = request.form['media_type']
        tmdb_id = request.form.get('tmdb_id')
        directory = request.form.get('directory', '')

        app.logger.info(
            f"Download: {artwork_type} for '{media_title}' "
            f"(type={media_type}, tmdb_id={tmdb_id}, dir={directory})"
        )

        # Select base folders
        base_folders = movie_folders if media_type == 'movie' else tv_folders

        # Find matching directory
        save_dir = ArtworkService.find_matching_directory(
            media_title=media_title,
            tmdb_id=int(tmdb_id) if tmdb_id else None,
            media_type=media_type,
            base_folders=base_folders,
            directory_hint=directory
        )

        if not save_dir:
            # No match found - show directory selection UI
            flash(f"Could not find matching directory for '{media_title}'", "warning")
            # TODO: Implement select_directory.html
            return redirect(url_for('tv_shows' if media_type == 'tv' else 'index'))

        # Download and save artwork
        local_path = ArtworkService.download_and_save_artwork(
            artwork_url=artwork_url,
            artwork_type=artwork_type,
            media_title=media_title,
            save_dir=save_dir
        )

        if local_path:
            # Send Slack notification
            message = f"{artwork_type.capitalize()} for '{media_title}' has been downloaded!"
            slack_service.send_notification(message, local_path, artwork_url)

            # Return success page with JavaScript to go back
            # This uses browser cache instead of triggering a new scan
            return render_template(
                'download_success.html',
                artwork_type=artwork_type,
                media_title=media_title,
                media_type=media_type
            )
        else:
            flash(f"Failed to save {artwork_type}", "error")
            # On failure, redirect normally
            redirect_url = url_for('tv_shows' if media_type == 'tv' else 'index')
            anchor = f"#{ArtworkService.generate_clean_id(media_title)}"
            return redirect(redirect_url + anchor)

    except Exception as e:
        app.logger.exception(f"Error downloading artwork: {e}")
        flash("An error occurred while downloading artwork", "error")
        return redirect(url_for('index'))


# ============================================================================
# FILE SERVING ROUTES
# ============================================================================

@app.route('/artwork/<path:filename>')
def serve_artwork(filename):
    """Serve artwork files (backdrops, logos, posters) from the filesystem"""
    base_folders = movie_folders + tv_folders
    refresh = request.args.get('refresh', 'false')

    for base_folder in base_folders:
        full_path = os.path.join(base_folder, filename)

        # Skip Synology system directories
        if '@eaDir' in full_path or '#recycle' in full_path:
            continue

        if os.path.exists(full_path):
            # Serve the file using SMB-safe method
            response = safe_send_file(full_path)

            if refresh == 'true':
                # No caching for refresh
                response.cache_control.no_cache = True
                response.cache_control.must_revalidate = True
                response.cache_control.max_age = 0
            else:
                # Long-term caching for efficiency
                response.cache_control.max_age = 31536000  # 1 year

            return response

    app.logger.error(f"File not found: {filename}")
    return "File not found", 404


# ============================================================================
# ERROR HANDLERS
# ============================================================================

@app.errorhandler(404)
def not_found(error):
    """Handle 404 errors"""
    return render_template('error.html', error="Page not found", code=404), 404


@app.errorhandler(500)
def internal_error(error):
    """Handle 500 errors"""
    app.logger.exception("Internal server error")
    return render_template('error.html', error="Internal server error", code=500), 500


# ============================================================================
# MAIN ENTRY POINT
# ============================================================================

if __name__ == '__main__':
    port = int(os.getenv('PORT', 5000))

    app.run(
        host="0.0.0.0",
        port=port,
        debug=False,
        use_reloader=False
    )
