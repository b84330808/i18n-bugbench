// Hidden test for pdfkit-1828, written for i18n-bugbench (MIT).
//
// Bundles the built Node entry point (js/pdfkit.node.mjs) into a CommonJS file
// with esbuild, the way an application bundler would, and loads the bundle.
//
// Usage: node check_cjs_bundle.mjs <pdfkit checkout after `yarn build`>
import { execFileSync } from 'node:child_process';
import { mkdtempSync, rmSync, writeFileSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { join, resolve } from 'node:path';
import { pathToFileURL } from 'node:url';

const checkout = resolve(process.argv[2]);
const { build } = await import(pathToFileURL(join(checkout, '.bbtools/node_modules/esbuild/lib/main.js')).href);

const dir = mkdtempSync(join(tmpdir(), 'pdfkit-cjs-'));
try {
  const entry = join(dir, 'index.mjs');
  // esbuild doesn't resolve file:// URLs; an absolute path with forward slashes works everywhere.
  const entryPoint = join(checkout, 'js/pdfkit.node.mjs').replaceAll('\\', '/');
  writeFileSync(entry, `import PDFDocument from ${JSON.stringify(entryPoint)};\nconsole.log(typeof PDFDocument);\n`);
  const outfile = join(dir, 'dist', 'index.cjs');
  await build({
    entryPoints: [entry],
    bundle: true,
    platform: 'node',
    format: 'cjs',
    outfile,
    logLevel: 'error',
  });
  const out = execFileSync(process.execPath, [outfile], { encoding: 'utf8', stdio: ['ignore', 'pipe', 'pipe'] });
  if (out.trim() !== 'function') {
    console.error(`expected "function", got ${JSON.stringify(out)}`);
    process.exit(1);
  }
  console.log('ok');
} catch (err) {
  console.error(err.stderr?.toString() || err.message || err);
  process.exit(1);
} finally {
  rmSync(dir, { recursive: true, force: true });
}
