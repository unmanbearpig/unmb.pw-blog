// -> init_travel Add scroll detection and video layout handling

document.addEventListener("DOMContentLoaded", function() {
    // Check if we're on a travel page
    if (document.body.classList.contains('travel-page')) {
        console.log("Travel page initialized");
        
        // Add custom navigation
        setupTravelNavigation();
        
        // Function to check scroll position and update classes
        function updateScrollState() {
            const scrollPos = window.scrollY;
            const viewportHeight = window.innerHeight;
            
            // Calculate scroll percentage
            const scrollPercentage = (scrollPos / viewportHeight) * 100;
            
            // Add scrolled class when scrolled down more than 10% of viewport height
            if (scrollPercentage > 10) {
                document.body.classList.add('scrolled');
                
                // When user has scrolled significantly, add a class to fully hide header
                if (scrollPercentage > 20) {
                    document.body.classList.add('header-hidden');
                } else {
                    document.body.classList.remove('header-hidden');
                }
            } else {
                document.body.classList.remove('scrolled');
                document.body.classList.remove('header-hidden');
            }
        }
        
        // Initialize scroll state
        updateScrollState();
        
        // Add event listener with throttling
        let scrollTimeout;
        let lastScrollPos = 0;
        let scrollDirection = 'down';
        
        window.addEventListener('scroll', function() {
            // Determine scroll direction
            const currentScrollPos = window.scrollY;
            scrollDirection = currentScrollPos > lastScrollPos ? 'down' : 'up';
            lastScrollPos = currentScrollPos;
            
            // If user is scrolling up, show header immediately
            if (scrollDirection === 'up') {
                document.body.classList.remove('header-hidden');
            }
            
            // Throttle the main scroll updates
            if (!scrollTimeout) {
                scrollTimeout = setTimeout(function() {
                    updateScrollState();
                    scrollTimeout = null;
                }, 100);
            }
        });
        
        // Handle resize events too, for better responsiveness
        window.addEventListener('resize', updateScrollState);
        
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
        
        // Setup custom travel navigation
        function setupTravelNavigation() {
            // Get the header element
            const header = document.querySelector('.site-header .wrapper');
            
            if (!header) return;
            
            // Remove any existing travel navigation (in case of dynamic page updates)
            const existingNav = header.querySelector('.travel-nav');
            if (existingNav) {
                existingNav.remove();
            }
            
            // Create navigation container
            const nav = document.createElement('div');
            nav.className = 'travel-nav';
            
            // Create the link based on current page
            const link = document.createElement('a');
            link.className = 'travel-home-link';
            
            // Check if we're on a travel post or travel index
            const isPostPage = document.querySelector('article.travel-post') !== null;
            const isIndexPage = document.querySelector('div[data-travel-page="index"]') !== null;
            
            if (isPostPage) {
                // If we're on a post page, link to travel index
                link.href = '/travel/';
                link.textContent = 'Back to Travel';
            } else {
                // Otherwise, link to main site
                link.href = '/';
                link.textContent = 'Main Site';
            }
            
            // Add the link to the nav
            nav.appendChild(link);
            
            // Add the nav to the header
            header.appendChild(nav);
            
            console.log("Travel navigation set up:", isPostPage ? "Post page" : "Index page");
        }
    }
}); 