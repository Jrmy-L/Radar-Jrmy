'use strict';

const STORAGE_KEY = 'radar-position-proposals-v1';

export function initAlerts(data) {
  const currentProposals = data.technologies
    .filter(t => t.position_proposal)
    .map(t => t.id);

  const stored = JSON.parse(localStorage.getItem(STORAGE_KEY) || '{"ids":[],"generatedAt":""}');
  const newProposals = currentProposals.filter(id => !stored.ids.includes(id));

  updateNavBadge(currentProposals.length);

  if (newProposals.length === 0) return;

  const newTechs = data.technologies.filter(t => newProposals.includes(t.id));
  showBanner(newTechs, () => {
    localStorage.setItem(STORAGE_KEY, JSON.stringify({
      ids: currentProposals,
      generatedAt: data.generated_at,
    }));
  });
}

function updateNavBadge(count) {
  const badge = document.getElementById('rising-badge');
  const countEl = document.getElementById('rising-count');
  if (!badge || !countEl) return;
  if (count > 0) {
    countEl.textContent = count;
    badge.style.display = 'inline-flex';
  } else {
    badge.style.display = 'none';
  }
}

function showBanner(techs, onDismiss) {
  const existing = document.getElementById('alert-banner');
  if (existing) existing.remove();

  const banner = document.createElement('div');
  banner.id = 'alert-banner';
  banner.className = 'alert-banner';
  banner.setAttribute('role', 'alert');
  banner.innerHTML = `
    <div class="alert-content">
      <span class="alert-icon">📈</span>
      <span class="alert-text">
        <strong>${techs.length} nouvelle${techs.length > 1 ? 's' : ''} proposition${techs.length > 1 ? 's' : ''} à examiner :</strong>
        <span class="alert-tags">
          ${techs.map(t => `<span class="proposal-badge">${t.name} : ${t.position_proposal.from} → ${t.position_proposal.to}</span>`).join('')}
        </span>
      </span>
    </div>
    <button class="alert-dismiss" aria-label="Fermer la notification">✕</button>
  `;

  banner.querySelector('.alert-dismiss').addEventListener('click', () => {
    banner.classList.add('alert-hiding');
    setTimeout(() => banner.remove(), 300);
    onDismiss();
  });

  const nav = document.querySelector('nav');
  if (nav) {
    nav.insertAdjacentElement('afterend', banner);
  } else {
    document.body.prepend(banner);
  }
}
