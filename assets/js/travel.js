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
    
    // Handle gallery item clicks - modified to exclude full and random-cycle items
    document.querySelectorAll('.gallery').forEach(gallery => {
        // Skip random-cycle galleries
        if (gallery.classList.contains('random-cycle')) return;
        
        const items = gallery.querySelectorAll('.gallery-item');
        items.forEach((item, idx) => {
            // Skip full-width items
            if (item.classList.contains('full')) return;
            
            item.addEventListener('click', () => {
                // Only include non-full items in navigation
                galleryItems = Array.from(items).filter(i => !i.classList.contains('full'));
                currIdx = galleryItems.indexOf(item);
                showFullscreen(item);
            });
        });
    });
    
    function showFullscreen(item) {
        const content = item.querySelector('img, video-player');
        if (!content) return;
        
        const fullContent = content.cloneNode(true);
        const fsContent = overlay.querySelector('.fullscreen-content');
        fsContent.innerHTML = '';
        fsContent.appendChild(fullContent);
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

document.addEventListener("DOMContentLoaded", function() {
    // Check if we're on a travel page
    if (document.body.classList.contains('travel-page')) {
        console.log("Travel page initialized");
        
        // Ensure video players are properly sized
        function adjustVideoPlayerSize() {
            const videoPlayers = document.querySelectorAll('video-player');
            if (videoPlayers.length) {
                // Apply fullwidth class to each video player
                videoPlayers.forEach(player => {
                    player.classList.add('fullwidth-video');
                    
                    // Find quality selectors and ensure they have proper styling
                    const selectors = player.querySelectorAll('.video-quality-selector, select, .quality-selector');
                    selectors.forEach(selector => {
                        selector.classList.add('contained-width');
                    });
                });
                
                // Also look for standalone quality selectors
                const qualitySelectors = document.querySelectorAll('.video-quality-selector, .quality-selector');
                qualitySelectors.forEach(selector => {
                    selector.classList.add('contained-width');
                });
                
                // Force recalculation of video player sizes
                setTimeout(() => {
                    window.dispatchEvent(new Event('resize'));
                }, 100);
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