import { useEffect, useRef, useState } from 'react';
import { Link } from 'react-router-dom';
import BlogNavbar from './BlogNavbar';

function formatBlogDate(dateStr) {
  if (!dateStr) return '';
  const date = new Date(dateStr);
  return date.toLocaleDateString('en-US', {
    year: 'numeric',
    month: 'long',
    day: 'numeric',
  });
}

function getPostCover(post) {
  const rawCover = post?.cover_image || post?.image_url || post?.image;
  if (!rawCover) {
    return 'https://placehold.co/1200x800/EAE6DB/3D2A20?text=Fun+With+Art';
  }
  let secureCover = rawCover;
  if (secureCover.startsWith('http://')) {
    secureCover = secureCover.replace('http://', 'https://');
  }
  if (secureCover.startsWith('https://') || secureCover.startsWith('data:')) {
    return secureCover;
  }
  const apiBase = window.__UDAAN_API_BASE__ || 'http://127.0.0.1:8000/api';
  const backendHost = apiBase.replace(/\/api\/?$/, '');
  const finalCover = `${backendHost}${secureCover.startsWith('/') ? '' : '/'}${secureCover}`;
  return finalCover.startsWith('http://') ? finalCover.replace('http://', 'https://') : finalCover;
}

function getPostExcerpt(post) {
  return post.excerpt || post.summary || 'A new studio story is on the wheel.';
}

function BlogCard({ post, featured }) {
  const titleStyle = {
    fontFamily: post.title_font_family || undefined,
    color: post.title_color || undefined,
    fontWeight: post.title_is_bold ? '700' : undefined,
    fontStyle: post.title_is_italic ? 'italic' : undefined,
    fontSize: (featured && post.title_font_size) ? post.title_font_size : undefined,
  };

  const excerptStyle = {
    fontFamily: post.excerpt_font_family || undefined,
  };

  if (featured) {
    return (
      <Link to={`/blogs/${post.slug}`} className="blog-hero-card">
        <div className="blog-hero-card__image">
          <img 
            src={getPostCover(post)} 
            alt={post.title} 
            fetchPriority="high" 
            decoding="async" 
          />
          <div className="blog-hero-card__overlay" />
          <div className="blog-hero-card__content">
            <span className="blog-hero-card__label">Featured Story</span>
            <h1 className="blog-hero-card__title" style={titleStyle}>{post.title}</h1>
            <p className="blog-hero-card__excerpt" style={excerptStyle}>{getPostExcerpt(post)}</p>
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
        <img 
          src={getPostCover(post)} 
          alt={post.title} 
          className="blog-card__image" 
          loading="lazy" 
          decoding="async" 
        />
      </div>
      <div className="blog-card__body">
        <h3 className="blog-card__title" style={titleStyle}>{post.title}</h3>
        <p className="blog-card__excerpt" style={excerptStyle}>{getPostExcerpt(post)}</p>
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
  const lenisRef = useRef(null);
  const rafRef = useRef(null);

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
        if (!cancelled) {
          setLoading(false);
        }
      }
    }

    load();
    return () => {
      cancelled = true;
    };
  }, []);

  useEffect(() => {
    if (typeof window.Lenis !== 'function') {
      return undefined;
    }

    try {
      const lenis = new window.Lenis({ duration: 1.8, smooth: true });
      lenisRef.current = lenis;
      let lastScrollY = window.scrollY;
      const mainNav = document.getElementById('main-nav');

      lenis.on('scroll', (e) => {
        const scrollY = e.scroll;
        if (scrollY > lastScrollY && scrollY > 150) {
          mainNav?.classList.add('hide');
        } else {
          mainNav?.classList.remove('hide');
        }
        lastScrollY = scrollY;
      });

      function raf(time) {
        lenis.raf(time);
        rafRef.current = requestAnimationFrame(raf);
      }

      rafRef.current = requestAnimationFrame(raf);
    } catch (e) {
      lenisRef.current = null;
    }

    return () => {
      if (rafRef.current) {
        cancelAnimationFrame(rafRef.current);
      }
      lenisRef.current?.destroy();
      lenisRef.current = null;
    };
  }, []);

  if (loading) {
    return (
      <div className="blog-loading">
        <div className="blog-loading__spinner" />
        <p>Gathering stories...</p>
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

  if (!posts.length) {
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
      <div className="blog-bg-shape blog-bg-shape--1" />
      <div className="blog-bg-shape blog-bg-shape--2" />
      <div className="blog-bg-shape blog-bg-shape--3" />
      <BlogNavbar />

      <main className="blog-index__main">
        {featured ? <BlogCard post={featured} featured /> : null}
        {grid.length > 0 ? (
          <section className="blog-index__grid-section">
            <h2 className="blog-index__grid-heading">More from the Studio</h2>
            <div className="blog-grid">
              {grid.map((post) => (
                <BlogCard key={post.id || post.slug} post={post} />
              ))}
            </div>
          </section>
        ) : null}
      </main>

      <footer className="blog-footer">
        <div className="blog-footer__inner">
          <p>© {new Date().getFullYear()} Fun With Art - Handcrafted in New Delhi</p>
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
