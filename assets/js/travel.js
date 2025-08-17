// -> init_travel Add video layout handling and resize events

// -> init_carousel Handle carousel navigation
function initCarousels() {
    const carousels = document.querySelectorAll('.carousel');
    
    carousels.forEach(carousel => {
        let curr = 0;
        const items = carousel.querySelectorAll('.gallery-item');
        const inner = carousel.querySelector('.carousel-inner');
        
        // Create nav buttons
        const nav = document.createElement('div');
        nav.className = 'carousel-nav';
        nav.innerHTML = `
            <button class="carousel-btn prev">←</button>
            <button class="carousel-btn next">→</button>
        `;
        
        carousel.appendChild(nav);
        
        // Handle navigation
        nav.querySelector('.prev').addEventListener('click', () => {
            curr = (curr - 1 + items.length) % items.length;
            inner.style.transform = `translateX(-${curr * 100}%)`;
        });
        
        nav.querySelector('.next').addEventListener('click', () => {
            curr = (curr + 1) % items.length;
            inner.style.transform = `translateX(-${curr * 100}%)`;
        });
    });
}

// -> init_fullscreen Handle fullscreen gallery
function initFullscreenGallery() {
    // Create fullscreen overlay
    const overlay = document.createElement('div');
    overlay.className = 'fullscreen-overlay';
    overlay.innerHTML = `
        <div class="fullscreen-nav">
            <button class="fs-nav-btn prev">←</button>
            <button class="fs-nav-btn next">→</button>
        </div>
        <div class="fullscreen-content"></div>
    `;
    document.body.appendChild(overlay);
    
    let currIdx = 0;
    let galleryItems = [];
    
    // Collect all gallery items from the page first
    document.querySelectorAll('.gallery').forEach(gallery => {
        // Skip random-cycle galleries
        if (gallery.classList.contains('random-cycle')) return;
        
        const items = gallery.querySelectorAll('.gallery-item');
        items.forEach(item => {
            // Skip full-width items
            if (item.classList.contains('full')) return;
            
            item.addEventListener('click', () => {
                // Get all gallery items from the page
                galleryItems = Array.from(document.querySelectorAll('.gallery:not(.random-cycle) .gallery-item:not(.full)'));
                currIdx = galleryItems.indexOf(item);
                showFullscreen(item);
            });
        });
    });
    
    function showFullscreen(item) {
        const content = item.querySelector('img, video-player');
        if (!content) return;
        
        const fsContent = overlay.querySelector('.fullscreen-content');
        fsContent.innerHTML = '';
        
        if (content.tagName === 'IMG') {
            // Create a new image element for fullscreen
            const fullImg = document.createElement('img');
            fullImg.src = content.src;
            fullImg.alt = '';  // Explicitly set empty alt text
            fullImg.style.maxWidth = '95vw';
            fullImg.style.maxHeight = '95vh';
            fullImg.style.objectFit = 'contain';
            fsContent.appendChild(fullImg);
        } else {
            // For video players, we can still clone
            const fullContent = content.cloneNode(true);
            fsContent.appendChild(fullContent);
        }
        
        overlay.classList.add('active');
        document.body.style.overflow = 'hidden';
    }
    
    function navigate(dir) {
        currIdx = (currIdx + dir + galleryItems.length) % galleryItems.length;
        showFullscreen(galleryItems[currIdx]);
    }
    
    // Nav button clicks
    overlay.querySelector('.prev').addEventListener('click', (e) => {
        e.stopPropagation();
        navigate(-1);
    });
    
    overlay.querySelector('.next').addEventListener('click', (e) => {
        e.stopPropagation();
        navigate(1);
    });
    
    // Close on overlay click (but not content)
    overlay.addEventListener('click', () => {
        overlay.classList.remove('active');
        overlay.querySelector('.fullscreen-content').innerHTML = '';
        document.body.style.overflow = '';
    });
    
    overlay.querySelector('.fullscreen-content').addEventListener('click', (e) => {
        e.stopPropagation();
    });
    
    // Keyboard navigation
    document.addEventListener('keydown', (e) => {
        if (!overlay.classList.contains('active')) return;
        
        switch (e.key) {
            case 'Escape':
                overlay.click();
                break;
            case 'ArrowLeft':
                navigate(-1);
                break;
            case 'ArrowRight':
                navigate(1);
                break;
        }
    });
}

// -> init_random_cycle Handle random cycle galleries
function initRandomCycles() {
    const galleries = document.querySelectorAll('.random-cycle');
    
    galleries.forEach(gallery => {
        const items = gallery.querySelectorAll('.gallery-item');
        if (items.length === 0) return;
        
        // Create nav buttons
        const nav = document.createElement('div');
        nav.className = 'random-cycle-nav';
        nav.innerHTML = `
            <button class="random-cycle-btn prev">←</button>
            <button class="random-cycle-btn next">→</button>
        `;
        gallery.appendChild(nav);
        
        // Show random initial image
        const idx = Math.floor(Math.random() * items.length);
        items[idx].classList.add('active');
        
        // Handle navigation
        let currIdx = idx;
        
        // Add click handler to the gallery itself
        gallery.addEventListener('click', (e) => {
            // Only proceed if clicking the gallery or image (not nav buttons)
            if (!e.target.closest('.random-cycle-btn')) {
                items[currIdx].classList.remove('active');
                currIdx = (currIdx + 1) % items.length;
                items[currIdx].classList.add('active');
            }
        });
        
        // Keep existing nav button handlers
        nav.querySelector('.prev').addEventListener('click', (e) => {
            e.stopPropagation(); // Prevent gallery click
            items[currIdx].classList.remove('active');
            currIdx = (currIdx - 1 + items.length) % items.length;
            items[currIdx].classList.add('active');
        });
        
        nav.querySelector('.next').addEventListener('click', (e) => {
            e.stopPropagation(); // Prevent gallery click
            items[currIdx].classList.remove('active');
            currIdx = (currIdx + 1) % items.length;
            items[currIdx].classList.add('active');
        });
    });
}

// Handle scroll detection
function initScrollDetection() {
    function updateScrollState() {
        const scrollPos = window.scrollY;
        const viewportHeight = window.innerHeight;
        const scrollPercentage = (scrollPos / viewportHeight) * 100;
        
        if (scrollPercentage > 10) {
            document.body.classList.add('scrolled');
            if (scrollPercentage > 20) {
                // Hide header logic is now handled in scroll event listener
                // This just handles initial state
                if (document.body.classList.contains('header-hidden')) {
                    document.body.classList.add('header-hidden');
                }
            } else {
                document.body.classList.remove('header-hidden');
            }
        } else {
            document.body.classList.remove('scrolled');
            document.body.classList.remove('header-hidden');
        }
    }
    
    // Initial check
    updateScrollState();
    
    // Throttled scroll handler
    let scrollTimeout;
    let lastScrollPos = 0;
    const SCROLL_THRESHOLD_SHOW = 50; // Minimum pixels scrolled up to show header
    const SCROLL_THRESHOLD_HIDE = 20; // Minimum pixels scrolled down to hide header
    
    window.addEventListener('scroll', function() {
        const currentScrollPos = window.scrollY;
        
        // Show header immediately when at the very top
        if (currentScrollPos === 0) {
            document.body.classList.remove('header-hidden');
            document.body.classList.remove('scrolled');
        }
        // Show header when scrolling up significantly
        else if (currentScrollPos < lastScrollPos) {
            const scrollDifference = lastScrollPos - currentScrollPos;
            if (scrollDifference >= SCROLL_THRESHOLD_SHOW) {
                document.body.classList.remove('header-hidden');
            }
        }
        // Hide header when scrolling down significantly
        else if (currentScrollPos > lastScrollPos) {
            const scrollDifference = currentScrollPos - lastScrollPos;
            if (scrollDifference >= SCROLL_THRESHOLD_HIDE) {
                document.body.classList.add('header-hidden');
            }
        }
        
        lastScrollPos = currentScrollPos;
        
        // Throttle main updates
        if (!scrollTimeout) {
            scrollTimeout = setTimeout(function() {
                updateScrollState();
                scrollTimeout = null;
            }, 100);
        }
    });
    
    // Handle resize
    window.addEventListener('resize', updateScrollState);
}

// Add titles to images that have alt text
function initImageTitles() {
    document.querySelectorAll('img[alt]:not([alt=""])').forEach(img => {
        if (!img.title) {
            img.title = img.alt;
        }
    });
}

// Initialize all travel page features
function initTravel() {
    initCarousels();
    initFullscreenGallery();
    initRandomCycles();
    initScrollDetection();
    initImageTitles();
}

document.addEventListener("DOMContentLoaded", function() {
    // Check if we're on a travel page
    if (document.body.classList.contains('travel-page')) {
        console.log("Travel page initialized");
        
        // Initialize scroll detection
        initScrollDetection();
        
        // Initialize image titles
        initImageTitles();
        
        // Ensure video players are properly sized
        function adjustVideoPlayerSize() {
            console.log('-> adjust_video_player_size')
            const vplayers = document.querySelectorAll('video-player');
            if (vplayers.length) {
                // Apply fullwidth class only if not gallery-video
                vplayers.forEach(player => {
                    if (!player.classList.contains('gallery-video')) {
                        player.classList.add('fullwidth-video');
                    }
                    
                    // Find quality selectors and ensure they have proper styling
                    const sels = player.querySelectorAll(
                        '.video-quality-selector, select, .quality-selector'
                    );
                    sels.forEach(sel => sel.classList.add('contained-width'));
                });
                
                // Also look for standalone quality selectors
                const qualSels = document.querySelectorAll(
                    '.video-quality-selector, .quality-selector'
                );
                qualSels.forEach(sel => sel.classList.add('contained-width'));
                
                // Force recalculation of video player sizes
                setTimeout(() => window.dispatchEvent(new Event('resize')), 100);
            }
        }
        
        // Run video adjustment after load and after any dynamic content changes
        window.addEventListener('load', adjustVideoPlayerSize);
        
        // Check periodically for any dynamically added video players
        setInterval(adjustVideoPlayerSize, 1000);
        
        // Initialize carousels
        initCarousels();
        
        // Initialize fullscreen gallery
        initFullscreenGallery();
        
        // Initialize random cycle galleries
        initRandomCycles();
    }
}); 