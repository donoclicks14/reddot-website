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
const hero = document.querySelector('.hero, .page-hero');
if (hero) {
  new IntersectionObserver(([entry]) => {
    bar.classList.toggle('show', !entry.isIntersecting);
  }).observe(hero);
} else {
  bar.classList.add('show');
}
