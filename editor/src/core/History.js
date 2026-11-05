import { Emitter } from '../utils/emitter.js';

/**
 * 撤销 / 重做栈。
 * 每条命令形如 { label, undo(), redo() }，由调用方决定如何回滚。
 */
export class History extends Emitter {
  constructor(limit = 150) {
    super();
    this.limit = limit;
    this.stack = [];
    this.index = -1; // 指向最后一条已执行的命令
    this._suspended = false;
  }

  get canUndo() {
    return this.index >= 0;
  }

  get canRedo() {
    return this.index < this.stack.length - 1;
  }

  get undoLabel() {
    return this.canUndo ? this.stack[this.index].label : '';
  }

  get redoLabel() {
    return this.canRedo ? this.stack[this.index + 1].label : '';
  }

  /**
   * 合并式入栈：同一个 mergeKey 的连续操作（例如连点 ▲ 步进）在 1.2s 内只留一条记录，
   * 撤销时一次回到最初的数值，避免“按十下要撤十次”。
   */
  pushOrMerge(command, mergeKey = null) {
    if (!mergeKey || this._suspended) {
      this.push(command);
      return;
    }
    const top = this.stack[this.index];
    const now = performance.now();
    if (top && top.mergeKey === mergeKey && now - (top.time || 0) < 1200) {
      top.redo = command.redo;
      top.time = now;
      this.emit('change', this.state());
      return;
    }
    command.mergeKey = mergeKey;
    command.time = now;
    this.push(command);
  }

  push(command) {
    if (this._suspended || !command) return;
    // 丢弃 redo 分支
    this.stack.length = this.index + 1;
    this.stack.push(command);
    if (this.stack.length > this.limit) this.stack.shift();
    this.index = this.stack.length - 1;
    this.emit('change', this.state());
  }

  undo() {
    if (!this.canUndo) return null;
    const cmd = this.stack[this.index];
    this._suspended = true;
    try {
      cmd.undo();
    } finally {
      this._suspended = false;
    }
    this.index -= 1;
    this.emit('change', this.state());
    return cmd;
  }

  redo() {
    if (!this.canRedo) return null;
    const cmd = this.stack[this.index + 1];
    this._suspended = true;
    try {
      cmd.redo();
    } finally {
      this._suspended = false;
    }
    this.index += 1;
    this.emit('change', this.state());
    return cmd;
  }

  clear() {
    this.stack.length = 0;
    this.index = -1;
    this.emit('change', this.state());
  }

  state() {
    return {
      canUndo: this.canUndo,
      canRedo: this.canRedo,
      undoLabel: this.undoLabel,
      redoLabel: this.redoLabel,
      size: this.stack.length,
    };
  }
}

/** 生成对象变换快照 */
export function snapshotTransform(object) {
  return {
    position: object.position.clone(),
    quaternion: object.quaternion.clone(),
    scale: object.scale.clone(),
  };
}

/** 应用对象变换快照 */
export function applyTransform(object, snap) {
  object.position.copy(snap.position);
  object.quaternion.copy(snap.quaternion);
  object.scale.copy(snap.scale);
  object.updateMatrix();
  object.updateMatrixWorld(true);
}

/** 判断两份快照是否一致（用于过滤空操作） */
export function isSameTransform(a, b, eps = 1e-5) {
  return (
    a.position.distanceToSquared(b.position) < eps * eps &&
    Math.abs(a.quaternion.dot(b.quaternion)) > 1 - eps &&
    a.scale.distanceToSquared(b.scale) < eps * eps
  );
}
