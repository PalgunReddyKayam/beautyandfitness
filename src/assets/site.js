const y = document.getElementById('year'); if (y) y.textContent = new Date().getFullYear();

const reduce = window.matchMedia('(prefers-reduced-motion: reduce)').matches;

/* Hero scene follows the pointer */
const stage = document.getElementById('stage');
const scene = document.getElementById('scene');
if (stage && scene && !reduce && window.matchMedia('(pointer:fine)').matches) {
  stage.addEventListener('mousemove', e => {
    const r = stage.getBoundingClientRect();
    const x = (e.clientX - r.left) / r.width - .5;
    const y = (e.clientY - r.top) / r.height - .5;
    scene.style.transform = `rotateY(${x * 14}deg) rotateX(${-y * 10}deg)`;
  });
  stage.addEventListener('mouseleave', () => { scene.style.transform = ''; });
}

/* Tilt cards & pillars toward the cursor */
function tilt(el, max) {
  el.addEventListener('mousemove', e => {
    const r = el.getBoundingClientRect();
    const x = (e.clientX - r.left) / r.width - .5;
    const y = (e.clientY - r.top) / r.height - .5;
    el.style.transform = `rotateY(${x * max}deg) rotateX(${-y * max}deg) translateY(-6px)`;
  });
  el.addEventListener('mouseleave', () => { el.style.transform = ''; });
}
if (!reduce && window.matchMedia('(pointer:fine)').matches) {
  document.querySelectorAll('.card').forEach(c => tilt(c, 10));
  document.querySelectorAll('.tilt').forEach(c => tilt(c, 5));
}

/* Newsletter (front-end only — connect a form service later) */
const form = document.getElementById('form');
if (form) form.addEventListener('submit', e => {
  e.preventDefault();
  document.getElementById('ok').style.display = 'block';
  e.target.reset();
});
