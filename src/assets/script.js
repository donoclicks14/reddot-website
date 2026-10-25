// Mobile menu
const toggle = document.querySelector('.menu-toggle');
const nav = document.getElementById('nav');
toggle.addEventListener('click', () => {
  const open = toggle.getAttribute('aria-expanded') !== 'true';
  toggle.setAttribute('aria-expanded', open);
  toggle.setAttribute('aria-label', open ? 'Close menu' : 'Open menu');
  nav.classList.toggle('open', open);
});

// Tap list: expand a beer
document.querySelectorAll('.tap-row').forEach((row) => {
  row.addEventListener('click', () => {
    const open = row.getAttribute('aria-expanded') !== 'true';
    row.setAttribute('aria-expanded', open);
    row.parentElement.classList.toggle('open', open);
  });
});

// Enquiry form (demo: validates and confirms; wire to Netlify Forms or email in production)
const form = document.getElementById('enquiry');
if (form) {
  form.addEventListener('submit', (e) => {
    e.preventDefault();
    const error = form.querySelector('.form-error');
    const done = form.querySelector('.form-done');
    const missing = [];
    form.querySelectorAll('[required]').forEach((field) => {
      const bad = !field.value.trim() || !field.checkValidity();
      field.setAttribute('aria-invalid', bad);
      if (bad) missing.push(field.closest('label').firstChild.textContent.trim().toLowerCase());
    });
    if (missing.length) {
      error.textContent = `Add your ${missing.join(', ')} so our events team can reply.`;
      error.hidden = false;
      form.querySelector('[aria-invalid="true"]').focus();
      return;
    }
    error.hidden = true;
    done.textContent = `Enquiry sent. Our events team will reply to ${form.email.value}.`;
    done.hidden = false;
    form.reset();
  });
}

// Mobile booking bar appears once the page hero has scrolled away
const bar = document.querySelector('.mobile-book');
const hero = document.querySelector('.hero, .page-hero, .shop-hero');
if (hero) {
  new IntersectionObserver(([entry]) => {
    bar.classList.toggle('show', !entry.isIntersecting);
  }).observe(hero);
} else {
  bar.classList.add('show');
}

/* ---------- Shop ---------- */
const PRODUCTS = window.RD_PRODUCTS || {};
const BASE = window.RD_BASE || '';
const FREE_DELIVERY = 75;
const money = (n) => 'S$' + (Number.isInteger(n) ? n.toLocaleString('en-SG') : n.toFixed(2));

// Cart lives in this browser only (demo). Every read/write is guarded.
const store = {
  load() { try { return JSON.parse(localStorage.getItem('rd-cart')) || []; } catch { return []; } },
  save(items) { try { localStorage.setItem('rd-cart', JSON.stringify(items)); } catch { /* storage unavailable */ } },
};
let cart = store.load().filter((i) => PRODUCTS[i.id] && PRODUCTS[i.id].formats[i.fmt]);

const cartEl = document.getElementById('cart');
const cartBtn = document.querySelector('.cart-btn');
const countEl = document.querySelector('.cart-count');
const itemsEl = cartEl.querySelector('.cart-items');
let lastFocus = null;

function lineTotal(i) { return PRODUCTS[i.id].formats[i.fmt].price * i.qty; }

function renderCart() {
  const count = cart.reduce((n, i) => n + i.qty, 0);
  const total = cart.reduce((n, i) => n + lineTotal(i), 0);
  countEl.textContent = count;
  countEl.hidden = count === 0;
  cartBtn.setAttribute('aria-label', `Open cart, ${count} item${count === 1 ? '' : 's'}`);
  cartEl.classList.toggle('is-empty', count === 0);

  itemsEl.innerHTML = cart.map((i, idx) => {
    const p = PRODUCTS[i.id];
    const f = p.formats[i.fmt];
    const fmt = Object.keys(p.formats).length > 1 ? f.label : '';
    return `<li class="cart-item" style="--tint:${p.tint}">
      <div class="cart-thumb"><img src="${f.img}" alt=""></div>
      <div>
        <a class="cart-name" href="${BASE}${p.url}">${p.name}</a>
        ${fmt ? `<p class="cart-fmt">${fmt}</p>` : ''}
        <div class="cart-line">
          <span class="qty"><button type="button" class="qty-btn" data-idx="${idx}" data-step="-1" aria-label="One fewer ${p.name}">−</button><span>${i.qty}</span><button type="button" class="qty-btn" data-idx="${idx}" data-step="1" aria-label="One more ${p.name}">+</button></span>
          <button type="button" class="cart-remove" data-idx="${idx}">Remove</button>
        </div>
      </div>
      <p class="cart-price">${money(lineTotal(i))}</p>
    </li>`;
  }).join('');

  cartEl.querySelector('.cart-total strong').textContent = money(total);
  const ship = cartEl.querySelector('.cart-ship');
  const left = FREE_DELIVERY - total;
  ship.classList.toggle('done', left <= 0);
  ship.querySelector('.cart-ship-text').textContent = count === 0 ? `Free delivery in Singapore on orders over ${money(FREE_DELIVERY)}.`
    : left > 0 ? `Add ${money(left)} more for free delivery.` : 'You get free delivery.';
  ship.querySelector('.cart-ship-bar span').style.width = Math.min(100, (total / FREE_DELIVERY) * 100) + '%';
  cartEl.querySelector('.cart-note').textContent = '';
}

function openCart() {
  lastFocus = document.activeElement;
  cartEl.hidden = false;
  document.body.classList.add('cart-open');
  cartEl.querySelector('.cart-close').focus();
}
function closeCart() {
  cartEl.hidden = true;
  document.body.classList.remove('cart-open');
  if (lastFocus) lastFocus.focus();
}

function addToCart(id, fmt, qty) {
  const existing = cart.find((i) => i.id === id && i.fmt === fmt);
  if (existing) existing.qty = Math.min(99, existing.qty + qty);
  else cart.push({ id, fmt, qty });
  store.save(cart);
  renderCart();
  countEl.classList.remove('bump');
  void countEl.offsetWidth;
  countEl.classList.add('bump');
  openCart();
}

cartBtn.addEventListener('click', openCart);
cartEl.addEventListener('click', (e) => {
  if (e.target.closest('[data-close]')) return closeCart();
  const step = e.target.closest('.qty-btn[data-idx]');
  const remove = e.target.closest('.cart-remove');
  if (step) {
    const item = cart[step.dataset.idx];
    item.qty = Math.max(0, Math.min(99, item.qty + Number(step.dataset.step)));
    if (item.qty === 0) cart.splice(step.dataset.idx, 1);
  } else if (remove) {
    cart.splice(remove.dataset.idx, 1);
  } else {
    return;
  }
  store.save(cart);
  renderCart();
});
cartEl.querySelector('.cart-checkout').addEventListener('click', () => {
  cartEl.querySelector('.cart-note').textContent =
    'This is a demo shop. At launch, checkout connects to secure payment (card or PayNow) and delivery booking.';
});
document.addEventListener('keydown', (e) => {
  if (e.key === 'Escape' && !cartEl.hidden) closeCart();
});

// Add-to-cart forms (cards and product pages)
document.querySelectorAll('.add-form').forEach((f) => {
  f.addEventListener('submit', (e) => {
    e.preventDefault();
    const choice = f.querySelector('input[type="radio"]:checked, input[type="hidden"]');
    const qtyInput = f.querySelector('input[name="qty"]');
    const qty = qtyInput ? Math.max(1, Math.min(99, parseInt(qtyInput.value, 10) || 1)) : 1;
    addToCart(f.dataset.product, choice.value, qty);
  });
});

// Product page: quantity stepper, format switch updates price and photo
document.querySelectorAll('.buy-form .qty-btn').forEach((b) => {
  b.addEventListener('click', () => {
    const input = b.parentElement.querySelector('input');
    input.value = Math.max(1, Math.min(99, (parseInt(input.value, 10) || 1) + Number(b.dataset.step)));
  });
});
const stage = document.querySelector('.pdp-stage');
function showFormat(fmt) {
  if (!stage) return;
  stage.querySelectorAll('img').forEach((img) => { img.hidden = img.dataset.format !== fmt; });
  document.querySelectorAll('.thumbs button').forEach((t) => t.setAttribute('aria-pressed', t.dataset.format === fmt));
  const buy = document.querySelector('.buy-form');
  if (buy) document.querySelectorAll('[data-live-price]').forEach((el) => { el.textContent = money(PRODUCTS[buy.dataset.product].formats[fmt].price); });
  const radio = document.querySelector(`.buy-form input[value="${fmt}"]`);
  if (radio) radio.checked = true;
}
document.querySelectorAll('.buy-form input[type="radio"]').forEach((r) => r.addEventListener('change', () => showFormat(r.value)));
document.querySelectorAll('.thumbs button').forEach((t) => t.addEventListener('click', () => showFormat(t.dataset.format)));

// Phone: a slim "Add to cart" bar appears whenever the buy controls are off-screen
const buyForm = document.querySelector('.buy-form');
const buyBar = document.querySelector('.buy-bar');
if (buyForm && buyBar) {
  new IntersectionObserver(([entry]) => {
    buyBar.classList.toggle('show', !entry.isIntersecting);
  }, { rootMargin: '0px 0px -40px 0px' }).observe(buyForm.querySelector('.buy-row'));
  buyBar.querySelector('[data-buybar]').addEventListener('click', () => buyForm.requestSubmit());
}

// Shop grid: filter chips and sort
const grid = document.getElementById('product-grid');
if (grid) {
  const cards = [...grid.children];
  const shown = document.getElementById('shown');
  let filter = 'all';
  const apply = () => {
    let n = 0;
    cards.forEach((c) => { const on = filter === 'all' || c.dataset.cat === filter; c.hidden = !on; if (on) n++; });
    shown.textContent = n;
  };
  document.querySelectorAll('.chip').forEach((chip) => {
    chip.addEventListener('click', () => {
      filter = chip.dataset.filter;
      document.querySelectorAll('.chip').forEach((c) => c.setAttribute('aria-pressed', c === chip));
      apply();
    });
  });
  document.getElementById('sort').addEventListener('change', (e) => {
    const v = e.target.value;
    const sorted = v === 'featured' ? cards
      : [...cards].sort((a, b) => (v === 'low' ? 1 : -1) * (a.dataset.price - b.dataset.price));
    sorted.forEach((c) => grid.appendChild(c));
  });
}

renderCart();
