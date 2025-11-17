# Design Document: Movie AI Suggestor

## Overview

The Movie AI Suggestor is a web-based recommendation system that combines a Python backend with a clean, separated frontend architecture. The system analyzes user viewing history from CSV imports (TV Time, Letterboxd) and leverages The Movie Database (TMDb) API to provide personalized movie and TV show recommendations using machine learning algorithms.

**Key Design Principles:**
- Separation of concerns: HTML, CSS, and JavaScript in separate files
- Responsive design for desktop and mobile experiences
- Graceful error handling with user-friendly messaging
- Performance optimization through caching and parallel API requests
- Extensible architecture for future enhancements

## Architecture

### System Components

```
┌─────────────────────────────────────────────────────────────┐
│                        Web Browser                          │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐     │
│  │  index.html  │  │  styles.css  │  │   app.js     │     │
│  └──────────────┘  └──────────────┘  └──────────────┘     │
└────────────────────────────┬────────────────────────────────┘
                             │ HTTP/REST
                             ▼
┌─────────────────────────────────────────────────────────────┐
│                    Python Backend (Flask)                   │
│  ┌──────────────────────────────────────────────────────┐  │
│  │              API Endpoints Layer                     │  │
│  │  /upload-csv  /add-movie  /recommendations          │  │
│  └──────────────────────────────────────────────────────┘  │
│  ┌──────────────────┐  ┌────────────────────────────────┐  │
│  │  CSV Import      │  │  Recommendation Engine         │  │
│  │  Module          │  │  (ML Algorithm)                │  │
│  └──────────────────┘  └────────────────────────────────┘  │
│  ┌──────────────────┐  ┌────────────────────────────────┐  │
│  │  TMDb API        │  │  Cache Manager                 │  │
│  │  Client          │  │  (In-memory/Redis)             │  │
│  └──────────────────┘  └────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
                             │
                             ▼
                    ┌─────────────────┐
                    │   TMDb API      │
                    │  (External)     │
                    └─────────────────┘
```

### Technology Stack

**Frontend:**
- HTML5 for semantic markup
- CSS3 with Flexbox/Grid for responsive layouts
- Vanilla JavaScript (ES6+) for client-side logic
- Fetch API for HTTP requests

**Backend:**
- Python 3.8+
- Flask web framework for REST API
- Pandas for CSV processing
- Scikit-learn for recommendation algorithms
- Requests library for TMDb API integration

**Data Storage:**
- In-memory data structures for user sessions
- Optional: Redis for caching TMDb responses
- File-based error logging



## Components and Interfaces

### 1. Frontend Components

#### HTML Structure (index.html)
**Purpose:** Provides semantic page structure and user interface elements

**Key Sections:**
- Header with application title and branding
- File upload section with drag-and-drop support
- Manual movie entry form
- Recommendations display grid
- Movie detail modal/overlay
- Loading indicators and error message containers

**Design Decision:** Single-page application structure to minimize page reloads and provide smooth user experience.

#### CSS Styling (styles.css)
**Purpose:** Defines visual presentation and responsive behavior

**Key Features:**
- Mobile-first responsive design with breakpoints at 768px and 1024px
- CSS Grid for recommendation card layout
- Flexbox for form layouts and navigation
- CSS custom properties (variables) for theming
- Loading spinner animations
- Modal overlay styling
- Error message styling with visual hierarchy

**Design Decision:** No CSS frameworks (Bootstrap, Tailwind) to keep bundle size minimal and maintain full control over styling.

#### JavaScript Logic (app.js)
**Purpose:** Handles all client-side interactions and API communication

**Key Responsibilities:**
- File upload handling and validation
- Form submission for manual movie entry
- API communication with backend
- DOM manipulation for displaying recommendations
- Error handling and user feedback
- Progress indicator management
- Movie detail modal interactions

**Design Decision:** Vanilla JavaScript without frameworks to reduce complexity and load times, suitable for the application's scope.

### 2. Backend Components

#### Flask API Server
**Endpoints:**

```python
POST /api/upload-csv
- Accepts: multipart/form-data with CSV file
- Returns: { success: bool, movies_imported: int, errors: [] }
- Validates CSV format and processes viewing history

POST /api/add-movie
- Accepts: { title: str, rating: float, date: str }
- Returns: { success: bool, movie: {}, matches: [] }
- Queries TMDb and adds to user history

GET /api/recommendations
- Accepts: Query params for filtering (optional)
- Returns: { recommendations: [], processing_time: float }
- Generates personalized recommendations

GET /api/movie/{tmdb_id}
- Returns: Detailed movie information from TMDb
- Used for movie detail view
```

**Design Decision:** RESTful API design for clear separation between frontend and backend, enabling future mobile app development.

#### CSV Import Module
**Purpose:** Parse and validate CSV files from TV Time and Letterboxd

**Class Structure:**
```python
class CSVImporter:
    def __init__(self, file_stream):
        # Initialize with file stream
        
    def detect_format(self) -> str:
        # Auto-detect TV Time vs Letterboxd format
        
    def parse(self) -> List[MovieEntry]:
        # Parse CSV and return structured data
        
    def validate_row(self, row) -> Tuple[bool, str]:
        # Validate individual row, return (is_valid, error_message)
```

**Supported Formats:**
- TV Time: Columns expected - "Show Name", "Episode Name", "Date Watched", "Rating"
- Letterboxd: Columns expected - "Name", "Year", "Rating", "Watched Date"

**Design Decision:** Auto-detection of CSV format reduces user friction and supports multiple export sources without manual selection.

#### TMDb API Client
**Purpose:** Interface with The Movie Database API

**Class Structure:**
```python
class TMDbClient:
    def __init__(self, api_key: str, cache_manager: CacheManager):
        # Initialize with API credentials and cache
        
    def search_movie(self, title: str, year: int = None) -> List[Movie]:
        # Search for movies, return ranked matches
        
    def get_movie_details(self, tmdb_id: int) -> MovieDetails:
        # Fetch complete movie metadata
        
    def _retry_request(self, url: str, max_retries: int = 3):
        # Implement exponential backoff retry logic
```

**Features:**
- Exponential backoff: 1s, 2s, 4s delays between retries
- Response caching with TTL of 24 hours
- Parallel request batching for bulk operations
- Rate limiting compliance (40 requests per 10 seconds)

**Design Decision:** Caching strategy balances API quota conservation with data freshness. 24-hour TTL is acceptable since movie metadata rarely changes.

#### Recommendation Engine
**Purpose:** Generate personalized movie suggestions using collaborative filtering

**Algorithm Approach:**
Content-based filtering with weighted scoring:

1. **Genre Preference Analysis**
   - Calculate genre frequency from highly-rated movies (rating >= 4.0)
   - Apply weight factor of 1.5x for preferred genres

2. **Rating Pattern Analysis**
   - Identify rating distribution patterns
   - Detect user's rating tendencies (harsh vs generous)

3. **Temporal Analysis**
   - Consider viewing frequency and recency
   - Recent viewing patterns weighted higher (decay factor)

4. **Scoring Formula**
```
recommendation_score = (
    genre_match_score * 0.4 +
    rating_similarity_score * 0.3 +
    popularity_score * 0.2 +
    recency_bonus * 0.1
) * 100
```

**Class Structure:**
```python
class RecommendationEngine:
    def __init__(self, user_history: List[MovieEntry]):
        # Initialize with user's viewing history
        
    def analyze_preferences(self) -> UserProfile:
        # Build user preference profile
        
    def generate_recommendations(self, count: int = 10) -> List[Recommendation]:
        # Generate ranked recommendations
        
    def calculate_score(self, candidate_movie: Movie) -> float:
        # Calculate recommendation score for a movie
```

**Design Decision:** Content-based filtering chosen over collaborative filtering due to cold-start problem (new users) and privacy concerns. No need for other users' data.

#### Cache Manager
**Purpose:** Reduce redundant TMDb API calls and improve performance

**Implementation Options:**
- **Development:** In-memory Python dictionary with TTL tracking
- **Production:** Redis for persistent caching across server restarts

**Cache Keys:**
- `tmdb:movie:{tmdb_id}` - Movie details
- `tmdb:search:{title}:{year}` - Search results

**Design Decision:** Dual implementation strategy allows simple development setup while supporting scalable production deployment.



## Data Models

### Frontend Data Structures

```javascript
// Movie object received from backend
const Movie = {
    tmdb_id: number,
    title: string,
    release_year: number,
    genres: string[],
    poster_url: string,
    synopsis: string,
    recommendation_score: number,  // 0-100 percentage
    cast: string[],
    director: string,
    runtime: number
};

// User history entry
const HistoryEntry = {
    movie: Movie,
    rating: number,  // 0-5 scale
    watched_date: string  // ISO 8601 format
};

// API response structure
const RecommendationResponse = {
    success: boolean,
    recommendations: Movie[],
    processing_time: number,
    error?: string
};
```

### Backend Data Models

```python
from dataclasses import dataclass
from datetime import datetime
from typing import List, Optional

@dataclass
class MovieEntry:
    """Represents a movie in user's viewing history"""
    title: str
    rating: float  # 0-5 scale
    watched_date: datetime
    tmdb_id: Optional[int] = None
    genres: List[str] = None
    release_year: Optional[int] = None

@dataclass
class Movie:
    """Complete movie information from TMDb"""
    tmdb_id: int
    title: str
    release_year: int
    genres: List[str]
    poster_path: str
    overview: str
    vote_average: float
    popularity: float
    cast: List[str]
    director: str
    runtime: int
    
    def to_dict(self) -> dict:
        """Serialize for JSON response"""
        return {
            'tmdb_id': self.tmdb_id,
            'title': self.title,
            'release_year': self.release_year,
            'genres': self.genres,
            'poster_url': f"https://image.tmdb.org/t/p/w500{self.poster_path}",
            'synopsis': self.overview,
            'cast': self.cast[:5],  # Top 5 cast members
            'director': self.director,
            'runtime': self.runtime
        }

@dataclass
class UserProfile:
    """User preference profile for recommendations"""
    genre_preferences: dict  # {genre: weight}
    avg_rating: float
    rating_std_dev: float
    preferred_decades: List[int]
    viewing_frequency: float  # movies per month

@dataclass
class Recommendation:
    """Movie recommendation with score"""
    movie: Movie
    score: float  # 0-100 percentage
    reasoning: str  # Brief explanation of why recommended
```

### Database Schema (Future Enhancement)

While the initial version uses in-memory storage, here's the schema for future persistence:

```sql
-- Users table (for multi-user support)
CREATE TABLE users (
    id INTEGER PRIMARY KEY,
    username VARCHAR(50) UNIQUE,
    created_at TIMESTAMP
);

-- User viewing history
CREATE TABLE viewing_history (
    id INTEGER PRIMARY KEY,
    user_id INTEGER REFERENCES users(id),
    tmdb_id INTEGER,
    title VARCHAR(255),
    rating FLOAT,
    watched_date DATE,
    created_at TIMESTAMP
);

-- Cache table for TMDb responses
CREATE TABLE tmdb_cache (
    cache_key VARCHAR(255) PRIMARY KEY,
    response_data JSON,
    expires_at TIMESTAMP
);
```

**Design Decision:** Start with in-memory storage for MVP, but design data models that can easily transition to database persistence.

## Error Handling

### Error Categories and Responses

#### 1. CSV Upload Errors

**Invalid File Format:**
```json
{
    "success": false,
    "error": "Invalid file format. Please upload a CSV file.",
    "error_code": "INVALID_FORMAT"
}
```

**Parsing Errors:**
```json
{
    "success": false,
    "error": "CSV parsing failed. Check that your file matches TV Time or Letterboxd format.",
    "error_code": "PARSE_ERROR",
    "invalid_rows": [3, 7, 12],
    "details": "Missing required columns: 'Rating', 'Date Watched'"
}
```

#### 2. TMDb API Errors

**Authentication Error:**
```json
{
    "success": false,
    "error": "TMDb API authentication failed. Please check your API key configuration.",
    "error_code": "API_AUTH_ERROR"
}
```

**Rate Limit Exceeded:**
```json
{
    "success": false,
    "error": "Too many requests. Please wait a moment and try again.",
    "error_code": "RATE_LIMIT",
    "retry_after": 10
}
```

**Network Error:**
```json
{
    "success": false,
    "error": "Unable to connect to movie database. Please check your internet connection.",
    "error_code": "NETWORK_ERROR",
    "retry_available": true
}
```

#### 3. Recommendation Engine Errors

**Insufficient Data:**
```json
{
    "success": false,
    "error": "Not enough viewing history to generate recommendations. Please add at least 5 rated movies.",
    "error_code": "INSUFFICIENT_DATA",
    "current_count": 2,
    "required_count": 5
}
```

### Error Handling Strategy

**Backend:**
- All exceptions logged to `logs/error.log` with timestamp, stack trace, and context
- Custom exception classes for different error types
- Graceful degradation: partial results returned when possible
- Retry logic with exponential backoff for transient failures

**Frontend:**
- User-friendly error messages displayed in dedicated error container
- Technical details hidden from users but logged to console
- Retry buttons for recoverable errors
- Form validation before submission to prevent unnecessary API calls

**Design Decision:** Separate error codes enable frontend to handle different error types appropriately (e.g., showing retry button for network errors but not for validation errors).



## Performance Optimization

### Frontend Performance

**1. Lazy Loading Images**
- Poster images loaded with `loading="lazy"` attribute
- Placeholder images shown while loading
- Progressive image loading for better perceived performance

**2. Debouncing and Throttling**
- Search input debounced (300ms delay)
- Scroll events throttled for infinite scroll (if implemented)

**3. DOM Optimization**
- Minimize reflows by batching DOM updates
- Use document fragments for bulk insertions
- Virtual scrolling for large recommendation lists (future enhancement)

**4. Asset Optimization**
- Minified CSS and JavaScript for production
- Gzip compression enabled on server
- CSS loaded in `<head>`, JavaScript loaded before `</body>`

### Backend Performance

**1. Parallel API Requests**
```python
import asyncio
import aiohttp

async def fetch_multiple_movies(movie_titles: List[str]) -> List[Movie]:
    """Fetch multiple movies from TMDb in parallel"""
    async with aiohttp.ClientSession() as session:
        tasks = [fetch_movie(session, title) for title in movie_titles]
        return await asyncio.gather(*tasks)
```

**Design Decision:** Parallel requests reduce total processing time from O(n) to O(1) for batch operations, critical for meeting the 10-second recommendation generation requirement.

**2. Caching Strategy**
- TMDb responses cached for 24 hours
- User profiles cached during session
- Cache warming: pre-fetch popular movies on startup

**3. CSV Processing Optimization**
- Stream processing for large files (chunk size: 1000 rows)
- Pandas vectorized operations for data transformation
- Early validation to fail fast on invalid files

**4. Recommendation Algorithm Optimization**
- Pre-compute genre vectors for candidate movies
- Use numpy for vectorized similarity calculations
- Limit candidate pool to top 1000 popular movies (configurable)

### Performance Targets (from Requirements)

| Operation | Target | Strategy |
|-----------|--------|----------|
| CSV parsing (500 movies) | < 5 seconds | Stream processing, pandas optimization |
| Recommendation generation | < 10 seconds | Parallel API calls, caching, vectorized calculations |
| Initial page load | < 2 seconds | Minified assets, CDN (future) |
| Progress indicators | > 3 seconds | Show for any operation exceeding threshold |

**Design Decision:** Performance targets are aggressive but achievable with proper optimization. Caching and parallel processing are critical success factors.

## Testing Strategy

### Frontend Testing

**1. Unit Tests (Jest)**
- API client functions
- Data transformation utilities
- Form validation logic
- Error message formatting

**2. Integration Tests**
- File upload flow
- Manual movie entry flow
- Recommendation display
- Error handling scenarios

**3. UI/Visual Testing**
- Responsive design at different breakpoints
- Cross-browser compatibility (Chrome, Firefox, Safari, Edge)
- Accessibility testing (WCAG 2.1 AA compliance)
- Loading states and animations

**4. Manual Testing Checklist**
- CSV upload with valid TV Time export
- CSV upload with valid Letterboxd export
- CSV upload with invalid file
- Manual movie entry with exact match
- Manual movie entry with multiple matches
- Recommendation generation with various history sizes
- Error scenarios (network failure, API errors)
- Mobile device testing

### Backend Testing

**1. Unit Tests (pytest)**
```python
# Test CSV parsing
def test_csv_importer_tv_time_format()
def test_csv_importer_letterboxd_format()
def test_csv_importer_invalid_format()

# Test TMDb client
def test_tmdb_search_exact_match()
def test_tmdb_search_multiple_matches()
def test_tmdb_retry_logic()
def test_tmdb_caching()

# Test recommendation engine
def test_recommendation_genre_preference()
def test_recommendation_insufficient_data()
def test_recommendation_score_calculation()
```

**2. Integration Tests**
- End-to-end API workflows
- Database operations (when implemented)
- External API integration with mocked responses

**3. Performance Tests**
- Load testing with various CSV sizes (100, 500, 1000 movies)
- API response time monitoring
- Memory usage profiling
- Concurrent user simulation (future)

**4. Error Handling Tests**
- TMDb API failure scenarios
- Network timeout simulation
- Invalid input handling
- Edge cases (empty CSV, malformed data)

### Test Data

**Sample CSV Files:**
- `test_data/tv_time_sample.csv` - 50 movies, valid format
- `test_data/letterboxd_sample.csv` - 50 movies, valid format
- `test_data/invalid_format.csv` - Invalid structure
- `test_data/large_history.csv` - 500 movies for performance testing

**Mock TMDb Responses:**
- Successful search results
- Multiple match scenarios
- API error responses (401, 429, 500)
- Network timeout scenarios

**Design Decision:** Test-driven development approach for backend, with comprehensive unit tests before integration tests. Frontend testing focuses on user workflows and visual regression.

## Security Considerations

### API Key Management
- TMDb API key stored in environment variables, never in code
- `.env` file excluded from version control
- Separate keys for development and production

### Input Validation
- CSV file size limit: 10MB
- File type validation (MIME type checking)
- SQL injection prevention (parameterized queries when DB added)
- XSS prevention (sanitize user inputs, use textContent not innerHTML)

### Rate Limiting
- Backend rate limiting: 100 requests per minute per IP
- TMDb API quota monitoring and alerts
- Graceful degradation when limits approached

### CORS Configuration
- Whitelist specific origins in production
- Credentials not included in CORS requests
- Preflight request handling

**Design Decision:** Security-first approach with defense in depth. Multiple layers of validation and sanitization prevent common vulnerabilities.

## Deployment Architecture

### Development Environment
```
localhost:5000 (Flask backend)
localhost:3000 (Frontend dev server - optional)
```

### Production Environment (Future)
```
┌─────────────────┐
│   CloudFlare    │  CDN + DDoS protection
└────────┬────────┘
         │
┌────────▼────────┐
│  Nginx/Apache   │  Static file serving + reverse proxy
└────────┬────────┘
         │
┌────────▼────────┐
│  Gunicorn       │  WSGI server (4 workers)
└────────┬────────┘
         │
┌────────▼────────┐
│  Flask App      │  Application server
└────────┬────────┘
         │
┌────────▼────────┐
│  Redis Cache    │  TMDb response caching
└─────────────────┘
```

**Design Decision:** Simple deployment for MVP (single server), with clear path to scale horizontally by adding application servers behind load balancer.

## Future Enhancements

### Phase 2 Features
- User accounts and authentication
- Save and share recommendation lists
- Watch later / favorites functionality
- Social features (share with friends)

### Phase 3 Features
- Collaborative filtering using multiple users' data
- Streaming service availability integration
- Mobile native apps (iOS/Android)
- Advanced filters (decade, runtime, language)

### Technical Improvements
- GraphQL API for more flexible queries
- WebSocket for real-time updates
- Progressive Web App (PWA) capabilities
- A/B testing framework for recommendation algorithms

**Design Decision:** Modular architecture enables incremental feature additions without major refactoring. Current design supports future multi-user and social features.

