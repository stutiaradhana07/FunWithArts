import { useEffect, useRef, useState } from 'react';
import { Navigate, Route, Routes, useLocation, useParams } from 'react-router-dom';
import LegacyPage from './components/LegacyPage';
import IntroSplash, { markIntroSeen, shouldShowIntro } from './components/IntroSplash';
import BlogIndex from './components/BlogIndex';
import BlogPost from './components/BlogPost';

// ── Timing constants (ms) ──
const CURTAIN_DURATION = 1050;  // matches CSS curtainSweep
const EXIT_DURATION = 350;      // pageExit
const ENTER_DELAY = 420;       // start bloom after curtain fully covers

/* ── Multi‑layered pottery‑inspired page‑transition overlay ── */
function PageTransitionOverlay({ active }) {
  return (
    <div
      className={`page-transition-overlay${active ? ' page-transition-overlay--active' : ''}`}
      aria-hidden="true"
    >
      <div className="page-transition-curtain">
        <div className="page-transition-curtain__base" />
        <div className="page-transition-curtain__glow" />
        <div className="page-transition-curtain__noise" />
        <div className="page-transition-curtain__sheen" />
        <div className="page-transition-curtain__speckles" />
      </div>
    </div>
  );
}

function ProductRoute() {
  const { id } = useParams();
  const [ready, setReady] = useState(false);

  useEffect(() => {
    let cancelled = false;

    async function prepare() {
      try {
        const products = await window.UdaanAPI.fetchProducts();
        const product = products.find(
          (item) => String(item.id) === String(id) || window.UdaanAPI.normalize(item.name) === window.UdaanAPI.normalize(id)
        );

        if (product) {
          const payload = {
            id: product.id,
            title: product.name,
            price: Number(product.price),
            desc: product.description || '',
            img: product.image_url || product.image || '',
          };
          localStorage.setItem('udaan_active_product', JSON.stringify(payload));
        } else {
          localStorage.removeItem('udaan_active_product');
        }
      } catch (error) {
        // Leave the legacy page to show its own fallback state.
      }

      if (!cancelled) {
        setReady(true);
      }
    }

    prepare();
    return () => {
      cancelled = true;
    };
  }, [id]);

  if (!ready) {
    return <div className="legacy-loading">Loading studio...</div>;
  }

  return <LegacyPage source="product.html" title="Product Details | Fun With Art" />;
}

export default function App() {
  const location = useLocation();
  const [showIntro, setShowIntro] = useState(() => shouldShowIntro(location.pathname));
  const [homeRevealed, setHomeRevealed] = useState(false);
  const [transitioning, setTransitioning] = useState(false);
  const [phase, setPhase] = useState('idle'); // 'idle' | 'exiting' | 'entering'
  const prevPath = useRef(location.pathname);
  const timers = useRef([]);

  // ── Orchestrated page‑transition sequence ──
  useEffect(() => {
    if (prevPath.current === location.pathname) return;
    prevPath.current = location.pathname;

    // Clear any stale timers
    timers.current.forEach(clearTimeout);
    timers.current = [];

    // 1. Exit animation on current page
    setPhase('exiting');

    // 2. Fire curtain
    setTransitioning(true);

    // 3. After exit completes, switch to entering phase (new content rendered by React)
    const t1 = setTimeout(() => {
      setPhase('entering');
    }, EXIT_DURATION);

    // 4. Curtain finishes, reset everything
    const t2 = setTimeout(() => {
      setTransitioning(false);
      setPhase('idle');
    }, CURTAIN_DURATION);

    timers.current = [t1, t2];

    return () => {
      timers.current.forEach(clearTimeout);
    };
  }, [location.pathname]);

  useEffect(() => {
    const onHome = shouldShowIntro(location.pathname);
    setShowIntro(onHome);
    if (onHome) setHomeRevealed(false);
  }, [location.pathname]);

  // ── Shell class composition ──
  const shellClass = [
    'legacy-page-shell',
    showIntro && !homeRevealed ? 'legacy-page-shell--intro-pending' : '',
    phase === 'exiting' ? 'legacy-page-shell--exiting' : '',
    phase === 'entering' ? 'legacy-page-shell--entering' : '',
  ]
    .filter(Boolean)
    .join(' ');

  return (
    <>
      <PageTransitionOverlay active={transitioning} />

      {showIntro ? (
        <IntroSplash
          onExitStart={() => setHomeRevealed(true)}
          onComplete={() => { markIntroSeen(); setShowIntro(false); }}
        />
      ) : null}
      <div className={shellClass}>
      <Routes>
      <Route path="/" element={<LegacyPage source="legacy-index.html" title="Fun With Art | Handcrafted in New Delhi" />} />
      <Route path="/collection" element={<LegacyPage source="collection.html" title="The Archive | Fun With Art" />} />
      <Route path="/cart" element={<LegacyPage source="cart.html" title="Your Bag | Fun With Art" />} />
      <Route path="/wishlist" element={<LegacyPage source="wishlist.html" title="Saved | Fun With Art" />} />
      <Route path="/checkout" element={<LegacyPage source="checkout.html" title="Checkout | Fun With Art" />} />
      <Route path="/contact" element={<LegacyPage source="contact.html" title="Contact Us | Fun With Art" />} />
      <Route path="/studio" element={<LegacyPage source="studio.html" title="The Studio | Fun With Art" />} />
      <Route path="/login" element={<LegacyPage source="login.html" title="Account | Fun With Art" />} />
      <Route path="/forgot-password" element={<LegacyPage source="forgot-password.html" title="Forgot Password | Fun With Art" />} />
      <Route path="/reset-password" element={<LegacyPage source="reset-password.html" title="Create New Password | Fun With Art" />} />
      <Route path="/account" element={<LegacyPage source="account.html" title="My Account | Fun With Art" />} />
      <Route path="/orders" element={<LegacyPage source="orders.html" title="Track Your Order | Fun With Art" />} />
      <Route path="/product/:id" element={<ProductRoute />} />
      <Route path="/blogs" element={<BlogIndex />} />
      <Route path="/blogs/:slug" element={<BlogPost />} />
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
      </div>
    </>
  );
}
