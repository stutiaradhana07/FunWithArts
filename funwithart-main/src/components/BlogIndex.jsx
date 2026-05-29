import { useEffect, useRef, useState } from 'react';
import { Link } from 'react-router-dom';
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
    return 'https://images.unsplash.com/photo-1578749556568-bc2c40e68b61?auto=format&fit=crop&w=1200&q=80';
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

function BlogCard({ post, featured }) {
  const category = getPostCategory(post);
  const titleStyle = {
    fontFamily: post.title_font_family || undefined,
    color: post.title_color || undefined,
    fontWeight: post.title_is_bold ? '700' : undefined,
    fontStyle: post.title_is_italic ? 'italic' : undefined,
    fontSize: (featured && post.title_font_size) ? post.title_font_size : undefined,
  };

  const categoryThemes = {
    'Craftsmanship': { bg: 'rgba(215, 168, 141, 0.12)', color: '#c47a5a', border: 'rgba(215, 168, 141, 0.3)' },
    'Studio Life': { bg: 'rgba(138, 90, 69, 0.1)', color: '#8a5a45', border: 'rgba(138, 90, 69, 0.25)' },
    'Inspiration': { bg: 'rgba(224, 169, 138, 0.15)', color: '#a05a3f', border: 'rgba(224, 169, 138, 0.3)' },
  };

  const theme = categoryThemes[category] || categoryThemes['Inspiration'];

  if (featured) {
    return (
      <Link to={`/blogs/${post.slug}`} className="blog-hero-card">
        <div className="blog-hero-card__image-container">
          <img 
            src={getPostCover(post)} 
            alt={post.title} 
            fetchPriority="high" 
            decoding="async" 
          />
          <div className="blog-hero-card__image-overlay" />
        </div>
        <div className="blog-hero-card__content-panel">
          <div className="blog-hero-card__badge-row">
            <span className="blog-card__tag" style={{ background: theme.bg, color: theme.color, borderColor: theme.border }}>
              {category}
            </span>
            <span className="blog-hero-card__label">Featured Article</span>
          </div>
          <h1 className="blog-hero-card__title" style={titleStyle}>{post.title}</h1>
          <p className="blog-hero-card__excerpt">{getPostExcerpt(post)}</p>
          
          <div className="blog-hero-card__footer">
            <div className="blog-card__author-block">
              <div className="blog-card__author-avatar">
                {post.author_name ? post.author_name.charAt(0).toUpperCase() : 'F'}
              </div>
              <div className="blog-card__author-meta">
                <p className="blog-card__author-name">By {post.author_name || 'Udaan Studio'}</p>
                <p className="blog-card__date">{formatBlogDate(post.created_at)}</p>
              </div>
            </div>
            
            <span className="blog-hero-card__cta">
              Read Story
              <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
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
        <span className="blog-card__tag blog-card__tag--absolute" style={{ background: theme.bg, color: theme.color, borderColor: theme.border }}>
          {category}
        </span>
      </div>
      <div className="blog-card__body">
        <h3 className="blog-card__title" style={titleStyle}>{post.title}</h3>
        <p className="blog-card__excerpt">{getPostExcerpt(post)}</p>
        
        <div className="blog-card__footer">
          <div className="blog-card__author-block">
            <div className="blog-card__author-avatar blog-card__author-avatar--sm">
              {post.author_name ? post.author_name.charAt(0).toUpperCase() : 'F'}
            </div>
            <div className="blog-card__author-meta">
              <p className="blog-card__author-name">By {post.author_name || 'Udaan Studio'}</p>
              <p className="blog-card__date">{formatBlogDate(post.created_at)}</p>
            </div>
          </div>
          <span className="blog-card__arrow">
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

export default function BlogIndex() {
  const [posts, setPosts] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [selectedCategory, setSelectedCategory] = useState('all');
  const [email, setEmail] = useState('');
  const [submitting, setSubmitting] = useState(false);
  
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

  const handleSubscribe = async (e) => {
    e.preventDefault();
    if (!email) return;
    setSubmitting(true);
    try {
      await window.UdaanAPI.subscribeNewsletter(email);
      setEmail('');
      if (typeof window.showToast === 'function') {
        window.showToast('Welcome to the studio circle! 🎨');
      } else {
        alert('Welcome to our studio circle!');
      }
    } catch (err) {
      if (typeof window.showToast === 'function') {
        window.showToast(err.message || 'Could not subscribe right now.');
      } else {
        alert(err.message || 'Could not subscribe right now.');
      }
    } finally {
      setSubmitting(false);
    }
  };

  const getFilteredPosts = () => {
    if (selectedCategory === 'all') return posts;
    return posts.filter(post => {
      const cat = getPostCategory(post).toLowerCase();
      if (selectedCategory === 'studio') return cat === 'studio life';
      if (selectedCategory === 'craft') return cat === 'craftsmanship';
      if (selectedCategory === 'inspiration') return cat === 'inspiration';
      return true;
    });
  };

  if (loading) {
    return (
      <div className="blog-loading">
        <div className="blog-loading__spinner" />
        <p>Gathering stories from the studio...</p>
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

  const filteredPosts = getFilteredPosts();
  const [featured, ...grid] = filteredPosts;

  return (
    <div className="blog-index">
      {/* Decorative Ornaments drifting in the background */}
      <div className="blog-bg-shape blog-bg-shape--1" />
      <div className="blog-bg-shape blog-bg-shape--2" />
      <div className="blog-bg-shape blog-bg-shape--3" />
      <VaseIcon1 className="blog-decor-doodle blog-decor-doodle--1" />
      <VaseIcon2 className="blog-decor-doodle blog-decor-doodle--2" />
      <SparkleIcon className="blog-decor-doodle blog-decor-doodle--3" />
      <SparkleIcon className="blog-decor-doodle blog-decor-doodle--4" />

      <BlogNavbar />

      <main className="blog-index__main">
        {/* Stunning Editorial Header */}
        <header className="blog-index__header">
          <div className="blog-index__subtitle-wrapper">
            <span className="blog-index__subtitle">Handcrafted Musings</span>
            <SparkleIcon className="blog-index__subtitle-sparkle" />
          </div>
          <h1 className="blog-index__title">Stories from the Kiln</h1>
          <p className="blog-index__desc">
            A quiet corner documenting our creative process, insights from the potting wheel, and reflections on shaping earth and art.
          </p>
          <div className="blog-index__line-divider" />
        </header>

        {/* Elegant Pill Category Filters */}
        <div className="blog-filters-container">
          <div className="blog-filters">
            {[
              { id: 'all', label: 'All Journals', count: posts.length, icon: '📖' },
              { id: 'studio', label: 'Studio Life', count: posts.filter(p => getPostCategory(p) === 'Studio Life').length, icon: '🏺' },
              { id: 'craft', label: 'Craftsmanship', count: posts.filter(p => getPostCategory(p) === 'Craftsmanship').length, icon: '✋' },
              { id: 'inspiration', label: 'Inspiration', count: posts.filter(p => getPostCategory(p) === 'Inspiration').length, icon: '✦' }
            ].map(cat => (
              <button
                key={cat.id}
                className={`blog-filter-btn ${selectedCategory === cat.id ? 'active' : ''}`}
                onClick={() => setSelectedCategory(cat.id)}
              >
                <span className="blog-filter-btn__icon">{cat.icon}</span>
                <span className="blog-filter-btn__label">{cat.label}</span>
                <span className="blog-filter-btn__count">{cat.count}</span>
              </button>
            ))}
          </div>
        </div>

        {/* Dynamic Post Feed */}
        <div className="blog-index__feed">
          {featured ? (
            <div className="blog-index__featured-section">
              <BlogCard post={featured} featured />
            </div>
          ) : null}

          {grid.length > 0 ? (
            <section className="blog-index__grid-section">
              <h2 className="blog-index__grid-heading">More Studio Diaries</h2>
              <div className="blog-grid">
                {grid.map((post) => (
                  <BlogCard key={post.id || post.slug} post={post} />
                ))}
              </div>
            </section>
          ) : null}

          {!filteredPosts.length ? (
            <div className="blog-index__empty-filter">
              <VaseIcon2 className="blog-index__empty-icon" />
              <h3>Kiln is Warming Up</h3>
              <p>We are currently shaping new articles for this category. Check back soon.</p>
              <button className="blog-cta-btn" onClick={() => setSelectedCategory('all')}>
                View All Stories
              </button>
            </div>
          ) : null}
        </div>
      </main>

      {/* Gorgeous Hand-drawn Newsletter Subscription Banner */}
      <section className="blog-cta">
        <div className="blog-cta__inner">
          <div className="blog-cta__badge">
            <SparkleIcon className="blog-cta__badge-star" />
            <span>Studio Circle</span>
          </div>
          <h2>Join the Studio Circle</h2>
          <p>Sign up to receive behind-the-scenes diaries, glazing secrets, and exclusive early access to upcoming handcrafted collections.</p>
          <form className="blog-cta__form" onSubmit={handleSubscribe}>
            <input 
              type="email" 
              placeholder="Your email address" 
              className="blog-cta__input" 
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              required 
              disabled={submitting}
            />
            <button type="submit" className="blog-cta__submit" disabled={submitting}>
              {submitting ? 'Joining...' : 'Join Circle'}
            </button>
          </form>
        </div>
      </section>

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
