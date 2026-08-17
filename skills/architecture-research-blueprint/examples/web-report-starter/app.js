/**
 * Architecture Web Report - Google Cloud Clean Engineering JS Engine
 * Features:
 * - Robust individual Mermaid 10 async rendering with try/catch & theme cache
 * - Fullscreen Lightbox Modal with Zoom In/Out/Reset/Fit, Mouse Pan Drag, Wheel Zoom & Shortcuts
 * - Theme Switcher (Dark/Light) with localStorage persistence
 * - Sticky Navigation tracking via IntersectionObserver
 */

document.addEventListener('DOMContentLoaded', () => {
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
              <h3 class="modal-title" id="modalTitle">Visualizador de Arquitetura em Alta Resolução</h3>
            </div>
            <div class="modal-actions">
              <div class="zoom-controls">
                <button id="zoomOutBtn" class="btn-ctrl" title="Diminuir Zoom (-)" aria-label="Diminuir Zoom">
                  <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="11" cy="11" r="8"/><line x1="21" y1="21" x2="16.65" y2="16.65"/><line x1="8" y1="11" x2="14" y2="11"/></svg>
                </button>
                <span id="zoomLevelIndicator" class="zoom-indicator">100%</span>
                <button id="zoomInBtn" class="btn-ctrl" title="Aumentar Zoom (+)" aria-label="Aumentar Zoom">
                  <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="11" cy="11" r="8"/><line x1="21" y1="21" x2="16.65" y2="16.65"/><line x1="11" y1="8" x2="11" y2="14"/><line x1="8" y1="11" x2="14" y2="11"/></svg>
                </button>
                <button id="zoomResetBtn" class="btn-ctrl" title="Redefinir Zoom (100%)" aria-label="Redefinir Zoom">
                  <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M3 12a9 9 0 1 0 9-9 9.75 9.75 0 0 0-6.74 2.74L3 8"/><path d="M3 3v5h5"/></svg>
                </button>
                <button id="zoomFitBtn" class="btn-ctrl" title="Ajustar à Tela" aria-label="Ajustar à Tela">
                  <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M8 3H5a2 2 0 0 0-2 2v3m18 0V5a2 2 0 0 0-2-2h-3m0 18h3a2 2 0 0 0 2-2v-3M3 16v3a2 2 0 0 0 2 2h3"/></svg>
                </button>
              </div>
              <button id="modalCloseBtn" class="btn-close" title="Fechar (ESC)" aria-label="Fechar">
                <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/></svg>
              </button>
            </div>
          </div>
          <div class="modal-body" id="modalBody">
            <div class="pan-zoom-stage" id="panZoomStage">
              <div class="pan-zoom-content" id="panZoomContent"></div>
            </div>
            <div class="modal-hint">💡 Dica: Arraste com o mouse para mover e use o Scroll para controlar o zoom.</div>
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
      titleEl.textContent = title || 'Visualizador de Arquitetura';
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
          console.error('Timeout ao carregar Mermaid.js da CDN.');
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
          zoomBadge.innerHTML = '🔍 Expandir / Zoom';
          zoomBadge.setAttribute('title', 'Clique para abrir em tela cheia com zoom interativo');
          wrapper.appendChild(zoomBadge);

          const getDiagramTitle = () => {
            const card = wrapper.closest('.card') || wrapper.closest('.card-diagram') || wrapper.closest('.doc-section');
            return card ? (card.querySelector('.card-title')?.innerText || card.querySelector('.section-tag')?.innerText || 'Diagrama de Arquitetura') : 'Diagrama de Arquitetura';
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
          console.error(`Erro no Diagrama #${i + 1}:`, err);
          el.innerHTML = `
            <div style="background: #fce8e6; border: 1px solid #ea4335; border-radius: 8px; padding: 16px; margin: 12px 0;">
              <div style="color: #c5221f; font-weight: 600;">⚠️ Erro de Renderização no Diagrama #${i + 1}</div>
              <div style="color: #3c4043; font-size: 13px;">${err.message || 'Sintaxe inválida'}</div>
            </div>
          `;
        }
      }

      document.querySelectorAll('.app-main img').forEach((img) => {
        img.style.cursor = 'zoom-in';
        img.onclick = () => openDiagramModal(img, img.alt || 'Imagem de Arquitetura');
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
});
