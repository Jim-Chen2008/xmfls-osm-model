/** 轻量 toast 提示 */
const ICONS = {
  info: '<svg viewBox="0 0 24 24" width="13" height="13" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round"><circle cx="12" cy="12" r="9"/><path d="M12 11v6"/><path d="M12 7.6h.01"/></svg>',
  success: '<svg viewBox="0 0 24 24" width="13" height="13" fill="none" stroke="currentColor" stroke-width="1.9" stroke-linecap="round" stroke-linejoin="round"><path d="m5 12.5 4.5 4.5L19 7"/></svg>',
  error: '<svg viewBox="0 0 24 24" width="13" height="13" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round"><circle cx="12" cy="12" r="9"/><path d="M12 7.5v5.5"/><path d="M12 16.6h.01"/></svg>',
};

let container = null;

export function toast(message, type = 'info', duration = 2600) {
  if (!container) container = document.getElementById('toasts');
  if (!container) return;

  const el = document.createElement('div');
  el.className = `toast ${type}`;
  el.innerHTML = `<span style="display:grid;place-items:center;color:${type === 'error' ? 'var(--accent)' : 'var(--green)'}">${ICONS[type] || ICONS.info}</span><span></span>`;
  el.lastElementChild.textContent = message;
  container.appendChild(el);

  setTimeout(() => {
    el.classList.add('leaving');
    setTimeout(() => el.remove(), 220);
  }, duration);

  // 最多同时保留 4 条
  while (container.children.length > 4) container.firstElementChild.remove();
  return el;
}
