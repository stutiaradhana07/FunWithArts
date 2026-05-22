/** Cute line-art pottery doodles for the intro screen */
export default function IntroPotteryDoodles() {
  const stroke = 'currentColor';
  const sw = 1.8;

  return (
    <div className="intro-doodles" aria-hidden="true">
      <svg className="intro-doodle intro-doodle--1" viewBox="0 0 80 100" fill="none">
        <path
          d="M25 35 Q40 20 55 35 L58 70 Q40 88 22 70 Z"
          stroke={stroke}
          strokeWidth={sw}
          strokeLinecap="round"
          strokeLinejoin="round"
        />
        <ellipse cx="40" cy="32" rx="18" ry="6" stroke={stroke} strokeWidth={sw} />
        <path d="M32 50 Q40 58 48 50" stroke={stroke} strokeWidth={1.4} strokeLinecap="round" />
      </svg>

      <svg className="intro-doodle intro-doodle--2" viewBox="0 0 90 90" fill="none">
        <path
          d="M20 55 Q45 15 70 55 L65 75 Q45 85 25 75 Z"
          stroke={stroke}
          strokeWidth={sw}
          strokeLinecap="round"
        />
        <circle cx="38" cy="48" r="2.5" fill="currentColor" opacity="0.6" />
        <circle cx="52" cy="48" r="2.5" fill="currentColor" opacity="0.6" />
        <path d="M36 58 Q45 64 54 58" stroke={stroke} strokeWidth={1.4} strokeLinecap="round" />
      </svg>

      <svg className="intro-doodle intro-doodle--3" viewBox="0 0 100 60" fill="none">
        <ellipse cx="50" cy="45" rx="35" ry="12" stroke={stroke} strokeWidth={sw} />
        <path
          d="M30 45 L32 25 Q50 12 68 25 L70 45"
          stroke={stroke}
          strokeWidth={sw}
          strokeLinecap="round"
          strokeLinejoin="round"
        />
        <path d="M42 20 Q50 8 58 20" stroke={stroke} strokeWidth={1.2} strokeLinecap="round" opacity="0.5" />
      </svg>

      <svg className="intro-doodle intro-doodle--4" viewBox="0 0 70 70" fill="none">
        <circle cx="35" cy="38" r="22" stroke={stroke} strokeWidth={sw} />
        <path d="M20 38 Q35 28 50 38" stroke={stroke} strokeWidth={1.4} strokeLinecap="round" />
        <path
          d="M35 16 L35 8 M28 12 L42 12"
          stroke={stroke}
          strokeWidth={1.4}
          strokeLinecap="round"
        />
        <path d="M30 40 Q35 44 40 40" stroke={stroke} strokeWidth={1.2} strokeLinecap="round" opacity="0.4" />
      </svg>

      <svg className="intro-doodle intro-doodle--5" viewBox="0 0 60 80" fill="none">
        <path
          d="M15 50 Q30 25 45 50 L42 68 Q30 78 18 68 Z"
          stroke={stroke}
          strokeWidth={sw}
          strokeLinejoin="round"
        />
        <path d="M22 55 L38 55" stroke={stroke} strokeWidth={1.2} strokeLinecap="round" opacity="0.5" />
      </svg>

      <svg className="intro-doodle intro-doodle--6" viewBox="0 0 50 50" fill="none">
        <path
          d="M8 25 Q25 5 42 25 Q25 45 8 25"
          stroke={stroke}
          strokeWidth={1.5}
          strokeLinecap="round"
        />
        <circle cx="25" cy="25" r="4" fill="currentColor" opacity="0.25" />
      </svg>

      <svg className="intro-doodle intro-doodle--7" viewBox="0 0 80 50" fill="none">
        <path
          d="M5 35 Q25 10 40 35 M40 35 Q55 10 75 35"
          stroke={stroke}
          strokeWidth={1.4}
          strokeLinecap="round"
        />
        <circle cx="25" cy="22" r="3" fill="currentColor" opacity="0.4" />
        <circle cx="55" cy="22" r="3" fill="currentColor" opacity="0.4" />
      </svg>

      <svg className="intro-doodle intro-doodle--8" viewBox="0 0 40 40" fill="none">
        <path d="M20 4 L22 16 L34 18 L22 20 L20 32 L18 20 L6 18 L18 16 Z" stroke={stroke} strokeWidth={1.2} strokeLinejoin="round" />
      </svg>
    </div>
  );
}
