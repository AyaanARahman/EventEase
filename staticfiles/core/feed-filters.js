class FeedFilter {
    constructor(options) {
        this.gridId = options.gridId;
        this.filterButtons = options.filterButtons;
        this.sortSelect = options.sortSelect;
        this.itemClass = options.itemClass;
        this.searchInput = options.searchInput;
        this.loadingSpinner = options.loadingSpinner;
        
        this.grid = document.getElementById(this.gridId);
        this.currentFilters = options.initialFilters || {
            category: 'all',
            status: 'all',
            size: 'all',
            priority: 'all'
        };
        
        this.searchTimeout = null;
        this.initializeFilters();
    }

    initializeFilters() {
        // Initialize filter buttons
        document.querySelectorAll(this.filterButtons).forEach(button => {
            button.addEventListener('click', (e) => {
                const filterType = button.dataset.filterType;
                const filterValue = button.dataset.filter;
                
                // Update active state
                document.querySelectorAll(`[data-filter-type="${filterType}"]`)
                    .forEach(btn => btn.classList.remove('active'));
                button.classList.add('active');
                
                // Update filters
                this.currentFilters[filterType] = filterValue;
                
                this.showLoading();
                setTimeout(() => {
                    this.applyFilters();
                    this.hideLoading();
                }, 200);
            });
        });

        // Initialize sort
        if (this.sortSelect) {
            document.querySelector(this.sortSelect).addEventListener('change', (e) => {
                this.showLoading();
                setTimeout(() => {
                    this.applySort(e.target.value);
                    this.hideLoading();
                }, 200);
            });
        }

        // Initialize search with debounce
        if (this.searchInput) {
            document.querySelector(this.searchInput).addEventListener('input', (e) => {
                clearTimeout(this.searchTimeout);
                this.searchTimeout = setTimeout(() => {
                    this.showLoading();
                    this.applySearch(e.target.value);
                    this.hideLoading();
                }, 300);
            });
        }
    }

    applyFilters(searchTerm = '') {
        const items = document.querySelectorAll(this.itemClass);
        let visibleCount = 0;
        
        items.forEach(item => {
            let show = true;
            
            // Check each active filter
            Object.entries(this.currentFilters).forEach(([type, value]) => {
                if (value !== 'all' && item.dataset[type]) {
                    const itemValue = item.dataset[type];
                    if (itemValue !== value) {
                        show = false;
                    }
                }
            });
            
            // Apply search filter if exists
            if (searchTerm) {
                const title = item.dataset.title.toLowerCase();
                if (!title.includes(searchTerm.toLowerCase())) {
                    show = false;
                }
            }
            
            item.style.display = show ? '' : 'none';
            if (show) visibleCount++;
        });

        // Show/hide no results message
        this.updateNoResults(visibleCount === 0);
    }

    applySort(sortValue) {
        const items = Array.from(document.querySelectorAll(this.itemClass));
        
        items.sort((a, b) => {
            const titleA = a.dataset.title.toLowerCase();
            const titleB = b.dataset.title.toLowerCase();
            const dateA = new Date(a.dataset.date);
            const dateB = new Date(b.dataset.date);
            const membersA = parseInt(a.dataset.members || 0);
            const membersB = parseInt(b.dataset.members || 0);

            switch(sortValue) {
                case 'newest':
                    return dateB - dateA;
                case 'oldest':
                    return dateA - dateB;
                case 'name-asc':
                    return titleA.localeCompare(titleB);
                case 'name-desc':
                    return titleB.localeCompare(titleA);
                case 'members':
                    return membersB - membersA;
                case 'size':
                    return this.compareSizes(a.dataset.size, b.dataset.size);
                default:
                    return 0;
            }
        });

        this.grid.innerHTML = '';
        items.forEach(item => this.grid.appendChild(item));
    }

    compareSizes(sizeA, sizeB) {
        const sizeOrder = { 'large': 3, 'medium': 2, 'small': 1 };
        return sizeOrder[sizeB] - sizeOrder[sizeA];
    }

    applySearch(searchTerm) {
        this.applyFilters(searchTerm);
    }

    updateNoResults(show) {
        const noResults = document.querySelector('.no-results');
        if (noResults) {
            noResults.style.display = show ? 'block' : 'none';
        }
    }

    showLoading() {
        if (this.loadingSpinner) {
            document.querySelector(this.loadingSpinner).classList.add('active');
        }
    }

    hideLoading() {
        if (this.loadingSpinner) {
            document.querySelector(this.loadingSpinner).classList.remove('active');
        }
    }

    reset() {
        // Reset all filters to default
        Object.keys(this.currentFilters).forEach(key => {
            this.currentFilters[key] = 'all';
        });

        // Reset all filter buttons
        document.querySelectorAll(this.filterButtons).forEach(btn => {
            btn.classList.remove('active');
            if (btn.dataset.filter === 'all') {
                btn.classList.add('active');
            }
        });

        // Reset search input
        if (this.searchInput) {
            document.querySelector(this.searchInput).value = '';
        }

        // Reset sort select
        if (this.sortSelect) {
            document.querySelector(this.sortSelect).value = 'newest';
        }

        this.applyFilters();
    }
}