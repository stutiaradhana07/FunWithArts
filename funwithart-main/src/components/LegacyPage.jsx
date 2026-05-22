import { useEffect, useRef, useState } from 'react';
import { useNavigate } from 'react-router-dom';

const FONT_HREF =
  'https://fonts.googleapis.com/css2?family=Playfair+Display:ital,wght@0,400;0,600;1,400;1,600&family=Syne:wght@400;700&family=Lato:wght@300;400;700&display=swap';

// ── Whitelist of app-internal path prefixes that should use client-side routing ──
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
];

function isInternalAppLink(href) {
  if (!href) return false;
  // Match root path exactly
  if (href === '/') return true;
  // Match any whitelisted prefix
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
  // Skip if target is _blank
  if (target && target !== '_self') return false;
  // Skip if the anchor has a download attribute
  const el = target;
  // Only intercept internal app links
  return isInternalAppLink(href);
}

function clearManagedNodes() {
  document.querySelectorAll(
    'style[data-legacy-style], link[data-legacy-link], script[data-legacy-script]'
  ).forEach((node) => {
    node.remove();
  });
  document.body.classList.remove('legacy-route-active');
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
  const [contentKey, setContentKey] = useState(0);
  const navigate = useNavigate();
  const clickHandlerRef = useRef(null);

  // ── Click interceptor: route internal links through React Router ──
  useEffect(() => {
    const container = ref.current;
    if (!container) return;

    function handleClick(e) {
      // Walk up from the clicked element to find the nearest <a>
      let anchor = e.target;
      while (anchor && anchor !== container && anchor.tagName !== 'A') {
        anchor = anchor.parentElement;
      }
      if (!anchor || anchor.tagName !== 'A') return;

      const rawHref = anchor.getAttribute('href');
      const linkTarget = anchor.getAttribute('target');

      if (!shouldInterceptClick(linkTarget, rawHref)) return;

      e.preventDefault();
      // Resolve relative paths against the current origin
      const resolved = new URL(rawHref, window.location.origin);
      navigate(resolved.pathname + resolved.search + resolved.hash);
    }

    container.addEventListener('click', handleClick, true); // capture phase
    clickHandlerRef.current = handleClick;

    return () => {
      container.removeEventListener('click', clickHandlerRef.current, true);
    };
  }, [navigate, contentKey]);

  useEffect(() => {
    let cancelled = false;

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
      clearManagedNodes();
      if (ref.current) {
        ref.current.innerHTML = '';
      }
    };
  }, [source, title]);

  useEffect(() => {
    setContentKey((k) => k + 1);
  }, [source]);

  return (
    <div className="legacy-page-shell">
      {loading ? <div className="legacy-loading">Loading studio...</div> : null}
      <div ref={ref} className="legacy-page-content" key={contentKey} />
    </div>
  );
}
