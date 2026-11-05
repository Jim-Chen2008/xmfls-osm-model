import * as THREE from 'three';
import { GLTFLoader } from 'three/examples/jsm/loaders/GLTFLoader.js';
import { GLTFExporter } from 'three/examples/jsm/exporters/GLTFExporter.js';
import { Emitter } from '../utils/emitter.js';
import {
  base64ToArrayBuffer,
  bakeWorldTransform,
  disposeObject,
  robustBounds,
  safeFilename,
  downloadBlob,
} from '../utils/helpers.js';
import DEFAULT_MODEL_B64 from '../assets/default-model.b64';

/**
 * 模型导入 / 导出。
 * 默认模型以 base64 内联在包里，因此双击 index.html（file://）也能直接打开场景。
 */
export class ModelIO extends Emitter {
  constructor({ viewer, history }) {
    super();
    this.viewer = viewer;
    this.history = history;
    this.loader = new GLTFLoader();
    this.exporter = new GLTFExporter();
    this.modelName = '未命名模型';
    this.modelFile = '';
    this.animations = [];
  }

  /* ============ 导入 ============ */
  async loadDefault() {
    this.emit('loading', '正在载入默认校园模型…');
    const buffer = base64ToArrayBuffer(DEFAULT_MODEL_B64);
    return this.loadArrayBuffer(buffer, {
      name: '厦门外国语学校（海沧校区）',
      file: '厦门外国语学校海沧校区-足球场原点.glb',
    });
  }

  async loadFile(file) {
    this.emit('loading', `正在解析 ${file.name}…`);
    const isGltf = /\.gltf$/i.test(file.name);
    const data = isGltf ? await file.text() : await file.arrayBuffer();
    return this.loadArrayBuffer(data, { name: file.name.replace(/\.(glb|gltf)$/i, ''), file: file.name });
  }

  loadArrayBuffer(data, { name = 'Model', file = '' } = {}) {
    return new Promise((resolve, reject) => {
      const onLoad = (gltf) => {
        try {
          const root = gltf.scene || gltf.scenes?.[0];
          if (!root) throw new Error('文件中没有可用的场景节点');

          let unnamed = 0;
          root.traverse((obj) => {
            if (!obj.name) obj.name = `${obj.isMesh ? 'mesh' : 'node'}_${unnamed++}`;
            if (obj.isMesh) {
              obj.castShadow = true;
              obj.receiveShadow = true;
              const mats = Array.isArray(obj.material) ? obj.material : [obj.material];
              for (const m of mats) {
                if (!m) continue;
                if (m.map) m.map.anisotropy = 4;
                m.needsUpdate = true;
              }
            }
          });
          root.name = name;

          // GIS / OSM 导出的模型常把世界坐标直接烘进顶点，节点自身位置是 (0,0,0)，
          // 这会让变换手柄永远停在场景原点上。这里把每个网格的几何中心归零，
          // 并等量补偿节点位移 —— 外观完全不变，但每个对象都有了可用的轴心。
          normalizePivots(root);

          // 清掉旧模型并释放显存
          for (const child of [...this.viewer.modelRoot.children]) {
            this.viewer.modelRoot.remove(child);
            disposeObject(child);
          }

          this.viewer.setModel(root);
          const { box, full } = robustBounds(root);
          this.viewer.applyBounds(box, full);

          this.modelName = name;
          this.modelFile = file;
          this.animations = gltf.animations || [];
          this.history.clear();

          this.emit('loaded', {
            root,
            box,
            full,
            name,
            file,
            animations: this.animations,
          });
          resolve({ root, box, full });
        } catch (err) {
          reject(err);
        }
      };

      const onError = (err) => {
        const message = err?.message || String(err);
        reject(new Error(/draco/i.test(message) ? '该模型使用了 Draco 压缩，需先用工具解压后再导入' : message));
      };

      try {
        this.loader.parse(data, '', onLoad, onError);
      } catch (err) {
        onError(err);
      }
    });
  }

  /* ============ 导出 ============ */
  async exportScene() {
    const root = this.viewer.modelRoot;
    const stamp = timestamp();
    const filename = `${safeFilename(this.modelName, 'scene')}-edited-${stamp}.glb`;
    await this._export(root, filename);
    return filename;
  }

  async exportObject(object) {
    if (!object) throw new Error('请先选中一个对象');
    const holder = new THREE.Group();
    holder.name = object.name || 'selection';
    holder.add(bakeWorldTransform(object));
    const filename = `${safeFilename(object.name || this.modelName, 'object')}-${timestamp()}.glb`;
    await this._export(holder, filename);
    return filename;
  }

  _export(input, filename) {
    return new Promise((resolve, reject) => {
      this.emit('exporting');
      this.exporter.parse(
        input,
        (result) => {
          try {
            const blob = new Blob([result], { type: 'model/gltf-binary' });
            downloadBlob(blob, filename);
            this.emit('exported', { filename, size: blob.size });
            resolve({ filename, size: blob.size });
          } catch (err) {
            reject(err);
          }
        },
        (err) => reject(err),
        {
          binary: true,
          onlyVisible: true,
          truncateDrawRange: true,
          maxTextureSize: 4096,
          includeCustomExtensions: false,
        }
      );
    });
  }
}

function timestamp() {
  const d = new Date();
  const p = (n) => String(n).padStart(2, '0');
  return `${d.getFullYear()}${p(d.getMonth() + 1)}${p(d.getDate())}-${p(d.getHours())}${p(d.getMinutes())}`;
}

/**
 * 把几何中心搬到对象原点，同时补偿节点位移（视觉零变化）。
 * 这样平移/旋转手柄就落在物体自身中心，而不是整个场景的原点。
 */
function normalizePivots(root) {
  // 统计几何体被引用次数：共享几何体需要先克隆，避免影响其他网格
  const usage = new Map();
  root.traverse((obj) => {
    if (!obj.isMesh || !obj.geometry) return;
    usage.set(obj.geometry, (usage.get(obj.geometry) || 0) + 1);
  });

  const center = new THREE.Vector3();
  const offset = new THREE.Vector3();

  root.traverse((obj) => {
    if (!obj.isMesh || !obj.geometry) return;
    let geo = obj.geometry;
    if (usage.get(geo) > 1) {
      geo = geo.clone();
      obj.geometry = geo;
      usage.set(geo, 1);
    }
    if (!geo.boundingBox) geo.computeBoundingBox();
    if (!geo.boundingBox) return;

    geo.boundingBox.getCenter(center);
    if (center.lengthSq() < 1e-8) return;

    geo.translate(-center.x, -center.y, -center.z);
    geo.computeBoundingBox();
    geo.computeBoundingSphere();

    // 局部矩阵 L = T·R·S，归零后需要 L' = L·T(C)，即位移补偿 R·S·C
    offset.copy(center).applyQuaternion(obj.quaternion).multiply(obj.scale);
    obj.position.add(offset);
    obj.updateMatrix();
  });

  root.updateMatrixWorld(true);
}

