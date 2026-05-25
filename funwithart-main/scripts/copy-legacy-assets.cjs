// Post-build script: copies legacy HTML files, shared.js, and image/video
// assets from the project root into dist/ so LegacyPage's fetch() calls work.
//
// Vite only bundles the React SPA; this bridges the gap for the hybrid
// SPA/MPA architecture where LegacyPage fetches standalone HTML at runtime.

const fs = require('fs');
const path = require('path');

const ROOT = path.resolve(__dirname, '..');
const DIST = path.join(ROOT, 'dist');

if (!fs.existsSync(DIST)) {
  console.error('dist/ directory not found — run vite build first');
  process.exit(1);
}

const EXTENSIONS = new Set([
  '.html', '.jpg', '.jpeg', '.png', '.svg', '.webp', '.gif',
  '.mp4', '.webm', '.ico',
]);

// Special files that must be copied
const SPECIAL = new Set(['shared.js']);

// Files that should NOT be copied (Vite handles index.html)
const SKIP = new Set(['index.html', 'package.json', 'package-lock.json']);

let copied = 0;

for (const entry of fs.readdirSync(ROOT, { withFileTypes: true })) {
  if (!entry.isFile()) continue;
  if (SKIP.has(entry.name)) continue;

  const ext = path.extname(entry.name).toLowerCase();
  const shouldCopy = EXTENSIONS.has(ext) || SPECIAL.has(entry.name);

  if (shouldCopy) {
    const src = path.join(ROOT, entry.name);
    const dest = path.join(DIST, entry.name);
    fs.copyFileSync(src, dest);
    console.log(`  copied: ${entry.name}`);
    copied++;
  }
}

console.log(`\nCopied ${copied} legacy asset(s) to dist/`);