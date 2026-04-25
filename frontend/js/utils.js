// Shared utilities — Sensor-SmAArt-City

const TYPE_CONFIG = {
  air_quality:   { label: 'Air Quality',   color: '#0EA5E9' },
  soil:          { label: 'Soil',           color: '#D97706' },
  water:         { label: 'Water',          color: '#7C3AED' },
  weather:       { label: 'Weather',        color: '#6B7280' },
  parking:       { label: 'Parking',        color: '#1D4ED8' },
  environmental: { label: 'Environmental',  color: '#16A34A' },
  unknown:       { label: 'Unknown',        color: '#6B7280' },
};

const STATUS_CONFIG = {
  online:   { label: 'Online',   dot: '#10B981', cls: 'bg-emerald-50 text-emerald-700 ring-1 ring-emerald-200' },
  offline:  { label: 'Offline',  dot: '#EF4444', cls: 'bg-red-50 text-red-600 ring-1 ring-red-200' },
  warning:  { label: 'Warning',  dot: '#F59E0B', cls: 'bg-amber-50 text-amber-700 ring-1 ring-amber-200' },
  critical: { label: 'Critical', dot: '#EF4444', cls: 'bg-red-50 text-red-600 ring-1 ring-red-200' },
};

function typeLabel(t) { return (TYPE_CONFIG[t] || TYPE_CONFIG.unknown).label; }

function statusBadge(status) {
  const cfg = STATUS_CONFIG[status] || STATUS_CONFIG.offline;
  const pulse = status === 'online'
    ? `<span class="relative flex w-2 h-2"><span class="animate-ping absolute inline-flex h-full w-full rounded-full opacity-50" style="background:${cfg.dot}"></span><span class="relative rounded-full w-2 h-2" style="background:${cfg.dot}"></span></span>`
    : `<span class="w-2 h-2 rounded-full flex-shrink-0" style="background:${cfg.dot}"></span>`;
  return `<span class="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-medium ${cfg.cls}">${pulse}${cfg.label}</span>`;
}

function severityBadge(severity, display) {
  const map = { high: 'bg-red-50 text-red-600 ring-1 ring-red-200', medium: 'bg-amber-50 text-amber-700 ring-1 ring-amber-200', low: 'bg-blue-50 text-blue-600 ring-1 ring-blue-200' };
  return `<span class="px-2.5 py-1 rounded-full text-xs font-medium ${map[severity] || 'bg-gray-100 text-gray-600'}">${display}</span>`;
}

function batteryBar(pct) {
  if (pct === null || pct === undefined) return '<span class="text-xs text-gray-400">N/A</span>';
  const color = pct > 50 ? '#10B981' : pct > 20 ? '#F59E0B' : '#EF4444';
  const textColor = pct > 50 ? 'text-emerald-600' : pct > 20 ? 'text-amber-600' : 'text-red-500';
  return `<div class="flex items-center gap-2">
    <div class="flex-1 h-1.5 bg-gray-100 rounded-full overflow-hidden" style="min-width:72px">
      <div class="h-full rounded-full transition-all" style="width:${pct}%;background:${color}"></div>
    </div>
    <span class="text-xs font-semibold ${textColor} w-8 text-right">${pct}%</span>
  </div>`;
}

function renderSidebar(activePage) {
  const nav = [
    { id: 'dashboard', href: 'index.html',     label: 'Dashboard',
      icon: `<path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.75" d="M4 5a1 1 0 011-1h4a1 1 0 011 1v5a1 1 0 01-1 1H5a1 1 0 01-1-1V5zm10 0a1 1 0 011-1h4a1 1 0 011 1v2a1 1 0 01-1 1h-4a1 1 0 01-1-1V5zm0 8a1 1 0 011-1h4a1 1 0 011 1v5a1 1 0 01-1 1h-4a1 1 0 01-1-1v-5zM4 14a1 1 0 011-1h4a1 1 0 011 1v2a1 1 0 01-1 1H5a1 1 0 01-1-1v-2z"/>` },
    { id: 'sensors', href: 'sensors.html', label: 'Sensors',
      icon: `<path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.75" d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z"/><path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.75" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z"/>` },
    { id: 'locations', href: 'locations.html', label: 'Locations',
      icon: `<path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.75" d="M17.657 16.657L13.414 20.9a1.998 1.998 0 01-2.827 0l-4.244-4.243a8 8 0 1111.314 0z"/><path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.75" d="M15 11a3 3 0 11-6 0 3 3 0 016 0z"/>` },
    { id: 'alerts', href: 'alerts.html', label: 'Alerts', badge: true,
      icon: `<path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.75" d="M15 17h5l-1.405-1.405A2.032 2.032 0 0118 14.158V11a6.002 6.002 0 00-4-5.659V5a2 2 0 10-4 0v.341C7.67 6.165 6 8.388 6 11v3.159c0 .538-.214 1.055-.595 1.436L4 17h5m6 0v1a3 3 0 11-6 0v-1m6 0H9"/>` },
  ];

  const items = nav.map(n => {
    const active = n.id === activePage;
    const cls = active
      ? 'flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium bg-blue-600 text-white'
      : 'flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium text-gray-400 hover:bg-gray-800 hover:text-white transition-all duration-150';
    const badgeHtml = n.badge
      ? `<span class="ml-auto text-xs bg-red-500 text-white rounded-full min-w-[20px] h-5 px-1.5 items-center justify-center hidden font-medium" id="nav-alert-badge">0</span>`
      : '';
    return `<a href="${n.href}" class="${cls}">
      <svg class="w-4 h-4 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">${n.icon}</svg>
      <span>${n.label}</span>${badgeHtml}
    </a>`;
  }).join('');

  return `<aside class="w-56 bg-gray-900 flex flex-col flex-shrink-0 h-screen">
    <div class="px-4 py-5 flex items-center gap-3 border-b border-gray-800">
      <div class="w-8 h-8 rounded-lg flex items-center justify-center flex-shrink-0" style="background:linear-gradient(135deg,#3B82F6,#6366F1)">
        <svg class="w-4.5 h-4.5 text-white w-5 h-5" fill="none" stroke="white" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 10V3L4 14h7v7l9-11h-7z"/>
        </svg>
      </div>
      <div>
        <p class="text-sm font-semibold text-white leading-tight">SmAArt City</p>
        <p class="text-xs text-gray-500">IoT Control Center</p>
      </div>
    </div>
    <div class="px-3 pt-2 pb-1">
      <p class="text-xs font-semibold text-gray-600 uppercase tracking-wider px-3 py-2">Navigation</p>
    </div>
    <nav class="flex-1 px-3 space-y-0.5">${items}</nav>
    <div class="px-3 pb-4 border-t border-gray-800 pt-3">
      <div class="flex items-center gap-3 px-3 py-2.5 rounded-lg">
        <div class="w-7 h-7 rounded-full bg-gray-700 flex items-center justify-center flex-shrink-0">
          <svg class="w-3.5 h-3.5 text-gray-300" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z"/>
          </svg>
        </div>
        <div class="min-w-0">
          <p class="text-xs font-medium text-gray-300 truncate">Admin</p>
          <p class="text-xs text-gray-600 truncate">admin@smartcity</p>
        </div>
      </div>
    </div>
  </aside>`;
}

async function loadAlertBadge() {
  try {
    const data = await dbGetStats();
    const badge = document.getElementById('nav-alert-badge');
    if (badge && data.active_alerts > 0) {
      badge.textContent = data.active_alerts;
      badge.classList.remove('hidden');
      badge.classList.add('inline-flex');
    }
  } catch (_) {}
}
