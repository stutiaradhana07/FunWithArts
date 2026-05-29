import { useEffect, useRef, useState } from 'react';
import { Link, useParams } from 'react-router-dom';
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
    return 'https://placehold.co/1600x900/EAE6DB/3D2A20?text=Fun+With+Art';
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

  return (
    <div className="blog-post" ref={headerRef} style={{ position: 'relative', overflow: 'hidden' }}>
      <div className="blog-bg-shape blog-bg-shape--1" />
      <div className="blog-bg-shape blog-bg-shape--2" />
      <div className="blog-bg-shape blog-bg-shape--3" />
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

      <section className="blog-title-block">
        <div className="blog-title-block__inner">
          <Link to="/blogs" className="blog-title-block__back">
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <line x1="19" y1="12" x2="5" y2="12" />
              <polyline points="12 19 5 12 12 5" />
            </svg>
            All Stories
          </Link>
          <h1 className="blog-title-block__title" style={titleStyle}>{post.title}</h1>
          <div className="blog-title-block__meta">
            <span>By {post.author_name || 'Udaan Studio'}</span>
            <span className="blog-title-block__sep">·</span>
            <span>{formatBlogDate(post.created_at)}</span>
          </div>
        </div>
      </section>

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
