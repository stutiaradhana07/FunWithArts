import { useEffect, useRef, useState } from 'react';
import { Link, useParams } from 'react-router-dom';

function formatBlogDate(dateStr) {
  if (!dateStr) return '';
  const date = new Date(dateStr);
  return date.toLocaleDateString('en-US', {
    year: 'numeric',
    month: 'long',
    day: 'numeric',
  });
}

export default function BlogPost() {
  const { slug } = useParams();
  const [post, setPost] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const headerRef = useRef(null);
  const [scrollY, setScrollY] = useState(0);

  useEffect(() => {
    let cancelled = false;

    async function load() {
      try {
        const data = await window.UdaanAPI.fetchBlogPost(slug);
        if (!cancelled) {
          setPost(data);
          document.title = `${data.title} | Fun With Art`;
        }
      } catch (err) {
        if (!cancelled) {
          if (err.message && (err.message.includes('404') || err.message.includes('not found'))) {
            setError('not_found');
          } else {
            setError('load_error');
          }
        }
      } finally {
        if (!cancelled) setLoading(false);
      }
    }

    load();
    return () => { cancelled = true; };
  }, [slug]);

  useEffect(() => {
    const onScroll = () => setScrollY(window.scrollY);
    window.addEventListener('scroll', onScroll, { passive: true });
    return () => window.removeEventListener('scroll', onScroll);
  }, []);

  if (loading) {
    return (
      <div className="blog-loading">
        <div className="blog-loading__spinner" />
        <p>Opening the kiln…</p>
      </div>
    );
  }

  if (error === 'not_found') {
    return (
      <div className="blog-error">
        <svg width="56" height="56" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
          <circle cx="12" cy="12" r="10" />
          <line x1="12" y1="8" x2="12" y2="12" />
          <line x1="12" y1="16" x2="12.01" y2="16" />
        </svg>
        <h1>Story Not Found</h1>
        <p>This article may have been moved or is no longer available.</p>
        <Link to="/blogs" className="blog-cta-btn">← Back to Stories</Link>
      </div>
    );
  }

  if (error || !post) {
    return (
      <div className="blog-error">
        <p>Something went wrong loading this story. Please try again.</p>
        <Link to="/blogs" className="blog-cta-btn">← Back to Stories</Link>
      </div>
    );
  }

  return (
    <div className="blog-post" ref={headerRef}>
      {/* ── Nav ── */}
      <nav className="blog-nav">
        <Link to="/" className="blog-nav__logo">Fun With Art</Link>
        <div className="blog-nav__links">
          <Link to="/collection">Collection</Link>
          <Link to="/studio">Studio</Link>
          <Link to="/blogs">Blogs</Link>
        </div>
      </nav>

      {/* ── Immersive Parallax Header ── */}
      <header className="blog-header">
        <div
          className="blog-header__bg"
          style={{ transform: `translateY(${scrollY * 0.35}px)` }}
        >
          <img src={post.cover_image} alt={post.title} />
          <div className="blog-header__gradient" />
        </div>
      </header>

      {/* ── Title Block ── */}
      <section className="blog-title-block">
        <div className="blog-title-block__inner">
          <Link to="/blogs" className="blog-title-block__back">
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <line x1="19" y1="12" x2="5" y2="12" />
              <polyline points="12 19 5 12 12 5" />
            </svg>
            All Stories
          </Link>
          <h1 className="blog-title-block__title">{post.title}</h1>
          <div className="blog-title-block__meta">
            <span>By {post.author_name || 'Udaan Studio'}</span>
            <span className="blog-title-block__sep">·</span>
            <span>{formatBlogDate(post.created_at)}</span>
          </div>
        </div>
      </section>

      {/* ── Reading Column ── */}
      <main className="blog-content">
        <div className="blog-content__body">
          {post.content ? (
            <div
              className="blog-content__html"
              dangerouslySetInnerHTML={{ __html: post.content }}
            />
          ) : (
            <p className="blog-content__fallback">
              This story is still being written. Check back soon for the full article.
            </p>
          )}
        </div>
      </main>

      {/* ── Call to Action ── */}
      <section className="blog-cta">
        <div className="blog-cta__inner">
          <h2>Inspired by the craft?</h2>
          <p>Explore our handcrafted collection — each piece carries its own story.</p>
          <Link to="/collection" className="blog-cta-btn">
            Shop the Studio
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <line x1="5" y1="12" x2="19" y2="12" />
              <polyline points="12 5 19 12 12 19" />
            </svg>
          </Link>
        </div>
      </section>

      {/* ── Footer ── */}
      <footer className="blog-footer">
        <div className="blog-footer__inner">
          <p>© {new Date().getFullYear()} Fun With Art — Handcrafted in New Delhi</p>
          <div className="blog-footer__links">
            <Link to="/contact">Contact</Link>
            <Link to="/support">Support</Link>
            <Link to="/legal">Legal</Link>
          </div>
        </div>
      </footer>
    </div>
  );
}