#!/usr/bin/env node
/**
 * validate_output.js — PostToolUse hook
 * Fires after every Write tool call.
 * Validates papers.csv integrity and sends errors back to Claude.
 */
const fs = require('fs');

async function main() {
  // Read tool call data from stdin
  const chunks = [];
  for await (const chunk of process.stdin) chunks.push(chunk);
  const toolData = JSON.parse(Buffer.concat(chunks).toString());

  // Only act on writes to outputs/papers.csv
  const filePath = toolData.tool_input?.path || toolData.tool_input?.file_path || '';
  if (!filePath.includes('papers.csv')) process.exit(0);

  // Read file
  let content;
  try {
    content = fs.readFileSync('outputs/papers.csv', 'utf8');
  } catch (e) {
    console.error('VALIDATION ERROR: could not read outputs/papers.csv — ' + e.message);
    process.exit(2);
  }

  const lines = content.trim().split('\n');

  // Must have at least a header and one data row
  if (lines.length < 2) {
    console.error('VALIDATION ERROR: papers.csv is empty or has no data rows.');
    process.exit(2);
  }

  // Parse header — handle quoted fields
  const headers = parseCSVLine(lines[0]);

  // Required columns — includes score_reason added in updated filter.py
  const required = ['title', 'authors', 'year', 'doi', 'relevance_score', 'score_reason'];
  const missing  = required.filter(h => !headers.includes(h));
  if (missing.length > 0) {
    console.error(`VALIDATION ERROR: papers.csv is missing columns: ${missing.join(', ')}`);
    process.exit(2);
  }

  const titleIdx  = headers.indexOf('title');
  const reasonIdx = headers.indexOf('score_reason');
  const scoreIdx  = headers.indexOf('relevance_score');

  let emptyReasons  = 0;
  let invalidScores = 0;
  const seen  = new Set();
  const dupes = [];

  for (const line of lines.slice(1)) {
    if (!line.trim()) continue;
    const fields = parseCSVLine(line);

    // Check for duplicate titles (normalised first 60 chars)
    const title = (fields[titleIdx] || '').slice(0, 60).toLowerCase().replace(/\s+/g, ' ');
    if (title && seen.has(title)) {
      dupes.push(title);
    } else {
      seen.add(title);
    }

    // Check score_reason is not empty
    const reason = (fields[reasonIdx] || '').trim();
    if (!reason) emptyReasons++;

    // Check relevance_score is a valid number
    const score = parseFloat(fields[scoreIdx]);
    if (isNaN(score) || score < 0 || score > 10) invalidScores++;
  }

  const rowCount = lines.length - 1;
  const errors   = [];
  const warnings = [];

  if (invalidScores > 0)
    errors.push(`${invalidScores} rows have invalid relevance_score (must be 0–10)`);

  if (emptyReasons > 0)
    warnings.push(`${emptyReasons} rows have empty score_reason — filter.py may not have run correctly`);

  if (dupes.length > 5)
    warnings.push(`${dupes.length} duplicate titles detected — deduplication may have failed`);

  if (errors.length > 0) {
    for (const e of errors) console.error('VALIDATION ERROR: ' + e);
    process.exit(2);
  }

  for (const w of warnings) console.error('VALIDATION WARNING: ' + w);

  console.log(
    `Validation passed: ${rowCount} papers, ` +
    `all required columns present (including score_reason).`
  );
  process.exit(0);
}

/**
 * Minimal CSV line parser that handles double-quoted fields containing commas.
 * Not a full RFC 4180 implementation but handles the common cases filter.py produces.
 */
function parseCSVLine(line) {
  const fields = [];
  let current  = '';
  let inQuotes = false;

  for (let i = 0; i < line.length; i++) {
    const ch = line[i];
    if (ch === '"') {
      if (inQuotes && line[i + 1] === '"') {
        current += '"';
        i++;
      } else {
        inQuotes = !inQuotes;
      }
    } else if (ch === ',' && !inQuotes) {
      fields.push(current);
      current = '';
    } else {
      current += ch;
    }
  }
  fields.push(current);
  return fields;
}

main().catch(e => {
  console.error('Hook error:', e.message);
  process.exit(0);   // don't block Claude on hook crashes
});