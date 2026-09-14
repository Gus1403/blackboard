#!/usr/bin/env node
// fig.mjs <template> [spec.json|-] [out.svg]   Render a Blackboard figure to SVG (same code the board runs). Prints lint warnings to stderr.
// fig.mjs --list                                Templates.
import { createRequire } from 'node:module'; import fs from 'node:fs'; import path from 'node:path';
const require = createRequire(import.meta.url);
const Fig = require(path.join(path.dirname(new URL(import.meta.url).pathname), '..', 'board', 'fig.js'));
const [tpl, specPath, out] = process.argv.slice(2);
if (!tpl || tpl === '--list') { console.log(Fig.templates.join('\n')); process.exit(0); }
const src = !specPath || specPath === '-' ? fs.readFileSync(0, 'utf8') : fs.readFileSync(specPath, 'utf8');
let spec; try { spec = JSON.parse(src); } catch (e) { console.error('spec is not valid JSON: ' + e.message); process.exit(2); }
const { svg, warnings } = Fig.render(tpl, spec);
if (out) fs.writeFileSync(out, svg); else process.stdout.write(svg + '\n');
for (const w of warnings) console.error('warn: ' + w);
if (out) console.error(`wrote ${out}`);
