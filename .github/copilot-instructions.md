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
Run specific unit tests with:
```
python test_openaiquerylib.py
```

These tests can be run with these options:
- `--flush` - Removes existing cache data and starts a new cache
- `--nocache` - Does not use a cache for this test run

To run all tests including integration tests, use:
```
python run_tests.py
```

The integration tests cover:
- Page loading tests for home, login, registration, item choice, and game pages
- User registration and login flow
- Basic application functionality

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
4. PRs with passing tests must be submitted as "Ready for review" (not as Drafts). Only use Draft status if the PR is not ready for any feedback or review.
5. Never commit `__pycache__/*.pyc` or other build artifacts - refer to .gitignore
6. Do not add or modify files not directly related to your changes
7. Avoid committing database files (*.db), cache files, or any files excluded by .gitignore
8. Make minimal, focused changes that directly address the issue at hand
9. Do not submit pull requests as Drafts. PRs should be "Ready for review" unless you have a specific reason to mark them as a Draft.

## Backup Procedures

Use `backup.sh` to back up cache files and databases:
- Backs up files like `openai.cache.json`, `itemdb.json`, `tooldict.json`
- Files are stored in the `cachebackup` directory with sequential numbering