# Implementation Plan

## Current State Analysis
The workspace contains a basic frontend-only movie tracker with localStorage, but lacks the Python backend, TMDb API integration, and ML-based recommendation engine specified in the requirements and design documents.

## Implementation Tasks

- [x] 1. Set up Python Flask backend infrastructure


  - Create Flask application with proper project structure (app.py, requirements.txt, config.py)
  - Set up environment variable management for API keys (.env file)
  - Configure CORS for frontend-backend communication
  - Implement basic error logging to file system
  - _Requirements: 5.4, 8.4_

- [x] 2. Implement TMDb API client module


  - [x] 2.1 Create TMDbClient class with authentication

    - Implement API key configuration from environment variables
    - Create base request method with proper headers
    - _Requirements: 2.1, 5.1_
  

  - [ ] 2.2 Implement movie search functionality
    - Create search_movie method with title and optional year parameters
    - Implement ranking logic for multiple matches based on popularity and release year
    - Handle API response parsing and error cases
    - _Requirements: 2.1, 2.2_

  
  - [ ] 2.3 Implement movie details retrieval
    - Create get_movie_details method for fetching complete metadata
    - Extract and structure cast, director, runtime, genres, synopsis, poster path
    - Store TMDb movie ID for future reference

    - _Requirements: 2.1, 2.5_
  
  - [ ] 2.4 Add retry logic with exponential backoff
    - Implement retry mechanism for failed requests (up to 3 attempts)
    - Add exponential backoff delays (1s, 2s, 4s)

    - Handle timeout and network errors gracefully
    - _Requirements: 2.3, 5.5_
  
  - [x] 2.5 Implement response caching



    - Create in-memory cache with TTL tracking (24 hours)
    - Cache both search results and movie details
    - Implement cache key generation for searches and details
    - _Requirements: 2.4_


- [ ] 3. Implement CSV import module
  - [ ] 3.1 Create CSVImporter class with format detection
    - Implement auto-detection for TV Time and Letterboxd formats
    - Parse CSV headers to identify format type

    - _Requirements: 1.5_
  
  - [ ] 3.2 Implement CSV parsing for both formats
    - Extract movie titles, ratings, and watch dates from TV Time format
    - Extract movie titles, ratings, and watch dates from Letterboxd format
    - Create MovieEntry data structures from parsed rows

    - _Requirements: 1.2_
  
  - [ ] 3.3 Add CSV validation and error reporting
    - Validate file format is CSV
    - Validate required columns exist
    - Track invalid rows with specific error messages

    - Return validation results with row numbers for errors
    - _Requirements: 1.1, 1.3_
  




  - [ ] 3.4 Integrate TMDb lookup for imported movies
    - Query TMDb API for each imported movie title
    - Match movies based on title and year
    - Handle cases where movies are not found
    - Implement parallel requests for performance
    - _Requirements: 2.1, 6.4_

  
  - [ ] 3.5 Implement success confirmation
    - Count successfully imported movies
    - Return confirmation message with import count
    - _Requirements: 1.4_


- [ ] 4. Implement recommendation engine with ML algorithm
  - [ ] 4.1 Create UserProfile analysis
    - Calculate genre preferences from highly-rated movies (rating >= 4.0)
    - Compute average rating and standard deviation
    - Identify preferred decades from viewing history

    - Calculate viewing frequency patterns
    - _Requirements: 3.2, 3.5_
  
  - [ ] 4.2 Implement content-based filtering algorithm
    - Create scoring formula with weighted components (genre 40%, rating similarity 30%, popularity 20%, recency 10%)
    - Apply 1.5x weight factor for preferred genres
    - Calculate recommendation scores (0-100 percentage)
    - _Requirements: 3.2, 3.5_
  
  - [ ] 4.3 Implement recommendation generation
    - Require minimum of 5 rated movies before generating recommendations
    - Exclude movies already in user history
    - Return at least 10 recommendations ranked by score
    - Generate reasoning text for each recommendation
    - _Requirements: 3.1, 3.3, 3.4_
  
  - [ ] 4.4 Optimize recommendation performance
    - Implement vectorized calculations using numpy
    - Limit candidate pool to top 1000 popular movies
    - Ensure processing completes within 10 seconds for 500 movies
    - _Requirements: 6.2_

- [ ] 5. Create Flask API endpoints
  - [ ] 5.1 Implement POST /api/upload-csv endpoint
    - Accept multipart/form-data with CSV file
    - Validate file size (max 10MB)
    - Call CSVImporter to parse and validate
    - Return success status, import count, and any errors
    - Complete processing within 5 seconds for 500 movies
    - _Requirements: 1.1, 1.2, 1.3, 1.4, 6.1_
  
  - [ ] 5.2 Implement POST /api/add-movie endpoint
    - Accept JSON with title, rating, and date
    - Query TMDb API to validate and retrieve metadata
    - Return movie matches for user selection
    - Add confirmed movie to user history
    - _Requirements: 7.1, 7.2, 7.3, 7.4_
  
  - [x] 5.3 Implement GET /api/recommendations endpoint



    - Validate user has sufficient viewing history (minimum 5 movies)
    - Call RecommendationEngine to generate suggestions
    - Return recommendations with scores and reasoning
    - Include processing time in response
    - _Requirements: 3.1, 3.2, 3.3, 3.4, 5.3_
  
  - [x] 5.4 Implement GET /api/movie/:tmdb_id endpoint

    - Fetch detailed movie information from TMDb
    - Return complete metadata for movie detail view
    - Use cached data when available
    - _Requirements: 2.1, 4.3_
  

  - [ ] 5.5 Add comprehensive error handling to all endpoints
    - Return structured error responses with error codes
    - Log all errors to file with context
    - Handle TMDb API errors (auth, rate limit, network)


    - Provide user-friendly error messages
    - _Requirements: 5.1, 5.2, 5.3, 5.4, 5.5_

- [ ] 6. Update frontend HTML structure (index.html)
  - [ ] 6.1 Restructure page layout for new features
    - Add header with application title and branding
    - Create file upload section with drag-and-drop support
    - Add manual movie entry form with TMDb search results display
    - Create recommendations display grid
    - Add movie detail modal/overlay structure
    - _Requirements: 4.1, 7.1, 8.1_
  
  - [ ] 6.2 Add loading indicators and error containers
    - Create loading spinner elements
    - Add error message display containers
    - Add progress indicators for long operations
    - _Requirements: 4.5, 5.2, 6.5_
  
  - [ ] 6.3 Ensure semantic HTML5 markup
    - Use proper semantic tags (header, main, section, article)
    - Remove inline JavaScript (move to app.js)
    - Ensure proper accessibility attributes
    - _Requirements: 8.1, 8.5_

- [ ] 7. Update frontend CSS styling (stylesheet.css)
  - [ ] 7.1 Implement responsive design system
    - Create mobile-first responsive layout
    - Add breakpoints at 768px and 1024px
    - Implement CSS Grid for recommendation cards
    - Use Flexbox for form layouts
    - _Requirements: 4.4, 8.2_
  
  - [ ] 7.2 Add CSS custom properties for theming
    - Define color variables for consistent theming
    - Create reusable spacing and typography variables
    - _Requirements: 8.2_
  
  - [ ] 7.3 Style new UI components
    - Style movie detail modal with overlay
    - Create loading spinner animations
    - Style error messages with visual hierarchy
    - Design recommendation cards with poster images
    - Style percentage match indicators
    - _Requirements: 4.1, 4.2, 4.5_
  
  - [ ] 7.4 Ensure page loads within 2 seconds
    - Minimize CSS file size
    - Remove unused styles
    - Optimize animations for performance
    - _Requirements: 6.3_

- [ ] 8. Update frontend JavaScript logic (app.js)
  - [ ] 8.1 Implement CSV file upload with validation
    - Add file type validation (CSV only)
    - Implement drag-and-drop support
    - Send file to backend /api/upload-csv endpoint
    - Display import confirmation or errors
    - Show progress indicator during upload
    - _Requirements: 1.1, 1.3, 1.4, 5.2_
  
  - [ ] 8.2 Implement manual movie entry with TMDb search
    - Create form submission handler
    - Call /api/add-movie endpoint
    - Display TMDb search results for user selection
    - Handle movie confirmation and history update
    - Support adding multiple movies without re-upload
    - _Requirements: 7.1, 7.2, 7.3, 7.4, 7.5_
  
  - [ ] 8.3 Implement recommendations display
    - Call /api/recommendations endpoint
    - Display movie cards with poster, title, year, genre, synopsis
    - Show recommendation score as percentage match
    - Handle insufficient data error gracefully
    - _Requirements: 4.1, 4.2, 5.3_
  
  - [ ] 8.4 Implement movie detail modal
    - Create click handler for recommendation cards
    - Fetch detailed movie info from /api/movie/:tmdb_id
    - Display cast, director, runtime in modal
    - Add close functionality
    - _Requirements: 4.3_
  
  - [ ] 8.5 Add comprehensive error handling
    - Display user-friendly error messages for all error types
    - Show retry buttons for recoverable errors (network failures)
    - Handle API authentication errors
    - Handle rate limit errors with retry timing
    - Log technical details to console
    - _Requirements: 5.1, 5.2, 5.5_
  
  - [ ] 8.6 Implement loading states and progress indicators
    - Show loading spinner for operations > 3 seconds
    - Display progress for CSV upload and processing
    - Show loading state during recommendation generation
    - _Requirements: 4.5, 6.5_
  
  - [ ] 8.7 Remove localStorage and integrate with backend
    - Replace localStorage with backend API calls
    - Remove hardcoded movie database
    - Fetch all data from Flask backend
    - _Requirements: All backend integration requirements_

- [ ] 9. Create project documentation and configuration files
  - [ ] 9.1 Create requirements.txt for Python dependencies
    - List Flask, pandas, scikit-learn, requests, python-dotenv
    - Specify version constraints
    - _Requirements: 8.4_
  
  - [ ] 9.2 Create .env.example file
    - Document required environment variables (TMDB_API_KEY)
    - Provide example values and instructions
    - _Requirements: 5.1_
  
  - [ ] 9.3 Create README.md with setup instructions
    - Document installation steps
    - Explain how to obtain TMDb API key
    - Provide usage examples
    - Include CSV format specifications
    - _Requirements: 1.5_

- [ ] 10. Integration and end-to-end testing
  - [ ] 10.1 Test CSV upload flow with TV Time format
    - Upload valid TV Time CSV
    - Verify movies are imported and matched with TMDb
    - Confirm success message displays
    - _Requirements: 1.1, 1.2, 1.4, 1.5_
  
  - [ ] 10.2 Test CSV upload flow with Letterboxd format
    - Upload valid Letterboxd CSV
    - Verify movies are imported and matched with TMDb
    - Confirm success message displays
    - _Requirements: 1.1, 1.2, 1.4, 1.5_
  
  - [ ] 10.3 Test manual movie entry flow
    - Add movie manually through form
    - Select from TMDb search results
    - Verify movie is added to history
    - _Requirements: 7.1, 7.2, 7.3, 7.4_
  
  - [ ] 10.4 Test recommendation generation
    - Generate recommendations with sufficient history (5+ movies)
    - Verify recommendations exclude user's history
    - Confirm scores and reasoning display correctly
    - _Requirements: 3.1, 3.2, 3.3, 3.4, 3.5_
  
  - [ ] 10.5 Test error scenarios
    - Test invalid CSV upload
    - Test TMDb API errors (simulate network failure)
    - Test insufficient data for recommendations
    - Verify error messages display correctly
    - _Requirements: 5.1, 5.2, 5.3, 5.5_
  
  - [ ] 10.6 Test responsive design
    - Verify layout on mobile devices (< 768px)
    - Test on tablet devices (768px - 1024px)
    - Confirm desktop layout (> 1024px)
    - _Requirements: 4.4_
  
  - [ ] 10.7 Test performance requirements
    - Verify CSV parsing completes within 5 seconds (500 movies)
    - Confirm recommendations generate within 10 seconds (500 movies)
    - Check initial page load is under 2 seconds
    - Verify progress indicators appear for operations > 3 seconds
    - _Requirements: 6.1, 6.2, 6.3, 6.5_
