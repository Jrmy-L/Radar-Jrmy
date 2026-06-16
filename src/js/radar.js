'use strict';

import { loadData, getCategoryColor, trajectoryLabel, formatNumber } from './data-loader.js';

const WIDTH = 760;
const HEIGHT = 760;
const CX = WIDTH / 2;
const CY = HEIGHT / 2;
const MAX_R = 340;

const RINGS = [
  { id: 'adopt',  label: 'ADOPT',  r: MAX_R * 0.25, color: '#F29F52' },
  { id: 'trial',  label: 'TRIAL',  r: MAX_R * 0.50, color: '#FDE892' },
  { id: 'assess', label: 'ASSESS', r: MAX_R * 0.75, color: '#CEC4E5' },
  { id: 'hold',   label: 'HOLD',   r: MAX_R * 1.00, color: '#5E5483' },
];

const RING_INDEX = { adopt: 0, trial: 1, assess: 2, hold: 3 };

const CATEGORIES = [
  'languages', 'frameworks_front', 'frameworks_back',
  'mobile', 'databases', 'devops',
  'observability', 'security', 'messaging', 'ai',
];

let allTechs = [];
const activeCategories = new Set(CATEGORIES);
let tooltip = null;

function ringInner(idx) {
  return idx === 0 ? 0 : RINGS[idx - 1].r;
}

function randomAngle(seed) {
  const x = Math.sin(seed * 12.9898 + 78.233) * 43758.5453;
  return (x - Math.floor(x)) * 2 * Math.PI;
}

function randomRadius(minR, maxR, seed) {
  const x = Math.sin(seed * 93.9898 + 17.211) * 53421.5453;
  const t = (x - Math.floor(x));
  return minR + t * (maxR - minR);
}

function placeDot(tech, index) {
  const ringIdx = RING_INDEX[tech.position] ?? 3;
  const minR = ringInner(ringIdx) + 12;
  const maxR = RINGS[ringIdx].r - 12;
  const angle = randomAngle(index);
  const r = randomRadius(minR, maxR, index + 0.5);
  return {
    x: CX + r * Math.cos(angle),
    y: CY + r * Math.sin(angle),
  };
}

function buildSvg() {
  const svg = d3.select('#radar-svg')
    .attr('width', WIDTH)
    .attr('height', HEIGHT)
    .attr('viewBox', `0 0 ${WIDTH} ${HEIGHT}`);

  svg.selectAll('*').remove();

  const bg = svg.append('g').attr('class', 'rings');
  [...RINGS].reverse().forEach(ring => {
    bg.append('circle')
      .attr('cx', CX).attr('cy', CY).attr('r', ring.r)
      .attr('fill', ring.color).attr('fill-opacity', 0.06)
      .attr('stroke', ring.color).attr('stroke-opacity', 0.25).attr('stroke-width', 1);
    bg.append('text')
      .attr('x', CX).attr('y', CY - ring.r + 14)
      .attr('text-anchor', 'middle')
      .attr('fill', ring.color).attr('font-size', 11).attr('font-weight', '700')
      .attr('letter-spacing', '0.1em').attr('opacity', 0.7)
      .text(ring.label);
  });

  bg.append('line').attr('x1', CX).attr('y1', CY - MAX_R - 8).attr('x2', CX).attr('y2', CY + MAX_R + 8)
    .attr('stroke', '#2d3148').attr('stroke-width', 1);
  bg.append('line').attr('x1', CX - MAX_R - 8).attr('y1', CY).attr('x2', CX + MAX_R + 8).attr('y2', CY)
    .attr('stroke', '#2d3148').attr('stroke-width', 1);

  const visible = allTechs.filter(t => activeCategories.has(t.category));

  const dotsG = svg.append('g').attr('class', 'dots');

  visible.forEach((tech) => {
    const pos = placeDot(tech, allTechs.indexOf(tech));
    const color = getCategoryColor(tech.category);
    const g = dotsG.append('g')
      .attr('transform', `translate(${pos.x},${pos.y})`)
      .attr('class', 'dot')
      .style('cursor', 'pointer');

    g.append('circle')
      .attr('r', 7)
      .attr('fill', color)
      .attr('fill-opacity', 0.85)
      .attr('stroke', '#0f1117')
      .attr('stroke-width', 1.5);

    if (tech.trajectory === 'rising') {
      g.append('text').attr('y', -10).attr('text-anchor', 'middle')
        .attr('font-size', 9).attr('fill', '#1D9E75').text('↑');
    } else if (tech.trajectory === 'declining') {
      g.append('text').attr('y', -10).attr('text-anchor', 'middle')
        .attr('font-size', 9).attr('fill', '#A32D2D').text('↓');
    }

    g.on('mouseenter', (event) => showTooltip(event, tech))
      .on('mousemove', (event) => moveTooltip(event))
      .on('mouseleave', hideTooltip)
      .on('click', () => {
        window.location.href = `table.html#${tech.id}`;
      });
  });

  return svg;
}

function showTooltip(event, tech) {
  const gh = tech.metrics?.github;
  const npm = tech.metrics?.npm;
  const traj = trajectoryLabel(tech.trajectory);

  tooltip.innerHTML = `
    <strong>${tech.name}</strong>
    <div class="metric-row"><span>Position</span><span class="badge badge-${tech.position}">${tech.position}</span></div>
    <div class="metric-row"><span>Trajectoire</span><span>${traj}</span></div>
    ${gh ? `<div class="metric-row"><span>Stars GitHub</span><span>${formatNumber(gh.stars)}</span></div>` : ''}
    ${npm ? `<div class="metric-row"><span>DL/semaine</span><span>${formatNumber(npm.downloads_weekly)}</span></div>` : ''}
    ${tech.notes ? `<div style="margin-top:6px;color:#8892a4;font-style:italic;font-size:11px">${tech.notes}</div>` : ''}
  `;
  tooltip.classList.add('visible');
  moveTooltip(event);
}

function moveTooltip(event) {
  const x = event.clientX + 14;
  const y = event.clientY - 10;
  const rect = tooltip.getBoundingClientRect();
  tooltip.style.left = `${Math.min(x, window.innerWidth - rect.width - 16)}px`;
  tooltip.style.top = `${Math.max(y, 8)}px`;
}

function hideTooltip() {
  tooltip.classList.remove('visible');
}

function buildCategoryFilters() {
  const container = document.getElementById('category-filters');
  CATEGORIES.forEach(cat => {
    const label = document.createElement('label');
    const cb = document.createElement('input');
    cb.type = 'checkbox';
    cb.checked = true;
    cb.value = cat;
    cb.addEventListener('change', () => {
      if (cb.checked) activeCategories.add(cat);
      else activeCategories.delete(cat);
      buildSvg();
    });
    const dot = document.createElement('span');
    dot.style.cssText = `display:inline-block;width:8px;height:8px;border-radius:50%;background:${getCategoryColor(cat)}`;
    label.appendChild(cb);
    label.appendChild(dot);
    label.appendChild(document.createTextNode(' ' + cat.replace('_', ' ')));
    container.appendChild(label);
  });
}

async function init() {
  tooltip = document.getElementById('tooltip');

  try {
    const data = await loadData();
    allTechs = data.technologies;
    document.getElementById('last-update').textContent =
      new Date(data.generated_at).toLocaleString('fr-FR');

    buildCategoryFilters();
    buildSvg();
  } catch (err) {
    document.getElementById('radar-container').innerHTML =
      `<div class="error">Erreur : ${err.message}</div>`;
  }
}

init();
