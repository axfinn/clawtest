# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [Unreleased]

### Added

- Initial project structure with Flask application
- Health check endpoint (`GET /api/v1/health`)
- AI chat endpoint (`POST /api/v1/chat`) with MiniMax API integration
- Code execution endpoint (`POST /api/v1/execute`) supporting multiple languages
- Models listing endpoint (`GET /api/v1/models`)
- MiniMax API client (`MiniMaxClient`) supporting M2.1 and M2.5 models
- Code executor (`CodeExecutor`) for Python, JavaScript, and Bash
- SQLite database support for development
- PostgreSQL support for production
- CORS support for cross-origin requests
- Docker support for containerized deployment

### Changed

- Updated project structure to use Flask Blueprints
- Improved error handling with standardized ApiResponse format
- Added timeout configuration for code execution

### Deprecated

- None

### Removed

- None

### Fixed

- Code executor timeout handling
- Temporary file cleanup after execution

### Security

- API key authentication for protected endpoints
- Environment variable based secret management

---

## [0.1.0] - 2024-01-15

### Added

- Initial release
- Basic Flask application setup
- Health check endpoint
- MiniMax API client (M2.5 model)
- Python code execution

---

## Version History

| Version | Date | Status |
|---------|------|--------|
| 0.1.0 | 2024-01-15 | Initial release |
| Unreleased | - | Development |

---

## Upgrade Guide

### Upgrading from 0.1.x

1. Update your dependencies:
   ```bash
   pip install -r requirements.txt
   ```

2. Update environment variables if needed:
   - `SECRET_KEY` - Generate a new secure key
   - `DATABASE_URL` - Ensure correct format for your database

3. Run database migrations (if applicable):
   ```bash
   python -m flask db upgrade
   ```

4. Restart the application:
   ```bash
   # Development
   python -m src.app
   
   # Production
   systemctl restart clawtest
   ```

---

## Breaking Changes

Currently there are no breaking changes. This section will be updated as the project evolves.

---

## Deprecation Timeline

No features are currently deprecated. This section will be updated as the project evolves.
