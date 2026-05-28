(function () {
  const apiBase = window.__UDAAN_API_BASE__ || 'http://127.0.0.1:8000/api';

  const STORAGE_KEYS = {
    cart: 'udaan_cart_v2',
    wishlist: 'udaan_wishlist_v2',
    activeProduct: 'udaan_active_product',
    auth: 'udaan_auth_v1',
  };

  const normalize = (value) =>
    String(value || '')
      .toLowerCase()
      .replace(/[^a-z0-9]+/g, ' ')
      .trim();

  function getAuth() {
    try {
      const raw = localStorage.getItem(STORAGE_KEYS.auth);
      return raw ? JSON.parse(raw) : null;
    } catch (error) {
      return null;
    }
  }

  function setAuth(auth) {
    if (auth) {
      localStorage.setItem(STORAGE_KEYS.auth, JSON.stringify(auth));
    } else {
      localStorage.removeItem(STORAGE_KEYS.auth);
    }
    document.dispatchEvent(new CustomEvent('udaan:auth-change', { detail: { auth: getAuth() } }));
  }

  function isLoggedIn() {
    return Boolean(getAuth()?.token);
  }

  function getAuthHeaders() {
    const auth = getAuth();
    if (!auth?.token) return {};
    return { Authorization: `Token ${auth.token}` };
  }

  function formatApiError(payload, status) {
    if (!payload) return `Request failed (${status})`;
    if (typeof payload === 'string') return payload;
    if (payload.error) return payload.error;
    if (payload.detail) return payload.detail;
    const firstKey = Object.keys(payload)[0];
    if (firstKey) {
      const value = payload[firstKey];
      if (Array.isArray(value)) return String(value[0]);
      if (typeof value === 'string') return value;
    }
    return JSON.stringify(payload);
  }

  async function request(path, options = {}) {
    const response = await fetch(`${apiBase}${path}`, {
      headers: {
        'Content-Type': 'application/json',
        ...getAuthHeaders(),
        ...(options.headers || {}),
      },
      ...options,
    });

    let payload = null;
    try {
      payload = await response.json();
    } catch (error) {
      payload = null;
    }

    if (!response.ok) {
      throw new Error(formatApiError(payload, response.status));
    }

    if (response.status === 204) return null;
    return payload;
  }

  async function healthCheck() {
    return request('/health/');
  }

  async function fetchProducts() {
    return request('/products/');
  }

  async function searchProducts(query, options = {}) {
    const params = new URLSearchParams();
    params.set('q', String(query || '').trim());
    if (options.category) params.set('category', options.category);
    if (options.is_new) params.set('is_new', 'true');
    if (options.limit) params.set('limit', String(options.limit));
    return request(`/search/?${params.toString()}`);
  }

  async function checkDelivery(pincode) {
    return request(`/delivery-check/?pincode=${encodeURIComponent(pincode)}`);
  }

  async function subscribeNewsletter(email) {
    return request('/blogs/subscribe/', {
      method: 'POST',
      body: JSON.stringify({ email }),
    });
  }

  async function submitOrder(payload) {
    return request('/orders/', {
      method: 'POST',
      body: JSON.stringify(payload),
    });
  }

  async function registerUser({ username, email, password }) {
    const payload = await request('/auth/register/', {
      method: 'POST',
      body: JSON.stringify({ username, email, password }),
    });
    setAuth({ token: payload.token, user: payload.user });
    await syncGuestWishlistToServer();
    return payload;
  }

  async function loginUser({ username, password }) {
   const payload = await request('/auth/login/', {
     method: 'POST',
     body: JSON.stringify({ username, password }),
   });
   setAuth({ token: payload.token, user: payload.user });
   await syncGuestWishlistToServer();
   return payload;
 }

 async function googleLogin(idToken) {
   const payload = await request('/auth/google/', {
     method: 'POST',
     body: JSON.stringify({ id_token: idToken }),
   });
   setAuth({ token: payload.token, user: payload.user });
   await syncGuestWishlistToServer();
   return payload;
 }

  async function logoutUser() {
    try {
      if (isLoggedIn()) {
        await request('/auth/logout/', { method: 'POST' });
      }
    } catch (error) {
      // Token may already be invalid — still clear local session.
    } finally {
      if (window.google?.accounts?.id) {
        try {
          google.accounts.id.disableAutoSelect();
        } catch (e) {
          console.warn('Failed to call disableAutoSelect:', e);
        }
      }
      setAuth(null);
    }
  }

  async function requestPasswordReset(email) {
    return request('/auth/password_reset/', {
      method: 'POST',
      body: JSON.stringify({ email }),
    });
  }

  async function confirmPasswordReset(uidb64, token, newPassword) {
    return request('/auth/password_reset_confirm/', {
      method: 'POST',
      body: JSON.stringify({ uidb64, token, new_password: newPassword }),
    });
  }

  async function fetchBlogPosts() {
    return request('/blogs/');
  }

  async function fetchBlogPost(slug) {
    return request(`/blogs/${slug}/`);
  }

  async function fetchCurrentUser() {
    const payload = await request('/auth/me/');
    const auth = getAuth();
    if (auth) {
      setAuth({ ...auth, user: payload });
    }
    return payload;
  }

  async function fetchCurrentProfile() {
    return request('/users/profile/');
  }

  async function updateCurrentUser(payload = {}) {
    const nextUser = {};
    const nextProfile = {};

    if (payload.username != null) {
      nextUser.username = String(payload.username).trim();
    }

    if (payload.phone != null) {
      nextProfile.phone = String(payload.phone).trim();
    }

    let user = getAuth()?.user || null;
    let profile = null;

    if (Object.keys(nextUser).length > 0) {
      user = await request('/auth/me/', {
        method: 'PATCH',
        body: JSON.stringify(nextUser),
      });

      const auth = getAuth();
      if (auth) {
        setAuth({ ...auth, user });
      }
    }

    if (Object.keys(nextProfile).length > 0) {
      profile = await request('/users/profile/', {
        method: 'PATCH',
        body: JSON.stringify(nextProfile),
      });
    }

    return { ...(user || {}), ...(profile || {}) };
  }

  async function fetchOrders() {
    const data = await request('/orders/');
    // Paginated endpoint returns { count, next, previous, results }
    return Array.isArray(data) ? data : (data.results || []);
  }

  async function fetchOrder(orderId) {
    return request(`/orders/${orderId}/`);
  }

  async function guestOrderLookup(orderId, contactEmail) {
    return request(`/orders/lookup/?order_id=${encodeURIComponent(orderId)}&contact_email=${encodeURIComponent(contactEmail)}`);
  }

  async function fetchWorkshops() {
    return request('/workshops/');
  }

  async function fetchWorkshop(workshopId) {
    return request(`/workshops/${workshopId}/`);
  }

  async function initiateWorkshopPayment(workshopId, seats = 1) {
    return request('/workshops/initiate-payment/', {
      method: 'POST',
      body: JSON.stringify({ workshop_id: workshopId, seats }),
    });
  }

  async function verifyWorkshopPayment(razorpay_order_id, razorpay_payment_id, razorpay_signature) {
    return request('/workshops/payment/verify/', {
      method: 'POST',
      body: JSON.stringify({ razorpay_order_id, razorpay_payment_id, razorpay_signature }),
    });
  }

  async function initiateOrderPayment(orderId) {
    return request('/payments/create-order/', {
      method: 'POST',
      body: JSON.stringify({ order_id: orderId }),
    });
  }

  async function verifyOrderPayment(razorpay_order_id, razorpay_payment_id, razorpay_signature) {
    return request('/payments/verify/', {
      method: 'POST',
      body: JSON.stringify({ razorpay_order_id, razorpay_payment_id, razorpay_signature }),
    });
  }

  async function fetchMyBookings() {
    return request('/workshops/bookings/');
  }

  async function fetchWishlist() {
    return request('/users/wishlist/');
  }

  async function addToWishlist(productId) {
    return request('/users/wishlist/', {
      method: 'POST',
      body: JSON.stringify({ product_id: productId }),
    });
  }

  async function removeFromWishlist(productId) {
    return request(`/users/wishlist/${productId}/`, { method: 'DELETE' });
  }

  function mapApiProduct(product) {
    return {
      id: String(product.id),
      productId: product.id,
      title: product.name,
      price: Number(product.price),
      img: product.image_url || product.image || '',
      category: (product.category || 'decor').toLowerCase(),
      desc: product.description || '',
      badge: product.is_new || product.isNew ? 'New' : '',
      avg_rating: product.avg_rating != null ? Number(product.avg_rating) : null,
      review_count: product.review_count != null ? Number(product.review_count) : 0,
    };
  }

  function mapWishlistItemToLocal(item) {
    const product = item.product || {};
    return {
      id: String(product.id),
      productId: product.id,
      title: product.name,
      imgSrc: product.image_url || product.image || '',
      basePrice: Number(product.price),
      wishlistItemId: item.id,
    };
  }

  function getLocalWishlist() {
    try {
      const items = JSON.parse(localStorage.getItem(STORAGE_KEYS.wishlist) || '[]');
      return Array.isArray(items) ? items : [];
    } catch (error) {
      return [];
    }
  }

  function setLocalWishlist(items) {
    localStorage.setItem(STORAGE_KEYS.wishlist, JSON.stringify(items));
  }

  async function loadWishlistCache() {
    if (isLoggedIn()) {
      try {
        const items = await fetchWishlist();
        return items.map(mapWishlistItemToLocal);
      } catch (error) {
        console.warn('Could not load server wishlist:', error);
        return [];
      }
    }
    return getLocalWishlist();
  }

  function isProductWishlisted(productId, wishlistItems) {
    const id = String(productId);
    return wishlistItems.some(
      (item) => String(item.productId || item.id) === id || String(item.id) === id
    );
  }

  async function toggleWishlist(product) {
    const productId = Number(product.productId || product.id);
    if (!productId) {
      throw new Error('This item is not linked to a live product yet.');
    }

    if (isLoggedIn()) {
      const current = await fetchWishlist();
      const exists = current.some((item) => item.product?.id === productId);
      if (exists) {
        await removeFromWishlist(productId);
        return false;
      }
      await addToWishlist(productId);
      return true;
    }

    const local = getLocalWishlist();
    const id = String(product.id || productId);
    const index = local.findIndex(
      (item) => String(item.id) === id || String(item.productId) === String(productId)
    );

    if (index > -1) {
      local.splice(index, 1);
      setLocalWishlist(local);
      return false;
    }

    local.push({
      id,
      productId,
      imgSrc: product.img || product.imgSrc || '',
      title: product.title || product.name,
      basePrice: Number(product.price || product.basePrice),
    });
    setLocalWishlist(local);
    return true;
  }

  async function syncGuestWishlistToServer() {
    if (!isLoggedIn()) return;
    const local = getLocalWishlist();
    if (!local.length) return;

    for (const item of local) {
      const productId = Number(item.productId || item.id);
      if (!productId) continue;
      try {
        await addToWishlist(productId);
      } catch (error) {
        // Ignore duplicates or unavailable products.
      }
    }
    setLocalWishlist([]);
  }

  // ── Cart API helpers ──────────────────────────────────────────────────────

  let _cachedCartCount = 0;
  let _cartRefreshPromise = null;

  async function fetchCart() {
    return request('/cart/');
  }

  async function addToCart(productId, quantity = 1) {
    const cart = await request('/cart/add/', {
      method: 'POST',
      body: JSON.stringify({ product_id: Number(productId), quantity: Number(quantity) || 1 }),
    });
    _cachedCartCount = cart.item_count || 0;
    return cart;
  }

  async function updateCartItem(itemId, quantity) {
    if (quantity <= 0) {
      return removeCartItem(itemId);
    }
    const result = await request(`/cart/items/${itemId}/`, {
      method: 'PATCH',
      body: JSON.stringify({ quantity }),
    });
    // Re-fetch full cart to get accurate item_count
    const cart = await fetchCart();
    _cachedCartCount = cart.item_count || 0;
    return result;
  }

  async function removeCartItem(itemId) {
    await request(`/cart/items/${itemId}/delete/`, { method: 'DELETE' });
    const cart = await fetchCart();
    _cachedCartCount = cart.item_count || 0;
    return cart;
  }

  async function clearCart() {
    await request('/cart/clear/', { method: 'POST' });
    _cachedCartCount = 0;
  }

  async function mergeGuestCart(sessionId) {
    const cart = await request('/cart/merge/', {
      method: 'POST',
      body: JSON.stringify({ session_id: sessionId }),
    });
    _cachedCartCount = cart.item_count || 0;
    return cart;
  }

  /**
   * Map an API cart item to the legacy localStorage shape so existing
   * render functions continue to work.
   */
  function mapCartItemToLegacy(item) {
    return {
      id: String(item.product_id),
      productId: item.product_id,
      title: item.product_name,
      basePrice: Number(item.price),
      qty: item.quantity,
      imgSrc: '', // will be enriched by caller if needed
      cartItemId: item.id,
      stock: item.stock,
    };
  }

  /**
   * Fetch the server cart and return items in legacy shape.
   * Falls back to an empty array on network errors.
   */
  async function getCartItemsLegacy() {
    try {
      const cart = await fetchCart();
      _cachedCartCount = cart.item_count || 0;
      return (cart.items || []).map(mapCartItemToLegacy);
    } catch (error) {
      console.warn('Could not load server cart:', error);
      return [];
    }
  }

  async function getCartCount() {
    try {
      const cart = await fetchCart();
      _cachedCartCount = cart.item_count || 0;
    } catch (error) {
      // Return last-known cached count on error
    }
    return _cachedCartCount;
  }

  async function updateBadges() {
    const cartCountEl = document.getElementById('cart-count');
    const wishCountEl = document.getElementById('wishlist-count');

    // Fire-and-forget cart count refresh (don't block rendering)
    _cartRefreshPromise = getCartCount();
    const cartTotal = _cachedCartCount;

    if (cartCountEl) {
      cartCountEl.innerText = cartTotal;
      cartCountEl.style.opacity = cartTotal > 0 ? '1' : '0';
    }

    let wishlistItems = [];
    try {
      wishlistItems = await loadWishlistCache();
    } catch (error) {
      wishlistItems = getLocalWishlist();
    }

    if (wishCountEl) {
      wishCountEl.innerText = wishlistItems.length;
      wishCountEl.style.opacity = wishlistItems.length > 0 ? '1' : '0';
    }

    document.querySelectorAll('.product-card').forEach((card) => {
      const productId = card.getAttribute('data-product-id') || card.getAttribute('data-id');
      const btn = card.querySelector('.quick-save-btn');
      if (!btn || !productId) return;
      if (isProductWishlisted(productId, wishlistItems)) {
        btn.classList.add('saved');
      } else {
        btn.classList.remove('saved');
      }
    });

    // Await the background cart refresh so next read is up-to-date
    if (_cartRefreshPromise) {
      await _cartRefreshPromise;
      _cartRefreshPromise = null;
      // Update badge text now that we have the fresh count
      if (cartCountEl) {
        cartCountEl.innerText = _cachedCartCount;
        cartCountEl.style.opacity = _cachedCartCount > 0 ? '1' : '0';
      }
    }

    return { cartTotal: _cachedCartCount, wishlistCount: wishlistItems.length, wishlistItems };
  }

  function wireAccountNav(root = document) {
    root.querySelectorAll('[data-account-link]').forEach((link) => {
      const auth = getAuth();
      const loggedOutHref = link.dataset.accountHrefLoggedOut || 'login.html';
      const loggedInHref = link.dataset.accountHrefLoggedIn || 'account.html';
      const dest = auth?.user ? loggedInHref : loggedOutHref;

      if (link.classList.contains('nav-route')) {
        link.setAttribute('data-target', dest);
      } else {
        link.setAttribute('href', dest);
      }

      if (auth?.user) {
        link.setAttribute('title', 'My account');
        link.classList.add('is-logged-in');
        if (link.dataset.accountLabelLoggedIn) {
          link.textContent = link.dataset.accountLabelLoggedIn;
        }
      } else {
        link.setAttribute('title', 'Sign in or create account');
        link.classList.remove('is-logged-in');
        if (link.dataset.accountLabelLoggedOut) {
          link.textContent = link.dataset.accountLabelLoggedOut;
        }
      }
    });
  }

  async function buildProductMap() {
    const products = await fetchProducts();
    const map = new Map();
    products.forEach((product) => {
      map.set(normalize(product.name), product);
    });
    return map;
  }

  async function buildOrderItems(cartData) {
    if (!Array.isArray(cartData) || cartData.length === 0) {
      throw new Error('Your bag is empty.');
    }

    const products = await fetchProducts();
    const byId = new Map(products.map((product) => [String(product.id), product]));
    const byName = new Map(products.map((product) => [normalize(product.name), product]));

    return cartData.map((line) => {
      const product =
        (line.productId != null && byId.get(String(line.productId))) ||
        (line.id != null && byId.get(String(line.id))) ||
        (line.title && byName.get(normalize(line.title)));

      if (!product) {
        throw new Error(
          `We could not match "${line.title || line.id}" to a live product. Refresh and try again.`
        );
      }

      return {
        product_id: product.id,
        quantity: Number(line.qty) || 1,
      };
    });
  }

  async function submitCheckoutOrder(form, cartData) {
    const items = await buildOrderItems(cartData);
    const paymentMethod = form.querySelector('input[name="payment"]:checked')?.value || 'cod';

    return submitOrder({
      contact_email: form.querySelector('[name="contact_email"]').value.trim(),
      contact_phone: form.querySelector('[name="contact_phone"]').value.trim(),
      shipping_first_name: form.querySelector('[name="shipping_first_name"]').value.trim(),
      shipping_last_name: form.querySelector('[name="shipping_last_name"]').value.trim(),
      shipping_address_line_1: form.querySelector('[name="shipping_address_line_1"]').value.trim(),
      shipping_address_line_2: form.querySelector('[name="shipping_address_line_2"]')?.value.trim() || '',
      shipping_city: form.querySelector('[name="shipping_city"]').value.trim(),
      shipping_state: form.querySelector('[name="shipping_state"]').value.trim(),
      shipping_pincode: form.querySelector('[name="shipping_pincode"]').value.trim(),
      payment_method: paymentMethod,
      items,
    });
  }

  function wireNewsletterForms(root = document) {
    root.querySelectorAll('.news-input-group').forEach((group) => {
      const input = group.querySelector('.news-input');
      const btn = group.querySelector('.news-btn');
      if (!input || !btn || btn.dataset.apiWired === 'true') return;

      btn.dataset.apiWired = 'true';
      btn.addEventListener('click', async (event) => {
        event.preventDefault();
        const email = input.value.trim();
        if (!email) return;

        const original = btn.innerText;
        btn.innerText = 'Joining...';
        btn.disabled = true;

        try {
          await subscribeNewsletter(email);
          input.value = '';
          if (typeof window.showToast === 'function') {
            window.showToast('Welcome to the studio circle!');
          }
        } catch (error) {
          if (typeof window.showToast === 'function') {
            window.showToast(error.message || 'Could not subscribe right now.');
          }
        } finally {
          btn.innerText = original;
          btn.disabled = false;
        }
      });
    });
  }

  function formatMoney(value) {
    return '₹' + Number(value || 0).toLocaleString('en-IN', { maximumFractionDigits: 2 });
  }

  function formatOrderStatus(status) {
    return String(status || '')
      .replace(/_/g, ' ')
      .replace(/\b\w/g, (char) => char.toUpperCase());
  }

  function formatWorkshopDate(dateStr, timeStr) {
    if (!dateStr) return '';
    const date = new Date(`${dateStr}T${timeStr || '00:00:00'}`);
    if (Number.isNaN(date.getTime())) return dateStr;
    return date.toLocaleString('en-IN', {
      weekday: 'short',
      day: 'numeric',
      month: 'short',
      hour: 'numeric',
      minute: '2-digit',
    });
  }

  // ── Reviews API helpers ───────────────────────────────────────────────────

  /**
   * Render star rating HTML (supports half-stars).
   * @param {number|null} rating  e.g. 4.5, 3.0, null
   * @param {object} [opts]
   * @param {boolean} [opts.showCount]  append " (24)" after stars
   * @param {number} [opts.count]       review count
   * @param {string} [opts.size]        'sm' | 'md' | 'lg' (default 'sm')
   * @param {boolean} [opts.clickable]  show "Write a review" / "No reviews yet" fallback
   * @returns {string} HTML string
   */
  function renderStars(rating, opts = {}) {
    const { showCount, count, size = 'sm', clickable } = opts;
    const countVal = count != null ? Number(count) : 0;
    const ratingVal = rating != null ? Number(rating) : null;

    if (ratingVal == null && !clickable) {
      return `<span class="star-rating star-rating--${size} star-rating--empty">No reviews yet</span>`;
    }

    if (ratingVal == null && clickable) {
      return `<span class="star-rating star-rating--${size} star-rating--empty">No reviews yet</span>`;
    }

    let html = `<span class="star-rating star-rating--${size}">`;
    const full = Math.floor(ratingVal);
    const half = ratingVal - full >= 0.25 && ratingVal - full < 0.75;
    const showFullStar = ratingVal - full >= 0.75;

    for (let i = 0; i < 5; i++) {
      if (i < full) {
        html += `<svg class="star-icon star-icon--full" viewBox="0 0 24 24"><path d="M12 2l3.09 6.26L22 9.27l-5 4.87 1.18 6.88L12 17.77l-6.18 3.25L7 14.14 2 9.27l6.91-1.01L12 2z"/></svg>`;
      } else if (i === full && half) {
        html += `<svg class="star-icon star-icon--half" viewBox="0 0 24 24"><defs><linearGradient id="half-grad"><stop offset="50%" stop-color="currentColor"/><stop offset="50%" stop-color="transparent" stop-opacity="0.3"/></linearGradient></defs><path d="M12 2l3.09 6.26L22 9.27l-5 4.87 1.18 6.88L12 17.77l-6.18 3.25L7 14.14 2 9.27l6.91-1.01L12 2z" fill="url(#half-grad)" stroke="currentColor" stroke-width="0.5"/></svg>`;
      } else if (i === full && showFullStar) {
        html += `<svg class="star-icon star-icon--full" viewBox="0 0 24 24"><path d="M12 2l3.09 6.26L22 9.27l-5 4.87 1.18 6.88L12 17.77l-6.18 3.25L7 14.14 2 9.27l6.91-1.01L12 2z"/></svg>`;
      } else {
        html += `<svg class="star-icon star-icon--empty" viewBox="0 0 24 24"><path d="M12 2l3.09 6.26L22 9.27l-5 4.87 1.18 6.88L12 17.77l-6.18 3.25L7 14.14 2 9.27l6.91-1.01L12 2z"/></svg>`;
      }
    }

    html += `</span>`;

    if (showCount && countVal > 0) {
      html += ` <span class="review-count-text">(${countVal})</span>`;
    }

    return html;
  }

  async function fetchProductReviews(productId, page = 1, pageSize = 5) {
    return request(`/products/${productId}/reviews/?page=${page}&page_size=${pageSize}`);
  }

  async function fetchReviewSummary(productId) {
    return request(`/products/${productId}/reviews/summary/`);
  }

  async function submitReview(productId, { rating, title, comment }) {
    return request(`/products/${productId}/reviews/`, {
      method: 'POST',
      body: JSON.stringify({ rating, title: title || '', comment: comment || '' }),
    });
  }

  async function fetchProductQuestions(productId) {
    return request(`/products/${productId}/questions/`);
  }

  async function submitProductQuestion(productId, { askerName, question }) {
    return request(`/products/${productId}/questions/`, {
      method: 'POST',
      body: JSON.stringify({
        asker_name: askerName || 'Anonymous',
        question: question || '',
      }),
    });
  }

  async function answerProductQuestion(productId, questionId, { answerText }) {
    return request(`/products/${productId}/questions/${questionId}/answer/`, {
      method: 'PATCH',
      body: JSON.stringify({ answer_text: answerText || '' }),
    });
  }

  async function deleteProductQuestion(productId, questionId) {
    return request(`/products/${productId}/questions/${questionId}/answer/`, {
      method: 'DELETE',
    });
  }
  
  function updateNavLinks() {
    const isLoggedIn = window.UdaanAPI?.isLoggedIn();
    const signinLink = document.getElementById('nav-signin-link');
    const signupLink = document.getElementById('nav-signup-link');

    if (isLoggedIn) {
        if (signinLink) {
            signinLink.innerText = 'Account';
            signinLink.href = '/account';
            signinLink.classList.add('is-logged-in');
        }
        if (signupLink) {
            signupLink.innerText = 'My Account';
            signupLink.href = '/account';
        }
    } else {
        // This part ensures that if they logout, it switches back to Sign In
        if (signinLink) {
            signinLink.innerText = 'Sign In';
            signinLink.href = '/login';
            signinLink.classList.remove('is-logged-in');
        }
    }
}

// Run it immediately
document.addEventListener('DOMContentLoaded', updateNavLinks);
// Run it again after a slight delay just in case the API is slow to initialize
window.addEventListener('load', updateNavLinks);

  function wireSiteSearchForms(root = document) {
    root.querySelectorAll('[data-site-search]').forEach((form) => {
      if (form.dataset.searchWired === 'true') return;
      form.dataset.searchWired = 'true';

      const input = form.querySelector('input[type="search"], input[name="q"]');
      if (!input) return;

      form.addEventListener('submit', (event) => {
        event.preventDefault();
        const q = input.value.trim();
        if (q.length < 2) {
          if (typeof window.showToast === 'function') {
            window.showToast('Type at least 2 characters to search.');
          }
          return;
        }
        window.location.href = `search.html?q=${encodeURIComponent(q)}`;
      });
    });
  }

  // ── Google Sign-In global helpers ───────────────────────────────────────

  /**
   * Default credential callback — used on pages other than /login.
   * Overridden by login.html with a page-specific handler that manipulates
   * form buttons and shows inline errors.
   */
  window.handleGoogleCredentialResponse = async function (response) {
    const idToken = response.credential;
    if (!idToken) {
      console.error('Google sign-in did not return a credential.');
      return;
    }

    try {
      await window.UdaanAPI.googleLogin(idToken);
      if (typeof window.showToast === 'function') {
        window.showToast('Signed in with Google!');
      }
      // Redirect to account after a short delay
      setTimeout(() => { window.location.href = '/account'; }, 800);
    } catch (error) {
      console.error('Google sign-in failed:', error);
      if (typeof window.showToast === 'function') {
        window.showToast(error.message || 'Google sign-in failed.');
      }
    }
  };

  /**
   * Called by the GIS SDK once it has loaded (via the `onload` query param
   * on the script tag).  Initialises the Google One-Tap / Sign-In button on
   * pages that include the #googleSignInDiv container.
   */
  window.onGoogleLibraryLoad = function () {
    const clientIdMeta = document.querySelector('meta[name="google-signin-client_id"]');
    const clientId = (clientIdMeta && clientIdMeta.content) || 'YOUR_GOOGLE_CLIENT_ID';

    if (!clientId || clientId === 'YOUR_GOOGLE_CLIENT_ID') {
      console.warn(
        'Google Sign-In client ID not configured. ' +
        'Add <meta name="google-signin-client_id" content="..."> or set GOOGLE_CLIENT_ID.'
      );
    }

    if (window.google?.accounts?.id) {
      try {
        google.accounts.id.disableAutoSelect();
      } catch (e) {
        console.warn('Failed to call disableAutoSelect:', e);
      }
    }

    google.accounts.id.initialize({
      client_id: clientId,
      callback: window.handleGoogleCredentialResponse,
      auto_select: false,
      context: 'signin',
    });

    const btnContainer = document.getElementById('googleSignInDiv');
    if (btnContainer) {
      google.accounts.id.renderButton(btnContainer, {
        theme: 'outline',
        size: 'large',
        text: 'continue_with',
        shape: 'rectangular',
        width: btnContainer.offsetWidth > 300 ? 300 : btnContainer.offsetWidth,
      });
    }

    // Non-blocking One Tap prompt (appears top-right)
    google.accounts.id.prompt();
  };

  // ── End Google Sign-In ──────────────────────────────────────────────────

  document.addEventListener('DOMContentLoaded', () => {
    wireAccountNav();
    wireSiteSearchForms();
    updateBadges();
  });

  document.addEventListener('udaan:auth-change', () => {
    wireAccountNav(document);
    updateBadges();
  });

  window.UdaanAPI = {
    apiBase,
    STORAGE_KEYS,
    normalize,
    request,
    healthCheck,
    fetchProducts,
    searchProducts,
    mapApiProduct,
    buildProductMap,
    buildOrderItems,
    submitCheckoutOrder,
    fetchBlogPosts,
    fetchBlogPost,
    checkDelivery,
    subscribeNewsletter,
    submitOrder,
    wireNewsletterForms,
    getAuth,
    setAuth,
    isLoggedIn,
    registerUser,
    loginUser,
    googleLogin,
    logoutUser,
    requestPasswordReset,
    confirmPasswordReset,
    fetchBlogPosts,
    fetchBlogPost,
    fetchCurrentUser,
    fetchCurrentProfile,
    updateCurrentUser,
    fetchOrders,
    fetchOrder,
    guestOrderLookup,
    fetchWorkshops,
    fetchWorkshop,
    initiateWorkshopPayment,
    verifyWorkshopPayment,
    initiateOrderPayment,
    verifyOrderPayment,
    fetchMyBookings,
    fetchWishlist,
    addToWishlist,
    removeFromWishlist,
    getLocalWishlist,
    setLocalWishlist,
    loadWishlistCache,
    toggleWishlist,
    isProductWishlisted,
    syncGuestWishlistToServer,
    // Cart API
    fetchCart,
    addToCart,
    updateCartItem,
    removeCartItem,
    clearCart,
    mergeGuestCart,
    getCartItemsLegacy,
    mapCartItemToLegacy,
    getCartCount,
    // Reviews API
    renderStars,
    fetchProductReviews,
    fetchReviewSummary,
    submitReview,
    fetchProductQuestions,
    submitProductQuestion,
    answerProductQuestion,
    deleteProductQuestion,
    // Badges
    updateBadges,
    wireAccountNav,
    wireSiteSearchForms,
    formatMoney,
    formatOrderStatus,
    formatWorkshopDate,
  };
})();
