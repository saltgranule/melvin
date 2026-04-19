/* hero.js — minimal interactivity for the landing page */

(function () {
  'use strict';

  /* ── theme toggle removed ── */

  /* ── nav scroll state ── */
  const nav = document.getElementById('site-nav');

  window.addEventListener('scroll', () => {
    if (window.scrollY > 8) {
      nav.classList.add('nav--scrolled');
    } else {
      nav.classList.remove('nav--scrolled');
    }
  }, { passive: true });

  /* ── type-cycle on embed text ── */
  const messages = [
    { label: 'melvin', text: 'module <span class="embed__highlight">economy</span> enabled for <span class="embed__highlight">salt\'s server</span>.', tags: ['balance', 'daily', 'shop', 'leaderboard'] },
    { label: 'melvin', text: 'module <span class="embed__highlight">moderation</span> enabled for <span class="embed__highlight">salt\'s server</span>.', tags: ['warn', 'ban', 'automod', 'cases'] },
    { label: 'melvin', text: 'module <span class="embed__highlight">levels</span> enabled for <span class="embed__highlight">salt\'s server</span>.', tags: ['xp', 'milestone', 'roles'] },
    { label: 'melvin', text: 'module <span class="embed__highlight">frogboard</span> enabled for <span class="embed__highlight">salt\'s server</span>.', tags: ['stars', 'channel', 'threshold'] },
  ];

  const embedText = document.querySelector('#hero-embed .embed__text');
  const embedTags = document.querySelector('#hero-embed .embed__tags');

  if (embedText && embedTags) {
    let idx = 0;

    setInterval(() => {
      idx = (idx + 1) % messages.length;
      const m = messages[idx];

      embedText.style.opacity = '0';
      embedTags.style.opacity = '0';

      setTimeout(() => {
        embedText.innerHTML = m.text;
        embedTags.innerHTML = m.tags.map(t => `<span class="tag">${t}</span>`).join('');
        embedText.style.transition = 'opacity 280ms ease';
        embedTags.style.transition = 'opacity 280ms ease';
        embedText.style.opacity = '1';
        embedTags.style.opacity = '1';
      }, 200);

    }, 3200);
  }

  /* ── faq accordion ── */
  const faqTriggers = document.querySelectorAll('.faq__trigger');

  faqTriggers.forEach(trigger => {
    trigger.addEventListener('click', () => {
      const item = trigger.closest('.faq__item');
      item.classList.toggle('is-open');
    });
  });

})();
