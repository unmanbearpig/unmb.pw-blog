// -> init_travel Add video layout handling and resize events

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
    }
}); 