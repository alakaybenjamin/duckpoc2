// Global state
let searchTerms = [];
let currentPage = 1;
let currentCategory = 'clinical_study'; // Initial category setting
let isLoading = false;
let debounceTimer;

// Track if we're currently loading collections to prevent duplicate calls
let isLoadingCollections = false;
let lastCollectionsLoadTime = 0;
const COLLECTIONS_LOAD_DEBOUNCE = 2000; // 2 seconds

// Function to show error message
function showSearchError(message) {
    const errorDiv = document.createElement('div');
    errorDiv.className = 'alert alert-danger alert-dismissible fade show';
    errorDiv.innerHTML = `
        ${message}
        <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
    `;
    searchResults.innerHTML = '';
    searchResults.appendChild(errorDiv);
}

// CSRF token management
function getCsrfToken() {
    // First try to get it from meta tag
    const metaToken = document.querySelector('meta[name="csrf-token"]');
    if (metaToken) {
        return metaToken.content;
    }
    // If not in meta, try to get from session storage
    return sessionStorage.getItem('csrf_token');
}

// Add a function to refresh the CSRF token
async function refreshCsrfToken() {
    try {
        console.log('Attempting to refresh CSRF token...');
        const response = await fetch('/api/auth/csrf-token', { 
            method: 'GET',
            credentials: 'include'
        });
        
        if (!response.ok) {
            console.error('Failed to refresh CSRF token:', response.status);
            return false;
        }
        
        const data = await response.json();
        
        if (data.csrf_token) {
            console.log('Successfully refreshed CSRF token');
            // Store the token in sessionStorage
            sessionStorage.setItem('csrf_token', data.csrf_token);
            return true;
        } else {
            console.error('No CSRF token in response');
            return false;
        }
    } catch (error) {
        console.error('Error refreshing CSRF token:', error);
        return false;
    }
}

document.addEventListener('DOMContentLoaded', function() {
    console.log('Document loaded, initializing search functionality');
    
    // Refresh the CSRF token on page load
    refreshCsrfToken().then(() => {
        console.log('CSRF token refreshed on page load');
    }).catch(err => {
        console.error('Failed to refresh CSRF token on page load:', err);
    });

    // Store CSRF token in session storage for future requests
    const token = getCsrfToken();
    if (token) {
        sessionStorage.setItem('csrf_token', token);
    }

    const searchInput = document.getElementById('searchInput');
    const searchButton = document.getElementById('searchButton');
    const searchResults = document.getElementById('searchResults');
    const searchPills = document.getElementById('searchPills');
    const paginationContainer = document.getElementById('pagination');
    const suggestionsContainer = document.getElementById('suggestions');
    
    // Log important elements to debug
    console.log('Search input:', searchInput);
    console.log('Search button:', searchButton);
    console.log('Search results container:', searchResults);
    
    // Initialize search with any pre-populated input value
    if (searchInput && searchInput.value.trim()) {
        console.log('Initial search term found:', searchInput.value.trim());
        addSearchTerm(searchInput.value.trim());
    } else {
        // If no search terms, perform a blank search to show all results
        console.log('No initial search term, performing blank search');
        // Add a dummy term that will be removed immediately after
        searchTerms.push("*");
        performSearch();
        searchTerms = [];
    }

    // Add a new search term
    function addSearchTerm(term) {
        const trimmedTerm = term.trim();
        if (!trimmedTerm || searchTerms.includes(trimmedTerm)) return;

        if (searchTerms.length >= 3) {
            alert('Maximum 3 search terms allowed');
            return;
        }

        searchTerms.push(trimmedTerm);
        updateSearchPills();
        if (searchInput) {
            searchInput.value = '';
        }
        performSearch();
    }

    // Update the search pills display
    function updateSearchPills() {
        if (!searchPills) return;
        searchPills.innerHTML = searchTerms.map(term => `
            <div class="search-pill">
                ${term}
                <button type="button" class="btn-close btn-close-white" 
                        aria-label="Remove" onclick="removeSearchTerm('${term}')"></button>
            </div>
        `).join('');
    }

    // Remove a search term
    window.removeSearchTerm = function(term) {
        searchTerms = searchTerms.filter(t => t !== term);
        updateSearchPills();
        if (searchTerms.length > 0) {
            performSearch();
        } else {
            clearSearch();
        }
    };

    // Clear all search
    function clearSearch() {
        searchTerms = [];
        searchPills.innerHTML = '';
        searchResults.innerHTML = '';
        searchInput.value = '';
        if (paginationContainer) paginationContainer.innerHTML = '';
    }

    // Update the performSearch function to handle collection types correctly
    async function performSearch() {
        // Allow searching with no terms (to show all results)
        if (isLoading) return;

        try {
            isLoading = true;
            showLoading();
            
            // Refresh the CSRF token before making the request
            await refreshCsrfToken();
            
            console.log('Current search terms:', searchTerms);
            console.log('Current category:', currentCategory);

            // Get filter values
            const statusSelect = document.getElementById('statusFilter');
            const selectedStatuses = statusSelect ? Array.from(statusSelect.selectedOptions).map(opt => opt.value) : [];
            
            const filters = {
                status: selectedStatuses.length > 0 ? selectedStatuses : undefined,
                phase: document.getElementById('phaseFilter')?.value,
                drug: document.getElementById('drugFilter')?.value,
                start_date: document.getElementById('startDateFilter')?.value,
                end_date: document.getElementById('endDateFilter')?.value,
                indication_category: document.getElementById('indicationCategoryFilter')?.value,
                severity: document.getElementById('severityFilter')?.value,
                procedure_category: document.getElementById('procedureCategoryFilter')?.value,
                risk_level: document.getElementById('riskLevelFilter')?.value,
                duration: {
                    min: document.getElementById('minDurationFilter')?.value,
                    max: document.getElementById('maxDurationFilter')?.value
                }
            };

            // Remove empty filters
            Object.keys(filters).forEach(key => {
                if (!filters[key] || filters[key] === '') {
                    delete filters[key];
                }
            });

            // Use a sensible default query if no search terms
            const queryText = searchTerms.length > 0 ? searchTerms.join(' OR ') : "";
            
            // Build request body
            const requestBody = {
                query: queryText,
                collection_type: currentCategory,
                schema_type: currentCategory === 'clinical_study' ? 'clinical_study_custom' : 'default',
                page: currentPage,
                per_page: 10,
                filters: filters
            };

            console.log('Performing search with request:', requestBody);
            console.log('Category: ' + currentCategory);
            console.log('Schema type being sent:', requestBody.schema_type);
            
            // Get headers with CSRF token
            const csrfToken = getCsrfToken();
            console.log('Using CSRF token:', csrfToken);
            
            const headers = {
                'Content-Type': 'application/json',
                'X-CSRF-Token': csrfToken
            };
            
            // Add auth token if available
            const authToken = getAuthToken();
            if (authToken && authToken !== "server-authenticated") {
                headers['Authorization'] = `Bearer ${authToken}`;
            }

            // Make API request
            const response = await fetch('/api/search', {
                method: 'POST',
                headers: headers,
                body: JSON.stringify(requestBody),
                credentials: 'include' // Include cookies in the request
            });

            if (!response.ok) {
                // Log detailed error information
                console.error(`API error: ${response.status} ${response.statusText}`);
                
                try {
                    // Try to get error details from response
                    const errorData = await response.json();
                    console.error('Error details:', errorData);
                    
                    if (response.status === 403 && errorData.detail && errorData.detail.includes('CSRF')) {
                        console.log('CSRF token validation failed, attempting to refresh token...');
                        
                        // Try to refresh the CSRF token
                        const refreshed = await refreshCsrfToken();
                        if (refreshed) {
                            console.log('Token refreshed, retrying search...');
                            isLoading = false;
                            hideLoading();
                            // Try the search again with the new token
                            performSearch();
                            return;
                        } else {
                            throw new Error('CSRF validation failed. Please refresh the page and try again.');
                        }
                    } else if (response.status === 401) {
                        console.error('Authentication failed. Redirecting to login page.');
                        window.location.href = '/auth/login?next=' + encodeURIComponent(window.location.pathname);
                        return;
                    }
                    
                    throw new Error(errorData.detail || `API error: ${response.status}`);
                } catch (parseError) {
                    // If we can't parse the JSON response
                    throw new Error(`HTTP error! status: ${response.status}`);
                }
            }

            const data = await response.json();
            displayResults(data);
            updatePagination(data);

        } catch (error) {
            console.error('Search error:', error);
            showSearchError('An error occurred while searching. Please try again.');
        } finally {
            isLoading = false;
            hideLoading();
        }
    }

    // Show loading indicator
    function showLoading() {
        const loadingDiv = document.createElement('div');
        loadingDiv.id = 'searchLoading';
        loadingDiv.className = 'text-center my-4';
        loadingDiv.innerHTML = '<div class="spinner-border text-primary" role="status"><span class="visually-hidden">Loading...</span></div>';
        searchResults.innerHTML = '';
        searchResults.appendChild(loadingDiv);
    }

    // Hide loading indicator
    function hideLoading() {
        const loadingDiv = document.getElementById('searchLoading');
        if (loadingDiv) {
            loadingDiv.remove();
        }
    }

    // Update pagination
    function updatePagination(data) {
        if (!paginationContainer) return;

        const totalPages = Math.ceil(data.total / data.per_page);
        if (totalPages <= 1) {
            paginationContainer.innerHTML = '';
            return;
        }

        let paginationHtml = '<nav><ul class="pagination justify-content-center">';

        // Previous button
        paginationHtml += `
            <li class="page-item ${currentPage === 1 ? 'disabled' : ''}">
                <a class="page-link" href="#" data-page="${currentPage - 1}" aria-label="Previous">
                    <span aria-hidden="true">&laquo;</span>
                </a>
            </li>
        `;

        // Page numbers
        for (let i = 1; i <= totalPages; i++) {
            paginationHtml += `
                <li class="page-item ${i === currentPage ? 'active' : ''}">
                    <a class="page-link" href="#" data-page="${i}">${i}</a>
                </li>
            `;
        }

        // Next button
        paginationHtml += `
            <li class="page-item ${currentPage === totalPages ? 'disabled' : ''}">
                <a class="page-link" href="#" data-page="${currentPage + 1}" aria-label="Next">
                    <span aria-hidden="true">&raquo;</span>
                </a>
            </li>
        `;

        paginationHtml += '</ul></nav>';
        paginationContainer.innerHTML = paginationHtml;

        // Add click handlers for pagination
        paginationContainer.querySelectorAll('.page-link').forEach(link => {
            link.addEventListener('click', (e) => {
                e.preventDefault();
                const newPage = parseInt(e.target.closest('.page-link').dataset.page);
                if (newPage !== currentPage) {
                    currentPage = newPage;
                    performSearch();
                }
            });
        });
    }

    // Event listeners
    searchButton?.addEventListener('click', () => {
        const term = searchInput?.value;
        if (term) addSearchTerm(term);
    });

    searchInput?.addEventListener('keypress', (e) => {
        if (e.key === 'Enter') {
            e.preventDefault();
            const term = searchInput?.value;
            if (term) addSearchTerm(term);
        }
    });

    // Initialize filters
    const filterIds = [
        'statusFilter', 'phaseFilter', 'startDateFilter', 'endDateFilter',
        'indicationCategoryFilter', 'severityFilter', 'procedureCategoryFilter',
        'riskLevelFilter', 'minDurationFilter', 'maxDurationFilter'
    ];

    filterIds.forEach(filterId => {
        const element = document.getElementById(filterId);
        if (element) {
            element.addEventListener('change', () => {
                if (searchTerms.length > 0) {
                    performSearch();
                }
            });
        }
    });

    // Display results
    function displayResults(data) {
        const resultsContainer = document.getElementById('searchResults');
        if (!resultsContainer) return;
        
        console.log('Displaying search results:', data);
        console.log('Raw data structure:', JSON.stringify(data));
        console.log('Has study_details?', data.results && data.results[0] && 'study_details' in data.results[0]);
        hideLoading();
        
        if (!data || !data.results || data.results.length === 0) {
            resultsContainer.innerHTML = '<div class="alert alert-info">No results found. Try a different search term or adjust your filters.</div>';
            const paginationContainer = document.getElementById('pagination');
            if (paginationContainer) {
                paginationContainer.innerHTML = '';
            }
            return;
        }
        
        // Check if we're using the new format with pagination inside the pagination object
        const paginationData = data.pagination || data;
        
        // Update the pagination UI
        updatePagination({
            total: paginationData.total,
            page: paginationData.page,
            per_page: paginationData.per_page
        });

        // Generate HTML for each search result
        const resultsHTML = data.results.map(result => {
            let dataProductsHtml = '';
            
            // Display data products if available
            if (result.data_products && result.data_products.length > 0) {
                const dpItems = result.data_products.map(dp => `
                    <div class="data-product-item p-2 mb-2 border-start border-4 border-info rounded bg-light">
                        <div class="d-flex justify-content-between align-items-start">
                            <div>
                                <h6 class="mb-1">${dp.title}</h6>
                                <p class="small mb-1">${dp.description || 'No description available'}</p>
                            </div>
                            <span class="badge bg-info text-dark">${dp.type}</span>
                        </div>
                        <div class="small text-muted mt-1">
                            Format: ${dp.format || 'N/A'} | 
                            Size: ${dp.size || 'N/A'} | 
                            Access: ${dp.access_level || 'Public'}
                        </div>
                    </div>
                `).join('');
                
                dataProductsHtml = `
                    <div class="data-products mt-3">
                        <h6 class="text-muted mb-2">Associated Data Products</h6>
                        ${dpItems}
                    </div>
                `;
            }
            
            // Check if we're using the new format with study_details
            const studyDetails = result.study_details || (result.data || {});
            const resultType = result.type || (currentCategory || "unknown");
            
            return `
            <div class="search-result-item mb-4 p-3 border rounded bg-light">
                <h4 class="mb-2">${result.title}</h4>
                <div class="result-metadata mb-2">
                    <span class="badge bg-primary me-2">${resultType}</span>
                    ${studyDetails.phase ? `<span class="badge bg-secondary me-2">Phase: ${studyDetails.phase}</span>` : ''}
                    ${studyDetails.status ? `<span class="badge bg-info me-2">Status: ${studyDetails.status}</span>` : ''}
                    ${studyDetails.drug ? `<span class="badge bg-dark me-2">Drug: ${studyDetails.drug}</span>` : ''}
                    ${studyDetails.indication_category ? `<span class="badge bg-success me-2">Category: ${studyDetails.indication_category}</span>` : ''}
                    ${studyDetails.risk_level ? `<span class="badge bg-warning text-dark me-2">Risk: ${studyDetails.risk_level}</span>` : ''}
                    ${studyDetails.severity ? `<span class="badge bg-danger me-2">Severity: ${studyDetails.severity}</span>` : ''}
                </div>
                ${result.description ? `<p class="result-description mb-2">${result.description}</p>` : ''}
                <div class="study-details mt-2">
                    <small class="text-muted">
                        ${studyDetails.institution ? `Institution: ${studyDetails.institution}<br>` : ''}
                        ${studyDetails.participant_count ? `Participants: ${studyDetails.participant_count}<br>` : ''}
                        ${studyDetails.start_date ? `Start Date: ${new Date(studyDetails.start_date).toLocaleDateString()}<br>` : ''}
                        ${studyDetails.end_date ? `End Date: ${new Date(studyDetails.end_date).toLocaleDateString()}<br>` : ''}
                        ${studyDetails.duration ? `Duration: ${studyDetails.duration} days<br>` : ''}
                        ${studyDetails.procedure_category ? `Procedure: ${studyDetails.procedure_category}` : ''}
                    </small>
                </div>
                ${dataProductsHtml}
            </div>
            `;
        }).join('');
        
        resultsContainer.innerHTML = resultsHTML;
    }

    function updateSelectedItemsList() {
        const selectedItemsList = document.getElementById('selectedItemsList');
        if (!selectedItemsList) return;

        const checkedProducts = document.querySelectorAll('.form-check-input:checked');
        const items = Array.from(checkedProducts).map(checkbox => {
            const label = checkbox.closest('.data-product-item').querySelector('.form-check-label').textContent.trim();
            return `<div class="selected-item">${label}</div>`;
        });

        selectedItemsList.innerHTML = items.length > 0
            ? items.join('')
            : '<p class="text-muted">No items selected</p>';
    }

    function updateMenuVisibility() {
        const actionsMenu = document.querySelector('.actions-menu');
        if (actionsMenu) {
            const hasCheckedItems = document.querySelectorAll('.form-check-input:checked').length > 0;
            actionsMenu.classList.toggle('d-none', !hasCheckedItems);
        }
    }

    // Suggestion Handling (from original code)
    function debounceSearch() {
        clearTimeout(debounceTimer);
        const query = searchInput?.value.trim();

        if (query.length < 2) {
            if (suggestionsContainer) {
                suggestionsContainer.style.display = 'none';
            }
            return;
        }

        debounceTimer = setTimeout(() => fetchSuggestions(query), 300);
    }

    // Update the fetchSuggestions function
    async function fetchSuggestions(query) {
        if (!query || query.length < 2 || !suggestionsContainer) return;

        try {
            // Use scientific_paper as default collection type
            const searchType = currentCategory === 'all' ? 'scientific_paper' : currentCategory;
            
            console.log(`Fetching suggestions for "${query}" with type ${searchType}`);
            
            // Get CSRF token
            const csrfToken = getCsrfToken();
            
            // Build URL with proper encoding
            const url = `/api/suggest?q=${encodeURIComponent(query)}&collection_type=${encodeURIComponent(searchType)}`;
            
            // Set up headers with CSRF token
            const headers = {
                'X-CSRF-Token': csrfToken
            };
            
            // Add auth token if available
            const authToken = getAuthToken();
            if (authToken && authToken !== "server-authenticated") {
                headers['Authorization'] = `Bearer ${authToken}`;
            }

            const response = await fetch(url, {
                headers: headers,
                credentials: 'include'
            });

            if (!response.ok) {
                console.error(`Error fetching suggestions: ${response.status} ${response.statusText}`);
                const errorText = await response.text();
                console.error(`Error details: ${errorText}`);
                throw new Error(`Error ${response.status}: ${response.statusText}`);
            }

            const data = await response.json();
            console.log('Suggestions data:', data);
            
            if (data.suggestions && data.suggestions.length > 0) {
                displaySuggestions(data.suggestions);
            } else {
                suggestionsContainer.style.display = 'none';
            }
        } catch (error) {
            console.error('Error fetching suggestions:', error);
            suggestionsContainer.style.display = 'none';
        }
    }

    function displaySuggestions(suggestions) {
        if (!suggestionsContainer || !searchInput) return;

        suggestionsContainer.innerHTML = '';
        suggestions.forEach(suggestion => {
            const div = document.createElement('div');
            div.className = 'suggestion-item';
            div.innerHTML = `
                <span class="suggestion-text">${suggestion.text}</span>
                <span class="suggestion-type">${suggestion.type}</span>
            `;

            div.addEventListener('click', () => {
                if (searchInput) {
                    searchInput.value = suggestion.text;
                    suggestionsContainer.style.display = 'none';
                    performSearch();
                }
            });

            suggestionsContainer.appendChild(div);
        });

        suggestionsContainer.style.display = 'block';
    }

    function showError(message) {
        const errorDiv = document.createElement('div');
        errorDiv.className = 'alert alert-danger alert-dismissible fade show';
        errorDiv.innerHTML = `${message} <button type="button" class="btn-close" data-bs-dismiss="alert"></button>`;
        document.querySelector('.search-container').insertBefore(errorDiv, searchResults);
        setTimeout(() => {
            errorDiv.remove();
        }, 5000);
    }

    function showSuccess(message) {
        const successDiv = document.createElement('div');
        successDiv.className = 'alert alert-success alert-dismissible fade show';
        successDiv.innerHTML = `${message} <button type="button" class="btn-close" data-bs-dismiss="alert"></button>`;
        document.querySelector('.search-container').insertBefore(successDiv, searchResults);
        setTimeout(() => {
            successDiv.remove();
        }, 5000);
    }

    window.addToCollection = addToCollection;

    // Initialize category selection
    const categoryButtons = document.querySelectorAll('.category-btn');
    categoryButtons.forEach(button => {
        button.addEventListener('click', () => {
            categoryButtons.forEach(btn => btn.classList.remove('active'));
            button.classList.add('active');
            currentCategory = button.getAttribute('data-category');
            if (searchInput.value.trim()) {
                performSearch();
            }
        });
    });

    // Create search actions menu
    const searchContainer = document.querySelector('.search-container');
    if (searchContainer) {
        // Add menu before search results
        const actionsMenu = document.createElement('div');
        actionsMenu.className = 'search-actions-menu mt-3 mb-3 d-none actions-menu';
        actionsMenu.innerHTML = `
            <div class="d-flex justify-content-end">
                <div class="dropdown">
                    <button class="btn btn-primary dropdown-toggle" type="button" data-bs-toggle="dropdown" aria-expanded="false">
                        Actions
                    </button>
                    <ul class="dropdown-menu dropdown-menu-end">
                        <li><a class="dropdown-item" href="#" id="addToCollectionMenuItem">
                            <i class="bi bi-plus-circle me-2"></i>Add to Collection
                        </a></li>
                    </ul>
                </div>
            </div>
        `;

        // Insert menu after search box but before results
        const searchBox = searchContainer.querySelector('.search-box-container') || searchContainer.firstChild;
        searchBox.parentNode.insertBefore(actionsMenu, searchBox.nextSibling);

        // Add collection modal
        const modalHtml = `
            <div class="modal fade" id="collectionModal" tabindex="-1">
                <div class="modal-dialog">
                    <div class="modal-content">
                        <div class="modal-header">
                            <h5 class="modal-title">Add to Collection</h5>
                            <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
                        </div>
                        <div class="modal-body">
                            <div id="selectedItems" class="mb-3">
                                <h6>Selected Items:</h6>
                                <div id="selectedItemsList" class="border rounded p-2"></div>
                            </div>
                            <div class="collections-section">
                                <h6>Choose Collection:</h6>
                                <div id="collectionsListContainer" class="border rounded p-2"></div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        `;
        document.body.insertAdjacentHTML('beforeend', modalHtml);
    }

    // Reset filters
    document.getElementById('resetFilters')?.addEventListener('click', function() {
        // Reset filter form elements
        const statusSelect = document.getElementById('statusFilter');
        if (statusSelect) {
            // Deselect all options for multiselect
            for (let option of statusSelect.options) {
                option.selected = false;
            }
        }
        
        document.getElementById('phaseFilter')?.value = '';
        document.getElementById('drugFilter')?.value = ''; // Added drug filter reset
        document.getElementById('startDateFilter')?.value = '';
        document.getElementById('endDateFilter')?.value = '';
        document.getElementById('indicationCategoryFilter')?.value = '';
        document.getElementById('severityFilter')?.value = '';
        document.getElementById('procedureCategoryFilter')?.value = '';
        document.getElementById('riskLevelFilter')?.value = '';
        document.getElementById('minDurationFilter')?.value = '';
        document.getElementById('maxDurationFilter')?.value = '';
        
        // Reset pagination to page 1
        currentPage = 1;
        performSearch();
    });

    function updateVisibleFilters(category) { //Updated function
        // Show all filter sections by default
        document.getElementById('studyFilters').style.display = 'block';
        document.getElementById('indicationFilters').style.display = 'block';
        document.getElementById('procedureFilters').style.display = 'block';

        // Highlight the appropriate category button
        const categoryButtons = document.querySelectorAll('.category-btn');
        categoryButtons.forEach(btn => {
            btn.classList.toggle('active', btn.getAttribute('data-category') === category);
        });
    }
    // Initialize
    updateVisibleFilters(currentCategory);
    setInitialFiltersFromURL();

    // Add event listener for save button
    document.getElementById('saveSearchButton')?.addEventListener('click', saveCurrentSearch);

    function setInitialFiltersFromURL() {
        const urlParams = new URLSearchParams(window.location.search);

        // Set search query if present
        const query = urlParams.get('q');
        if (query) {
            // Add the query term to searchTerms array
            addSearchTerm(query);
        }

        // Set the correct category based on the current page URL
        if (window.location.pathname.includes('scientific-papers')) {
            currentCategory = 'scientific_paper';
            // Update UI to show the correct category
            const categoryButtons = document.querySelectorAll('.category-btn');
            categoryButtons.forEach(btn => {
                btn.classList.toggle('active', btn.getAttribute('data-category') === 'scientific_paper');
            });
        }

        // If we have a query, perform the search
        if (query && searchInput) {
            searchInput.value = query;
            performSearch();
        }
    }

    function getAuthToken() {
        // Check if we're already on a server-authenticated page
        // If the user is viewing this page, they must be authenticated server-side
        // This prevents unnecessary redirects
        const isServerAuthenticated = document.body.getAttribute('data-authenticated') === 'true';
        if (isServerAuthenticated) {
            return "server-authenticated"; // Dummy token to indicate server-side auth
        }
        return localStorage.getItem('auth_token');
    }

    // Function to fetch the JWT token from the server
    async function fetchTokenFromServer() {
        try {
            const response = await fetch('/auth/get-token', {
                method: 'GET',
                headers: {
                    'Accept': 'application/json',
                    'X-CSRF-Token': getCsrfToken()
                },
                credentials: 'include' // Include cookies
            });
            
            if (response.ok) {
                const data = await response.json();
                if (data.token) {
                    // Save token to localStorage for future API requests
                    localStorage.setItem('auth_token', data.token);
                    console.log('Token fetched from server and saved');
                    return data.token;
                }
            }
            return null;
        } catch (error) {
            console.error('Error fetching token:', error);
            return null;
        }
    }
    
    // Function to ensure we have a valid auth token, fetching from server if needed
    async function ensureAuthToken() {
        let token = getAuthToken();
        if (!token || token === "server-authenticated") {
            // Try to fetch from server
            token = await fetchTokenFromServer();
            if (token) {
                return token;
            }
            // Fallback to redirecting to login
            window.location.href = '/auth/login?next=' + encodeURIComponent(window.location.pathname);
            return null;
        }
        return token;
    }

    // Get standard headers for API requests
    function getHeaders() {
        // Get the latest CSRF token
        const csrfToken = getCsrfToken();
        
        console.log('Including CSRF token in request headers:', csrfToken);
        
        const headers = {
            'Content-Type': 'application/json',
            'X-CSRF-Token': csrfToken
        };
        
        const token = getAuthToken();
        
        // Only add Authorization header if there's a real token (not server-authenticated)
        if (token && token !== "server-authenticated") {
            headers['Authorization'] = `Bearer ${token}`;
            console.log('Including Bearer token in request headers');
        }
        
        return headers;
    }

    // Check if user is authenticated, if not redirect to login
    function checkAuthentication(returnPath = window.location.pathname) {
        // If we're already server-authenticated, no need to redirect
        const isServerAuthenticated = document.body.getAttribute('data-authenticated') === 'true';
        if (isServerAuthenticated) {
            return true; // Already authenticated
        }
        
        // Check for client-side token
        const token = localStorage.getItem('auth_token');
        if (!token) {
            window.location.href = '/auth/login?next=' + encodeURIComponent(returnPath);
            return false;
        }
        
        return true; // Has token
    }

    async function saveCurrentSearch() {
        if (!checkAuthentication()) return;
        
        const query = searchInput.value.trim();
        try {
            const response = await fetch('/api/search-history', {
                method: 'POST',
                headers: getHeaders(),
                body: JSON.stringify({
                    query: query,
                    category: currentCategory,
                    results_count: document.querySelectorAll('.search-result-item').length,
                    is_saved: true
                })
            });

            if (!response.ok) {
                if (response.status === 401) {
                    window.location.href = '/auth/login?next=' + encodeURIComponent(window.location.pathname);
                    return;
                }
                throw new Error(`HTTP error! status: ${response.status}`);
            }

            const data = await response.json();
            if (data.success) {
                const alertDiv = document.createElement('div');
                alertDiv.className = 'alert alert-success alert-dismissible fade show';
                alertDiv.innerHTML = `
                    Search saved successfully!
                    <a href="/saved-searches">View Saved Searches</a>
                    <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
                `;
                document.querySelector('.search-container').insertBefore(alertDiv, document.querySelector('.search-box-container'));

                setTimeout(() => {
                    alertDiv.remove();
                }, 5000);
            }
        } catch (error) {
            console.error('Error saving search:', error);
            alert('Failed to save search. Please try again.');
        }
    }

    window.showCreateCollectionForm = function() {
        document.getElementById('collectionsListView').style.display = 'none';
        document.getElementById('createCollectionForm').style.display = 'block';
    };

    window.showCollectionsList = function() {
        document.getElementById('createCollectionForm').style.display = 'none';
        document.getElementById('collectionsListView').style.display = 'block';
    };

    window.createNewCollection = async function(event) {
        event.preventDefault();

        if (!checkAuthentication('/collections')) return;

        const title = document.getElementById('collectionTitle').value.trim();
        const description = document.getElementById('collectionDescription').value.trim();

        if (!title) {
            showError('Title is required');
            return;
        }

        try {
            const response = await fetch('/api/collections', {
                method: 'POST',
                headers: getHeaders(),
                body: JSON.stringify({
                    title: title,
                    description: description || null
                })
            });

            if (!response.ok) {
                const error = await response.json();
                throw new Error(error.detail || 'Failed to create collection');
            }

            const collection = await response.json();

            // Reset form
            document.getElementById('collectionTitle').value = '';
            document.getElementById('collectionDescription').value = '';

            // Close the modal
            const modal = bootstrap.Modal.getInstance(document.getElementById('collectionModal'));
            if (modal) {
                modal.hide();
            }

            // Show success message
            showSuccess('Collection created successfully');

            // Reload collections list
            setTimeout(() => {
                loadCollections();
                showCollectionsList();
            }, 500);

        } catch (error) {
            console.error('Error creating collection:', error);
            showError(error.message || 'Failed to create collection. Please try again.');
        }
    };

    const collectionModal = `
        <div class="modal fade" id="collectionModal" tabindex="-1" aria-labelledby="collectionModalLabel" aria-hidden="true">
            <div class="modal-dialog">
                <div class="modal-content">
                    <div class="modal-header">
                        <h5 class="modal-title" id="collectionModalLabel">Add to Collection</h5>
                        <button type="button" class="btn-close" data-bs-dismiss="modal" aria-label="Close"></button>
                    </div><div class="modal-body">
                        <!-- Collections List View -->
                        <div id="collectionsListView">
                            <div id="collectionsListContainer">
                                Loading collections...
                            </div>
                            <div class="mt-3">
                                <button type="button" class="btn btn-primary" onclick="window.showCreateCollectionForm()">
                                    Create New Collection
                                </button>
                            </div>
                        </div>

                        <!-- Create Collection Form -->
                        <div id="createCollectionForm" style="display: none;">
                            <form onsubmit="window.createNewCollection(event)">
                                <div class="mb-3">
                                    <label for="collectionTitle" class="form-label">Collection Title</label>
                                    <input type="text" class="form-control" id="collectionTitle" required>
                                </div>
                                <div class="mb-3">
                                    <label for="collectionDescription" class="form-label">Description</label>
                                    <textarea class="form-control" id="collectionDescription" rows="3"></textarea>
                                </div>
                                <div class="d-flex justify-content-between">
                                    <button type="button" class="btn btn-secondary" onclick="window.showCollectionsList()">
                                        Back to Collections
                                    </button>
                                    <button type="submit" class="btn btn-primary">Create Collection</button>
                                </div>
                            </form>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    `;

    // Remove any existing modal
    const existingModal = document.getElementById('collectionModal');
    if (existingModal) {
        existingModal.remove();
    }

    // Add the updated modal
    document.body.insertAdjacentHTML('beforeend', collectionModal);

    // Add event handler for "Add to Collection" menu item
    document.getElementById('addToCollectionMenuItem')?.addEventListener('click', () => {
        const modal = new bootstrap.Modal(document.getElementById('collectionModal'));
        loadCollections();
        updateSelectedItemsList();
        modal.show();
    });

    async function loadCollections() {
        // Debounce collections loading
        const now = Date.now();
        if (isLoadingCollections || (now - lastCollectionsLoadTime < COLLECTIONS_LOAD_DEBOUNCE)) {
            console.log('Preventing duplicate loadCollections call');
            return;
        }
        
        isLoadingCollections = true;
        
        if (!checkAuthentication('/collections')) {
            isLoadingCollections = false;
            return;
        }

        try {
            // Update the timestamp
            lastCollectionsLoadTime = Date.now();
            
            const response = await fetch('/api/collections', {
                method: 'GET',
                headers: getHeaders()
            });

            if (!response.ok) {
                if (response.status === 401 && document.body.getAttribute('data-authenticated') !== 'true') {
                    // Only redirect if we're not already server-authenticated
                    window.location.href = '/auth/login?next=/collections';
                    isLoadingCollections = false;
                    return;
                }
                throw new Error(`HTTP error! status: ${response.status}`);
            }

            const collections = await response.json();
            const container = document.getElementById('collectionsListContainer');
            if (!container) {
                isLoadingCollections = false;
                return;
            }

            if (collections.length === 0) {
                container.innerHTML = '<p>No collections yet. Create your first collection.</p>';
            } else {
                container.innerHTML = collections.map(collection => `
                    <div class="collection-option mb-2">
                        <button class="btn btn-outline-secondary w-100 text-start"
                                onclick="addToCollection(${collection.id})">
                            ${collection.title}
                            <small class="d-block text-muted">${collection.description || ''}</small>
                        </button>
                    </div>
                `).join('');
            }
        } catch (error) {
            console.error('Error loading collections:', error);
            const container = document.getElementById('collectionsListContainer');
            if (container) {
                container.innerHTML = '<p class="text-danger">Error loading collections. Please try again.</p>';
            }
        } finally {
            isLoadingCollections = false;
        }
    }

    // Make loadCollections available globally
    window.loadCollections = loadCollections;

    async function addToCollection(collectionId) {
        if (!checkAuthentication('/collections')) return;
        
        const selectedIds = Array.from(document.querySelectorAll('input[name="selectedItems"]:checked'))
            .map(el => el.value);
        
        if (selectedIds.length === 0) {
            showError('No items selected to add to collection');
            return;
        }
        
        try {
            const response = await fetch(`/api/collections/${collectionId}/items`, {
                method: 'POST',
                headers: getHeaders(),
                body: JSON.stringify({ item_ids: selectedIds })
            });
            
            if (!response.ok) {
                throw new Error('Failed to add items to collection');
            }
            
            // Show success message
            showSuccess('Items added to collection successfully');
            
            // Clear checkboxes
            document.querySelectorAll('input[name="selectedItems"]').forEach(el => {
                el.checked = false;
            });
        } catch (error) {
            console.error('Error adding to collection:', error);
            showError('Failed to add items to collection');
        }
    }
    searchInput?.addEventListener('input',debounceSearch);

    // Function to populate dynamic filter options
    async function populateDynamicFilters() {
        try {
            // Only do this for clinical studies page
            if (currentCategory !== 'clinical_study') return;
            
            // Fetch available filters
            const response = await fetch('/api/filters?collection_type=clinical_study', {
                method: 'GET',
                headers: getHeaders()
            });
            
            if (!response.ok) {
                console.error('Failed to fetch filters');
                return;
            }
            
            const filtersData = await response.json();
            
            // Populate drug filter if it exists
            if (filtersData.drug && Array.isArray(filtersData.drug)) {
                const drugFilter = document.getElementById('drugFilter');
                if (drugFilter) {
                    // Clear existing options except the "All" option
                    while (drugFilter.options.length > 1) {
                        drugFilter.remove(1);
                    }
                    
                    // Add new options
                    filtersData.drug.forEach(drug => {
                        if (drug) { // Only add non-empty values
                            const option = document.createElement('option');
                            option.value = drug;
                            option.textContent = drug;
                            drugFilter.appendChild(option);
                        }
                    });
                }
            }
        } catch (error) {
            console.error('Error populating filters:', error);
        }
    }

    // Apply all filters when form is submitted
    document.getElementById('applyFilters')?.addEventListener('click', function() {
        // Reset pagination to page 1 when applying new filters
        currentPage = 1;
        performSearch();
    });

    // Call populateDynamicFilters when the page loads
    if (document.getElementById('drugFilter')) {
        // This is the clinical studies page
        populateDynamicFilters();
    }
});