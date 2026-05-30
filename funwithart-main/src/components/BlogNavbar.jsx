import { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';

export default function BlogNavbar() {
  const [isLoggedIn, setIsLoggedIn] = useState(false);
  const [isDrawerOpen, setIsDrawerOpen] = useState(false);

  useEffect(() => {
    const syncAuth = () => {
      const auth = window.UdaanAPI?.getAuth?.();
      setIsLoggedIn(Boolean(auth?.token));
    };

    syncAuth();
    document.addEventListener('udaan:auth-change', syncAuth);

    return () => {
      document.removeEventListener('udaan:auth-change', syncAuth);
      document.body.classList.remove('drawer-open');
    };
  }, []);

  useEffect(() => {
    window.UdaanAPI?.updateBadges?.();
  }, [isDrawerOpen]); // Re-sync badges on drawer opening

  const toggleDrawer = () => {
    const nextState = !isDrawerOpen;
    setIsDrawerOpen(nextState);
    document.body.classList.toggle('drawer-open', nextState);
  };

  const desktopAccountClass = isLoggedIn ? 'is-logged-in' : '';
  const primaryAccountClass = isLoggedIn ? 'nav-account-link is-logged-in' : 'nav-account-link';

  return (
    <nav id="main-nav">
      <Link to="/" className="logo-fusion">
        <span className="english-part">FUN WITH </span>
        <span className="hindi-char">Art</span>
      </Link>

      <div className="nav-links desktop-links blog-nav-links">
        <Link to="/">Home</Link>
        <Link to="/collection">Collection</Link>
        <Link to="/studio">Studio</Link>
        <Link to="/blogs" className="active">Blogs</Link>
        <Link to={isLoggedIn ? '/account' : '/login?tab=register'} className={desktopAccountClass}>
          {isLoggedIn ? 'My Account' : 'Sign Up'}
        </Link>
      </div>

      <div className="nav-actions">
        <Link to={isLoggedIn ? '/account' : '/login'} className={primaryAccountClass}>
          {isLoggedIn ? 'Account' : 'Sign In'}
        </Link>
        <Link to="/search" className="nav-icon" aria-label="Search" title="Search">
          <svg viewBox="0 0 24 24">
            <circle cx="11" cy="11" r="7" />
            <line x1="16.5" y1="16.5" x2="21" y2="21" />
          </svg>
        </Link>
        <Link to="/wishlist" className="nav-icon" aria-label="Open Wishlist">
          <svg viewBox="0 0 24 24">
            <path d="M20.84 4.61a5.5 5.5 0 0 0-7.78 0L12 5.67l-1.06-1.06a5.5 5.5 0 0 0-7.78 7.78l1.06 1.06L12 21.23l7.78-7.78 1.06-1.06a5.5 5.5 0 0 0 0-7.78z" />
          </svg>
          <span className="badge-count" id="wishlist-count">0</span>
        </Link>
        <Link to="/cart" className="nav-icon" aria-label="Open Cart">
          <svg viewBox="0 0 24 24" stroke="currentColor" strokeWidth="1.5" fill="none">
            <path d="M6 2L3 6v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2V6l-3-4z" />
            <line x1="3" y1="6" x2="21" y2="6" />
            <path d="M16 10a4 4 0 0 1-8 0" />
          </svg>
          <span className="badge-count" id="cart-count">0</span>
        </Link>
        
        {/* Responsive Mobile Hamburger Button */}
        <button
          className={`mobile-hamburger-btn ${isDrawerOpen ? 'active' : ''}`}
          onClick={toggleDrawer}
          aria-label="Toggle Navigation"
        >
          <span className="hamburger-line line-1"></span>
          <span className="hamburger-line line-2"></span>
          <span className="hamburger-line line-3"></span>
        </button>
      </div>

      {/* Responsive Mobile Menu Drawer */}
      <div
        className={`mobile-drawer-overlay ${isDrawerOpen ? 'active' : ''}`}
        onClick={(e) => {
          if (e.target === e.currentTarget) toggleDrawer();
        }}
      >
        <div className="mobile-drawer">
          <div className="mobile-drawer-header">
            <Link to="/" className="logo-fusion mobile-logo" onClick={toggleDrawer}>
              <span className="english-part">FUN WITH </span>
              <span className="hindi-char">Art</span>
            </Link>
            <button className="mobile-drawer-close" onClick={toggleDrawer} aria-label="Close menu">
              ✕
            </button>
          </div>
          <div className="mobile-drawer-links">
            <Link to="/" className="mobile-nav-link" onClick={toggleDrawer}>
              Home
            </Link>
            <Link to="/collection" className="mobile-nav-link" onClick={toggleDrawer}>
              Collection
            </Link>
            <Link to="/studio" className="mobile-nav-link" onClick={toggleDrawer}>
              Studio
            </Link>
            <Link to="/blogs" className="mobile-nav-link active" onClick={toggleDrawer}>
              Blogs
            </Link>
            <hr className="mobile-drawer-divider" />
            <Link to="/wishlist" className="mobile-nav-link mobile-wishlist-link" onClick={toggleDrawer}>
              <span>Wishlist</span>
              <span className="mobile-badge-count wishlist-count-badge">0</span>
            </Link>
            <Link to="/cart" className="mobile-nav-link mobile-cart-link" onClick={toggleDrawer}>
              <span>Your Bag</span>
              <span className="mobile-badge-count cart-count-badge">0</span>
            </Link>
            <hr className="mobile-drawer-divider" />
            <Link to={isLoggedIn ? '/account' : '/login'} className="mobile-nav-link mobile-auth-link" onClick={toggleDrawer}>
              {isLoggedIn ? 'My Account' : 'Sign In'}
            </Link>
          </div>
        </div>
      </div>
    </nav>
  );
}
