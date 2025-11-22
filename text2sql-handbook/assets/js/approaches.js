// Approaches page functionality with filters and search

let allApproaches = [];
let filteredApproaches = [];
let currentFilters = {
  difficulty: 'all',
  techStack: 'all',
  llmModel: 'all',
  database: 'all'
};
let currentSort = 'recent';
let searchQuery = '';
let currentPage = 1;
const itemsPerPage = 10;

// Load approaches data
async function loadApproaches() {
  try {
    const response = await fetch('assets/data/approaches.json?v=5');
    const data = await response.json();
    allApproaches = data.approaches;
    filteredApproaches = [...allApproaches];
    renderApproaches();
  } catch (error) {
    console.error('Error loading approaches:', error);
    document.getElementById('approaches-grid').innerHTML =
      '<p class="text-center text-red-400 col-span-full">Error loading approaches. Please refresh the page.</p>';
  }
}

// Render approach cards
function renderApproaches() {
  const grid = document.getElementById('approaches-grid');
  const resultsCount = document.getElementById('results-count');

  if (filteredApproaches.length === 0) {
    grid.innerHTML = `
      <div class="col-span-full text-center py-12">
        <div class="text-6xl mb-4">🔍</div>
        <h3 class="text-2xl font-bold mb-4">No approaches found</h3>
        <p class="mb-6">Try adjusting your filters or search query</p>
        <button onclick="resetFilters()" class="btn-primary">Reset Filters</button>
      </div>
    `;
    if (resultsCount) {
      resultsCount.textContent = 'No results';
    }
    return;
  }

  if (resultsCount) {
    resultsCount.textContent = `${filteredApproaches.length} ${filteredApproaches.length === 1 ? 'approach' : 'approaches'}`;
  }

  // Pagination logic
  const totalPages = Math.ceil(filteredApproaches.length / itemsPerPage);
  const startIndex = (currentPage - 1) * itemsPerPage;
  const endIndex = startIndex + itemsPerPage;
  const currentItems = filteredApproaches.slice(startIndex, endIndex);

  const itemsHtml = currentItems.map(approach => {
    const difficultyClass = `difficulty-${approach.difficulty}`;

    // Format date
    const date = new Date(approach.datePublished);
    const formattedDate = date.toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' });

    return `
      <div class="flex flex-col md:flex-row gap-6 border-b border-gray-800 pb-8 last:border-0">
        <div class="flex-1 flex flex-col justify-center">
          <!-- Meta info -->
          <div class="flex items-center gap-2 mb-2 text-xs text-gray-400">
            <span class="font-medium text-gray-300">Muthu Kumaran</span>
            <span>·</span>
            <span>${formattedDate}</span>
            <span>·</span>
            <span>${approach.readTime}</span>
          </div>

          <a href="approaches/${approach.slug}.html" class="group block mb-3">
            <h2 class="text-xl md:text-2xl font-bold mb-2 group-hover:text-teal-400 transition-colors leading-tight">
              ${approach.title}
            </h2>
            <p class="text-gray-400 text-sm md:text-base line-clamp-2 leading-relaxed">
              ${approach.shortDescription}
            </p>
          </a>

          <div class="flex items-center justify-between mt-auto">
            <div class="flex items-center gap-3">
              <span class="px-2 py-1 text-xs font-medium rounded-md ${difficultyClass === 'difficulty-beginner' ? 'bg-green-900/30 text-green-300 border border-green-800' : difficultyClass === 'difficulty-intermediate' ? 'bg-blue-900/30 text-blue-300 border border-blue-800' : 'bg-purple-900/30 text-purple-300 border border-purple-800'}">
                ${approach.difficulty}
              </span>
              ${approach.tags.slice(0, 2).map(tag =>
      `<span class="hidden sm:inline-block px-2 py-1 text-xs rounded-md bg-gray-800 text-gray-400 border border-gray-700">${tag}</span>`
    ).join('')}
            </div>
            
            <div class="flex items-center gap-4 text-gray-500 text-sm">
              ${approach.github ? `
                <span class="flex items-center gap-1">
                  <svg class="w-4 h-4" fill="currentColor" viewBox="0 0 24 24"><path d="M12 0c-6.626 0-12 5.373-12 12 0 5.302 3.438 9.8 8.207 11.387.599.111.793-.261.793-.577v-2.234c-3.338.726-4.033-1.416-4.033-1.416-.546-1.387-1.333-1.756-1.333-1.756-1.089-.745.083-.729.083-.729 1.205.084 1.839 1.237 1.839 1.237 1.07 1.834 2.807 1.304 3.492.997.107-.775.418-1.305.762-1.604-2.665-.305-5.467-1.334-5.467-5.931 0-1.311.469-2.381 1.236-3.221-.124-.303-.535-1.524.117-3.176 0 0 1.008-.322 3.301 1.23.957-.266 1.983-.399 3.003-.404 1.02.005 2.047.138 3.006.404 2.291-1.552 3.297-1.23 3.297-1.23.653 1.653.242 2.874.118 3.176.77.84 1.235 1.911 1.235 3.221 0 4.609-2.807 5.624-5.479 5.921.43.372.823 1.102.823 2.222v3.293c0 .319.192.694.801.576 4.765-1.589 8.199-6.086 8.199-11.386 0-6.627-5.373-12-12-12z"/></svg>
                  ${approach.github.stars || 0}
                </span>
              ` : ''}
              <span class="flex items-center gap-1">
                <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 12h.01M12 12h.01M19 12h.01M6 12a1 1 0 11-2 0 1 1 0 012 0zm7 0a1 1 0 11-2 0 1 1 0 012 0zm7 0a1 1 0 11-2 0 1 1 0 012 0z"></path></svg>
              </span>
            </div>
          </div>
        </div>

        <a href="approaches/${approach.slug}.html" class="w-full md:w-48 h-32 flex-shrink-0 rounded-lg overflow-hidden relative group">
          ${approach.thumbnailImage
        ? `<img src="${approach.thumbnailImage}" alt="${approach.title}" class="w-full h-full object-cover transform group-hover:scale-105 transition-transform duration-500">`
        : `<div class="w-full h-full bg-gradient-to-br ${approach.thumbnailGradient} flex items-center justify-center text-4xl transform group-hover:scale-105 transition-transform duration-500">${approach.thumbnailIcon}</div>`
      }
        </a>
      </div>
    `;
  }).join('');

  grid.innerHTML = itemsHtml;

  // Render pagination
  renderPagination(totalPages);
}

function renderPagination(totalPages) {
  const grid = document.getElementById('approaches-grid');

  if (totalPages <= 1) return;

  const paginationHtml = `
    <div class="flex justify-center items-center gap-2 mt-8 pt-8 border-t border-gray-800">
      <button 
        onclick="changePage(${currentPage - 1})" 
        class="px-3 py-1 rounded-md text-sm font-medium ${currentPage === 1 ? 'text-gray-600 cursor-not-allowed' : 'text-gray-300 hover:bg-gray-800'}"
        ${currentPage === 1 ? 'disabled' : ''}
      >
        Previous
      </button>
      
      ${Array.from({ length: totalPages }, (_, i) => i + 1).map(page => `
        <button 
          onclick="changePage(${page})" 
          class="w-8 h-8 rounded-md text-sm font-medium flex items-center justify-center ${currentPage === page ? 'bg-primary-600 text-white bg-teal-600' : 'text-gray-300 hover:bg-gray-800'}"
        >
          ${page}
        </button>
      `).join('')}
      
      <button 
        onclick="changePage(${currentPage + 1})" 
        class="px-3 py-1 rounded-md text-sm font-medium ${currentPage === totalPages ? 'text-gray-600 cursor-not-allowed' : 'text-gray-300 hover:bg-gray-800'}"
        ${currentPage === totalPages ? 'disabled' : ''}
      >
        Next
      </button>
    </div>
  `;

  const paginationContainer = document.createElement('div');
  paginationContainer.innerHTML = paginationHtml;
  grid.appendChild(paginationContainer);
}

function changePage(page) {
  if (page < 1 || page > Math.ceil(filteredApproaches.length / itemsPerPage)) return;
  currentPage = page;
  renderApproaches();
  // Scroll to top of grid
  document.getElementById('approaches-grid').scrollIntoView({ behavior: 'smooth' });
}

// Filter approaches
function filterApproaches() {
  filteredApproaches = allApproaches.filter(approach => {
    // Difficulty filter
    if (currentFilters.difficulty !== 'all' && approach.difficulty !== currentFilters.difficulty) {
      return false;
    }

    // Tech stack filter
    if (currentFilters.techStack !== 'all') {
      const hasTag = approach.tags.some(tag =>
        tag.toLowerCase().includes(currentFilters.techStack.toLowerCase())
      );
      if (!hasTag) return false;
    }

    // LLM model filter
    if (currentFilters.llmModel !== 'all' && !approach.llmModel.toLowerCase().includes(currentFilters.llmModel.toLowerCase())) {
      return false;
    }

    // Database filter
    if (currentFilters.database !== 'all' && !approach.database.toLowerCase().includes(currentFilters.database.toLowerCase())) {
      return false;
    }

    // Search query
    if (searchQuery) {
      const searchLower = searchQuery.toLowerCase();
      const matchesSearch =
        approach.title.toLowerCase().includes(searchLower) ||
        approach.description.toLowerCase().includes(searchLower) ||
        approach.tags.some(tag => tag.toLowerCase().includes(searchLower)) ||
        approach.llmModel.toLowerCase().includes(searchLower) ||
        approach.database.toLowerCase().includes(searchLower);

      if (!matchesSearch) return false;
    }

    return true;
  });

  currentPage = 1; // Reset to first page on filter change
  sortApproaches();
  renderApproaches();
}

// Sort approaches
function sortApproaches() {
  switch (currentSort) {
    case 'recent':
      filteredApproaches.sort((a, b) => new Date(b.datePublished) - new Date(a.datePublished));
      break;
    case 'difficulty-easy':
      const difficultyOrder = { 'beginner': 1, 'intermediate': 2, 'advanced': 3 };
      filteredApproaches.sort((a, b) => difficultyOrder[a.difficulty] - difficultyOrder[b.difficulty]);
      break;
    case 'difficulty-hard':
      const difficultyOrderReverse = { 'beginner': 3, 'intermediate': 2, 'advanced': 1 };
      filteredApproaches.sort((a, b) => difficultyOrderReverse[a.difficulty] - difficultyOrderReverse[b.difficulty]);
      break;
    case 'alphabetical':
      filteredApproaches.sort((a, b) => a.title.localeCompare(b.title));
      break;
    case 'popular':
      filteredApproaches.sort((a, b) => b.github.stars - a.github.stars);
      break;
  }
}

// Setup filter event listeners
function setupFilters() {
  // Difficulty filters
  document.querySelectorAll('[data-filter-difficulty]').forEach(button => {
    button.addEventListener('click', () => {
      document.querySelectorAll('[data-filter-difficulty]').forEach(btn => btn.classList.remove('active'));
      button.classList.add('active');
      currentFilters.difficulty = button.dataset.filterDifficulty;
      filterApproaches();
    });
  });

  // Tech stack filters
  document.querySelectorAll('[data-filter-tech]').forEach(button => {
    button.addEventListener('click', () => {
      document.querySelectorAll('[data-filter-tech]').forEach(btn => btn.classList.remove('active'));
      button.classList.add('active');
      currentFilters.techStack = button.dataset.filterTech;
      filterApproaches();
    });
  });

  // LLM model filters
  document.querySelectorAll('[data-filter-llm]').forEach(button => {
    button.addEventListener('click', () => {
      document.querySelectorAll('[data-filter-llm]').forEach(btn => btn.classList.remove('active'));
      button.classList.add('active');
      currentFilters.llmModel = button.dataset.filterLlm;
      filterApproaches();
    });
  });

  // Database filters
  document.querySelectorAll('[data-filter-database]').forEach(button => {
    button.addEventListener('click', () => {
      document.querySelectorAll('[data-filter-database]').forEach(btn => btn.classList.remove('active'));
      button.classList.add('active');
      currentFilters.database = button.dataset.filterDatabase;
      filterApproaches();
    });
  });

  // Sort select
  const sortSelect = document.getElementById('sort-select');
  if (sortSelect) {
    sortSelect.addEventListener('change', (e) => {
      currentSort = e.target.value;
      sortApproaches();
      renderApproaches();
    });
  }

  // Search input
  const searchInput = document.getElementById('search-input');
  if (searchInput) {
    searchInput.addEventListener('input', (e) => {
      searchQuery = e.target.value;
      filterApproaches();
    });
  }
}

// Reset all filters
function resetFilters() {
  currentFilters = {
    difficulty: 'all',
    techStack: 'all',
    llmModel: 'all',
    database: 'all'
  };
  searchQuery = '';

  document.querySelectorAll('.filter-pill').forEach(pill => pill.classList.remove('active'));
  document.querySelectorAll('[data-filter-difficulty="all"]').forEach(btn => btn.classList.add('active'));
  document.querySelectorAll('[data-filter-tech="all"]').forEach(btn => btn.classList.add('active'));
  document.querySelectorAll('[data-filter-llm="all"]').forEach(btn => btn.classList.add('active'));
  document.querySelectorAll('[data-filter-database="all"]').forEach(btn => btn.classList.add('active'));

  const searchInput = document.getElementById('search-input');
  if (searchInput) searchInput.value = '';

  filterApproaches();
}

// Initialize when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
  loadApproaches();
  setupFilters();
});
