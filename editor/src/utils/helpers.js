import * as THREE from 'three';

/* ============================================================
   通用工具函数
   ============================================================ */

const _size = new THREE.Vector3();
const _center = new THREE.Vector3();

/**
 * 计算模型的“有意义”包围盒。
 *
 * GIS/OSM 导出的模型常带一张 5000m 的底图，如果直接对全场景求包围盒，
 * 相机会被拉到很远的地方。这里用「中位尺寸 + 离群剔除」的办法过滤掉超大底图，
 * 让自动取景聚焦在建筑群上。
 *
 * @param {THREE.Object3D} root
 * @param {number} outlierRatio 超过中位对角线多少倍视为离群
 * @returns {{ box: THREE.Box3, full: THREE.Box3 }}
 */
export function robustBounds(root, outlierRatio = 8) {
  const entries = [];
  const full = new THREE.Box3();

  root.updateWorldMatrix(true, true);
  root.traverse((obj) => {
    if (!obj.isMesh || !obj.geometry || obj.userData.__ignoreBounds) return;
    const geo = obj.geometry;
    if (!geo.boundingBox) geo.computeBoundingBox();
    if (!geo.boundingBox) return;
    const box = geo.boundingBox.clone().applyMatrix4(obj.matrixWorld);
    if (!isFinite(box.min.x) || !isFinite(box.max.x)) return;
    entries.push({ box, diag: box.getSize(_size).length() });
    full.union(box);
  });

  if (!entries.length) {
    const fallback = new THREE.Box3(new THREE.Vector3(-10, 0, -10), new THREE.Vector3(10, 10, 10));
    return { box: fallback, full: fallback.clone() };
  }

  const sorted = entries.map((e) => e.diag).sort((a, b) => a - b);
  const median = sorted[Math.floor(sorted.length / 2)] || 1;
  const limit = Math.max(median * outlierRatio, median + 1e-3);

  const box = new THREE.Box3();
  let has = false;
  for (const e of entries) {
    if (e.diag > limit) continue;
    if (!has) {
      box.copy(e.box);
      has = true;
    } else {
      box.union(e.box);
    }
  }
  if (!has) box.copy(full);
  return { box, full };
}

/** 世界包围盒尺寸 */
export function boxSize(box) {
  return box.getSize(new THREE.Vector3());
}

/** 世界包围盒中心 */
export function boxCenter(box) {
  return box.getCenter(new THREE.Vector3());
}

/** 对象是否在场景层级中可见（逐级检查 visible） */
export function isEffectivelyVisible(obj) {
  let cur = obj;
  while (cur) {
    if (!cur.visible) return false;
    cur = cur.parent;
  }
  return true;
}

/** 统计对象树里的网格数、三角面数、材质集合 */
export function collectStats(root) {
  let meshes = 0;
  let triangles = 0;
  let vertices = 0;
  const materials = new Set();
  const geometries = new Set();

  root.traverse((obj) => {
    if (!obj.isMesh || !obj.geometry) return;
    meshes += 1;
    const geo = obj.geometry;
    const pos = geo.attributes.position;
    if (pos) vertices += pos.count;
    const index = geo.index;
    if (index) triangles += Math.floor(index.count / 3);
    else if (pos) triangles += Math.floor(pos.count / 3);
    const mats = Array.isArray(obj.material) ? obj.material : [obj.material];
    for (const m of mats) if (m) materials.add(m);
    geometries.add(geo);
  });

  return { meshes, triangles, vertices, materials: materials.size, geometries: geometries.size, materialSet: materials };
}

/** 释放对象树占用的 GPU 资源 */
export function disposeObject(root) {
  root.traverse((obj) => {
    if (obj.geometry) obj.geometry.dispose();
    const mats = Array.isArray(obj.material) ? obj.material : obj.material ? [obj.material] : [];
    for (const mat of mats) {
      for (const key of Object.keys(mat)) {
        const value = mat[key];
        if (value && value.isTexture) value.dispose();
      }
      mat.dispose();
    }
  });
}

/** 数字格式化：固定小数位，避免出现 "-0.000" */
export function fmt(value, digits = 3) {
  if (!Number.isFinite(value)) return '0';
  let v = value;
  if (Math.abs(v) < Math.pow(10, -digits) / 2) v = 0;
  return v.toFixed(digits);
}

/** 角度归一到 (-180, 180] */
export function normalizeDeg(deg) {
  let d = deg % 360;
  if (d > 180) d -= 360;
  if (d <= -180) d += 360;
  return d;
}

/** 文件名合法化（保留中文） */
export function safeFilename(name, fallback = 'model') {
  const cleaned = String(name || '')
    .replace(/[\\/:*?"<>|\r\n\t]+/g, '-')
    .replace(/\s+/g, ' ')
    .trim()
    .slice(0, 80);
  return cleaned || fallback;
}

/** 触发浏览器下载 */
export function downloadBlob(blob, filename) {
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = filename;
  a.rel = 'noopener';
  document.body.appendChild(a);
  a.click();
  a.remove();
  setTimeout(() => URL.revokeObjectURL(url), 4000);
}

/** 复制文本（带 file:// 环境下的降级方案） */
export async function copyText(text) {
  const value = String(text);

  // 某些环境（file:// 或未授权）里 clipboard 的 Promise 可能一直挂起，加超时兜底
  try {
    if (navigator.clipboard && window.isSecureContext) {
      const result = await Promise.race([
        navigator.clipboard.writeText(value).then(() => true),
        new Promise((resolve) => setTimeout(() => resolve(false), 800)),
      ]);
      if (result) return true;
    }
  } catch {
    /* 继续尝试降级方案 */
  }

  try {
    const ta = document.createElement('textarea');
    ta.value = value;
    ta.setAttribute('readonly', '');
    ta.style.cssText = 'position:fixed;left:-9999px;top:0;opacity:0';
    document.body.appendChild(ta);
    ta.select();
    ta.setSelectionRange(0, value.length);
    const ok = document.execCommand('copy');
    ta.remove();
    return ok;
  } catch {
    return false;
  }
}

/** base64 → ArrayBuffer */
export function base64ToArrayBuffer(b64) {
  const binary = atob(b64);
  const len = binary.length;
  const bytes = new Uint8Array(len);
  for (let i = 0; i < len; i += 1) bytes[i] = binary.charCodeAt(i);
  return bytes.buffer;
}

/** 把对象的世界变换写成矩阵（导出选中对象时使用） */
export function bakeWorldTransform(obj) {
  const clone = obj.clone(true);
  clone.position.set(0, 0, 0);
  clone.quaternion.identity();
  clone.scale.set(1, 1, 1);
  clone.applyMatrix4(obj.matrixWorld);
  return clone;
}

/** 让浏览器有机会刷新一帧 UI */
export function nextFrame() {
  return new Promise((resolve) => requestAnimationFrame(() => setTimeout(resolve, 0)));
}

/** 节流 */
export function throttle(fn, wait = 100) {
  let last = 0;
  let timer = null;
  let lastArgs = null;
  return (...args) => {
    lastArgs = args;
    const now = performance.now();
    const remain = wait - (now - last);
    if (remain <= 0) {
      last = now;
      fn(...args);
    } else if (!timer) {
      timer = setTimeout(() => {
        timer = null;
        last = performance.now();
        fn(...lastArgs);
      }, remain);
    }
  };
}

/** 缩放到可读字符串，如 12.3k / 1.2M */
export function compactNumber(n) {
  if (n >= 1e6) return `${(n / 1e6).toFixed(2)}M`;
  if (n >= 1e4) return `${(n / 1e3).toFixed(1)}k`;
  return String(Math.round(n));
}

export { _center as _tmpCenter };
