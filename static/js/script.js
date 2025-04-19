/**
 * Nebulous Cinema - Interactive Movie Recommender System
 * Created by Sahil Harchandani
 * Version 1.1
 * Last Updated: April 2025
 */

// State management variables
let currentMovieId = null;
let currentLanguage = null;
let currentPage = 1;
const moviesPerPage = 12;
let isLoading = false; // Flag to prevent multiple simultaneous loading requests
let lastSearchQuery = ''; // Track last search query

// DOM elements
document.addEventListener('DOMContentLoaded', function() {
    // Initialize DOM elements
    const searchInput = document.getElementById('search-input');
    const searchBtn = document.getElementById('search-btn');
    const clearSearchBtn = document.getElementById('clear-search');
    const movieResults = document.getElementById('movie-results');
    const resultsTitle = document.getElementById('results-title');
    const recommendationsSection = document.querySelector('.recommendations');
    const recommendationsContainer = document.getElementById('recommendations-container');
    const showRecommendationsBtn = document.getElementById('show-recommendations');
    const movieModal = new bootstrap.Modal(document.getElementById('movieModal'));
    const backToTopBtn = document.getElementById('back-to-top');
    const shownMovieIds = new Set();
    
    // Filter buttons
    const allMoviesNav = document.getElementById('all-movies');
    const hollywoodFilterNav = document.getElementById('hollywood-filter');
    const bollywoodFilterNav = document.getElementById('bollywood-filter');
    
    const filterAll = document.getElementById('filter-all');
    const filterHollywood = document.getElementById('filter-hollywood');
    const filterBollywood = document.getElementById('filter-bollywood');
    
    // Create back to top button if it doesn't exist
    if (!backToTopBtn) {
        createBackToTopButton();
    }
    
    // Initialize the app
    initializeApp();
    
    /**
     * Initialize the application
     */
    function initializeApp() {
        setupEventListeners();
        fetchRandomMovies(moviesPerPage);
        
        // Create clear search button if it doesn't exist
        if (!clearSearchBtn && searchInput) {
            createClearSearchButton();
        }
    }
    
    /**
     * Create a clear search button
     */
    function createClearSearchButton() {
        const clearBtn = document.createElement('button');
        clearBtn.id = 'clear-search';
        clearBtn.className = 'clear-search-btn';
        clearBtn.innerHTML = '<i class="fas fa-times"></i>';
        clearBtn.style.cssText = `
            position: absolute;
            right: 45px;
            top: 50%;
            transform: translateY(-50%);
            background: none;
            border: none;
            color: #888;
            font-size: 1rem;
            cursor: pointer;
            display: none;
            z-index: 10;
        `;
        
        // Insert button into search container
        const searchContainer = searchInput.parentElement;
        searchContainer.style.position = 'relative';
        searchContainer.insertBefore(clearBtn, searchBtn);
        
        // Add event listener
        clearBtn.addEventListener('click', function() {
            searchInput.value = '';
            clearBtn.style.display = 'none';
            searchInput.focus();
        });
        
        // Show/hide clear button based on input
        searchInput.addEventListener('input', function() {
            clearBtn.style.display = this.value ? 'block' : 'none';
        });
        
        return clearBtn;
    }
    
    /**
     * Create a back to top button
     */
    function createBackToTopButton() {
        const backBtn = document.createElement('button');
        backBtn.id = 'back-to-top';
        backBtn.className = 'back-to-top';
        backBtn.innerHTML = '<i class="fas fa-chevron-up"></i>';
        backBtn.style.cssText = `
            position: fixed;
            bottom: 85px;
            right: 20px;
            width: 50px;
            height: 50px;
            border-radius: 50%;
            background: var(--gradient);
            color: white;
            border: none;
            box-shadow: 0 3px 10px rgba(0,0,0,0.2);
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 1.2rem;
            cursor: pointer;
            z-index: 1000;
            transition: all 0.3s;
            opacity: 0;
            visibility: hidden;
        `;
        
        document.body.appendChild(backBtn);
        
        // Back to top functionality
        backBtn.addEventListener('click', function() {
            window.scrollTo({
                top: 0,
                behavior: 'smooth'
            });
        });
        
        // Show/hide based on scroll position
        window.addEventListener('scroll', function() {
            if (window.pageYOffset > 300) {
                backBtn.style.opacity = '1';
                backBtn.style.visibility = 'visible';
            } else {
                backBtn.style.opacity = '0';
                backBtn.style.visibility = 'hidden';
            }
        });
        
        return backBtn;
    }
    
    /**
     * Set up all event listeners
     */
    function setupEventListeners() {
        // Search functionality
        searchBtn.addEventListener('click', performSearch);
        searchInput.addEventListener('keypress', function(e) {
            if (e.key === 'Enter') {
                performSearch();
            }
        });
        
        // Show recommendations button
        showRecommendationsBtn.addEventListener('click', function() {
            if (currentMovieId) {
                fetchRecommendations(currentMovieId);
                movieModal.hide();
                
                // Scroll to recommendations after a short delay
                setTimeout(() => {
                    recommendationsSection.scrollIntoView({ behavior: 'smooth', block: 'start' });
                }, 300);
            }
        });
        
        // Navbar filters
        allMoviesNav.addEventListener('click', function(e) {
            e.preventDefault();
            currentLanguage = null;
            updateActiveFilters();
            resultsTitle.textContent = 'All Movies';
            fetchRandomMovies(moviesPerPage);
        });
        
        hollywoodFilterNav.addEventListener('click', function(e) {
            e.preventDefault();
            currentLanguage = 'en';
            updateActiveFilters();
            resultsTitle.textContent = 'Hollywood Movies';
            fetchRandomMovies(moviesPerPage, 'en');
        });
        
        bollywoodFilterNav.addEventListener('click', function(e) {
            e.preventDefault();
            currentLanguage = 'hi';
            updateActiveFilters();
            resultsTitle.textContent = 'Bollywood Movies';
            fetchRandomMovies(moviesPerPage, 'hi');
        });
        
        // Button group filters
        filterAll.addEventListener('click', function() {
            currentLanguage = null;
            updateActiveFilters();
            resultsTitle.textContent = 'All Movies';
            fetchRandomMovies(moviesPerPage);
        });
        
        filterHollywood.addEventListener('click', function() {
            currentLanguage = 'en';
            updateActiveFilters();
            resultsTitle.textContent = 'Hollywood Movies';
            fetchRandomMovies(moviesPerPage, 'en');
        });
        
        filterBollywood.addEventListener('click', function() {
            currentLanguage = 'hi';
            updateActiveFilters();
            resultsTitle.textContent = 'Bollywood Movies';
            fetchRandomMovies(moviesPerPage, 'hi');
        });
        
        // Modal events
        document.getElementById('movieModal').addEventListener('hidden.bs.modal', function () {
            // When modal is closed, enable body scroll
            document.body.style.overflow = '';
        });
        
        document.getElementById('movieModal').addEventListener('show.bs.modal', function () {
            // When modal is opened, disable body scroll to prevent double scrollbars
            document.body.style.overflow = 'hidden';
        });
        
        // Handle infinite scroll for loading more movies
        window.addEventListener('scroll', handleScroll);
        
        // Handle resize events for responsive adjustments
        window.addEventListener('resize', debounce(function() {
            // Adjust UI elements if needed on resize
            if (window.innerWidth < 768) {
                // Mobile-specific adjustments
            } else {
                // Desktop-specific adjustments
            }
        }, 250));
    }
    
    /**
     * Debounce function to limit function call frequency
     */
    function debounce(func, delay) {
        let timeout;
        return function() {
            const context = this;
            const args = arguments;
            clearTimeout(timeout);
            timeout = setTimeout(() => func.apply(context, args), delay);
        };
    }
    
    /**
     * Handle scroll events for infinite loading
     */
    function handleScroll() {
        // Show/hide back to top button
        const backToTopBtn = document.getElementById('back-to-top');
        if (backToTopBtn) {
            if (window.pageYOffset > 300) {
                backToTopBtn.style.opacity = '1';
                backToTopBtn.style.visibility = 'visible';
            } else {
                backToTopBtn.style.opacity = '0';
                backToTopBtn.style.visibility = 'hidden';
            }
        }
        
        // Check if we should load more movies
        if (!isLoading && 
            window.innerHeight + window.pageYOffset >= document.body.offsetHeight - 500) {
            // Load more movies when approaching the bottom of the page
            loadMoreMovies();
        }
    }
    
    /**
     * Update active state on filter buttons
     */
    function updateActiveFilters() {
        // Update navbar filters
        allMoviesNav.classList.remove('active');
        hollywoodFilterNav.classList.remove('active');
        bollywoodFilterNav.classList.remove('active');
        
        // Update button group filters
        filterAll.classList.remove('active');
        filterHollywood.classList.remove('active');
        filterBollywood.classList.remove('active');
        
        if (currentLanguage === 'en') {
            hollywoodFilterNav.classList.add('active');
            filterHollywood.classList.add('active');
        } else if (currentLanguage === 'hi') {
            bollywoodFilterNav.classList.add('active');
            filterBollywood.classList.add('active');
        } else {
            allMoviesNav.classList.add('active');
            filterAll.classList.add('active');
        }
    }
    
    /**
     * Perform search based on input
     */
    function performSearch() {
        const query = searchInput.value.trim();
        
        // Don't search if query is empty
        if (!query) {
            showToast('Please enter a search term');
            return;
        }
        
        // Skip if same as last search
        if (query === lastSearchQuery) {
            return;
        }
        
        lastSearchQuery = query;
        resultsTitle.textContent = `Search Results for "${query}"`;
        showLoading(movieResults);
        
        // Reset pagination when starting a new search
        currentPage = 1;
        
        // Hide recommendations when searching
        recommendationsSection.style.display = 'none';
        
        fetch(`/api/search?query=${encodeURIComponent(query)}&limit=${moviesPerPage}&language=${currentLanguage || ''}&page=${currentPage}`)
            .then(handleResponse)
            .then(movies => {
                displayMovies(movies, movieResults, false);
                
                // Show no results message if needed
                if (!movies || movies.length === 0) {
                    showNoResults(movieResults, query);
                }
            })
            .catch(error => {
                console.error('Error searching movies:', error);
                showError(movieResults, 'Error searching movies. Please try again.');
            });
    }
    
    /**
     * Show a toast notification
     */
    function showToast(message, type = 'info') {
        // Check if toast container exists, create if not
        let toastContainer = document.querySelector('.toast-container');
        if (!toastContainer) {
            toastContainer = document.createElement('div');
            toastContainer.className = 'toast-container position-fixed bottom-0 end-0 p-3';
            document.body.appendChild(toastContainer);
        }
        
        // Create toast element
        const toastId = 'toast-' + Math.random().toString(36).substr(2, 9);
        const toast = document.createElement('div');
        toast.className = `toast align-items-center border-0 ${type === 'error' ? 'bg-danger' : 'bg-info'} text-white`;
        toast.setAttribute('role', 'alert');
        toast.setAttribute('aria-live', 'assertive');
        toast.setAttribute('aria-atomic', 'true');
        toast.id = toastId;
        
        toast.innerHTML = `
            <div class="d-flex">
                <div class="toast-body">
                    ${message}
                </div>
                <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast" aria-label="Close"></button>
            </div>
        `;
        
        toastContainer.appendChild(toast);
        
        // Initialize and show the toast
        const bsToast = new bootstrap.Toast(toast, {
            autohide: true,
            delay: 3000
        });
        
        bsToast.show();
        
        // Remove toast from DOM after it's hidden
        toast.addEventListener('hidden.bs.toast', function() {
            toast.remove();
        });
    }
    
    /**
     * Show no results message
     */
    function showNoResults(container, query) {
        container.innerHTML = `
            <div class="col-12 text-center py-5">
                <i class="fas fa-search text-muted" style="font-size: 3rem;"></i>
                <h4 class="mt-3">No movies found</h4>
                <p class="text-muted">We couldn't find any movies matching "${query}"</p>
                <button class="btn btn-primary mt-3" id="clear-search-results">
                    <i class="fas fa-home me-2"></i>Back to Featured Movies
                </button>
            </div>
        `;
        
        // Add click event to clear search button
        container.querySelector('#clear-search-results').addEventListener('click', function() {
            searchInput.value = '';
            const clearBtn = document.getElementById('clear-search');
            if (clearBtn) clearBtn.style.display = 'none';
            lastSearchQuery = '';
            resultsTitle.textContent = 'Featured Movies';
            fetchRandomMovies(moviesPerPage, currentLanguage);
        });
    }
    
    /**
     * Handle API response
     */
    function handleResponse(response) {
        if (!response.ok) {
            throw new Error(`Network response was not ok: ${response.status}`);
        }
        return response.json();
    }
    
    /**
     * Fetch random movies from API
     */
    function fetchRandomMovies(limit, language) {
        if (isLoading) return;
        
        isLoading = true;
        showLoading(movieResults);
        
        // Reset pagination when fetching new set of movies
        currentPage = 1;
        
        // Hide recommendations when loading random movies
        recommendationsSection.style.display = 'none';
        
        fetch(`/api/random?limit=${limit}&language=${language || ''}&page=${currentPage}`)
            .then(handleResponse)
            .then(movies => {
                displayMovies(movies, movieResults, false);
                isLoading = false;
            })
            .catch(error => {
                console.error('Error fetching random movies:', error);
                showError(movieResults, 'Error loading movies. Please try again.');
                isLoading = false;
            });
    }
    
    /**
     * Load more movies (pagination)
     */
    function loadMoreMovies() {
        // Don't load more if we're already loading
        if (isLoading) return;
        
        isLoading = true;
        
        // Create a loading indicator at the bottom
        const loadMoreIndicator = document.createElement('div');
        loadMoreIndicator.className = 'col-12 text-center py-3 load-more-indicator';
        loadMoreIndicator.innerHTML = `
            <div class="film-loader" style="width: 40px; height: 40px;">
                <div class="circle"></div>
            </div>
            <p class="mt-2 text-muted small">Loading more...</p>
        `;
        movieResults.appendChild(loadMoreIndicator);
        
        // Increment page number
        currentPage++;
        
        // Determine which API to call based on current view
        let apiUrl;
        const query = searchInput.value.trim();
        
        if (query) {
            // We're in search view
            apiUrl = `/api/search?query=${encodeURIComponent(query)}&limit=${moviesPerPage}&language=${currentLanguage || ''}&page=${currentPage}`;
        } else {
            // We're in random/browse view
            apiUrl = `/api/random?limit=${moviesPerPage}&language=${currentLanguage || ''}&page=${currentPage}`;
        }
        
        fetch(apiUrl)
            .then(handleResponse)
            .then(movies => {
                // Remove the loading indicator
                const indicator = document.querySelector('.load-more-indicator');
                if (indicator) {
                    indicator.remove();
                }
                
                if (movies && movies.length > 0) {
                    displayMovies(movies, movieResults, true);
                } else {
                    // No more movies to load, show "end of results" message
                    const endMessage = document.createElement('div');
                    endMessage.className = 'col-12 text-center py-3';
                    endMessage.innerHTML = `
                        <p class="text-muted">You've reached the end of the list</p>
                    `;
                    movieResults.appendChild(endMessage);
                }
                
                isLoading = false;
            })
            .catch(error => {
                console.error('Error loading more movies:', error);
                
                // Remove the loading indicator
                const indicator = document.querySelector('.load-more-indicator');
                if (indicator) {
                    indicator.remove();
                }
                
                // Show error at the bottom
                const errorMessage = document.createElement('div');
                errorMessage.className = 'col-12 text-center py-3';
                errorMessage.innerHTML = `
                    <p class="text-danger"><i class="fas fa-exclamation-circle me-2"></i>Failed to load more movies</p>
                    <button class="btn btn-sm btn-outline-danger retry-load-btn">Try Again</button>
                `;
                movieResults.appendChild(errorMessage);
                
                // Add retry button functionality
                errorMessage.querySelector('.retry-load-btn').addEventListener('click', function() {
                    errorMessage.remove();
                    loadMoreMovies();
                });
                
                isLoading = false;
            });
    }
    
    /**
     * Fetch recommendations for a specific movie
     */
    function fetchRecommendations(movieId) {
        showLoading(recommendationsContainer);
        recommendationsSection.style.display = 'block';
        
        fetch(`/api/recommend?movie_id=${movieId}&limit=8&language=${currentLanguage || ''}`)
            .then(handleResponse)
            .then(movies => {
                if (movies.error) {
                    showError(recommendationsContainer, movies.error);
                } else if (!movies || movies.length === 0) {
                    showError(recommendationsContainer, 'No recommendations found for this movie.');
                } else {
                    displayMovies(movies, recommendationsContainer, false);
                }
            })
            .catch(error => {
                console.error('Error fetching recommendations:', error);
                showError(recommendationsContainer, 'Error loading recommendations. Please try again.');
            });
    }
    
    /**
     * Show loading state in a container
     */
    function showLoading(container) {
        container.innerHTML = `
            <div class="col-12 text-center py-5">
                <div class="film-loader">
                    <div class="circle"></div>
                </div>
                <p class="mt-3 text-muted">Loading movies...</p>
            </div>
        `;
    }
    
    /**
     * Show error message in a container
     */
    function showError(container, message) {
        container.innerHTML = `
            <div class="col-12 text-center py-5">
                <i class="fas fa-exclamation-triangle text-warning" style="font-size: 3rem;"></i>
                <p class="mt-3 text-muted">${message}</p>
                <button class="btn btn-outline-primary mt-3 refresh-btn">
                    <i class="fas fa-sync-alt me-2"></i>Try Again
                </button>
            </div>
        `;
        
        // Add click event to refresh button
        container.querySelector('.refresh-btn').addEventListener('click', function() {
            if (container === movieResults) {
                fetchRandomMovies(moviesPerPage, currentLanguage);
            } else if (container === recommendationsContainer && currentMovieId) {
                fetchRecommendations(currentMovieId);
            }
        });
    }
    
    /**
     * Display movies in a container
     * @param {Array} movies - Array of movie objects
     * @param {Element} container - DOM element to display movies in
     * @param {Boolean} append - Whether to append to existing content
     */
    function displayMovies(movies, container, append = false) {
        if (!movies || movies.length === 0) {
            if (!append) {
                showError(container, 'No movies found. Try a different search or filter.');
            }
            return;
        }
        
        let html = '';
        
        movies.forEach(movie => {
            if (shownMovieIds.has(movie.id)) return; // Skip duplicates
            shownMovieIds.add(movie.id);


            const genres = movie.genres && movie.genres.length > 0 
                ? movie.genres.slice(0, 2).join(', ') 
                : 'Not specified';
                
            const releaseYear = movie.release_date 
                ? movie.release_date.substring(0, 4) 
                : 'Unknown';
            
            const languageBadge = movie.language === 'hi' 
                ? '<span class="language-badge badge-bollywood">Bollywood</span>' 
                : '<span class="language-badge badge-hollywood">Hollywood</span>';
            
            // Fix: Use proper TMDb image paths or fallback to placeholder
            const encodedTitle = encodeURIComponent(movie.title);
            const posterUrl = movie.poster_path 
                ? `https://image.tmdb.org/t/p/w300${movie.poster_path}` 
                : `https://via.placeholder.com/300x450/7209b7/ffffff?text=${encodedTitle}`;
            
            // Add rating badge if available
            const ratingBadge = movie.vote_average 
                ? `<span class="rating-badge">${movie.vote_average.toFixed(1)}</span>` 
                : '';
            
            html += `
                <div class="col-sm-6 col-md-4 col-lg-3 movie-item">
                    <div class="movie-card" data-movie-id="${movie.id}">
                        <div class="card-img-wrapper">
                            ${languageBadge}
                            ${ratingBadge}
                            <img src="${posterUrl}" class="movie-poster" alt="${movie.title}" loading="lazy">
                            <div class="movie-info">
                                <h5 class="movie-title">${movie.title}</h5>
                                <p class="movie-year-genre mb-0">${releaseYear} | ${genres}</p>
                            </div>
                            <div class="movie-hover">
                                <button class="view-details-btn">
                                    <i class="fas fa-info-circle me-2"></i>View Details
                                </button>
                            </div>
                        </div>
                    </div>
                </div>
            `;
        });
        
        if (append) {
            // Append to existing content
            const tempDiv = document.createElement('div');
            tempDiv.innerHTML = html;
            
            // Extract the movie items and append them one by one
            while (tempDiv.firstChild) {
                container.appendChild(tempDiv.firstChild);
            }
        } else {
            // Replace existing content
            container.innerHTML = html;
        }
        
        // Add click event to each movie card (including newly added ones)
        document.querySelectorAll('.movie-card').forEach(card => {
            card.addEventListener('click', function() {
                const movieId = this.getAttribute('data-movie-id');
                showMovieDetails(movieId);
            });
        });
        
        // Observe new cards for animations
        observeCards();
    }
    
    /**
     * Show movie details in modal
     */
    function showMovieDetails(movieId) {
        currentMovieId = movieId;
        
        const modalTitle = document.getElementById('movieModalTitle');
        const modalBody = document.getElementById('movieModalBody');
        
        // Show loading state
        modalTitle.textContent = 'Loading...';
        modalBody.innerHTML = `
            <div class="text-center py-4">
                <div class="film-loader">
                    <div class="circle"></div>
                </div>
                <p class="mt-3 text-muted">Loading details...</p>
            </div>
        `;
        
        // Open modal first for better UX
        movieModal.show();
        
        fetch(`/api/movie/${movieId}`)
            .then(handleResponse)
            .then(movie => {
                if (movie.error) {
                    modalBody.innerHTML = `
                        <div class="text-center py-4">
                            <i class="fas fa-exclamation-triangle text-warning" style="font-size: 3rem;"></i>
                            <p class="mt-3 text-muted">${movie.error}</p>
                        </div>
                    `;
                    return;
                }
                
                modalTitle.textContent = movie.title;
                
                // Format movie details
                const releaseYear = movie.release_date 
                    ? movie.release_date.substring(0, 4) 
                    : 'Unknown';
                    
                const genres = movie.genres && movie.genres.length > 0 
                    ? movie.genres.join(', ') 
                    : 'Not specified';
                    
                const directors = movie.directors && movie.directors.length > 0 
                    ? movie.directors.join(', ') 
                    : 'Not specified';
                    
                const cast = movie.cast && movie.cast.length > 0 
                    ? movie.cast.slice(0, 5).join(', ') 
                    : 'Not specified';
                    
                const runtime = movie.runtime 
                    ? `${movie.runtime} min` 
                    : 'Unknown';
                    
                const rating = movie.vote_average 
                    ? movie.vote_average.toFixed(1) 
                    : 'N/A';
                    
                // Generate rating stars
                let ratingStars = '';
                if (movie.vote_average) {
                    const starCount = Math.round(movie.vote_average / 2);
                    for (let i = 0; i < 5; i++) {
                        if (i < starCount) {
                            ratingStars += '<i class="fas fa-star"></i>';
                        } else {
                            ratingStars += '<i class="far fa-star"></i>';
                        }
                    }
                }
                
                // Fix: Use proper TMDb image path or fallback to placeholder
                const encodedTitle = encodeURIComponent(movie.title);
                const posterUrl = movie.poster_path 
                    ? `https://image.tmdb.org/t/p/w500${movie.poster_path}` 
                    : `https://via.placeholder.com/300x450/7209b7/ffffff?text=${encodedTitle}`;
                
                // Populate modal content
                modalBody.innerHTML = `
                    <div class="row">
                        <div class="col-md-4 mb-4 mb-md-0">
                            <div class="poster-container">
                                <img src="${posterUrl}" class="img-fluid movie-detail-img" alt="${movie.title}">
                                <div class="rating-badge-large">${rating}/10</div>
                            </div>
                            <div class="rating-stars mt-3">
                                ${ratingStars}
                            </div>
                            <div class="btn-group-vertical w-100 mt-3">
                                <button class="trailer-btn">
                                    <i class="fas fa-play-circle"></i> Watch Trailer
                                </button>
                                <button class="add-to-watchlist-btn mt-2">
                                    <i class="fas fa-bookmark"></i> Add to Watchlist
                                </button>
                            </div>
                        </div>
                        <div class="col-md-8">
                            <h4 class="movie-detail-title">${movie.title} <span class="text-muted">(${releaseYear})</span></h4>
                            
                            <div class="details-grid mt-3">
                                <div class="detail-item">
                                    <label>Genre</label>
                                    <span>${genres}</span>
                                </div>
                                <div class="detail-item">
                                    <label>Director</label>
                                    <span>${directors}</span>
                                </div>
                                <div class="detail-item">
                                    <label>Cast</label>
                                    <span>${cast}</span>
                                </div>
                                <div class="detail-item">
                                    <label>Runtime</label>
                                    <span>${runtime}</span>
                                </div>
                                <div class="detail-item">
                                    <label>Language</label>
                                    <span>${movie.language === 'hi' ? 'Hindi (Bollywood)' : 'English (Hollywood)'}</span>
                                </div>
                            </div>
                            
                            <div class="overview-section mt-4">
                                <h5 class="overview-title">Overview</h5>
                                <p>${movie.overview || 'No overview available for this movie.'}</p>
                            </div>
                            
                            <div class="share-section mt-4">
                                <h5 class="share-title">Share</h5>
                                <div class="social-buttons">
                                    <button class="social-btn facebook">
                                        <i class="fab fa-facebook-f"></i>
                                    </button>
                                    <button class="social-btn twitter">
                                        <i class="fab fa-twitter"></i>
                                    </button>
                                    <button class="social-btn instagram">
                                        <i class="fab fa-instagram"></i>
                                    </button>
                                    <button class="social-btn whatsapp">
                                        <i class="fab fa-whatsapp"></i>
                                    </button>
                                </div>
                            </div>
                        </div>
                    </div>
                `;
                
                // Add trailer button functionality
                // Add trailer button functionality
                const trailerBtn = modalBody.querySelector('.trailer-btn');
                trailerBtn.addEventListener('click', function() {
                    // Show trailer dialog
                    const trailerDialog = document.createElement('div');
                    trailerDialog.className = 'trailer-dialog';
                    trailerDialog.innerHTML = `
                        <div class="trailer-dialog-content">
                            <button class="close-trailer-btn">
                                <i class="fas fa-times"></i>
                            </button>
                            <div class="trailer-loading">
                                <div class="film-loader">
                                    <div class="circle"></div>
                                </div>
                                <p>Loading trailer...</p>
                            </div>
                            <div class="trailer-player" style="display: none;"></div>
                            <div class="trailer-error" style="display: none;">
                                <i class="fas fa-exclamation-triangle"></i>
                                <p>Trailer not available</p>
                            </div>
                        </div>
                    `;
                    
                    document.body.appendChild(trailerDialog);
                    
                    // Prevent body scrolling
                    document.body.style.overflow = 'hidden';
                    
                    // Close trailer on button click
                    trailerDialog.querySelector('.close-trailer-btn').addEventListener('click', function() {
                        trailerDialog.remove();
                        document.body.style.overflow = '';
                    });
                    
                    // Load trailer video
                    fetch(`/api/trailer/${movie.id}`)
                        .then(handleResponse)
                        .then(data => {
                            const loadingDiv = trailerDialog.querySelector('.trailer-loading');
                            const playerDiv = trailerDialog.querySelector('.trailer-player');
                            const errorDiv = trailerDialog.querySelector('.trailer-error');
                            
                            if (data.error || !data.key) {
                                loadingDiv.style.display = 'none';
                                errorDiv.style.display = 'flex';
                                return;
                            }
                            
                            // Set up YouTube embed
                            playerDiv.innerHTML = `
                                <iframe 
                                    width="100%" 
                                    height="100%" 
                                    src="https://www.youtube.com/embed/${data.key}?autoplay=1" 
                                    frameborder="0" 
                                    allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture" 
                                    allowfullscreen>
                                </iframe>
                            `;
                            
                            loadingDiv.style.display = 'none';
                            playerDiv.style.display = 'block';
                        })
                        .catch(error => {
                            console.error('Error loading trailer:', error);
                            const loadingDiv = trailerDialog.querySelector('.trailer-loading');
                            const errorDiv = trailerDialog.querySelector('.trailer-error');
                            
                            loadingDiv.style.display = 'none';
                            errorDiv.style.display = 'flex';
                        });
                });
                
                // Add watchlist button functionality
                const watchlistBtn = modalBody.querySelector('.add-to-watchlist-btn');
                watchlistBtn.addEventListener('click', function() {
                    // Check if movie is already in watchlist
                    const watchlist = JSON.parse(localStorage.getItem('watchlist') || '[]');
                    const isInWatchlist = watchlist.some(item => item.id === movie.id);
                    
                    if (isInWatchlist) {
                        // Remove from watchlist
                        const updatedWatchlist = watchlist.filter(item => item.id !== movie.id);
                        localStorage.setItem('watchlist', JSON.stringify(updatedWatchlist));
                        
                        // Update button
                        watchlistBtn.innerHTML = '<i class="fas fa-bookmark"></i> Add to Watchlist';
                        showToast('Removed from your watchlist', 'info');
                    } else {
                        // Add to watchlist
                        const movieToAdd = {
                            id: movie.id,
                            title: movie.title,
                            poster_path: movie.poster_path,
                            release_date: movie.release_date,
                            vote_average: movie.vote_average,
                            language: movie.language
                        };
                        
                        watchlist.push(movieToAdd);
                        localStorage.setItem('watchlist', JSON.stringify(watchlist));
                        
                        // Update button
                        watchlistBtn.innerHTML = '<i class="fas fa-check"></i> In Your Watchlist';
                        showToast('Added to your watchlist', 'info');
                    }
                });
                
                // Check if movie is in watchlist and update button
                const watchlist = JSON.parse(localStorage.getItem('watchlist') || '[]');
                const isInWatchlist = watchlist.some(item => item.id === movie.id);
                
                if (isInWatchlist) {
                    watchlistBtn.innerHTML = '<i class="fas fa-check"></i> In Your Watchlist';
                }
                
                // Add share buttons functionality
                const socialBtns = modalBody.querySelectorAll('.social-btn');
                socialBtns.forEach(btn => {
                    btn.addEventListener('click', function() {
                        const shareUrl = `https://nebulouscinema.com/movie/${movie.id}`;
                        const shareTitle = `Check out ${movie.title} on Nebulous Cinema`;
                        
                        let shareLink = '';
                        
                        if (btn.classList.contains('facebook')) {
                            shareLink = `https://www.facebook.com/sharer/sharer.php?u=${encodeURIComponent(shareUrl)}`;
                        } else if (btn.classList.contains('twitter')) {
                            shareLink = `https://twitter.com/intent/tweet?text=${encodeURIComponent(shareTitle)}&url=${encodeURIComponent(shareUrl)}`;
                        } else if (btn.classList.contains('instagram')) {
                            // Instagram doesn't support direct sharing links, show toast instead
                            showToast('Instagram sharing is not directly supported. Try copying the link!', 'info');
                            return;
                        } else if (btn.classList.contains('whatsapp')) {
                            shareLink = `https://api.whatsapp.com/send?text=${encodeURIComponent(shareTitle + ' ' + shareUrl)}`;
                        }
                        
                        if (shareLink) {
                            window.open(shareLink, '_blank', 'width=600,height=400');
                        }
                    });
                });
            })
            .catch(error => {
                console.error('Error loading movie details:', error);
                modalTitle.textContent = 'Error';
                modalBody.innerHTML = `
                    <div class="text-center py-4">
                        <i class="fas fa-exclamation-triangle text-warning" style="font-size: 3rem;"></i>
                        <p class="mt-3 text-muted">Error loading movie details. Please try again.</p>
                    </div>
                `;
            });
    }
    
    /**
     * Observe movie cards for animations
     */
    function observeCards() {
        // Use Intersection Observer to animate cards when they enter viewport
        const observer = new IntersectionObserver((entries) => {
            entries.forEach(entry => {
                if (entry.isIntersecting) {
                    entry.target.classList.add('visible');
                    observer.unobserve(entry.target);
                }
            });
        }, {
            threshold: 0.1
        });
        
        // Observe all movie cards
        document.querySelectorAll('.movie-card').forEach(card => {
            observer.observe(card);
        });
    }
});