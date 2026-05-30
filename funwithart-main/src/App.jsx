import { useEffect, useState } from 'react';
import { Navigate, Route, Routes, useLocation, useParams } from 'react-router-dom';
import LegacyPage from './components/LegacyPage';
import IntroSplash, { markIntroSeen, shouldShowIntro } from './components/IntroSplash';
import BlogIndex from './components/BlogIndex';
import BlogPost from './components/BlogPost';


function ProductRoute() {
  const { id } = useParams();

  useEffect(() => {
    try {
      const existing = localStorage.getItem('udaan_active_product');
      const parsed = existing ? JSON.parse(existing) : {};
      localStorage.setItem(
        'udaan_active_product',
        JSON.stringify({
          ...parsed,
          slug: parsed?.slug || id,
          id: parsed?.id || id,
        })
      );
    } catch (error) {
      localStorage.setItem('udaan_active_product', JSON.stringify({ id, slug: id }));
    }
  }, [id]);

  return <LegacyPage source="product.html" title="Product Details | Fun With Art" />;
}

export default function App() {
  const location = useLocation();
  const [showIntro, setShowIntro] = useState(() => shouldShowIntro(location.pathname));
  const [homeRevealed, setHomeRevealed] = useState(false);

  useEffect(() => {
    // Clear scroll locks on any page transition
    document.body.classList.remove('drawer-open');

    const onHome = shouldShowIntro(location.pathname);
    if (onHome) {
      // Mark as seen IMMEDIATELY so navigating away and back never re-triggers the splash
      markIntroSeen();
      setHomeRevealed(false);
    }
    setShowIntro(onHome);
  }, [location.pathname]);

  // ── Shell class composition ──
  const isBlogRoute = location.pathname.startsWith('/blogs');
  const shellClass = [
    'legacy-page-shell',
    showIntro && !homeRevealed ? 'legacy-page-shell--intro-pending' : '',
    isBlogRoute ? 'legacy-page-shell--blog' : '',
  ]
    .filter(Boolean)
    .join(' ');

  return (
    <>
      {showIntro ? (
        <IntroSplash
          onExitStart={() => setHomeRevealed(true)}
          onComplete={() => setShowIntro(false)}
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
      <Route path="/about" element={<LegacyPage source="about.html" title="Our Story | Fun With Art" />} />
      <Route path="/legal" element={<LegacyPage source="legal.html" title="Legal | Fun With Art" />} />
      <Route path="/login" element={<LegacyPage source="login.html" title="Account | Fun With Art" />} />
      <Route path="/forgot-password" element={<LegacyPage source="forgot-password.html" title="Forgot Password | Fun With Art" />} />
      <Route path="/reset-password" element={<LegacyPage source="reset-password.html" title="Create New Password | Fun With Art" />} />
      <Route path="/order-history" element={<LegacyPage source="order-history.html" title="Your Orders | Fun With Art" />} />
      <Route path="/support" element={<LegacyPage source="support.html" title="Support | Fun With Art" />} />
      <Route path="/account" element={<LegacyPage source="account.html" title="My Account | Fun With Art" />} />
      <Route path="/orders" element={<LegacyPage source="orders.html" title="Track Your Order | Fun With Art" />} />
      <Route path="/settings" element={<LegacyPage source="settings.html" title="Settings | Fun With Art" />} />
      <Route path="/addresses" element={<LegacyPage source="addresses.html" title="Saved Addresses | Fun With Art" />} />
      <Route path="/product/:id" element={<ProductRoute />} />
      <Route path="/search" element={<LegacyPage source="search.html" title="Search | Fun With Art" />} />
      <Route path="/blogs" element={<BlogIndex />} />
      <Route path="/blogs/:slug" element={<BlogPost />} />
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
      </div>
    </>
  );
}
