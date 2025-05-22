# From Caves to Cars - Developer Guidelines

This repository contains a Flask-based web application that simulates technological progression from primitive items to modern technology. The application leverages OpenAI APIs to generate content and manage the progression of technology within the game.

## Repository Structure

- `/` - Root directory with main Python modules and configuration files
- `/templates/` - Flask/Jinja2 HTML templates for web pages
- `/static/` - Static assets including CSS, JavaScript, and images
- `/static/images/` - Images for items in the game
- `/static/icons/` - Icon files for the application
- `/exampledatafiles/` - Example configuration files and starter data

## Key Files

- `fromcavestocars.py` - Main application file
- `main.py` - Entry point for the application
- `openaiquerylib.py` - Library for interacting with OpenAI APIs
- `fctcdb.py` - Database functionality
- `populator.py` - Logic for populating item data
- `fetchimages.py` - Utilities for fetching images for items
- `test_openaiquerylib.py` - Unit tests for the OpenAI query library

## Tools and Dependencies

### Primary Dependencies
- Flask - Web framework
- OpenAI API - For generating content and item descriptions
- Flask-Login - User authentication
- Flask-SQLAlchemy - Database ORM
- Flask-Dance - OAuth integration

### External Services
- OpenAI API - Content generation
- Google Images API - Image search (via googleimagelib.py)
- Pixabay API - Alternative image source (via pixabayimagelib.py)

## Development Workflow

### Setup
1. Install dependencies with `pip install -r requirements.txt`
2. Copy files from `exampledatafiles/` to the root directory
3. Set up environment variables for API keys

### Testing
Run unit tests with:
```
python test_openaiquerylib.py
```

Tests can be run with these options:
- `--flush` - Removes existing cache data and starts a new cache
- `--nocache` - Does not use a cache for this test run

### Running Locally
1. Set up required environment variables
2. Run `python main.py` to start the Flask server

## Deployment

The project is set up to deploy to Google Cloud Run using Cloud Build:
- See `cloudbuild.yaml` for the deployment configuration
- The application is containerized using Buildpacks

## Guidelines for Pull Requests

1. Make sure all unit tests pass before submitting
2. Update documentation when adding new features
3. Follow the existing code style and patterns
4. PRs with passing tests will automatically be marked as ready for review

## Backup Procedures

Use `backup.sh` to back up cache files and databases:
- Backs up files like `openai.cache.json`, `itemdb.json`, `tooldict.json`
- Files are stored in the `cachebackup` directory with sequential numbering