/**
 * 打包脚本：把 src/ 下的 ES Module 源码打包成一个可直接用 <script> 引入的 IIFE 文件。
 *
 * 为什么要打包？
 *   浏览器在 file:// 协议下会拦截 ES Module 的跨文件 import（CORS 限制），
 *   打包成单文件后 index.html 双击即可运行，无需启动本地服务器。
 *
 * 用法：
 *   npm install
 *   npm run build     # 生成 dist/app.js + dist/style.css
 *   npm run watch     # 开发时监听变更
 */
import * as esbuild from 'esbuild';
import { rmSync, mkdirSync } from 'node:fs';
import { fileURLToPath } from 'node:url';
import { dirname, resolve } from 'node:path';

const root = dirname(fileURLToPath(import.meta.url));
const outdir = resolve(root, 'dist');
const watch = process.argv.includes('--watch');

rmSync(outdir, { recursive: true, force: true });
mkdirSync(outdir, { recursive: true });

/** @type {import('esbuild').BuildOptions} */
const options = {
  absWorkingDir: root,
  entryPoints: {
    app: 'src/main.js',
    style: 'src/styles.css',
  },
  outdir,
  bundle: true,
  format: 'iife',
  target: ['es2020'],
  minify: !watch,
  sourcemap: false,
  legalComments: 'none',
  charset: 'utf8',
  logLevel: 'info',
  // .b64 以纯文本方式内联（默认模型 base64），保证离线下也能加载默认场景
  loader: { '.b64': 'text' },
};

if (watch) {
  const ctx = await esbuild.context(options);
  await ctx.watch();
  console.log('[watch] 正在监听源码变更…');
} else {
  const t0 = Date.now();
  await esbuild.build(options);
  console.log(`[build] 完成，用时 ${Date.now() - t0} ms → dist/app.js, dist/style.css`);
}
