import { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';

export default function BlogNavbar() {
  const [isLoggedIn, setIsLoggedIn] = useState(false);

  useEffect(() => {
    const syncAuth = () => {
      const auth = window.UdaanAPI?.getAuth?.();
      setIsLoggedIn(Boolean(auth?.token));
    };

    syncAuth();
    document.addEventListener('udaan:auth-change', syncAuth);

    return () => {
      document.removeEventListener('udaan:auth-change', syncAuth);
    };
  }, []);

  useEffect(() => {
    window.UdaanAPI?.updateBadges?.();
  }, []);

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
      </div>
    </nav>
  );
}
