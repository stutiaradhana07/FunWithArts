import { useEffect, useRef, useState } from 'react';
import IntroPotteryDoodles from './IntroPotteryDoodles';
import './IntroSplash.css';

const FADE_IN_MS = 1400;
const HOLD_MS = 5000;
const FADE_OUT_MS = 2600;

const INTRO_SEEN_KEY = 'fwa_intro_seen';

export function shouldShowIntro(pathname) {
  if (pathname !== '/') return false;
  if (typeof window !== 'undefined' && window.sessionStorage) {
    if (sessionStorage.getItem(INTRO_SEEN_KEY)) return false;
  }
  return true;
}

export function markIntroSeen() {
  if (typeof window !== 'undefined' && window.sessionStorage) {
    sessionStorage.setItem(INTRO_SEEN_KEY, '1');
  }
}

export default function IntroSplash({ onComplete, onExitStart }) {
  const [phase, setPhase] = useState('hidden');
  const splashRef = useRef(null);
  const cursorRef = useRef({ x: 0, y: 0 });
  const rafRef = useRef(null);

  useEffect(() => {
    document.body.classList.add('intro-active');
    const root = splashRef.current;
    if (root) {
      root.style.setProperty('--cursor-x', '50%');
      root.style.setProperty('--cursor-y', '50%');
    }

    const showTimer = window.requestAnimationFrame(() => {
      window.requestAnimationFrame(() => setPhase('visible'));
    });

    const exitTimer = window.setTimeout(() => {
      setPhase('exit');
      onExitStart?.();
    }, FADE_IN_MS + HOLD_MS);

    const doneTimer = window.setTimeout(
      () => onComplete?.(),
      FADE_IN_MS + HOLD_MS + FADE_OUT_MS
    );

    return () => {
      document.body.classList.remove('intro-active');
      window.cancelAnimationFrame(showTimer);
      window.clearTimeout(exitTimer);
      window.clearTimeout(doneTimer);
      if (rafRef.current) window.cancelAnimationFrame(rafRef.current);
    };
  }, [onComplete, onExitStart]);

  useEffect(() => {
    const root = splashRef.current;
    if (!root || phase === 'exit') return undefined;

    const updateGlow = () => {
      root.style.setProperty('--cursor-x', `${cursorRef.current.x}px`);
      root.style.setProperty('--cursor-y', `${cursorRef.current.y}px`);
      rafRef.current = null;
    };

    const onMove = (event) => {
      cursorRef.current = { x: event.clientX, y: event.clientY };
      if (!rafRef.current) {
        rafRef.current = window.requestAnimationFrame(updateGlow);
      }
    };

    const onTouch = (event) => {
      const touch = event.touches[0];
      if (!touch) return;
      cursorRef.current = { x: touch.clientX, y: touch.clientY };
      if (!rafRef.current) {
        rafRef.current = window.requestAnimationFrame(updateGlow);
      }
    };

    window.addEventListener('mousemove', onMove, { passive: true });
    window.addEventListener('touchmove', onTouch, { passive: true });

    return () => {
      window.removeEventListener('mousemove', onMove);
      window.removeEventListener('touchmove', onTouch);
    };
  }, [phase]);

  const phaseClass =
    phase === 'visible'
      ? ' intro-splash--visible'
      : phase === 'exit'
        ? ' intro-splash--exit'
        : '';

  return (
    <div
      ref={splashRef}
      className={`intro-splash${phaseClass}`}
      aria-hidden={phase === 'exit'}
      role="presentation"
    >
      <div className="intro-splash__bg" aria-hidden="true">
        <div className="intro-splash__gradient intro-splash__gradient--base" />
        <div className="intro-splash__gradient intro-splash__gradient--shift" />
        <div className="intro-splash__gradient intro-splash__gradient--warm" />
        <div className="intro-splash__cursor-glow" />
        <div className="intro-splash__cursor-glow intro-splash__cursor-glow--soft" />
        <IntroPotteryDoodles />
      </div>

      <div className="intro-splash__content">
        <div className="intro-splash__card">
          <span className="intro-splash__eyebrow">Welcome</span>
          <p className="intro-splash__line-1">Fun With</p>
          <h1 className="intro-splash__line-2">Art</h1>
          <div className="intro-splash__rule" />
          <p className="intro-splash__tagline">
            A ceramics brand · handcrafted in New Delhi
          </p>
        </div>
      </div>

      <div className="intro-splash__loader" aria-hidden="true">
        <span className="intro-splash__loader-label">Just a moment</span>
        <div className="intro-splash__loader-track">
          <div className="intro-splash__loader-bar" />
        </div>
      </div>
    </div>
  );
}
