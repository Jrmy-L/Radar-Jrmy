'use strict';

import {
  loadData,
  formatNumber,
  trajectoryLabel,
  formatDate,
  experienceLabel,
  collectionStatusLabel,
} from './data-loader.js';
import { initAlerts } from './alerts.js';

const CATEGORIES = {
  languages: 'Langages',
  frameworks_front: 'Front-end',
  frameworks_back: 'Back-end',
  mobile: 'Mobile',
  databases: 'Bases de données',
  devops: 'DevOps',
  observability: 'Observabilité',
  security: 'Sécurité',
  messaging: 'Messaging',
  ai: 'IA',
};

let allTechs = [];
let sortKey = 'name';
let sortAsc = true;

function positionOrder(p) {
  return { adopt: 0, trial: 1, assess: 2, hold: 3 }[p] ?? 99;
}

function experienceOrder(level) {
  return { unassessed: 0, observed: 1, studied: 2, practiced: 3, delivered: 4, operated: 5 }[level] ?? 0;
}

function renderRow(tech) {
  const gh = tech.metrics?.github;
  const npm = tech.metrics?.npm;
  const traj = trajectoryLabel(tech.trajectory);
  const trajClass = tech.trajectory || 'stable';
  const collectionStatus = tech.collection_status || 'failed';
  const proposal = tech.position_proposal;

  return `<tr class="data-row" data-id="${tech.id}" tabindex="0" role="button" aria-expanded="false" title="Cliquer pour voir les détails">
    <td><span class="row-toggle-icon">▶</span> <strong>${tech.name}</strong></td>
    <td>${CATEGORIES[tech.category] || tech.category}</td>
    <td><span class="badge badge-${tech.position}">${tech.position}</span></td>
    <td><span class="badge badge-experience-${tech.experience || 'unassessed'}">${experienceLabel(tech.experience)}</span></td>
    <td>${proposal ? `<span class="proposal-badge">${proposal.from} → ${proposal.to}</span>` : '—'}</td>
    <td><span class="badge badge-${trajClass}">${traj}</span></td>
    <td>${gh ? formatNumber(gh.stars) : '—'}</td>
    <td>${npm ? formatNumber(npm.downloads_weekly) : '—'}</td>
    <td>${tech.switching_cost || '—'}</td>
    <td title="${collectionStatusLabel(collectionStatus)}"><span class="collection-status collection-status-${collectionStatus}"></span>${formatDate(tech.collected_at)}</td>
  </tr>`;
}

function renderDetailRow(tech) {
  const pros = (tech.pros || []).map(p => `<li>${p}</li>`).join('') || '<li>—</li>';
  const cons = (tech.cons || []).map(c => `<li>${c}</li>`).join('') || '<li>—</li>';
  const useCases = (tech.use_cases || []).map(u => `<li>${u}</li>`).join('') || '<li>—</li>';
  const notes = tech.notes ? `<p class="detail-notes">${tech.notes}</p>` : '';

  return `<tr class="detail-row" data-detail-for="${tech.id}">
    <td colspan="10">
      <div class="detail-panel">
        ${notes}
        ${tech.position_proposal ? `<div class="position-proposal"><strong>Proposition : ${tech.position_proposal.from.toUpperCase()} → ${tech.position_proposal.to.toUpperCase()}</strong><span>${tech.position_proposal.reason}</span><small>Cette proposition ne modifie pas automatiquement le YAML.</small></div>` : ''}
        ${(tech.evidence || []).length ? `<div class="detail-section"><h4>🧭 Preuves d’expérience</h4><ul>${tech.evidence.map(item => `<li>${item}</li>`).join('')}</ul></div>` : ''}
        <div class="detail-grid">
          <div class="detail-section detail-pros">
            <h4>✅ Avantages</h4>
            <ul>${pros}</ul>
          </div>
          <div class="detail-section detail-cons">
            <h4>⚠️ Inconvénients</h4>
            <ul>${cons}</ul>
          </div>
          <div class="detail-section detail-usecases">
            <h4>🎯 Contexte d'utilisation</h4>
            <ul>${useCases}</ul>
          </div>
        </div>
      </div>
    </td>
  </tr>`;
}

function toggleDetail(row) {
  const id = row.dataset.id;
  const existing = document.querySelector(`tr[data-detail-for="${id}"]`);

  if (existing) {
    existing.remove();
    row.classList.remove('expanded');
    row.setAttribute('aria-expanded', 'false');
    row.querySelector('.row-toggle-icon').textContent = '▶';
    return;
  }

  // Close any other open detail
  document.querySelectorAll('.detail-row').forEach(r => r.remove());
  document.querySelectorAll('.data-row.expanded').forEach(r => {
    r.classList.remove('expanded');
    r.setAttribute('aria-expanded', 'false');
    r.querySelector('.row-toggle-icon').textContent = '▶';
  });

  const tech = allTechs.find(t => t.id === id);
  if (!tech) return;

  const detailTr = document.createElement('tbody');
  detailTr.innerHTML = renderDetailRow(tech);
  row.insertAdjacentElement('afterend', detailTr.firstElementChild);

  row.classList.add('expanded');
  row.setAttribute('aria-expanded', 'true');
  row.querySelector('.row-toggle-icon').textContent = '▼';
}

function getFilteredSorted() {
  const query = document.getElementById('search').value.toLowerCase();
  const posFilter = document.getElementById('filter-position').value;
  const experienceFilter = document.getElementById('filter-experience').value;
  const catFilter = document.getElementById('filter-category').value;

  const result = allTechs.filter(t => {
    const matchText = !query || t.name.toLowerCase().includes(query) || (t.notes || '').toLowerCase().includes(query);
    const matchPos = !posFilter || t.position === posFilter;
    const matchExperience = !experienceFilter || (t.experience || 'unassessed') === experienceFilter;
    const matchCat = !catFilter || t.category === catFilter;
    return matchText && matchPos && matchExperience && matchCat;
  });

  result.sort((a, b) => {
    let va, vb;
    if (sortKey === 'position') { va = positionOrder(a.position); vb = positionOrder(b.position); }
    else if (sortKey === 'experience') { va = experienceOrder(a.experience); vb = experienceOrder(b.experience); }
    else if (sortKey === 'stars') { va = a.metrics?.github?.stars ?? -1; vb = b.metrics?.github?.stars ?? -1; }
    else if (sortKey === 'npm') { va = a.metrics?.npm?.downloads_weekly ?? -1; vb = b.metrics?.npm?.downloads_weekly ?? -1; }
    else if (sortKey === 'trajectory') { va = a.trajectory || ''; vb = b.trajectory || ''; }
    else { va = (a[sortKey] || '').toString().toLowerCase(); vb = (b[sortKey] || '').toString().toLowerCase(); }

    if (va < vb) return sortAsc ? -1 : 1;
    if (va > vb) return sortAsc ? 1 : -1;
    return 0;
  });

  return result;
}

function render() {
  const tbody = document.getElementById('tbody');
  const filtered = getFilteredSorted();
  tbody.innerHTML = filtered.length
    ? filtered.map(renderRow).join('')
    : '<tr><td colspan="10" class="loading">Aucune technologie trouvée</td></tr>';
  document.getElementById('count').textContent = `${filtered.length} technologie${filtered.length > 1 ? 's' : ''}`;

  tbody.querySelectorAll('.data-row').forEach(row => {
    row.addEventListener('click', () => toggleDetail(row));
    row.addEventListener('keydown', e => {
      if (e.key === 'Enter' || e.key === ' ') { e.preventDefault(); toggleDetail(row); }
    });
  });
}

function setupSortHeaders() {
  document.querySelectorAll('th[data-sort]').forEach(th => {
    th.style.cursor = 'pointer';
    th.addEventListener('click', () => {
      const key = th.dataset.sort;
      if (sortKey === key) {
        sortAsc = !sortAsc;
      } else {
        sortKey = key;
        sortAsc = true;
      }
      document.querySelectorAll('th[data-sort]').forEach(h => h.classList.remove('sort-asc', 'sort-desc'));
      th.classList.add(sortAsc ? 'sort-asc' : 'sort-desc');
      render();
    });
  });
}

async function init() {
  try {
    const data = await loadData();
    allTechs = data.technologies;

    document.getElementById('last-update').textContent =
      new Date(data.generated_at).toLocaleString('fr-FR');

    initAlerts(data);

    const catSelect = document.getElementById('filter-category');
    const cats = [...new Set(allTechs.map(t => t.category))].sort();
    cats.forEach(c => {
      const opt = document.createElement('option');
      opt.value = c;
      opt.textContent = CATEGORIES[c] || c;
      catSelect.appendChild(opt);
    });

    setupSortHeaders();

    ['search', 'filter-position', 'filter-experience', 'filter-category'].forEach(id => {
      document.getElementById(id).addEventListener('input', render);
      document.getElementById(id).addEventListener('change', render);
    });

    render();
  } catch (err) {
    document.getElementById('tbody').innerHTML =
      `<tr><td colspan="10" class="error">Erreur de chargement : ${err.message}</td></tr>`;
  }
}

init();
