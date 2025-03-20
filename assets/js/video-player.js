class VideoPlayer extends HTMLElement {
  constructor() {
    super();
    this.attachShadow({ mode: 'open' });
  }

  static get observedAttributes() {
    return ['poster', 'sources'];
  }

  connectedCallback() {
    this.render();
    this.setupListeners();
  }

  render() {
    const vidId = this.getAttribute('vid-id') || 'vid_' + Math.random().toString(36).slice(2);
    const poster = this.getAttribute('poster');
    const sources = JSON.parse(this.getAttribute('sources') || '[]');
    
    // Extract resolutions using regex
    const resolutions = sources
      .map(src => src.match(/_(\d{3,4})p/)?.[1])
      .filter(Boolean)
      .sort((a, b) => Number(a) - Number(b));

    this.shadowRoot.innerHTML = `
      <style>
        :host {
          display: block;
        }
        .video-container {
          position: relative;
          padding-bottom: 56.25%;
          height: 0;
          overflow: hidden;
        }
        video {
          position: absolute;
          top: 0;
          left: 0;
          width: 100%;
          height: 100%;
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
}

customElements.define('video-player', VideoPlayer); 