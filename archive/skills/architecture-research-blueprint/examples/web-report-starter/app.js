/**
 * Architecture Web Report - Google Cloud Clean Engineering JS Engine
 * Features:
 * - Automatic Zero-Dependency DOM Math Sanitizer (converts residual $O(1)$, \to, etc. to clean HTML)
 * - Robust individual Mermaid 10 async rendering with try/catch & theme cache
 * - Fullscreen Lightbox Modal with Zoom In/Out/Reset/Fit, Mouse Pan Drag, Wheel Zoom & Shortcuts
 * - Theme Switcher (Dark/Light) with localStorage persistence
 * - Sticky Navigation tracking via IntersectionObserver
 * - Interactive Decision Wizard & Sizing/TCO Calculator engines
 */

document.addEventListener('DOMContentLoaded', () => {
  // ==========================================================================
  // 0. Automatic Client-Side DOM Math Sanitizer (LaTeX Fallback Defense)
  // ==========================================================================
  function autoCleanDomMath() {
    const mainContent = document.querySelector('.app-main');
    if (!mainContent) return;

    const symbolMap = [
        [/\\to/g, '→'],
        [/\\rightarrow/g, '→'],
        [/\\leftarrow/g, '←'],
        [/\\le\b/g, '≤'],
        [/\\leq\b/g, '≤'],
        [/\\ge\b/g, '≥'],
        [/\\geq\b/g, '≥'],
        [/\\approx\b/g, '≈'],
        [/\\neq\b/g, '≠'],
        [/\\times\b/g, '×'],
        [/\\pm\b/g, '±'],
        [/\\mu\b/g, 'µ'],
        [/\\Delta\b/g, 'Δ'],
        [/\\cdot\b/g, '·'],
        [/\\dots\b/g, '…'],
        [/\\in\b/g, '∈'],
        [/\\infty\b/g, '∞'],
        [/\\text\{([^}]+)\}/g, '$1'],
        [/\\mathbf\{([^}]+)\}/g, '<strong>$1</strong>'],
        [/\\mathit\{([^}]+)\}/g, '<em>$1</em>']
    ];

    function cleanText(text) {
      let cleaned = text;
      for (const [pattern, repl] of symbolMap) {
        cleaned = cleaned.replace(pattern, repl);
      }
      return cleaned;
    }

    const walker = document.createTreeWalker(
      mainContent,
      NodeFilter.SHOW_TEXT,
      {
        acceptNode(node) {
          const parent = node.parentElement;
          if (!parent) return NodeFilter.FILTER_REJECT;
          const tag = parent.tagName.toLowerCase();
          if (['script', 'style', 'pre', 'code', 'svg'].includes(tag) || parent.classList.contains('mermaid')) {
            return NodeFilter.FILTER_REJECT;
          }
          if (node.nodeValue && node.nodeValue.includes('$')) {
            return NodeFilter.FILTER_ACCEPT;
          }
          return NodeFilter.FILTER_SKIP;
        }
      }
    );

    const nodesToProcess = [];
    while (walker.nextNode()) {
      nodesToProcess.push(walker.currentNode);
    }

    nodesToProcess.forEach(textNode => {
      let val = textNode.nodeValue;
      if (!val || !val.includes('$')) return;

      // Match $...$ where it's not preceded by a backslash
      const mathRegex = /(?<!\\)\$([A-Za-z0-9_\\{}() \-\+=\/≤≥→·×\^]+?)\$(?!\d)/g;
      if (!mathRegex.test(val)) return;

      const span = document.createElement('span');
      span.innerHTML = val.replace(mathRegex, (match, inner) => {
        const trimmed = inner.trim();
        // If it's a currency expression like "10 to $20", "$10 - $20", or "100/mo", preserve verbatim
        if (/^\d+(?:,\d+)*(?:\.\d+)?(?:\s*(?:k|M|B|\/mo|\/month|\/hr|\/yr|USD|EUR|to\s+\$?\d+|-\s*\$?\d+))?$/i.test(trimmed)) {
          return match;
        }

        const converted = cleanText(trimmed);

        if (/^O\([^\)]+\)$/.test(converted)) {
          return `<code>${converted}</code>`;
        }
        if (/^[A-Za-z]$/.test(converted)) {
          return `<em>${converted}</em>`;
        }
        return `<code>${converted}</code>`;
      });

      if (textNode.parentNode) {
        textNode.parentNode.replaceChild(span, textNode);
      }
    });
  }

  // Execute DOM math sanitizer immediately
  autoCleanDomMath();

  // ==========================================================================
  // 1. Fullscreen Diagram Lightbox Modal (Zoom & Pan Engine)
  // ==========================================================================
  let currentScale = 1.0;
  let translateX = 0;
  let translateY = 0;
  let isDragging = false;
  let startX = 0;
  let startY = 0;

  function ensureDiagramModalExists() {
    if (document.getElementById('diagramModal')) return;

    const modalHtml = `
      <div id="diagramModal" class="diagram-modal" aria-hidden="true" role="dialog">
        <div class="modal-backdrop" id="modalBackdrop"></div>
        <div class="modal-container">
          <div class="modal-header">
            <div class="modal-title-group">
              <span class="modal-icon">🔍</span>
              <h3 class="modal-title" id="modalTitle">High-Resolution Architecture Viewer</h3>
            </div>
            <div class="modal-actions">
              <div class="zoom-controls">
                <button id="zoomOutBtn" class="btn-ctrl" title="Zoom Out (-)" aria-label="Zoom Out">
                  <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="11" cy="11" r="8"/><line x1="21" y1="21" x2="16.65" y2="16.65"/><line x1="8" y1="11" x2="14" y2="11"/></svg>
                </button>
                <span id="zoomLevelIndicator" class="zoom-indicator">100%</span>
                <button id="zoomInBtn" class="btn-ctrl" title="Zoom In (+)" aria-label="Zoom In">
                  <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="11" cy="11" r="8"/><line x1="21" y1="21" x2="16.65" y2="16.65"/><line x1="11" y1="8" x2="11" y2="14"/><line x1="8" y1="11" x2="14" y2="11"/></svg>
                </button>
                <button id="zoomResetBtn" class="btn-ctrl" title="Reset Zoom (100%)" aria-label="Reset Zoom">
                  <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M3 12a9 9 0 1 0 9-9 9.75 9.75 0 0 0-6.74 2.74L3 8"/><path d="M3 3v5h5"/></svg>
                </button>
                <button id="zoomFitBtn" class="btn-ctrl" title="Fit to Screen" aria-label="Fit to Screen">
                  <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M8 3H5a2 2 0 0 0-2 2v3m18 0V5a2 2 0 0 0-2-2h-3m0 18h3a2 2 0 0 0 2-2v-3M3 16v3a2 2 0 0 0 2 2h3"/></svg>
                </button>
              </div>
              <button id="modalCloseBtn" class="btn-close" title="Close (ESC)" aria-label="Close">
                <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/></svg>
              </button>
            </div>
          </div>
          <div class="modal-body" id="modalBody">
            <div class="pan-zoom-stage" id="panZoomStage">
              <div class="pan-zoom-content" id="panZoomContent"></div>
            </div>
            <div class="modal-hint">💡 Tip: Click and drag to pan; use scroll wheel or keys (+, -, 0, ESC) to zoom.</div>
          </div>
        </div>
      </div>
    `;
    document.body.insertAdjacentHTML('beforeend', modalHtml);
    initModalEventListeners();
  }

  function updateTransform() {
    const content = document.getElementById('panZoomContent');
    const indicator = document.getElementById('zoomLevelIndicator');
    if (content) {
      content.style.transform = `translate(${translateX}px, ${translateY}px) scale(${currentScale})`;
    }
    if (indicator) {
      indicator.textContent = `${Math.round(currentScale * 100)}%`;
    }
  }

  function openDiagramModal(element, title) {
    ensureDiagramModalExists();
    const modal = document.getElementById('diagramModal');
    const titleEl = document.getElementById('modalTitle');
    const content = document.getElementById('panZoomContent');

    if (titleEl) {
      titleEl.textContent = title || 'Architecture Diagram Viewer';
    }

    if (content && element) {
      const cloned = element.cloneNode(true);
      cloned.removeAttribute('style');
      if (cloned.tagName.toLowerCase() === 'svg') {
        cloned.style.width = '100%';
        cloned.style.height = 'auto';
        cloned.style.minWidth = '750px';
      } else if (cloned.tagName.toLowerCase() === 'img') {
        cloned.style.maxWidth = '90vw';
        cloned.style.maxHeight = '80vh';
        cloned.style.objectFit = 'contain';
      }
      content.innerHTML = '';
      content.appendChild(cloned);
    }

    currentScale = 1.0;
    translateX = 0;
    translateY = 0;
    updateTransform();

    modal.classList.add('active');
    document.body.style.overflow = 'hidden';
  }

  function closeDiagramModal() {
    const modal = document.getElementById('diagramModal');
    if (modal) {
      modal.classList.remove('active');
      document.body.style.overflow = '';
    }
  }

  function initModalEventListeners() {
    const modal = document.getElementById('diagramModal');
    const backdrop = document.getElementById('modalBackdrop');
    const closeBtn = document.getElementById('modalCloseBtn');
    const zoomInBtn = document.getElementById('zoomInBtn');
    const zoomOutBtn = document.getElementById('zoomOutBtn');
    const zoomResetBtn = document.getElementById('zoomResetBtn');
    const zoomFitBtn = document.getElementById('zoomFitBtn');
    const modalBody = document.getElementById('modalBody');

    if (backdrop) backdrop.addEventListener('click', closeDiagramModal);
    if (closeBtn) closeBtn.addEventListener('click', closeDiagramModal);

    if (zoomInBtn) {
      zoomInBtn.addEventListener('click', () => {
        currentScale = Math.min(5.0, currentScale + 0.25);
        updateTransform();
      });
    }

    if (zoomOutBtn) {
      zoomOutBtn.addEventListener('click', () => {
        currentScale = Math.max(0.3, currentScale - 0.25);
        updateTransform();
      });
    }

    if (zoomResetBtn) {
      zoomResetBtn.addEventListener('click', () => {
        currentScale = 1.0;
        translateX = 0;
        translateY = 0;
        updateTransform();
      });
    }

    if (zoomFitBtn) {
      zoomFitBtn.addEventListener('click', () => {
        currentScale = 1.4;
        translateX = 0;
        translateY = 0;
        updateTransform();
      });
    }

    if (modalBody) {
      modalBody.addEventListener('mousedown', (e) => {
        if (e.button !== 0) return;
        isDragging = true;
        startX = e.clientX - translateX;
        startY = e.clientY - translateY;
        modalBody.style.cursor = 'grabbing';
      });

      window.addEventListener('mousemove', (e) => {
        if (!isDragging) return;
        translateX = e.clientX - startX;
        translateY = e.clientY - startY;
        updateTransform();
      });

      window.addEventListener('mouseup', () => {
        if (isDragging) {
          isDragging = false;
          if (modalBody) modalBody.style.cursor = 'grab';
        }
      });

      modalBody.addEventListener('wheel', (e) => {
        e.preventDefault();
        const zoomFactor = e.deltaY < 0 ? 1.15 : 0.88;
        currentScale = Math.min(5.0, Math.max(0.3, currentScale * zoomFactor));
        updateTransform();
      }, { passive: false });
    }

    window.addEventListener('keydown', (e) => {
      if (!modal || !modal.classList.contains('active')) return;
      if (e.key === 'Escape') {
        closeDiagramModal();
      } else if (e.key === '+' || e.key === '=') {
        currentScale = Math.min(5.0, currentScale + 0.25);
        updateTransform();
      } else if (e.key === '-' || e.key === '_') {
        currentScale = Math.max(0.3, currentScale - 0.25);
        updateTransform();
      } else if (e.key === '0') {
        currentScale = 1.0;
        translateX = 0;
        translateY = 0;
        updateTransform();
      }
    });
  }

  // ==========================================================================
  // 2. Resilient Mermaid 10 Async Rendering
  // ==========================================================================
  async function renderMermaidDiagrams() {
    if (!window.mermaid) {
      let retries = 0;
      const interval = setInterval(async () => {
        retries++;
        if (window.mermaid) {
          clearInterval(interval);
          await doRender();
        } else if (retries > 30) {
          clearInterval(interval);
          console.error('Timeout loading Mermaid.js from CDN.');
        }
      }, 150);
      return;
    }
    await doRender();

    async function doRender() {
      const isDark = document.documentElement.getAttribute('data-theme') === 'dark';
      mermaid.initialize({
        startOnLoad: false,
        theme: isDark ? 'dark' : 'neutral',
        securityLevel: 'loose',
        fontFamily: 'Google Sans, Inter, sans-serif'
      });

      const mermaidNodes = document.querySelectorAll('.mermaid');
      for (let i = 0; i < mermaidNodes.length; i++) {
        const el = mermaidNodes[i];
        if (!el.hasAttribute('data-raw-code')) {
          el.setAttribute('data-raw-code', el.textContent.trim());
        }
        const rawCode = el.getAttribute('data-raw-code');
        try {
          const uniqueId = `mermaid-svg-${Date.now()}-${i}`;
          const { svg, bindFunctions } = await mermaid.render(uniqueId, rawCode);
          el.innerHTML = svg;
          if (bindFunctions) bindFunctions(el);

          let wrapper = el.parentElement;
          if (!wrapper.classList.contains('mermaid-wrapper')) {
            wrapper = document.createElement('div');
            wrapper.className = 'mermaid-wrapper';
            el.parentNode.insertBefore(wrapper, el);
            wrapper.appendChild(el);
          }

          const oldBadge = wrapper.querySelector('.diagram-zoom-badge');
          if (oldBadge) oldBadge.remove();

          const zoomBadge = document.createElement('button');
          zoomBadge.className = 'diagram-zoom-badge';
          zoomBadge.innerHTML = '🔍 Expand / Zoom';
          zoomBadge.setAttribute('title', 'Click to open in high-resolution fullscreen modal');
          wrapper.appendChild(zoomBadge);

          const getDiagramTitle = () => {
            const card = wrapper.closest('.card') || wrapper.closest('.card-diagram') || wrapper.closest('.doc-section');
            return card ? (card.querySelector('.card-title')?.innerText || card.querySelector('.section-tag')?.innerText || 'Architecture Diagram') : 'Architecture Diagram';
          };

          zoomBadge.onclick = (e) => {
            e.stopPropagation();
            const svg = el.querySelector('svg');
            if (svg) openDiagramModal(svg, getDiagramTitle());
          };

          el.onclick = () => {
            const svg = el.querySelector('svg');
            if (svg) openDiagramModal(svg, getDiagramTitle());
          };

        } catch (err) {
          console.error(`Error in Diagram #${i + 1}:`, err);
          el.innerHTML = `
            <div style="background: #fce8e6; border: 1px solid #ea4335; border-radius: 8px; padding: 16px; margin: 12px 0;">
              <div style="color: #c5221f; font-weight: 600;">⚠️ Rendering Error in Diagram #${i + 1}</div>
              <div style="color: #3c4043; font-size: 13px;">${err.message || 'Invalid syntax'}</div>
            </div>
          `;
        }
      }

      document.querySelectorAll('.app-main img').forEach((img) => {
        img.style.cursor = 'zoom-in';
        img.onclick = () => openDiagramModal(img, img.alt || 'Architecture Image');
      });
    }
  }

  renderMermaidDiagrams();

  // ==========================================================================
  // 3. Theme Toggle (Light / Dark) with Persistence
  // ==========================================================================
  const themeToggle = document.getElementById('themeToggle');
  const savedTheme = localStorage.getItem('architecture-guide-theme') || 'light';
  document.documentElement.setAttribute('data-theme', savedTheme);

  if (themeToggle) {
    themeToggle.addEventListener('click', () => {
      const currentTheme = document.documentElement.getAttribute('data-theme');
      const newTheme = currentTheme === 'dark' ? 'light' : 'dark';
      document.documentElement.setAttribute('data-theme', newTheme);
      localStorage.setItem('architecture-guide-theme', newTheme);
      renderMermaidDiagrams();
    });
  }

  // ==========================================================================
  // 4. Active Navigation Tracking via IntersectionObserver
  // ==========================================================================
  const navLinks = document.querySelectorAll('.sidebar-nav .nav-link');
  const sections = document.querySelectorAll('.doc-section');

  const sectionObserver = new IntersectionObserver((entries) => {
    entries.forEach((entry) => {
      if (entry.isIntersecting) {
        const activeId = entry.target.getAttribute('id');
        navLinks.forEach((link) => {
          if (link.getAttribute('href') === `#${activeId}`) {
            link.classList.add('active');
          } else {
            link.classList.remove('active');
          }
        });
      }
    });
  }, { root: null, rootMargin: '-20% 0px -70% 0px', threshold: 0 });

  sections.forEach((sec) => sectionObserver.observe(sec));

  // ==========================================================================
  // 5. Interactive Architecture Decision Wizard & Sizing Engine
  // ==========================================================================
  const wizardSelect = document.getElementById('wizardWorkloadType');
  const wizardResult = document.getElementById('wizardResult');

  if (wizardSelect && wizardResult) {
    wizardSelect.addEventListener('change', () => {
      const val = wizardSelect.value;
      let title = 'Recommended Topology';
      let desc = 'Select your workload profile to view architectural recommendations.';

      if (val === 'agentic') {
        title = '🤖 GenAI Agent Runtime on GKE Autopilot + gVisor';
        desc = 'Requires sandboxed execution for dynamic tool calling, Vertex AI Context Caching, and low-latency Vector Search.';
      } else if (val === 'microservices') {
        title = '⚡ Cloud Run + Cloud Service Mesh';
        desc = 'Ideal for stateless, auto-scaling event-driven services with Cloud Armor WAF and Memorystore caching.';
      } else if (val === 'data-mesh') {
        title = '📊 BigQuery Lakehouse + dbt & Cloud Composer';
        desc = 'Optimized for high-throughput batch/stream analytics with Dataplex data governance and columnar partitioning.';
      }

      wizardResult.innerHTML = `
        <div class="recommendation-title">${title}</div>
        <div class="recommendation-desc">${desc}</div>
      `;
    });
  }

  const tcoSlider = document.getElementById('tcoVolumeSlider');
  const tcoPrice = document.getElementById('tcoEstimatedPrice');
  const tcoVolumeLabel = document.getElementById('tcoVolumeLabel');

  if (tcoSlider && tcoPrice) {
    tcoSlider.addEventListener('input', () => {
      const reqPerSec = parseInt(tcoSlider.value, 10);
      if (tcoVolumeLabel) tcoVolumeLabel.textContent = `${reqPerSec} req/sec`;
      // Baseline equation: Base compute ($150) + $0.85 per RPS per month
      const monthlyEst = Math.round(150 + (reqPerSec * 0.85 * 30));
      tcoPrice.textContent = `$${monthlyEst.toLocaleString()}/mo`;
    });
  }
});
