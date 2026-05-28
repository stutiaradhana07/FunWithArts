import { useEffect, useRef, useState } from 'react';
import { useNavigate } from 'react-router-dom';

const FONT_HREF =
  'https://fonts.googleapis.com/css2?family=Playfair+Display:ital,wght@0,400;0,600;1,400;1,600&family=Syne:wght@400;700&family=Lato:wght@300;400;700&display=swap';

// ── Whitelist of app-internal path prefixes ──
const APP_ROUTES = [
  '/account',
  '/orders',
  '/collection',
  '/cart',
  '/wishlist',
  '/checkout',
  '/contact',
  '/studio',
  '/login',
  '/forgot-password',
  '/reset-password',
  '/product/',
  '/search',
  '/about',
  '/legal',
  '/support',
  '/success',
  '/settings',
  '/addresses',
  '/order-history',
];

function isInternalAppLink(href) {
  if (!href) return false;
  if (href === '/') return true;
  return APP_ROUTES.some((route) => href.startsWith(route));
}

function shouldInterceptClick(target, href) {
  if (!href) return false;
  // Skip external links, anchors, mailto, tel, download, javascript, new-tab
  if (
    href.startsWith('http://') ||
    href.startsWith('https://') ||
    href.startsWith('mailto:') ||
    href.startsWith('tel:') ||
    href.startsWith('javascript:') ||
    href.startsWith('#')
  )
    return false;
  if (target && target !== '_self') return false;
  return isInternalAppLink(href);
}

function clearManagedNodes() {
  document.querySelectorAll(
    'style[data-legacy-style], link[data-legacy-link], script[data-legacy-script]'
  ).forEach((node) => node.remove());
  document.body.classList.remove('legacy-route-active');
}

function makeProductRouteSegment(productCard) {
  if (!productCard) return '';

  const slug = productCard.getAttribute('data-product-slug');
  if (slug) return slug;

  const liveId = productCard.getAttribute('data-product-id');
  if (liveId) return liveId;

  const title =
    productCard.querySelector('.product-title')?.textContent ||
    productCard.querySelector('h3')?.textContent ||
    '';

  if (title) {
    return title
      .toLowerCase()
      .replace(/[^a-z0-9]+/g, '-')
      .replace(/^-+|-+$/g, '');
  }

  return productCard.getAttribute('data-id') || '';
}

function buildActiveProduct(productCard) {
  if (!productCard) return null;

  const title =
    productCard.querySelector('.product-title')?.textContent ||
    productCard.querySelector('h3')?.textContent ||
    '';

  const priceRaw =
    productCard.getAttribute('data-base-price') ||
    productCard.querySelector('.price')?.textContent?.replace(/[^\d.]/g, '') ||
    '0';

  return {
    id: productCard.getAttribute('data-product-id') || productCard.getAttribute('data-id') || '',
    slug: productCard.getAttribute('data-product-slug') || '',
    title,
    price: Number(priceRaw) || 0,
    desc: productCard.getAttribute('data-desc') || '',
    img: productCard.querySelector('.product-image, img')?.getAttribute('src') || '',
  };
}

function ensureLegacyFonts() {
  const existing = document.querySelector('link[data-legacy-fonts]');
  if (existing) return;
  const link = document.createElement('link');
  link.rel = 'stylesheet';
  link.href = FONT_HREF;
  link.dataset.legacyFonts = 'true';
  document.head.appendChild(link);
}

function injectLegacyLinks(doc, source) {
  doc.head.querySelectorAll('link[rel="stylesheet"]').forEach((linkTag) => {
    const href = linkTag.getAttribute('href');
    if (!href || href.includes('fonts.googleapis.com')) return;
    const link = document.createElement('link');
    link.rel = 'stylesheet';
    link.href = href;
    link.dataset.legacyLink = source;
    if (linkTag.crossOrigin) {
      link.crossOrigin = linkTag.crossOrigin;
    }
    document.head.appendChild(link);
  });
}

export default function LegacyPage({ source, title }) {
  const ref = useRef(null);
  const [loading, setLoading] = useState(true);
  const navigate = useNavigate();
  const clickHandlerRef = useRef(null);

  // ── Enhanced click interceptor (capture phase) ──
  useEffect(() => {
    const container = ref.current;
    if (!container) return;

    function handleClick(e) {
      let path = null;

      // 1. Check for <a> tag
      let anchor = e.target;
      while (anchor && anchor !== container && anchor.tagName !== 'A') {
        anchor = anchor.parentElement;
      }

      if (anchor && anchor.tagName === 'A') {
        const rawHref = anchor.getAttribute('href');
        const linkTarget = anchor.getAttribute('target');

        if (rawHref && !rawHref.startsWith('javascript:') && !rawHref.startsWith('#')) {
          try {
            // Resolve relative paths (e.g., "wishlist.html" → "/wishlist") BEFORE checking
            const resolved = new URL(rawHref, window.location.origin);
            const fullPath = resolved.pathname + resolved.search + resolved.hash;

            if (shouldInterceptClick(linkTarget, fullPath)) {
              path = fullPath;
            }
          } catch (err) {
            console.warn('Failed to parse URL:', rawHref, err);
          }
        }
      }

      // 2. Check for .view-link (product cards)
      if (!path) {
        const viewLink = e.target.closest('.view-link');
        if (viewLink) {
          const productCard = viewLink.closest('.product-card');
          const productId = makeProductRouteSegment(productCard);

          if (productId) {
            const product = buildActiveProduct(productCard);
            if (product) {
              localStorage.setItem('udaan_active_product', JSON.stringify(product));
            }
            path = `/product/${productId}`;
          }
        }
      }

      // 3. Check for data-target attribute (custom triggers)
      if (!path) {
        const dataTarget = e.target.closest('[data-target]');
        if (dataTarget) {
          const target = dataTarget.getAttribute('data-target');
          if (target && !target.startsWith('http')) {
            path = target;
          }
        }
      }

      if (path) {
        // Normalize path
        path = path.replace(/\.html$/, '');
        path = path.replace(/\/index\.html?$/, '/');
        path = path.replace(/\/legacy-index\.html?$/, '/');
        if (path === '/index' || path === '/legacy-index') path = '/';
        if (!path.startsWith('/')) path = '/' + path;

        // Kill all legacy transition/wipe handlers
        e.preventDefault();
        e.stopPropagation();
        e.stopImmediatePropagation();

        // True SPA navigation
        navigate(path);
        return;
      }
    }

    container.addEventListener('click', handleClick, true); // capture phase
    clickHandlerRef.current = handleClick;

    return () => {
      container.removeEventListener('click', clickHandlerRef.current, true);
    };
  }, [navigate, source]);

  useEffect(() => {
    let cancelled = false;
    const activeRafs = [];
    const originalRaf = window.requestAnimationFrame;
    const originalCancelRaf = window.cancelAnimationFrame;

    // Track original Lenis
    if (window.Lenis && !window.__original_lenis__) {
      window.__original_lenis__ = window.Lenis;
    }
    window.__active_lenis_instances__ = window.__active_lenis_instances__ || [];

    // Setup Lenis interceptor
    if (window.__original_lenis__) {
      window.Lenis = class InterceptedLenis extends window.__original_lenis__ {
        constructor(...args) {
          super(...args);
          this.__is_destroyed__ = false;
          window.__active_lenis_instances__.push(this);
        }
        raf(...args) {
          if (this.__is_destroyed__) return;
          return super.raf(...args);
        }
        destroy() {
          this.__is_destroyed__ = true;
          super.destroy();
        }
      };
    }

    // Setup requestAnimationFrame interceptor to auto-collect and clean up all loops
    window.requestAnimationFrame = (callback) => {
      const id = originalRaf((time) => {
        if (!cancelled) {
          callback(time);
        }
      });
      activeRafs.push(id);
      return id;
    };

    window.cancelAnimationFrame = (id) => {
      const idx = activeRafs.indexOf(id);
      if (idx > -1) activeRafs.splice(idx, 1);
      return originalCancelRaf(id);
    };

    async function loadPage() {
      setLoading(true);
      clearManagedNodes();
      if (ref.current) {
        ref.current.innerHTML = '';
      }

      const response = await fetch(`/${source}`);
      const html = await response.text();
      if (cancelled) return;

      const doc = new DOMParser().parseFromString(html, 'text/html');
      document.title = doc.title || title || document.title;

      ensureLegacyFonts();
      injectLegacyLinks(doc, source);
      document.body.classList.add('legacy-route-active');

      doc.head.querySelectorAll('style').forEach((styleTag) => {
        const style = document.createElement('style');
        style.dataset.legacyStyle = source;
        style.textContent = styleTag.textContent;
        document.head.appendChild(style);
      });

      const bodyClone = doc.body.cloneNode(true);
      bodyClone.querySelectorAll('script[src]').forEach((script) => script.remove());
      bodyClone.querySelectorAll('script').forEach((script) => script.remove());

      if (ref.current) {
        ref.current.innerHTML = bodyClone.innerHTML;
      }

      doc.body.querySelectorAll('script:not([src])').forEach((scriptTag) => {
        const script = document.createElement('script');
        script.dataset.legacyScript = source;
        if (scriptTag.textContent) {
          script.textContent = scriptTag.textContent;
        }
        document.body.appendChild(script);
      });

      if (ref.current && window.UdaanAPI) {
        window.UdaanAPI.wireNewsletterForms(ref.current);
        window.UdaanAPI.wireAccountNav(ref.current);
        window.UdaanAPI.wireSiteSearchForms(ref.current);
        window.UdaanAPI.updateBadges();
      }

      setLoading(false);
    }

    loadPage().catch(() => {
      if (!cancelled) {
        setLoading(false);
      }
    });

    return () => {
      cancelled = true;

      // Restore original requestAnimationFrame and cancel all pending animation frames
      window.requestAnimationFrame = originalRaf;
      window.cancelAnimationFrame = originalCancelRaf;
      activeRafs.forEach((id) => originalCancelRaf(id));

      // Destroy all active Lenis scroll managers created during this page session
      if (window.__active_lenis_instances__) {
        window.__active_lenis_instances__.forEach((instance) => {
          try {
            instance.destroy();
          } catch (e) {
            console.warn('Failed to destroy Lenis instance:', e);
          }
        });
        window.__active_lenis_instances__ = [];
      }

      // Restore original Lenis
      if (window.__original_lenis__) {
        window.Lenis = window.__original_lenis__;
      }

      clearManagedNodes();
      if (ref.current) {
        ref.current.innerHTML = '';
      }
    };
  }, [source, title]);

  // ── Render (loading screen removed) ──
  return (
    <div className="legacy-page-shell">
      <div ref={ref} className="legacy-page-content" key={source} />
    </div>
  );
}
