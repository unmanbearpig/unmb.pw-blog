class VideoPlayer extends HTMLElement {
  constructor() {
    super();
    this.attachShadow({ mode: 'open' });
  }

  static get observedAttributes() {
    return ['poster', 'sources', 'aspect-ratio'];
  }

  connectedCallback() {
    this.render();
    this.setupListeners();
    
    // Check if we came from autoplay navigation
    if (sessionStorage.getItem('videoPlayerState')) {
      try {
        const state = JSON.parse(sessionStorage.getItem('videoPlayerState'));
        if (state.fromAutoplay) {
          // We were auto-navigated from another page
          this.playVideo(state.volume, state.wasMuted, state.wasFullscreen);
          // Clear the state
          sessionStorage.removeItem('videoPlayerState');
        }
      } catch (e) {
        console.error('Error restoring video state:', e);
        sessionStorage.removeItem('videoPlayerState');
      }
    }

    // Check if this is a gallery video
    if (this.classList.contains('gallery-video')) {
      this.video.muted = true;
      
      // Remove controls attribute if present
      this.video.removeAttribute('controls');
      
      // Add hover event to show/hide controls
      this.addEventListener('mouseenter', () => {
        this.video.controls = true;
      });
      
      this.addEventListener('mouseleave', () => {
        this.video.controls = false;
      });
    }
  }

  render() {
    const vidId = this.getAttribute('vid-id') || 'vid_' + Math.random().toString(36).slice(2);
    const poster = this.getAttribute('poster');
    const sources = JSON.parse(this.getAttribute('sources') || '[]');
    const aspectRatio = this.getAttribute('aspect-ratio') || '16:9';
    const [w, h] = aspectRatio.split(':').map(Number);
    const paddingBottom = (h / w * 100).toFixed(2);
    const isGalleryVideo = this.classList.contains('gallery-video');
    
    // Extract resolutions using regex
    const resolutions = sources
      .map(src => src.match(/_(\d{3,4})p/)?.[1])
      .filter(Boolean)
      .sort((a, b) => Number(a) - Number(b));

    this.shadowRoot.innerHTML = `
      <style>
        :host {
          display: block;
          width: 100%;
          height: 100%;
        }
        .video-container {
          position: relative;
          width: 100%;
          padding-bottom: ${paddingBottom}%;  /* Dynamic aspect ratio */
        }
        video {
          position: absolute;
          top: 0;
          left: 0;
          width: 100%;
          height: 100%;
          object-fit: contain;
        }
        .quality-selector {
          margin-top: 10px;
          text-align: right;
        }
        select {
          padding: 5px;
          border-radius: 4px;
          background: var(--select-bg, #fff);
          color: var(--select-color, #000);
          border: 1px solid var(--select-border, #ccc);
        }
        .autoplay-toggle {
          display: inline-block;
          margin-right: 10px;
        }
        label {
          font-size: 14px;
          vertical-align: middle;
        }
        input[type="checkbox"] {
          vertical-align: middle;
        }
      </style>

      <div class="video-container">
        <video id="${vidId}" controls loading="lazy" preload="none" poster="${poster}" muted>
          ${sources.map(src => {
            const res = src.match(/_(\d{3,4})p/)?.[1];
            const media = res && res !== '720' ? 
              `media="(min-width: ${res * 1.8}px)"` : '';
            return `
              <source src="${src}" type="video/mp4" size="${res}" ${media}>
            `;
          }).join('')}
          Your browser does not support the video tag.
        </video>
      </div>

      <div class="quality-selector">
        ${!isGalleryVideo ? `
          <div class="autoplay-toggle">
            <input type="checkbox" id="autoplay_${vidId}" checked>
            <label for="autoplay_${vidId}">Auto-play next</label>
          </div>
        ` : ''}
        <select id="quality_select_${vidId}">
          ${resolutions.map(res => 
            `<option value="${res}">${res}p</option>`
          ).join('')}
        </select>
      </div>
    `;

    // Store references
    this.video = this.shadowRoot.querySelector('video');
    this.select = this.shadowRoot.querySelector('select');
    this.autoplay = this.shadowRoot.querySelector('input[type="checkbox"]');
    
    // Store sources map for quality switching
    this.sourcesMap = Object.fromEntries(
      sources.map(src => {
        const res = src.match(/_(\d{3,4})p/)?.[1];
        return [res, src];
      })
    );
  }

  setupListeners() {
    // -> setupListeners
    this.select.addEventListener('change', () => this.changeQuality());
    
    // Handle video end event
    this.video.addEventListener('ended', () => this.onVideoEnded());
    
    // Set initial quality based on screen size
    const defaultQual = this.getDefaultQuality();
    this.select.value = defaultQual;
    this.changeQuality();
  }

  getDefaultQuality() {
    // -> getDefaultQuality
    const width = screen.width * window.devicePixelRatio;
    const quals = Array.from(this.select.options)
      .map(opt => Number(opt.value))
      .sort((a, b) => b - a);
    
    return quals.find(q => width >= q * 1.8) || quals[quals.length - 1];
  }

  changeQuality() {
    // -> changeQuality
    const currTime = this.video.currentTime;
    const wasPlaying = !this.video.paused;
    
    this.video.src = this.sourcesMap[this.select.value];
    this.video.currentTime = currTime;
    if (wasPlaying) this.video.play();
  }

  onVideoEnded() {
    // -> onVideoEnded
    // Skip autoplay for gallery videos
    if (this.classList.contains('gallery-video')) return;
    
    if (!this.autoplay?.checked) return;
    
    // Store current state
    const wasFullscreen = !!document.fullscreenElement;
    const wasMuted = this.video.muted;
    const volume = this.video.volume;
    
    // Check if we're on index page
    const isIndex = document.querySelector('[data-travel-page="index"]');
    
    if (isIndex) {
      // We're on index page, look for "Show more" link with more videos
      const postItem = this.findAncestor(this, '.travel-post-item');
      if (!postItem) return;
      
      const readMoreLink = postItem.querySelector('.read-more-link a');
      if (readMoreLink && readMoreLink.textContent.includes('more video')) {
        // Store state in sessionStorage before navigation
        sessionStorage.setItem('videoPlayerState', JSON.stringify({
          wasFullscreen,
          wasMuted,
          volume,
          fromAutoplay: true
        }));
        
        // Navigate to post page
        window.location.href = readMoreLink.getAttribute('href');
        return;
      }
    }
    
    // Find the next video player
    const nextPlayer = this.findNextVideoPlayer();
    if (nextPlayer) {
      // Exit fullscreen first if needed
      this.exitFullscreenIfNeeded().then(() => {
        // Add animation styles to the head if not already there
        this.ensureAnimationStyles();
        
        // Add animation class to the next player before scrolling
        nextPlayer.classList.add('video-player-highlight');
        
        // Scroll to next video with smooth animation
        this.scrollToWithAnimation(nextPlayer, 500).then(() => {
          // Play after animation is complete
          nextPlayer.playVideo(volume, wasMuted, wasFullscreen);
          
          // Remove animation class after a delay
          setTimeout(() => {
            nextPlayer.classList.remove('video-player-highlight');
          }, 1500);
        });
      });
    }
  }
  
  ensureAnimationStyles() {
    // -> ensureAnimationStyles
    if (document.getElementById('video-player-animations')) return;
    
    const style = document.createElement('style');
    style.id = 'video-player-animations';
    style.textContent = `
      @keyframes videoPlayerHighlight {
        0% { box-shadow: 0 0 0 0 rgba(255, 255, 255, 0); }
        20% { box-shadow: 0 0 0 4px rgba(255, 215, 0, 0.7); }
        100% { box-shadow: 0 0 0 8px rgba(255, 215, 0, 0); }
      }
      
      video-player.video-player-highlight {
        animation: videoPlayerHighlight 1.5s ease-out;
        position: relative;
        z-index: 1;
      }
    `;
    
    document.head.appendChild(style);
  }
  
  scrollToWithAnimation(element, duration = 500) {
    // -> scrollToWithAnimation
    return new Promise(resolve => {
      const start = window.pageYOffset;
      const target = element.getBoundingClientRect().top + window.pageYOffset;
      const distance = target - start;
      let startTime = null;
      
      function animate(currentTime) {
        if (startTime === null) startTime = currentTime;
        const timeElapsed = currentTime - startTime;
        const progress = Math.min(timeElapsed / duration, 1);
        const ease = t => t<.5 ? 4*t*t*t : (t-1)*(2*t-2)*(2*t-2)+1; // Cubic easing
        
        window.scrollTo(0, start + distance * ease(progress));
        
        if (timeElapsed < duration) {
          requestAnimationFrame(animate);
        } else {
          element.scrollIntoView({ block: 'center' });
          resolve();
        }
      }
      
      requestAnimationFrame(animate);
    });
  }
  
  exitFullscreenIfNeeded() {
    // -> exitFullscreenIfNeeded
    return new Promise(resolve => {
      if (document.fullscreenElement) {
        // Add listener to detect when exit is complete
        const onExitFullscreen = () => {
          document.removeEventListener('fullscreenchange', onExitFullscreen);
          setTimeout(resolve, 100); // Small delay after exiting
        };
        
        document.addEventListener('fullscreenchange', onExitFullscreen);
        
        // Exit fullscreen
        if (document.exitFullscreen) {
          document.exitFullscreen();
        } else if (document.webkitExitFullscreen) {
          document.webkitExitFullscreen();
        } else if (document.msExitFullscreen) {
          document.msExitFullscreen();
        } else {
          // If can't exit for some reason, resolve anyway
          document.removeEventListener('fullscreenchange', onExitFullscreen);
          resolve();
        }
      } else {
        // Already not in fullscreen
        resolve();
      }
    });
  }
  
  findAncestor(el, selector) {
    // -> findAncestor
    while (el && el !== document) {
      const parent = el.parentElement;
      if (parent && parent.matches(selector)) return parent;
      el = parent;
    }
    return null;
  }
  
  findNextVideoPlayer() {
    // -> findNextVideoPlayer
    const allPlayers = Array.from(document.querySelectorAll('video-player'));
    const currIndex = allPlayers.indexOf(this);
    
    if (currIndex !== -1 && currIndex < allPlayers.length - 1) {
      return allPlayers[currIndex + 1];
    }
    
    return null;
  }
  
  playVideo(volume = 1.0, muted = false, goFullscreen = false) {
    // -> playVideo vol=${volume} muted=${muted} fs=${goFullscreen}
    // Set volume and mute state
    this.video.volume = volume;
    this.video.muted = muted;
    
    // Start playing
    const playPromise = this.video.play();
    
    if (!goFullscreen) return;
    
    // Handle fullscreen after playing starts - using a slightly longer delay for Firefox
    const isFirefox = navigator.userAgent.toLowerCase().indexOf('firefox') > -1;
    const delay = isFirefox ? 300 : 100; // Longer delay for Firefox
    
    if (playPromise !== undefined) {
      playPromise.then(() => {
        // Add a bit more delay for Firefox to ensure video is playing
        setTimeout(() => this.enterFullscreen(), delay);
      }).catch(err => {
        console.error("Error autoplay:", err);
        // Try to enter fullscreen anyway after a delay
        setTimeout(() => this.enterFullscreen(), delay);
      });
    } else {
      // Older browsers might not return a promise
      setTimeout(() => this.enterFullscreen(), delay);
    }
  }
  
  enterFullscreen() {
    // -> enterFullscreen
    try {
      // Firefox often needs a user interaction or a delay
      // Try with mozRequestFullScreen first (Firefox specific)
      if (this.video.mozRequestFullScreen) {
        console.log("Using Firefox fullscreen API");
        this.video.mozRequestFullScreen();
      } else if (this.video.requestFullscreen) {
        this.video.requestFullscreen();
      } else if (this.video.webkitRequestFullscreen) {
        this.video.webkitRequestFullscreen();
      } else if (this.video.msRequestFullscreen) {
        this.video.msRequestFullscreen();
      } else {
        // Fallback for Firefox using document.documentElement
        const isFirefox = navigator.userAgent.toLowerCase().indexOf('firefox') > -1;
        if (isFirefox && document.documentElement.requestFullscreen) {
          // For Firefox, sometimes requesting fullscreen on the document works better
          const container = this.findAncestor(this.video, '.video-container') 
            || this.shadowRoot.querySelector('.video-container');
          
          if (container) {
            container.requestFullscreen();
          } else {
            document.documentElement.requestFullscreen();
          }
        }
      }
    } catch (e) {
      console.error("Error entering fullscreen:", e);
      
      // Last resort for Firefox
      try {
        const isFirefox = navigator.userAgent.toLowerCase().indexOf('firefox') > -1;
        if (isFirefox) {
          // Try a different approach in Firefox
          const vidContainer = this.shadowRoot.querySelector('.video-container');
          if (vidContainer && vidContainer.requestFullscreen) {
            vidContainer.requestFullscreen();
          }
        }
      } catch (e2) {
        console.error("Failed fallback fullscreen attempt:", e2);
      }
    }
  }
}

customElements.define('video-player', VideoPlayer); 