// API Configuration
const API_BASE_URL = 'http://localhost:5000/api';

// State
let currentMovieForRating = null;
let authToken = localStorage.getItem('authToken');
let currentUser = JSON.parse(localStorage.getItem('currentUser') || 'null');
let darkTheme = localStorage.getItem('darkTheme') === 'true';

// Initialize app
document.addEventListener('DOMContentLoaded', function() {
    initializeTheme();
    checkAuth();
    initializeTabs();
    initializeUpload();
    initializeSearch();
    initializeRecommendations();
    loadCollection();
});

// Theme Management
function initializeTheme() {
    const themeToggle = document.getElementById('themeToggle');
    
    // Apply saved theme
    if (darkTheme) {
        document.body.classList.add('dark-theme');
        themeToggle.textContent = '☀️';
    } else {
        themeToggle.textContent = '🌙';
    }
    
    // Toggle theme on button click
    themeToggle.addEventListener('click', toggleTheme);
}

function toggleTheme() {
    darkTheme = !darkTheme;
    localStorage.setItem('darkTheme', darkTheme);
    
    const themeToggle = document.getElementById('themeToggle');
    if (darkTheme) {
        document.body.classList.add('dark-theme');
        themeToggle.textContent = '☀️';
    } else {
        document.body.classList.remove('dark-theme');
        themeToggle.textContent = '🌙';
    }
}

// Tab Management
function initializeTabs() {
    const tabButtons = document.querySelectorAll('.tab-btn');
    const tabContents = document.querySelectorAll('.tab-content');

    tabButtons.forEach(button => {
        button.addEventListener('click', () => {
            const tabName = button.dataset.tab;

            // Remove active class from all
            tabButtons.forEach(btn => btn.classList.remove('active'));
            tabContents.forEach(content => content.classList.remove('active'));

            // Add active class to clicked
            button.classList.add('active');
            document.getElementById(`${tabName}-tab`).classList.add('active');

            // Load collection when switching to collection tab
            if (tabName === 'collection') {
                loadCollection();
            }
        });
    });
}

// CSV Upload
function initializeUpload() {
    const uploadArea = document.getElementById('uploadArea');
    const fileInput = document.getElementById('csvFile');

    // Click to upload
    uploadArea.addEventListener('click', () => fileInput.click());

    // File selection
    fileInput.addEventListener('change', handleFileSelect);

    // Drag and drop
    uploadArea.addEventListener('dragover', (e) => {
        e.preventDefault();
        uploadArea.classList.add('drag-over');
    });

    uploadArea.addEventListener('dragleave', () => {
        uploadArea.classList.remove('drag-over');
    });

    uploadArea.addEventListener('drop', (e) => {
        e.preventDefault();
        uploadArea.classList.remove('drag-over');
        
        const files = e.dataTransfer.files;
        if (files.length > 0) {
            handleFile(files[0]);
        }
    });
}

function handleFileSelect(event) {
    const file = event.target.files[0];
    if (file) {
        handleFile(file);
    }
}

async function handleFile(file) {
    if (!file.name.endsWith('.csv')) {
        showStatus('importStatus', 'Please select a CSV file', 'error');
        return;
    }

    showLoading(true);

    const formData = new FormData();
    formData.append('file', file);

    try {
        const response = await fetch(`${API_BASE_URL}/upload-csv`, {
            method: 'POST',
            headers: {
                'Authorization': `Bearer ${authToken}`
            },
            body: formData
        });

        const data = await response.json();

        if (response.ok && data.success) {
            showStatus('importStatus', data.message, 'success');
            
            if (data.errors && data.errors.length > 0) {
                const errorList = data.errors.slice(0, 5).join('<br>');
                showStatus('importStatus', 
                    `${data.message}<br><br>Some errors occurred:<br>${errorList}`, 
                    'info');
            }
        } else {
            showStatus('importStatus', data.error || 'Import failed', 'error');
        }
    } catch (error) {
        console.error('Upload error:', error);
        showStatus('importStatus', 'Network error. Please check if the backend is running.', 'error');
    } finally {
        showLoading(false);
    }
}

// Movie Search
function initializeSearch() {
    const searchForm = document.getElementById('searchForm');
    searchForm.addEventListener('submit', handleSearch);
}

async function handleSearch(event) {
    event.preventDefault();

    const title = document.getElementById('movieTitle').value.trim();
    const year = document.getElementById('movieYear').value;

    if (!title) return;

    showLoading(true);

    try {
        const params = { title };
        if (year) params.year = year;

        const response = await fetch(`${API_BASE_URL}/add-movie`, {
            method: 'POST',
            headers: getAuthHeaders(),
            body: JSON.stringify(params)
        });

        const data = await response.json();

        if (response.ok && data.matches) {
            displaySearchResults(data.matches);
        } else {
            showStatus('addStatus', data.error || data.message || 'No results found', 'error');
            document.getElementById('searchResults').innerHTML = '';
        }
    } catch (error) {
        console.error('Search error:', error);
        showStatus('addStatus', 'Network error. Please check if the backend is running.', 'error');
    } finally {
        showLoading(false);
    }
}

function displaySearchResults(matches) {
    const resultsContainer = document.getElementById('searchResults');
    
    if (matches.length === 0) {
        resultsContainer.innerHTML = '<p>No results found</p>';
        return;
    }

    resultsContainer.innerHTML = `
        <h3>Select a movie:</h3>
        ${matches.map(movie => `
            <div class="search-result-item" onclick="selectMovie(${movie.tmdb_id})">
                <img src="${movie.poster_path || 'https://via.placeholder.com/80x120?text=No+Image'}" 
                     alt="${movie.title}" 
                     class="search-result-poster">
                <div class="search-result-info">
                    <div class="search-result-title">${movie.title} (${movie.year || 'N/A'})</div>
                    <div class="search-result-meta">${movie.overview ? movie.overview.substring(0, 150) + '...' : 'No description available'}</div>
                </div>
            </div>
        `).join('')}
    `;
}

async function selectMovie(tmdbId) {
    // Show rating form
    const resultsContainer = document.getElementById('searchResults');
    resultsContainer.innerHTML = `
        <div class="card">
            <h3>Rate this movie</h3>
            <form id="ratingForm" onsubmit="submitMovieRating(event, ${tmdbId})">
                <div class="form-group">
                    <input type="number" id="userRating" placeholder="Rating (0-10)" 
                           min="0" max="10" step="0.5" required>
                    <input type="date" id="watchDate" placeholder="Watch Date">
                </div>
                <button type="submit" class="btn-primary">Add to Collection</button>
            </form>
        </div>
    `;
}

async function submitMovieRating(event, tmdbId) {
    event.preventDefault();

    const rating = parseFloat(document.getElementById('userRating').value);
    const watchDate = document.getElementById('watchDate').value;

    showLoading(true);

    try {
        const response = await fetch(`${API_BASE_URL}/add-movie`, {
            method: 'POST',
            headers: getAuthHeaders(),
            body: JSON.stringify({
                tmdb_id: tmdbId,
                rating: rating,
                watch_date: watchDate || null
            })
        });

        const data = await response.json();

        if (response.ok && data.success) {
            showStatus('addStatus', data.message, 'success');
            document.getElementById('searchForm').reset();
            document.getElementById('searchResults').innerHTML = '';
        } else {
            showStatus('addStatus', data.error || 'Failed to add movie', 'error');
        }
    } catch (error) {
        console.error('Add movie error:', error);
        showStatus('addStatus', 'Network error. Please check if the backend is running.', 'error');
    } finally {
        showLoading(false);
    }
}

// Recommendations
let currentRecommendationOffset = 0;
let allRecommendations = [];

function initializeRecommendations() {
    const generateBtn = document.getElementById('generateBtn');
    const loadMoreBtn = document.getElementById('loadMoreBtn');
    generateBtn.addEventListener('click', generateRecommendations);
    loadMoreBtn.addEventListener('click', loadMoreRecommendations);
}

async function generateRecommendations() {
    showLoading(true);
    document.getElementById('recommendationsList').innerHTML = '';
    currentRecommendationOffset = 0;
    allRecommendations = [];

    try {
        const response = await fetch(`${API_BASE_URL}/recommendations`, {
            headers: getAuthHeaders()
        });
        const data = await response.json();

        if (response.ok && data.success) {
            allRecommendations = data.recommendations;
            displayRecommendations(allRecommendations.slice(0, 10));
            
            // Show load more button if there are more recommendations
            const loadMoreBtn = document.getElementById('loadMoreBtn');
            if (allRecommendations.length > 10) {
                loadMoreBtn.style.display = 'block';
                currentRecommendationOffset = 10;
            } else {
                loadMoreBtn.style.display = 'none';
            }
            
            showStatus('recommendationsStatus', 
                `Found ${data.count} personalized recommendations for you!`, 
                'success');
        } else {
            showStatus('recommendationsStatus', data.error || data.message, 'error');
        }
    } catch (error) {
        console.error('Recommendations error:', error);
        showStatus('recommendationsStatus', 
            'Network error. Please check if the backend is running.', 
            'error');
    } finally {
        showLoading(false);
    }
}

function loadMoreRecommendations() {
    const container = document.getElementById('recommendationsList');
    const nextBatch = allRecommendations.slice(currentRecommendationOffset, currentRecommendationOffset + 10);
    
    if (nextBatch.length === 0) {
        document.getElementById('loadMoreBtn').style.display = 'none';
        showStatus('recommendationsStatus', 'No more recommendations available', 'info');
        return;
    }
    
    // Append new recommendations
    nextBatch.forEach(movie => {
        const movieCard = createMovieCard(movie);
        container.appendChild(movieCard);
    });
    
    currentRecommendationOffset += 10;
    
    // Hide load more button if we've shown all
    if (currentRecommendationOffset >= allRecommendations.length) {
        document.getElementById('loadMoreBtn').style.display = 'none';
    }
}

function createMovieCard(movie) {
    const div = document.createElement('div');
    div.className = 'movie-card';
    div.onclick = () => showMovieDetails(movie.tmdb_id);
    div.innerHTML = `
        <img src="${movie.poster_path || 'https://via.placeholder.com/200x300?text=No+Image'}" 
             alt="${movie.title}" 
             class="movie-poster"
             onerror="this.src='https://via.placeholder.com/200x300?text=No+Image'">
        <div class="movie-info">
            <div class="movie-title">${movie.title}</div>
            <div class="movie-meta">${movie.year || 'N/A'} • ${movie.genres ? movie.genres.slice(0, 2).join(', ') : 'N/A'}</div>
            <div class="match-score">${Math.round(movie.match_score || 0)}% Match</div>
            <div class="movie-reasoning">${movie.reasoning || 'Recommended for you'}</div>
        </div>
    `;
    return div;
}

function displayRecommendations(recommendations) {
    const container = document.getElementById('recommendationsList');

    if (!recommendations || recommendations.length === 0) {
        container.innerHTML = '<p>No recommendations available</p>';
        return;
    }

    console.log('Displaying recommendations:', recommendations);

    container.innerHTML = '';
    recommendations.forEach(movie => {
        const movieCard = createMovieCard(movie);
        container.appendChild(movieCard);
    });
}

// Collection
async function loadCollection() {
    try {
        const response = await fetch(`${API_BASE_URL}/movies`, {
            headers: getAuthHeaders()
        });
        const data = await response.json();

        if (response.ok) {
            displayCollection(data.movies, data.count);
        }
    } catch (error) {
        console.error('Load collection error:', error);
    }
}

function displayCollection(movies, count) {
    const countContainer = document.getElementById('collectionCount');
    const listContainer = document.getElementById('collectionList');

    countContainer.textContent = `You have ${count} movie${count !== 1 ? 's' : ''} in your collection`;

    if (movies.length === 0) {
        listContainer.innerHTML = '<p>No movies in your collection yet. Start by importing a CSV or adding movies manually!</p>';
        return;
    }

    listContainer.innerHTML = movies.map(movie => `
        <div class="movie-card">
            <img src="${movie.poster_path || 'https://via.placeholder.com/200x300?text=No+Image'}" 
                 alt="${movie.title}" 
                 class="movie-poster"
                 onclick="showMovieDetails(${movie.tmdb_id})"
                 style="cursor: pointer;">
            <div class="movie-info">
                <div class="movie-title">${movie.title}</div>
                <div class="movie-meta">${movie.year || 'N/A'} • ${movie.genres ? movie.genres.slice(0, 2).join(', ') : 'N/A'}</div>
                ${movie.rating ? `<div class="match-score">Your Rating: ${movie.rating}/10</div>` : ''}
                <button class="btn-delete" onclick="deleteMovie(${movie.tmdb_id}, event)">🗑️ Delete</button>
            </div>
        </div>
    `).join('');
}

// Delete Movie
async function deleteMovie(tmdbId, event) {
    event.stopPropagation();
    
    if (!confirm('Are you sure you want to delete this movie from your collection?')) {
        return;
    }
    
    try {
        const response = await fetch(`${API_BASE_URL}/delete-movie/${tmdbId}`, {
            method: 'DELETE',
            headers: getAuthHeaders()
        });
        
        if (response.ok) {
            showStatus('collectionStatus', 'Movie deleted successfully', 'success');
            loadCollection();
        } else {
            const error = await response.json();
            showStatus('collectionStatus', error.error || 'Failed to delete movie', 'error');
        }
    } catch (error) {
        console.error('Delete movie error:', error);
        showStatus('collectionStatus', 'Error deleting movie', 'error');
    }
}

// Movie Details Modal
async function showMovieDetails(tmdbId) {
    showLoading(true);

    try {
        const response = await fetch(`${API_BASE_URL}/movie/${tmdbId}`, {
            headers: getAuthHeaders()
        });
        const movie = await response.json();

        if (response.ok) {
            displayMovieModal(movie);
        }
    } catch (error) {
        console.error('Movie details error:', error);
    } finally {
        showLoading(false);
    }
}

function displayMovieModal(movie) {
    const modal = document.getElementById('movieModal');
    const detailsContainer = document.getElementById('movieDetails');

    detailsContainer.innerHTML = `
        <div class="movie-detail-header" style="background-image: url('${movie.backdrop_path || movie.poster_path || ''}')">
            <div class="movie-detail-overlay">
                <h2>${movie.title} (${movie.year || 'N/A'})</h2>
                <p>${movie.genres ? movie.genres.join(', ') : 'N/A'}</p>
            </div>
        </div>
        <div class="movie-detail-body">
            <div class="movie-detail-section">
                <h3>Overview</h3>
                <p>${movie.overview || 'No overview available'}</p>
            </div>
            ${movie.director ? `
                <div class="movie-detail-section">
                    <h3>Director</h3>
                    <p>${movie.director}</p>
                </div>
            ` : ''}
            ${movie.cast && movie.cast.length > 0 ? `
                <div class="movie-detail-section">
                    <h3>Cast</h3>
                    <div class="cast-list">
                        ${movie.cast.map(actor => `
                            <span class="cast-member">${actor.name}</span>
                        `).join('')}
                    </div>
                </div>
            ` : ''}
            <div class="movie-detail-section">
                <h3>Details</h3>
                <p><strong>Runtime:</strong> ${movie.runtime ? movie.runtime + ' minutes' : 'N/A'}</p>
                <p><strong>Rating:</strong> ${movie.rating ? movie.rating + '/10' : 'N/A'}</p>
            </div>
        </div>
    `;

    modal.classList.add('show');

    // Close modal
    const closeBtn = document.querySelector('.modal-close');
    closeBtn.onclick = () => modal.classList.remove('show');

    modal.onclick = (e) => {
        if (e.target === modal) {
            modal.classList.remove('show');
        }
    };
}

// Utility Functions
function showStatus(elementId, message, type) {
    const statusElement = document.getElementById(elementId);
    statusElement.innerHTML = message;
    statusElement.className = `status-message ${type} show`;

    setTimeout(() => {
        statusElement.classList.remove('show');
    }, 5000);
}

function showLoading(show) {
    const spinner = document.getElementById('loadingSpinner');
    if (show) {
        spinner.classList.add('show');
    } else {
        spinner.classList.remove('show');
    }
}


// Chat functionality
function initializeChat() {
    const chatForm = document.getElementById('chatForm');
    const resetBtn = document.getElementById('resetChatBtn');
    
    if (chatForm) {
        chatForm.addEventListener('submit', handleChatSubmit);
    }
    
    if (resetBtn) {
        resetBtn.addEventListener('click', resetChat);
    }
}

async function handleChatSubmit(event) {
    event.preventDefault();
    
    const input = document.getElementById('chatInput');
    const message = input.value.trim();
    
    if (!message) return;
    
    // Add user message to chat
    addMessageToChat(message, 'user');
    
    // Clear input
    input.value = '';
    
    // Show typing indicator
    showTypingIndicator();
    
    try {
        const response = await fetch(`${API_BASE_URL}/chat`, {
            method: 'POST',
            headers: getAuthHeaders(),
            body: JSON.stringify({ message })
        });
        
        const data = await response.json();
        
        // Remove typing indicator
        removeTypingIndicator();
        
        if (response.ok && data.success) {
            // Add bot response to chat
            addMessageToChat(data.response, 'bot');
            
            // If there are movie suggestions, display them
            if (data.suggestions && data.suggestions.length > 0) {
                displayChatSuggestions(data.suggestions);
            }
        } else {
            addMessageToChat(
                data.message || 'Sorry, I encountered an error. Please try again.',
                'bot'
            );
        }
    } catch (error) {
        console.error('Chat error:', error);
        removeTypingIndicator();
        addMessageToChat(
            'Sorry, I\'m having trouble connecting. Make sure the backend is running and OpenAI API key is configured.',
            'bot'
        );
    }
}

function addMessageToChat(message, sender) {
    const messagesContainer = document.getElementById('chatMessages');
    
    const messageDiv = document.createElement('div');
    messageDiv.className = `chat-message ${sender}-message`;
    
    const contentDiv = document.createElement('div');
    contentDiv.className = 'message-content';
    contentDiv.textContent = message;
    
    messageDiv.appendChild(contentDiv);
    messagesContainer.appendChild(messageDiv);
    
    // Scroll to bottom
    messagesContainer.scrollTop = messagesContainer.scrollHeight;
}

function showTypingIndicator() {
    const messagesContainer = document.getElementById('chatMessages');
    
    const typingDiv = document.createElement('div');
    typingDiv.className = 'chat-message bot-message';
    typingDiv.id = 'typingIndicator';
    
    const indicatorDiv = document.createElement('div');
    indicatorDiv.className = 'typing-indicator';
    indicatorDiv.innerHTML = `
        <div class="typing-dot"></div>
        <div class="typing-dot"></div>
        <div class="typing-dot"></div>
    `;
    
    typingDiv.appendChild(indicatorDiv);
    messagesContainer.appendChild(typingDiv);
    
    messagesContainer.scrollTop = messagesContainer.scrollHeight;
}

function removeTypingIndicator() {
    const indicator = document.getElementById('typingIndicator');
    if (indicator) {
        indicator.remove();
    }
}

function displayChatSuggestions(suggestions) {
    // Display movie suggestions with posters in the chat
    const messagesContainer = document.getElementById('chatMessages');
    
    if (!suggestions || suggestions.length === 0) {
        return;
    }
    
    const suggestionsDiv = document.createElement('div');
    suggestionsDiv.className = 'chat-message bot-message';
    
    const contentDiv = document.createElement('div');
    contentDiv.className = 'message-content';
    
    // Create a grid of movie cards
    const moviesHtml = suggestions.map(movie => `
        <div class="chat-movie-card" onclick="showMovieDetails(${movie.tmdb_id})">
            <img src="${movie.poster_path || 'https://via.placeholder.com/80x120?text=No+Image'}" 
                 alt="${movie.title}" 
                 class="chat-movie-poster"
                 onerror="this.src='https://via.placeholder.com/80x120?text=No+Image'">
            <div class="chat-movie-info">
                <div class="chat-movie-title">${movie.title}</div>
                <div class="chat-movie-year">${movie.year || 'N/A'}</div>
                ${movie.overview ? `<div class="chat-movie-overview">${movie.overview}</div>` : ''}
            </div>
        </div>
    `).join('');
    
    contentDiv.innerHTML = `
        <strong>Here are some movies you might like:</strong>
        <div class="chat-suggestions-grid">
            ${moviesHtml}
        </div>
    `;
    
    suggestionsDiv.appendChild(contentDiv);
    messagesContainer.appendChild(suggestionsDiv);
    
    messagesContainer.scrollTop = messagesContainer.scrollHeight;
}

async function resetChat() {
    try {
        await fetch(`${API_BASE_URL}/chat/reset`, {
            method: 'POST',
            headers: getAuthHeaders()
        });
        
        // Clear chat messages except the initial greeting
        const messagesContainer = document.getElementById('chatMessages');
        messagesContainer.innerHTML = `
            <div class="chat-message bot-message">
                <div class="message-content">
                    Hi! I'm your movie assistant. I can help you discover great movies based on your taste. What kind of movies are you in the mood for?
                </div>
            </div>
        `;
    } catch (error) {
        console.error('Reset chat error:', error);
    }
}

// Initialize chat when DOM is ready
document.addEventListener('DOMContentLoaded', function() {
    initializeTabs();
    initializeUpload();
    initializeSearch();
    initializeRecommendations();
    initializeChat();
    loadCollection();
});


// ============ AUTHENTICATION ============

function checkAuth() {
    if (authToken && currentUser) {
        showMainApp();
    } else {
        showAuthModal();
    }
}

function showAuthModal() {
    document.getElementById('authModal').classList.remove('hidden');
    document.querySelector('main').style.display = 'none';
    document.querySelector('header').style.display = 'none';
    
    document.getElementById('loginForm').addEventListener('submit', handleLogin);
    document.getElementById('signupForm').addEventListener('submit', handleSignup);
}

function showMainApp() {
    document.getElementById('authModal').classList.add('hidden');
    document.querySelector('main').style.display = 'block';
    document.querySelector('header').style.display = 'block';
    
    updateUserDisplay();
    document.getElementById('logoutBtn').addEventListener('click', handleLogout);
}

function toggleAuthForm(event) {
    event.preventDefault();
    document.getElementById('loginForm').classList.toggle('active');
    document.getElementById('signupForm').classList.toggle('active');
}

async function handleLogin(event) {
    event.preventDefault();
    
    const username = document.getElementById('loginUsername').value;
    const password = document.getElementById('loginPassword').value;
    
    try {
        const response = await fetch(`${API_BASE_URL}/auth/login`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ username, password })
        });
        
        const data = await response.json();
        
        if (response.ok && data.success) {
            authToken = data.access_token;
            currentUser = data.user;
            
            localStorage.setItem('authToken', authToken);
            localStorage.setItem('currentUser', JSON.stringify(currentUser));
            
            showMainApp();
            showStatus('loginStatus', 'Login successful!', 'success');
        } else {
            showStatus('loginStatus', data.error || 'Login failed', 'error');
        }
    } catch (error) {
        console.error('Login error:', error);
        showStatus('loginStatus', 'Network error', 'error');
    }
}

async function handleSignup(event) {
    event.preventDefault();
    
    const username = document.getElementById('signupUsername').value;
    const email = document.getElementById('signupEmail').value;
    const password = document.getElementById('signupPassword').value;
    
    try {
        const response = await fetch(`${API_BASE_URL}/auth/signup`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ username, email, password })
        });
        
        const data = await response.json();
        
        if (response.ok && data.success) {
            authToken = data.access_token;
            currentUser = data.user;
            
            localStorage.setItem('authToken', authToken);
            localStorage.setItem('currentUser', JSON.stringify(currentUser));
            
            showMainApp();
            showStatus('signupStatus', 'Account created successfully!', 'success');
        } else {
            showStatus('signupStatus', data.error || 'Signup failed', 'error');
        }
    } catch (error) {
        console.error('Signup error:', error);
        showStatus('signupStatus', 'Network error', 'error');
    }
}

function handleLogout() {
    authToken = null;
    currentUser = null;
    
    localStorage.removeItem('authToken');
    localStorage.removeItem('currentUser');
    
    document.getElementById('loginForm').reset();
    document.getElementById('signupForm').reset();
    document.getElementById('loginForm').classList.add('active');
    document.getElementById('signupForm').classList.remove('active');
    
    showAuthModal();
}

function updateUserDisplay() {
    if (currentUser) {
        document.getElementById('userDisplay').textContent = `Welcome, ${currentUser.username}!`;
    }
}

function getAuthHeaders() {
    return {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${authToken}`
    };
}
