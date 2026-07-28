---
layout: default
title: Selected work
description: Selected products and engineering work by Ivan Fedyunin, including HostelPunk and Vestuario Antiguo.
permalink: /work/
full_width: true
theme: editorial
preload_image: /assets/images/portfolio/hostelpunk-home.webp
---

<div class="work-page">
  <header class="work-intro portfolio-shell">
    <p class="ui-label">Selected work</p>
    <h1>Systems I can explain from the product decision to the production failure.</h1>
    <p>Two current projects show the range: a data-heavy public product and a client system where brand, interface and operations have to agree.</p>
  </header>

  <section class="work-case work-case--hostelpunk portfolio-shell" id="hostelpunk">
    <header>
      <p class="ui-label">01 / HostelPunk / own product</p>
      <h2>Evidence-oriented hostel discovery at multi-source scale.</h2>
    </header>
    <figure>
      <img src="{{ "/assets/images/portfolio/hostelpunk-home.webp" | relative_url }}" width="1440" height="900" alt="The live HostelPunk homepage">
    </figure>
    <div class="work-case__grid">
      <div>
        <h3>The product problem</h3>
        <p>Generic review averages compress different travel experiences into the same score. HostelPunk isolates atmosphere, confidence, warning evidence, language mix and suspicious-review patterns so a traveler can inspect the reason behind a ranking.</p>
      </div>
      <div>
        <h3>The system</h3>
        <p>Python workers acquire and normalize source data. A shared PostgreSQL and PostGIS model links properties across providers. Versioned LLM, classifier, regex and deterministic extractors generate signals with evaluation data and provenance. A Go and HTMX application serves the public product.</p>
      </div>
      <div>
        <h3>My responsibility</h3>
        <p>Product definition, data model, acquisition, entity resolution, analysis, evaluation, backend, interface, deployment, monitoring and ongoing production decisions.</p>
      </div>
      <dl>
        <div><dt>74M</dt><dd>reviews</dd></div>
        <div><dt>22,600</dt><dd>linked properties</dd></div>
        <div><dt>235</dt><dd>versioned signals</dd></div>
        <div><dt>7</dt><dd>product languages</dd></div>
      </dl>
    </div>
    <div class="link-pair">
      <a href="https://hostelpunk.com/">Open HostelPunk</a>
      <a href="{% post_url 2026-05-15-hostelpunk %}">Read the product note</a>
    </div>
  </section>

  <section class="work-case work-case--vestuario portfolio-shell" id="vestuario">
    <header>
      <p class="ui-label">02 / Vestuario Antiguo / client product</p>
      <h2>A complete visual identity and the Rails system behind a rental atelier.</h2>
    </header>
    <div class="work-case__gallery">
      <img src="{{ "/assets/images/portfolio/landing-page.webp" | relative_url }}" width="1440" height="1000" alt="Vestuario Antiguo landing page">
      <img src="{{ "/assets/images/portfolio/collection-page.webp" | relative_url }}" width="1440" height="1000" alt="Vestuario Antiguo collection page">
    </div>
    <div class="work-case__grid">
      <div>
        <h3>Credit</h3>
        <p>Tatiana supplied the initial direction and references and approved the work. I created the full visual identity, including the logo, designed the interface, built the Rails application and continue to manage the technical product.</p>
      </div>
      <div>
        <h3>Public experience</h3>
        <p>Identity, editorial landing pages, albums, rental catalog, size and availability information, fitting shortlists and appointment requests.</p>
      </div>
      <div>
        <h3>Operational system</h3>
        <p>Orders, fittings, availability rules, cleaning buffers, manual blocks, media workflows, administration, deployment and production operation.</p>
      </div>
      <p class="review-caveat">The detailed case study remains an internal draft until the client approves the exact public material.</p>
    </div>
  </section>

  <section class="experience-ledger portfolio-shell">
    <header>
      <p class="ui-label">Commercial continuity</p>
      <h2>Selected experience beyond the flagship projects.</h2>
    </header>
    <div class="experience-ledger__rows">
      <article><span>2025 to 2026</span><h3>Oversize.io</h3><p>Python acquisition and extraction pipelines for hundreds of legal and regulatory sources in a Rails and PostgreSQL product.</p></article>
      <article><span>2016 to 2024</span><h3>ExamSuccess.com.au</h3><p>Eight years of Rails feature ownership and production support across student, tutor, testing and live-session workflows.</p></article>
      <article><span>2018</span><h3>Jualo.com</h3><p>Roughly 10x response-time improvement through caching and query work on a Rails marketplace serving more than four million monthly users.</p></article>
      <article><span>2009 to 2012</span><h3>RSoft and Rookee</h3><p>Network-hardware testing infrastructure and distributed search-engine data acquisition across bare-metal systems.</p></article>
    </div>
  </section>

  <section class="work-close portfolio-shell">
    <h2>Responsibility is the through line.</h2>
    <p>I use coding agents extensively, but I retain the product, architecture, review, testing, deployment and production responsibility.</p>
    <a class="action action--primary" href="mailto:ivan.fedyunin@gmail.com">Discuss a role</a>
  </section>
</div>
