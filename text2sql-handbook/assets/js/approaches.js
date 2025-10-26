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

// Load approaches data
async function loadApproaches() {
  try {
    const response = await fetch('assets/data/approaches.json');
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

  grid.innerHTML = filteredApproaches.map(approach => {
    const difficultyClass = `difficulty-${approach.difficulty}`;
    const featuredClass = approach.featured ? 'featured' : '';

    return `
      <a href="approaches/${approach.slug}.html" class="card group relative transition-all duration-300 overflow-hidden ${featuredClass}" data-aos="fade-up">
        <!-- Thumbnail -->
        <div class="relative h-40 overflow-hidden ${approach.thumbnailImage ? '' : 'bg-gradient-to-br ' + approach.thumbnailGradient}">
          ${approach.thumbnailImage
            ? `<img src="${approach.thumbnailImage}" alt="${approach.title}" class="w-full h-full object-cover group-hover:scale-105 transition-transform duration-300">`
            : `<span class="flex items-center justify-center h-full text-6xl">${approach.thumbnailIcon}</span>`
          }
          ${approach.featured ? '<div class="absolute top-3 right-3"><span class="px-3 py-1 bg-yellow-400 text-yellow-900 text-xs font-bold rounded-full shadow-lg">Featured</span></div>' : ''}
        </div>

        <!-- Content -->
        <div class="p-5">
          <!-- Meta info -->
          <div class="flex items-center gap-2 mb-3">
            <span class="text-xs flex items-center gap-1" style="color: var(--text-tertiary);">
              <svg class="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z"></path>
              </svg>
              ${approach.readTime}
            </span>
            <span class="px-2 py-0.5 text-xs font-semibold rounded-full ${difficultyClass === 'difficulty-beginner' ? 'bg-green-900 text-green-200' : difficultyClass === 'difficulty-intermediate' ? 'bg-blue-900 text-blue-200' : 'bg-purple-900 text-purple-200'}">${approach.difficulty}</span>
          </div>

          <!-- Title -->
          <h3 class="text-lg font-bold mb-2 group-hover:text-teal-400 transition-colors line-clamp-2">
            ${approach.title}
          </h3>

          <!-- Preview -->
          <p class="text-sm mb-3 line-clamp-2">${approach.shortDescription}</p>

          <!-- Tags -->
          <div class="flex flex-wrap gap-1.5">
            ${approach.tags.slice(0, 2).map(tag => `<span class="px-2 py-0.5 text-xs rounded-md" style="background-color: rgba(34, 211, 238, 0.1); border: 1px solid rgba(34, 211, 238, 0.2);">${tag}</span>`).join('')}
          </div>
        </div>

        <!-- Arrow indicator -->
        <div class="absolute bottom-4 right-4 opacity-0 group-hover:opacity-100 transition-opacity" style="color: var(--primary-400);">
          <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 7l5 5m0 0l-5 5m5-5H6"></path>
          </svg>
        </div>
      </a>
    `;
  }).join('');
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
