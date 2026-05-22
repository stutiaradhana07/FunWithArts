import { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';

function formatBlogDate(dateStr) {
  if (!dateStr) return '';
  const date = new Date(dateStr);
  return date.toLocaleDateString('en-US', {
    year: 'numeric',
    month: 'long',
    day: 'numeric',
  });
}

function BlogCard({ post, featured }) {
  if (featured) {
    return (
      <Link to={`/blogs/${post.slug}`} className="blog-hero-card">
        <div className="blog-hero-card__image">
          <img src={post.cover_image} alt={post.title} />
          <div className="blog-hero-card__overlay" />
          <div className="blog-hero-card__content">
            <span className="blog-hero-card__label">Featured Story</span>
            <h1 className="blog-hero-card__title">{post.title}</h1>
            <p className="blog-hero-card__excerpt">{post.excerpt}</p>
            <span className="blog-hero-card__cta">
              Read Story
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                <line x1="5" y1="12" x2="19" y2="12" />
                <polyline points="12 5 19 12 12 19" />
              </svg>
            </span>
          </div>
        </div>
      </Link>
    );
  }

  return (
    <Link to={`/blogs/${post.slug}`} className="blog-card">
      <div className="blog-card__image-wrap">
        <img src={post.cover_image} alt={post.title} className="blog-card__image" />
      </div>
      <div className="blog-card__body">
        <h3 className="blog-card__title">{post.title}</h3>
        <p className="blog-card__excerpt">{post.excerpt}</p>
        <div className="blog-card__meta">
          <span className="blog-card__author">By {post.author_name || 'Udaan Studio'}</span>
          <span className="blog-card__sep">·</span>
          <span className="blog-card__date">{formatBlogDate(post.created_at)}</span>
        </div>
      </div>
    </Link>
  );
}

export default function BlogIndex() {
  const [posts, setPosts] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    let cancelled = false;

    async function load() {
      try {
        const data = await window.UdaanAPI.fetchBlogPosts();
        if (!cancelled) {
          setPosts(Array.isArray(data) ? data : []);
        }
      } catch (err) {
        if (!cancelled) {
          setError('Unable to load stories. Please try again.');
        }
      } finally {
        if (!cancelled) setLoading(false);
      }
    }

    load();
    return () => { cancelled = true; };
  }, []);

  if (loading) {
    return (
      <div className="blog-loading">
        <div className="blog-loading__spinner" />
        <p>Gathering stories from the studio…</p>
      </div>
    );
  }

  if (error) {
    return (
      <div className="blog-error">
        <p>{error}</p>
      </div>
    );
  }

  if (posts.length === 0) {
    return (
      <div className="blog-empty">
        <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
          <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z" />
          <polyline points="14 2 14 8 20 8" />
          <line x1="16" y1="13" x2="8" y2="13" />
          <line x1="16" y1="17" x2="8" y2="17" />
        </svg>
        <h2>No Stories Yet</h2>
        <p>We're still shaping our first article in the studio. Check back soon.</p>
      </div>
    );
  }

  const [featured, ...grid] = posts;

  return (
    <div className="blog-index">
      {/* ── Nav (matches site aesthetic) ── */}
      <nav className="blog-nav">
        <Link to="/" className="blog-nav__logo">Fun With Art</Link>
        <div className="blog-nav__links">
          <Link to="/collection">Collection</Link>
          <Link to="/studio">Studio</Link>
          <Link to="/blogs" className="blog-nav__active">Blogs</Link>
        </div>
      </nav>

      <main className="blog-index__main">
        {/* ── Hero Section ── */}
        {featured && <BlogCard post={featured} featured />}

        {/* ── Grid Section ── */}
        {grid.length > 0 && (
          <section className="blog-index__grid-section">
            <h2 className="blog-index__grid-heading">More from the Studio</h2>
            <div className="blog-grid">
              {grid.map((post) => (
                <BlogCard key={post.id} post={post} />
              ))}
            </div>
          </section>
        )}
      </main>

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