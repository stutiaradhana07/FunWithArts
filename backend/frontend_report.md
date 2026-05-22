# Udaan Studio — Complete Frontend Report

## 1. Project Overview

**Udaan Studio** is a premium handmade pottery e-commerce website for a Delhi-based ceramics brand.  
The frontend is a **React 18 SPA** (Single Page Application) built with **Vite 5** as the bundler and **Tailwind CSS 3** for styling, with **Framer Motion** powering all animations.

There are **two coexisting frontend versions** in the project — an **original static HTML prototype** (`index.html`, `product.html`, `collection.html`, etc.) and the **active React app** (`src/`). The React app is the one connected to a dev server and is the one to wire up to Django.

---

## 2. Tech Stack

| Layer | Technology | Version |
|---|---|---|
| Framework | React | 18.3.1 |
| Bundler | Vite | 5.4.11 |
| Styling | Tailwind CSS | 3.4.1 |
| Animations | Framer Motion | 11.0.0 |
| Routing | React Router DOM | 6.22.0 |
| Icons | Lucide React | 0.460.0 |
| CSS util | clsx + tailwind-merge | — |
| Fonts | Google Fonts (Playfair Display + Inter) | — |
| Smooth Scroll (HTML only) | Lenis (CDN) | 1.0.29 |

**Dev server command:** `npm run dev` (inside `udaan-store/`)

---

## 3. Directory Structure

```
udaan-store/
├── index.html                     ← Root HTML shell for the React SPA
├── vite.config.js
├── tailwind.config.js
├── postcss.config.js
├── package.json
├── public/                        ← Static assets (product images, videos)
│   ├── wall-faces.jpg
│   ├── wall-green-pots.jpg
│   ├── wall-group.png
│   ├── wall-pen-holder.PNG
│   ├── tall-vases.jpg
│   ├── geometric-trio.jpg
│   ├── character-pots.jpg
│   ├── desk-set.jpg
│   ├── miniatures.jpg
│   ├── fountain.jpg
│   ├── wall-hands-1.jpg
│   ├── wall-hands-2.jpg
│   └── (WhatsApp videos/images — real studio content)
└── src/
    ├── main.jsx                   ← React entry point
    ├── App.jsx                    ← Root component, routing, providers
    ├── index.css                  ← Global Tailwind + utility CSS
    ├── context/
    │   └── CartContext.jsx        ← Global cart + wishlist state
    ├── data/
    │   └── products.js            ← Hardcoded product data (to be replaced by API)
    ├── pages/
    │   ├── Home.jsx
    │   ├── ProductDetail.jsx
    │   └── Checkout.jsx
    ├── sections/                  ← Homepage sections
    │   ├── Hero.jsx
    │   ├── Collections.jsx
    │   ├── CraftStory.jsx
    │   ├── Bestsellers.jsx
    │   ├── Testimonials.jsx
    │   └── Gallery.jsx
    └── components/
        ├── layout/
        │   ├── Navbar.jsx
        │   └── Footer.jsx
        ├── cart/
        │   └── CartDrawer.jsx
        ├── ui/
        │   ├── Button.jsx
        │   ├── ProductCard.jsx
        │   └── SplashScreen.jsx
        └── utils/
            └── ScrollToTop.jsx
```

> **Note:** There are also legacy static HTML pages (`cart.html`, `checkout.html`, `collection.html`, `contact.html`, `product.html`, `wishlist.html`) at the root of `udaan-store/`. These are the **original HTML prototype** and are NOT part of the React app. They are dead weight at this point — but they show design intent.

---

## 4. Design System (Tailwind Config)

### Color Palette

| Token | Hex | Usage |
|---|---|---|
| `brand-cream` | `#F5F0E6` | Page background, base |
| `brand-clay` | `#A47148` | Primary CTA, accents, active states |
| `brand-terracotta` | `#D8A47F` | Secondary buttons, highlights |
| `brand-charcoal` | `#2E2E2E` | Text, borders |
| `brand-sage` | `#A3B18A` | Reserved (not currently used in JSX) |
| `brand-blush` | `#E5B1A1` | Reserved |
| `brand-lavender` | `#B8B8D1` | Reserved |

### Typography

| Font | Family | Usage |
|---|---|---|
| Playfair Display | Serif (`font-playfair`) | All headings, product names, quotes |
| Inter | Sans-serif (`font-inter`) | Body text, labels, captions |

### Custom Animations (Tailwind)

| Class | Effect |
|---|---|
| `animate-fade-in-up` | Slides up + fades in (0.8s) |
| `animate-fade-in` | Simple opacity fade (1s) |

### Global CSS Utilities (`index.css`)

| Class | Purpose |
|---|---|
| `.noise-overlay` | Fixed SVG fractal noise texture over the entire UI at 3% opacity |
| `.premium-blur` | `backdrop-blur-md` + white/70 bg + border — used for glass-card elements |
| `.section-padding` | Standard `py-24 px-6 md:px-12 lg:px-24` |
| `.hover-lift` | Smooth `translateY(-12px)` + `shadow-2xl` on hover |
| `.fade-in` | CSS keyframe fade-in animation |
| Custom scrollbar | 5px width, clay-colored thumb, cream track |

---

## 5. Application Entry Points

### `main.jsx`
Standard React 18 `createRoot` entry. Mounts `<App />` into `#root` with `<React.StrictMode>`.

### `App.jsx` — Root Component
This is the application shell. Key responsibilities:

1. **Splash Screen gate** — `splashDone` state controls whether the app is visible. The whole app fades in only after the splash exits.
2. **Routing** — `BrowserRouter` wraps everything. Three routes:
   - `/` → `<Home />`
   - `/product/:id` → `<ProductDetail />`
   - `/checkout` → `<Checkout />`
3. **Lazy loading** — All three pages use `React.lazy()` + `<Suspense>` for code-splitting. Fallback shows "Preparing the Studio..." in clay color.
4. **Global layout** — `<Navbar>`, `<CartDrawer>`, and `<Footer>` are rendered outside routes (persistent across all pages).
5. **Noise overlay** — A `div.noise-overlay` sits at `z-index: 9999` for the premium texture effect.
6. **`<CartProvider>`** wraps the entire tree so cart/wishlist state is global.

---

## 6. State Management — `CartContext.jsx`

The **single source of truth** for shopping state. Uses React Context + `useState` with `localStorage` persistence.

### State

| State | Type | Persisted |
|---|---|---|
| `cart` | Array of cart items (product + quantity) | ✅ `localStorage('udaan_cart')` |
| `wishlist` | Array of products | ✅ `localStorage('udaan_wishlist')` |
| `isCartOpen` | Boolean (cart drawer visibility) | ❌ |

### Exposed Functions

| Function | Behaviour |
|---|---|
| `addToCart(product)` | Adds product or increments quantity. Auto-opens cart drawer. |
| `removeFromCart(id)` | Filters item out by ID |
| `updateQuantity(id, delta)` | Increments/decrements. Removes item if qty reaches 0. |
| `toggleWishlist(product)` | Adds/removes from wishlist array |
| `clearCart()` | Empties cart (called on order success) |

### Computed Values

| Value | How |
|---|---|
| `cartTotal` | `sum(price * quantity)` for all items |
| `cartCount` | `sum(quantity)` for all items |

> **Backend connection point:** When Django API is ready, `addToCart` and the cart state should sync with a server-side cart session or user account instead of (or in addition to) localStorage.

---

## 7. Data Layer — `products.js`

Currently **hardcoded** with 6 products. This is the **critical file to replace with API calls** to Django.

### Product Schema

```js
{
  id: 'p1',              // String ID — must match Django PK or slug
  name: 'The Guardians', // Display name
  category: 'Decor',     // Category label
  price: 7800,           // Price in INR (integer paise or rupees)
  image: '/wall-faces.jpg', // Path relative to /public/
  isNew: true,           // Renders a "New" badge on ProductCard
  description: '...',    // Short product description
}
```

### Current Products

| ID | Name | Category | Price (₹) | Status |
|---|---|---|---|---|
| p1 | The Guardians | Decor | 7,800 | New |
| p2 | Emerald Duo | Pots | 4,500 | — |
| p3 | Artisan Bowl | Tableware | 3,200 | New |
| p4 | Terracotta Holder | Office | 2,800 | — |
| p5 | Earth Vessel | Vase | 8,900 | — |
| p6 | Geometric Trio | Sets | 12,500 | New |

---

## 8. Pages

### 8.1 `Home.jsx`
Assembles the homepage from 6 ordered sections:

```
Hero → Collections → CraftStory → Bestsellers → Testimonials → Gallery
```

Also listens to `react-router-dom` `location.state.scrollTo` — when the Navbar's "Shop All" link is clicked from another page, it navigates home and smooth-scrolls to the `#shop` element.

---

### 8.2 `ProductDetail.jsx`

**Route:** `/product/:id`

**Behaviour:**
- Reads `:id` from URL params and finds the product in `products.js` via `.find()`
- Redirects to `/` if product not found
- Allows setting a **quantity** (1+) before adding to cart
- Shows product image + 2 fixed detail images (`wall-hands-1.jpg`, `wall-hands-2.jpg`) in a sticky left panel
- Right panel has: category, name, price, description, quantity selector, Add to Bag button, shipping/authenticity badges, and a **Pincode delivery checker** (currently frontend-only, returns a hardcoded "3-5 business days" message for any valid 6-digit code)
- The right panel is `lg:sticky lg:top-32` (sticky on desktop)

> **Backend connection point:** The pincode checker is fake. Django should expose a delivery estimate API endpoint.

---

### 8.3 `Checkout.jsx`

**Route:** `/checkout`

Three-step form: Contact → Shipping Address → Payment

**States:**
- `isSubmitting` — shows "Processing Ritual..." on the submit button during mock 2s delay
- `isSuccess` — renders a success screen after submit, calls `clearCart()`
- `paymentMethod` — `'card'` | `'upi'` | `'cod'`

**Payment Options:**
- Card: shows Card Number / MM-YY / CVV fields (animated in/out with `AnimatePresence`)
- UPI: just a selector, no extra fields
- COD: just a selector, no extra fields

**Shipping logic:**
- Shipping = ₹500 if `cartTotal < ₹10,000`, else FREE ("Complimentary")

**Empty cart guard:** If cart is empty, redirects to a "Your bag is empty" screen with a "Continue Exploring" button.

**Order Summary sidebar:** Lists all cart items with image, name, category, and price. Sticky on desktop (`lg:sticky lg:top-32`).

> **Backend connection point:** The `handleSubmit` function currently only does a `setTimeout` simulation. It needs to:
> 1. POST the form data + cart to a Django order creation endpoint
> 2. Optionally trigger a payment gateway (Razorpay/Stripe)
> 3. Use the real response to show success or errors

---

## 9. Homepage Sections

### 9.1 `Hero.jsx`
- Full-screen (`h-screen`) section using `desk-set.jpg` as background
- Background image has a **slow continuous scale animation** (scale 1.1 → 1, 20s loop) for a subtle parallax/breathing effect
- Layered content: eyebrow text → `h1` ("Fun with Art") → subtitle → CTA button
- **Scroll indicator** at bottom: vertical line + "Scroll" rotated text, fades in at 1.5s delay
- CTA button scrolls to `#shop` anchor

### 9.2 `Collections.jsx`
- Section ID: `#collections`
- 3 cards in a `grid-cols-1 md:grid-cols-2 lg:grid-cols-3` grid (600px tall each)
- Each card: full-background image, gradient overlay, title + tagline (tagline revealed on hover), animated underline expand
- All hover effects use CSS `group-hover` transitions
- Images: `wall-group.png`, `tall-vases.jpg`, `geometric-trio.jpg`
- "View All Series" link at top right links to `#shop`

### 9.3 `CraftStory.jsx`
- Section ID: `#story`
- Split layout: 2-column image grid (left) + brand story text (right)
- Images: `wall-hands-1.jpg`, `wall-hands-2.jpg` — offset vertically for visual rhythm
- Text has the brand narrative and an **"Learn Our Process"** outline button (currently `#` href)
- All elements animate in with `whileInView` (Framer Motion)

### 9.4 `Bestsellers.jsx`
- Section ID: `#shop`
- Shows first 4 products from `products.js`
- Desktop: `grid-cols-2 lg:grid-cols-4`
- Mobile: horizontally scrollable flex row (each card `w-[280px]`)
- Stagger animation: each `ProductCard` gets a `staggerIndex` (0–3) for delayed entry
- "View Full Archive" link at bottom (currently `href="#"`, not wired to a collection page)

### 9.5 `Testimonials.jsx`
- 3-column grid of customer quotes
- Static hardcoded data (3 reviews)
- Hover reveals full colour on quote text
- Quote marks in `font-playfair brand-clay`, large display size

### 9.6 `Gallery.jsx`
- CSS `columns` masonry layout: `columns-2 md:columns-3 lg:columns-4`
- 8 images from `/public/`
- Each image: scale-up hover + clay overlay fade
- Section title: "Studio Moments" / `@udaan_studio`

---

## 10. Layout Components

### 10.1 `Navbar.jsx`
- **Fixed** at top, `z-50`
- **Scroll-aware:** transparent + `py-8` when at top; switches to `premium-blur` (glassmorphism) + `py-4` after scrolling 50px
- **Centered logo** using `absolute left-1/2 -translate-x-1/2`: "UDAAN" (Playfair Bold) + "Studio" (Inter, clay)
- **Left:** 3 nav links (Shop All, Collections, Our Story) — desktop only
- **Right:** Search icon (desktop hidden on mobile), Heart (wishlist dot indicator), Shopping Bag (with count badge)
- **Mobile menu:** Full-screen slide-in overlay (`AnimatePresence` spring animation). Links in large italic Playfair. Close button top-right.
- Nav links use `handleNavClick` — smooth-scrolls to section IDs if on homepage, else navigates to `/` with `location.state.scrollTo`

> **Issue:** The Search button has no functionality — it's a visual placeholder.  
> **Issue:** The Heart/Wishlist button shows a dot indicator but clicking it does nothing (there's no Wishlist page).

### 10.2 `Footer.jsx`
- 4-column grid: Brand (2 cols) + Shop links + Support links
- Brand col: "UDAAN Studio" wordmark + italic tagline + social icons (Instagram, Globe, Twitter — all `href="#"`)
- **Newsletter box:** glassmorphism card (`premium-blur`), email input + "Join Us" Button — form not wired to any API
- Bottom bar: copyright + Privacy / Terms / Accessibility links (all `href="#"`)

---

## 11. UI Components

### 11.1 `Button.jsx`
Wraps `motion.button` with `whileTap={{ scale: 0.98 }}`.

**Variants:**

| Variant | Style |
|---|---|
| `primary` (default) | Clay background, white text |
| `secondary` | Terracotta background, white text |
| `outline` | Clay border, clay text → fills on hover |
| `ghost` | No background, charcoal text |

> **Note:** There is a `clay` variant referenced in `Checkout.jsx` (`variant="clay"`) but it's not defined in the variants object — falls back to undefined, so no styles apply. This is a bug.

### 11.2 `ProductCard.jsx`
- Wraps each product in `motion.div` with `whileInView` fade-up + stagger delay
- **Hover state** (`isHovered`): scales image to `1.05`
- **Wishlist button** top-right: filled heart if wishlisted (terracotta), outline if not
- **"Add to Bag" button**: only appears while hovered (AnimatePresence slide-up), calls `addToCart`
- **"New" badge**: rendered if `product.isNew === true`
- Product name and image link to `/product/:id`

### 11.3 `SplashScreen.jsx`
- Waits for all `<img>` tags on the page to load (tracks `loaded/total`)
- Shows: "Fun with Art" (italic subtitle) + "Udaan." (giant clay italic text) + loading percentage
- Exits with `opacity: 0, scale: 1.05` Framer Motion animation
- Calls `onComplete` callback 800ms after hiding — App then fades in
- Edge case handled: if no images on page, exits after 600ms

### 11.4 `ScrollToTop.jsx`
- Tiny utility rendered in `App.jsx` (but **currently not rendered** — it's imported in `App.jsx` but the JSX doesn't include `<ScrollToTop />`)
- Calls `window.scrollTo(0, 0)` on every route change via `useLocation`

> **Bug:** `ScrollToTop` is imported in `App.jsx` but **never actually included in the JSX tree**. Route changes won't auto-scroll to top.

---

## 12. Routing Summary

| Path | Page | Notes |
|---|---|---|
| `/` | `Home` | Full landing page with all sections |
| `/product/:id` | `ProductDetail` | ID must match a key in `products.js` |
| `/checkout` | `Checkout` | Guard: redirects to empty-bag screen if cart is empty |

All pages are **lazy-loaded** (code-split). No 404 page defined.

---

## 13. Animations Summary

| Element | Animation Type | Library |
|---|---|---|
| App fade-in on splash complete | CSS `opacity` transition | CSS |
| Splash screen entry/exit | `opacity + scale` | Framer Motion |
| Navbar scroll-blur transition | CSS `transition-all duration-500` | CSS |
| Mobile menu slide-in | `x: -100% → 0` Spring | Framer Motion |
| Cart drawer slide-in | `x: 100% → 0` Spring | Framer Motion |
| Cart overlay fade | `opacity 0 → 1` | Framer Motion |
| Free shipping progress bar | `width: 0 → X%` | Framer Motion |
| Hero heading/subtitle/button | Staggered `y + opacity` | Framer Motion |
| Hero scroll indicator | `opacity` delay 1.5s | Framer Motion |
| Hero background | `scale 1.1 → 1` 20s loop | Framer Motion |
| ProductCard entry | `y: 60 → 0, opacity` whileInView | Framer Motion |
| ProductCard image hover | `scale 1 → 1.05` | Framer Motion |
| Quick Add button | `y: 10 → 0, opacity` AnimatePresence | Framer Motion |
| Collections cards | `y: 60 → 0` whileInView stagger | Framer Motion |
| Collections image hover | `scale → 1.05` | Framer Motion |
| CraftStory images | `x: ±50 → 0` whileInView | Framer Motion |
| Story text elements | `y: 20 → 0` stagger | Framer Motion |
| Testimonials | `y: 20 → 0` stagger | Framer Motion |
| Gallery images | `scale: 0.95 → 1` whileInView | Framer Motion |
| Checkout payment method switch | `y ±10, opacity` AnimatePresence | Framer Motion |
| Checkout success screen | `scale: 0.9 → 1, opacity` | Framer Motion |
| ProductDetail image | `scale: 0.95 → 1, opacity` | Framer Motion |
| Button tap | `scale: 0.98` whileTap | Framer Motion |

---

## 14. Assets in `/public/`

All images are **real studio photos** — no stock imagery.

| File | Used In |
|---|---|
| `wall-faces.jpg` | Product p1, Gallery |
| `wall-green-pots.jpg` | Product p2, Gallery |
| `wall-group.png` | Product p3, Collections, Gallery |
| `wall-pen-holder.PNG` | Product p4 |
| `tall-vases.jpg` | Product p5, Collections, Gallery |
| `geometric-trio.jpg` | Product p6, Collections |
| `desk-set.jpg` | Hero background, Gallery |
| `miniatures.jpg` | Gallery |
| `fountain.jpg` | Gallery |
| `character-pots.jpg` | Gallery |
| `wall-hands-1.jpg` | CraftStory, ProductDetail (detail), Gallery |
| `wall-hands-2.jpg` | CraftStory, ProductDetail (detail) |
| WhatsApp images (5) | Currently unused in React app |
| WhatsApp videos (4) | Currently unused in React app |

---

## 15. Known Issues & Gaps (Frontend Only)

| # | Issue | File | Severity |
|---|---|---|---|
| 1 | `ScrollToTop` imported but not rendered | `App.jsx` | Medium |
| 2 | `variant="clay"` used in Checkout but not defined in Button | `Button.jsx`, `Checkout.jsx` | Low |
| 3 | Search button in Navbar is non-functional | `Navbar.jsx` | Low |
| 4 | Wishlist heart in Navbar has no click handler and no Wishlist page | `Navbar.jsx` | Medium |
| 5 | "View Full Archive" links in Bestsellers/Collections go to `#` | `Bestsellers.jsx`, `Collections.jsx` | Medium |
| 6 | Social media links in Footer are all `#` | `Footer.jsx` | Low |
| 7 | Newsletter form in Footer is not connected to any API | `Footer.jsx` | High |
| 8 | Pincode delivery checker returns hardcoded response | `ProductDetail.jsx` | High |
| 9 | Checkout form submit is a mock (setTimeout 2s) | `Checkout.jsx` | **Critical** |
| 10 | Product data is hardcoded in `products.js` | `data/products.js` | **Critical** |
| 11 | No 404 / Not Found route defined | `App.jsx` | Medium |
| 12 | "Learn Our Process" button in CraftStory links nowhere | `CraftStory.jsx` | Low |
| 13 | Product detail always shows same 2 "detail" images regardless of product | `ProductDetail.jsx` | Medium |
| 14 | Checkout order summary shows `Qty: 1` hardcoded instead of `item.quantity` | `Checkout.jsx` (line 184) | Medium |
| 15 | WhatsApp real studio videos in `/public/` are unused | — | Low |
| 16 | Static HTML files (6) still exist alongside React app | root of `udaan-store/` | Low |

---

## 16. Backend Integration Checklist

When the Django backend is ready, here are the specific frontend connection points:

| Frontend Feature | Django Endpoint Needed |
|---|---|
| Product listing (Bestsellers, Collections) | `GET /api/products/` |
| Product detail | `GET /api/products/:id/` |
| Pincode delivery check | `GET /api/delivery-check/?pincode=XXXXXX` |
| Newsletter signup | `POST /api/newsletter/subscribe/` |
| Cart sync (optional, for logged-in users) | `GET/POST/PATCH /api/cart/` |
| Order placement (Checkout submit) | `POST /api/orders/` |
| Payment integration | Razorpay/Stripe webhook + order status update |
| User auth (login/signup) | `POST /api/auth/login/`, `/api/auth/register/` |

> The frontend currently uses a **localStorage cart** with no authentication. If you want user accounts, you'll need to add an auth flow on the frontend too.

---

## 17. Two Frontend Versions — Summary

| | Static HTML Version | React App Version |
|---|---|---|
| Files | `index.html`, `product.html`, `collection.html`, etc. | `src/**` |
| Routing | Multi-page (separate HTML files) | SPA (React Router) |
| State | localStorage via vanilla JS | React Context + localStorage |
| Animations | CSS keyframes + Lenis smooth scroll | Framer Motion |
| Status | **Prototype / dead code** | **Active — wire this to Django** |
| Notable feature | Theatrical clay-swipe page transition, rubber marquee, 3D exploding grid | Splash screen, slide-in cart drawer, whileInView stagger animations |

The static HTML version has some **unique visual effects** not ported to React yet (rubber marquee skew on scroll speed, ambient typography parallax, wet clay image distortion, theatrical curtain wipe transition). These can be ported if desired.
