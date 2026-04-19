/* dashboard.js — logic for the servers selection and module management */

(function () {
  'use strict';

  // theme init
  const savedTheme = localStorage.getItem('theme');
  const prefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches;
  document.documentElement.dataset.theme = savedTheme || (prefersDark ? 'dark' : 'light');

  // fetch user info and guilds
  async function loadDashboard() {
    const list = document.getElementById('guild-list');
    if (!list) return;

    try {
      // fetch user and guilds in parallel
      const [meResp, guildsResp] = await Promise.all([
        fetch('/api/me'),
        fetch('/api/guilds'),
      ]);

      if (!meResp.ok || !guildsResp.ok) {
        window.location.href = '/auth/discord';
        return;
      }

      const { user } = await meResp.json();
      const { guilds } = await guildsResp.json();

      // update nav user info
      const navUser = document.getElementById('nav-user');
      const navPfp = document.getElementById('nav-pfp');
      const navName = document.getElementById('nav-username');

      if (navUser && user) {
        navPfp.src = user.avatar
          ? `https://cdn.discordapp.com/avatars/${user.id}/${user.avatar}.png`
          : 'public/melvin.jpg';
        navName.textContent = user.username.toLowerCase();
        navUser.hidden = false;
      }

      // render guilds (backend already filtered for manage_guild + bot present)
      list.innerHTML = '';

      if (!guilds || guilds.length === 0) {
        list.innerHTML = '<p class="user-handle">no mutual servers found. make sure melvin is added to your server.</p>';
        return;
      }

      guilds.forEach(guild => {
        const card = document.createElement('div');
        card.className = 'guild-card';
        card.onclick = () => window.location.href = `/manage/${guild.id}`;

        const iconDiv = document.createElement('div');
        iconDiv.className = 'guild-card__icon';
        if (guild.icon) {
          iconDiv.innerHTML = `<img src="https://cdn.discordapp.com/icons/${guild.id}/${guild.icon}.png" alt="">`;
        } else {
          iconDiv.textContent = guild.name.charAt(0).toLowerCase();
        }

        const nameSpan = document.createElement('span');
        nameSpan.className = 'guild-card__name';
        nameSpan.textContent = guild.name.toLowerCase();

        card.appendChild(iconDiv);
        card.appendChild(nameSpan);
        list.appendChild(card);
      });

    } catch (e) {
      console.error('dashboard error:', e);
    }
  }

  // ── management page logic ──
  async function loadGuildDetails() {
    const title = document.getElementById('guild-name-title');
    if (!title) return;

    const guildId = window.location.pathname.split('/').pop();
    try {
      const resp = await fetch(`/api/guild/${guildId}`);
      if (resp.ok) {
        const guild = await resp.json();
        
        // Update breadcrumb
        const breadcrumb = document.getElementById('guild-name-breadcrumb');
        const breadcrumbIcon = document.getElementById('guild-icon-breadcrumb');
        if (breadcrumb) breadcrumb.textContent = guild.name.toLowerCase();
        if (breadcrumbIcon && guild.icon) {
          breadcrumbIcon.src = `https://cdn.discordapp.com/icons/${guild.id}/${guild.icon}.png`;
          breadcrumbIcon.style.display = 'block';
        }
        title.textContent = guild.name.toLowerCase();

        // Update sidebar brand with guild icon
        const sidebarLogo = document.querySelector('.sidebar__logo');
        if (sidebarLogo && guild.icon) {
          sidebarLogo.src = `https://cdn.discordapp.com/icons/${guild.id}/${guild.icon}.png`;
        }

        // Init modules with real data
        initModules(guildId, guild.config);

        // Update metrics
        if (guild.metrics) {
          const safeUpdate = (id, val) => {
            const el = document.getElementById(id);
            if (el) el.textContent = val;
          };

          safeUpdate('stat-modules-enabled', guild.metrics.enabled_modules);
          safeUpdate('stat-messages-total', guild.metrics.message_count);
          safeUpdate('stat-commands-ran', guild.metrics.commands_ran);
          safeUpdate('stat-member-count', guild.metrics.member_count);
          safeUpdate('stat-peak-online', guild.metrics.peak_online);

          if (guild.metrics.joined_at) {
            const joined = new Date(guild.metrics.joined_at);
            const now = new Date();
            const diffTime = Math.abs(now - joined);
            const diffDays = Math.ceil(diffTime / (1000 * 60 * 60 * 24));
            document.getElementById('melvin-joined-text').textContent = `you added melvin ${diffDays === 1 ? '1 day' : diffDays + ' days'} ago.`;
          }
        }

        // Load audit logs preview
        loadHomeLogs(guildId);

      } else {
        window.location.href = '/servers';
      }
    } catch (e) {
      console.error('failed to load guild details', e);
    }
  }

  function initViewSwitching() {
    const navLinks = document.querySelectorAll('.sidebar__link');
    const views = document.querySelectorAll('.dashboard-view');
    if (navLinks.length === 0) return;

    navLinks.forEach(link => {
      link.addEventListener('click', (e) => {
        e.preventDefault();
        const targetView = link.getAttribute('data-view');
        
        navLinks.forEach(l => l.classList.remove('is-active'));
        link.classList.add('is-active');

        views.forEach(v => {
          v.hidden = v.id !== `view-${targetView}`;
        });
      });
    });
  }

  function formatRelativeTime(isoString) {
    const date = new Date(isoString);
    const now = new Date();
    const diff = Math.floor((now - date) / 1000);
    if (diff < 60) return 'just now';
    if (diff < 3600) return `${Math.floor(diff / 60)}m ago`;
    return '>1h ago';
  }

  async function loadHomeLogs(guildId) {
    const list = document.getElementById('home-audit-list');
    if (!list) return;

    try {
      const resp = await fetch(`/api/guild/${guildId}/logs`);
      if (resp.ok) {
        const logs = await resp.json();
        if (logs.length > 0) {
          list.innerHTML = logs.map(log => {
            let avatarUrl = '../public/melvin.jpg';
            if (log.user_avatar && log.user_avatar !== 'null') {
              const ext = log.user_avatar.startsWith('a_') ? 'gif' : 'webp';
              avatarUrl = `https://cdn.discordapp.com/avatars/${log.user_id}/${log.user_avatar}.${ext}?size=64`;
            }
            
            return `
              <div class="audit-item">
                  <div class="audit-item__left">
                      <img src="${avatarUrl}" class="audit-item__pfp" alt="">
                      <div class="audit-item__info">
                          <span class="audit-item__user">${log.user_name.toLowerCase()}</span>
                          <span class="audit-item__action">${log.action}</span>
                      </div>
                  </div>
                  <span class="audit-item__time">${formatRelativeTime(log.timestamp)}</span>
              </div>
            `;
          }).join('');
        }
      }
    } catch (e) {
      console.error('failed to load home logs', e);
    }
  }

  function initModules(guildId, config) {
    const container = document.getElementById('module-container');
    if (!container) return;

    const modules = [
      {
        id: 'base',
        name: 'base',
        desc: 'core commands and module framework. required for everything else.',
        enabled: config ? config.base_enabled : true,
        comingSoon: false,
      },
      { 
        id: 'moderation', 
        name: 'moderation', 
        desc: 'mute, kick, ban, and warn tools with persistent logging.', 
        enabled: config ? config.moderation_enabled : true,
        comingSoon: false,
      },
      {
        id: 'logging',
        name: 'logging',
        desc: 'event logs for edits, deletes, joins, leaves, roles, and server changes.',
        enabled: config ? config.logging_enabled : false,
        comingSoon: true,
      },
      {
        id: 'tickets',
        name: 'tickets',
        desc: 'private support tickets with transcripts and staff workflows.',
        enabled: config ? config.tickets_enabled : false,
        comingSoon: true,
      },
      {
        id: 'frogboard',
        name: 'frogboard',
        desc: 'reaction highlight board (starboard) with flat, minimalist embeds.',
        enabled: config ? config.frogboard_enabled : false,
        comingSoon: true,
      },
      {
        id: 'levels',
        name: 'levels',
        desc: 'xp and level rewards for chat and voice activity.',
        enabled: config ? config.levels_enabled : false,
        comingSoon: true,
      },
      {
        id: 'economy',
        name: 'economy',
        desc: 'seasonal currency, daily rewards, shop, and leaderboards.',
        enabled: config ? config.economy_enabled : false,
        comingSoon: true,
      },
      {
        id: 'counting',
        name: 'counting',
        desc: 'simple counting channel with configurable rules and math support.',
        enabled: config ? config.counting_enabled : false,
        comingSoon: true,
      },
    ];

    container.innerHTML = '';
    modules.forEach(m => {
      const card = document.createElement('div');
      card.className = 'module-card';
      const badge = m.comingSoon ? '<span class="module-badge">coming soon</span>' : '';
      card.innerHTML = `
        <div class="module-card__header">
          <div class="module-card__info">
            <div class="module-card__title-row">
              <h3>${m.name}</h3>
              ${badge}
            </div>
            <p>${m.desc}</p>
          </div>
          <label class="module-toggle">
            <input type="checkbox" ${m.enabled ? 'checked' : ''} data-module="${m.id}">
            <span class="module-toggle__slider"></span>
          </label>
        </div>
        <div class="module-card__actions">
          <button class="btn btn--small btn--ghost" ${m.comingSoon ? 'disabled' : ''}>configure</button>
        </div>
      `;

      // Handle toggle
      const checkbox = card.querySelector('input[type="checkbox"]');
      checkbox.addEventListener('change', async () => {
        const isEnabled = checkbox.checked;
        try {
          const payload = { [`${m.id}_enabled`]: isEnabled };
          await fetch(`/api/guild/${guildId}/config`, {
            method: 'PATCH',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
          });
        } catch (e) {
          console.error('failed to update config', e);
          checkbox.checked = !isEnabled; // revert
        }
      });

      container.appendChild(card);
    });
  }

  async function syncSidebarUser() {
    const pfp = document.getElementById('sidebar-pfp');
    const name = document.getElementById('sidebar-name');
    const handle = document.getElementById('sidebar-handle');
    if (!pfp) return;

    try {
      const resp = await fetch('/api/me');
      if (resp.ok) {
        const { user } = await resp.json();
        pfp.src = user.avatar
          ? `https://cdn.discordapp.com/avatars/${user.id}/${user.avatar}.png`
          : '../public/melvin.jpg';
        name.textContent = user.global_name || user.username;
        handle.textContent = `@${user.username}`;
      }
    } catch (e) {}
  }

  // init sequences
  if (document.getElementById('guild-list')) {
    loadDashboard();
  }
  if (document.getElementById('guild-name-title')) {
    loadGuildDetails();
    initViewSwitching();
    syncSidebarUser();
  }

  // theme toggle logic (shared if themeToggle exists)
  const themeToggle = document.getElementById('theme-toggle');
  if (themeToggle) {
    themeToggle.addEventListener('click', () => {
      const doc = document.documentElement;
      const isDark = doc.dataset.theme === 'dark';
      const newTheme = isDark ? 'light' : 'dark';
      doc.dataset.theme = newTheme;
      localStorage.setItem('theme', newTheme);
      
      const sunIcon = themeToggle.querySelector('.sun');
      const moonIcon = themeToggle.querySelector('.moon');
      if (sunIcon && moonIcon) {
        if (newTheme === 'dark') {
          sunIcon.style.display = 'block';
          moonIcon.style.display = 'none';
        } else {
          sunIcon.style.display = 'none';
          moonIcon.style.display = 'block';
        }
      }
    });
  }

})();
