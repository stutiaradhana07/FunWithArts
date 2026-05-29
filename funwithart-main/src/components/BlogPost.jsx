import { useEffect, useRef, useState } from 'react';
import { Link, useParams } from 'react-router-dom';
import BlogNavbar from './BlogNavbar';

// ── Organic SVG Ornaments matching the pottery studio theme ──

function SparkleIcon({ className }) {
  return (
    <svg className={className} viewBox="0 0 40 40" fill="currentColor" aria-hidden="true">
      <path d="M20 4 L22 16 L34 18 L22 20 L20 32 L18 20 L6 18 L18 16 Z" />
    </svg>
  );
}

function VaseIcon1({ className }) {
  return (
    <svg className={className} viewBox="0 0 80 100" fill="none" stroke="currentColor" strokeWidth="1.5" aria-hidden="true">
      <path d="M25 35 Q40 20 55 35 L58 70 Q40 88 22 70 Z" strokeLinecap="round" strokeLinejoin="round" />
      <ellipse cx="40" cy="32" rx="18" ry="6" />
      <path d="M32 50 Q40 58 48 50" strokeWidth="1.2" strokeLinecap="round" />
    </svg>
  );
}

function VaseIcon2({ className }) {
  return (
    <svg className={className} viewBox="0 0 90 90" fill="none" stroke="currentColor" strokeWidth="1.5" aria-hidden="true">
      <path d="M20 55 Q45 15 70 55 L65 75 Q45 85 25 75 Z" strokeLinecap="round" strokeLinejoin="round" />
      <circle cx="38" cy="48" r="2.5" fill="currentColor" opacity="0.6" />
      <circle cx="52" cy="48" r="2.5" fill="currentColor" opacity="0.6" />
      <path d="M36 58 Q45 64 54 58" strokeWidth="1.2" strokeLinecap="round" />
    </svg>
  );
}

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
    return 'https://images.unsplash.com/photo-1578749556568-bc2c40e68b61?auto=format&fit=crop&w=1600&q=80';
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
  return post.excerpt || post.summary || 'A new studio story is taking shape on the wheel.';
}

function getPostCategory(post) {
  if (post.category) return post.category;
  if (post.tag) return post.tag;
  if (post.tags && post.tags.length) return post.tags[0];

  const text = `${post.title} ${getPostExcerpt(post)}`.toLowerCase();
  if (text.includes('kiln') || text.includes('wheel') || text.includes('glaz') || text.includes('fir') || text.includes('clay') || text.includes('technique') || text.includes('craft')) {
    return 'Craftsmanship';
  }
  if (text.includes('behind') || text.includes('studio') || text.includes('workshop') || text.includes('process') || text.includes('day') || text.includes('diaries') || text.includes('delhi')) {
    return 'Studio Life';
  }
  return 'Inspiration';
}

export default function BlogPost() {
  const { slug } = useParams();
  const [post, setPost] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const headerRef = useRef(null);
  const lenisRef = useRef(null);
  const rafRef = useRef(null);
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
          setError(err.message?.includes('404') ? 'not_found' : 'load_error');
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
  }, [slug]);

  useEffect(() => {
    const onScroll = () => setScrollY(window.scrollY);
    window.addEventListener('scroll', onScroll, { passive: true });
    return () => window.removeEventListener('scroll', onScroll);
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
        const current = e.scroll;
        if (current > lastScrollY && current > 150) {
          mainNav?.classList.add('hide');
        } else {
          mainNav?.classList.remove('hide');
        }
        lastScrollY = current;
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
        <p>Opening the kiln...</p>
      </div>
    );
  }

  if (error === 'not_found') {
    return (
      <div className="blog-error">
        <h1>Story Not Found</h1>
        <p>This article may have been moved or is no longer available.</p>
        <Link to="/blogs" className="blog-cta-btn">Back to Stories</Link>
      </div>
    );
  }

  if (error || !post) {
    return (
      <div className="blog-error">
        <p>Something went wrong loading this story. Please try again.</p>
        <Link to="/blogs" className="blog-cta-btn">Back to Stories</Link>
      </div>
    );
  }

  const category = getPostCategory(post);
  const titleStyle = {
    fontWeight: post.title_is_bold ? '700' : undefined,
    fontStyle: post.title_is_italic ? 'italic' : undefined,
    fontSize: post.title_font_size || undefined,
    color: post.title_color || undefined,
    fontFamily: post.title_font_family || undefined,
  };

  const coverStyle = {
    objectPosition: post.cover_image_position || 'center center',
  };

  const categoryThemes = {
    'Craftsmanship': { bg: 'rgba(215, 168, 141, 0.12)', color: '#c47a5a', border: 'rgba(215, 168, 141, 0.3)' },
    'Studio Life': { bg: 'rgba(138, 90, 69, 0.1)', color: '#8a5a45', border: 'rgba(138, 90, 69, 0.25)' },
    'Inspiration': { bg: 'rgba(224, 169, 138, 0.15)', color: '#a05a3f', border: 'rgba(224, 169, 138, 0.3)' },
  };

  const theme = categoryThemes[category] || categoryThemes['Inspiration'];

  return (
    <div className="blog-post" ref={headerRef} style={{ position: 'relative', overflow: 'hidden' }}>
      {/* Drifting Background Ornament SVGs */}
      <div className="blog-bg-shape blog-bg-shape--1" />
      <div className="blog-bg-shape blog-bg-shape--2" />
      <div className="blog-bg-shape blog-bg-shape--3" />
      <VaseIcon1 className="blog-decor-doodle blog-decor-doodle--1" />
      <VaseIcon2 className="blog-decor-doodle blog-decor-doodle--2" />
      <SparkleIcon className="blog-decor-doodle blog-decor-doodle--3" />
      <SparkleIcon className="blog-decor-doodle blog-decor-doodle--4" />

      <BlogNavbar />

      <header className="blog-header">
        <div
          className="blog-header__bg"
          style={{ transform: `translateY(${scrollY * 0.35}px)` }}
        >
          <img
            src={getPostCover(post)}
            alt={post.title}
            style={coverStyle}
            fetchPriority="high"
            decoding="async"
          />
          <div className="blog-header__gradient" />
        </div>
      </header>

      {/* Floating Creative Title Block */}
      <section className="blog-title-block">
        <div className="blog-title-block__inner">
          <Link to="/blogs" className="blog-title-block__back">
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
              <line x1="19" y1="12" x2="5" y2="12" />
              <polyline points="12 19 5 12 12 5" />
            </svg>
            All Stories
          </Link>
          <h1 className="blog-title-block__title" style={titleStyle}>{post.title}</h1>
          
          <div className="blog-title-block__meta">
            <div className="blog-card__author-block">
              <div className="blog-card__author-avatar">
                {post.author_name ? post.author_name.charAt(0).toUpperCase() : 'F'}
              </div>
              <div className="blog-card__author-meta">
                <p className="blog-card__author-name">By {post.author_name || 'Udaan Studio'}</p>
                <p className="blog-card__date">{formatBlogDate(post.created_at)}</p>
              </div>
            </div>
            
            <span className="blog-card__tag" style={{ background: theme.bg, color: theme.color, borderColor: theme.border }}>
              {category}
            </span>
          </div>
        </div>
      </section>

      {/* Breathtaking Centered Reading Column */}
      <main className="blog-content">
        <div className="blog-content__body" style={{ fontFamily: post.content_font_family || undefined }}>
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
        
        {/* Tactile Back to Stories CTA at bottom of article */}
        <div className="blog-content__footer">
          <Link to="/blogs" className="blog-cta-btn">
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
              <line x1="19" y1="12" x2="5" y2="12" />
              <polyline points="12 19 5 12 12 5" />
            </svg>
            Back to Stories
          </Link>
        </div>
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
