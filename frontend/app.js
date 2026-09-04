const question = document.querySelector('#question');
const resultPanel = document.querySelector('#result-panel');

function escapeHtml(value) {
  return String(value ?? '').replace(/[&<>'"]/g, (character) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', "'": '&#39;', '"': '&quot;' })[character]);
}

function renderResult(data, title = 'Analysis result') {
  const columns = data.columns || [];
  const rows = data.rows || [];
  const body = rows.map((row) => `<tr>${columns.map((column) => `<td>${escapeHtml(row[column])}</td>`).join('')}</tr>`).join('');
  resultPanel.innerHTML = `<div class="result-header"><div><p class="eyebrow">RESULTS</p><h3>${escapeHtml(title)}</h3></div><span class="safe-badge">✓ Read-only</span></div>
    <p class="rationale">${data.rationale ? escapeHtml(data.rationale) : `${rows.length} row(s) returned${data.truncated ? ' · result limit reached' : ''}.`}</p>
    ${data.tables ? `<div class="source-list">Sources: ${data.tables.map(escapeHtml).join(' · ')}</div>` : ''}
    <div class="table-wrap"><table class="result-table"><thead><tr>${columns.map((column) => `<th>${escapeHtml(column)}</th>`).join('')}</tr></thead><tbody>${body || '<tr><td>No rows returned</td></tr>'}</tbody></table></div>`;
}

function showError(message) {
  resultPanel.innerHTML = `<div class="error">${escapeHtml(message)}</div>`;
}

function renderSchema(data) {
  const tables = data.tables || [];
  const tableMarkup = tables.map((table) => {
    const columns = table.columns || [];
    const columnMarkup = columns.map((column) => `<li><strong>${escapeHtml(column.COLUMN_NAME)}</strong><span>${escapeHtml(column.COLUMN_TYPE || column.DATA_TYPE || '')}</span></li>`).join('');
    return `<details class="schema-table" open><summary><strong>${escapeHtml(table.name)}</strong><span>${columns.length} column(s)</span></summary><ul class="schema-columns">${columnMarkup || '<li>No column metadata available</li>'}</ul></details>`;
  }).join('');
  const relationshipMarkup = (data.relationships || []).map((relationship) => `<span>${escapeHtml(relationship.from_table)}.${escapeHtml(relationship.from_column)} → ${escapeHtml(relationship.to_table)}.${escapeHtml(relationship.to_column)}</span>`).join(' · ');
  resultPanel.innerHTML = `<div class="result-header"><div><p class="eyebrow">SCHEMA EXPLORER</p><h3>Relevant tables</h3></div><span class="safe-badge">✓ Read-only</span></div>
    <p class="rationale">${tables.length} table(s) matched your search. Expand a table to inspect its columns.</p>
    <div class="schema-list">${tableMarkup || '<div class="empty-state"><h3>No matching tables</h3><p>Try a table or column name in the question box.</p></div>'}</div>
    ${relationshipMarkup ? `<div class="source-list">Relationships: ${relationshipMarkup}</div>` : ''}`;
}

async function postJson(url, payload) {
  const response = await fetch(url, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(payload) });
  const data = await response.json();
  if (!response.ok) throw new Error(data.detail || 'Request failed');
  return data;
}

document.querySelector('#ask-button').addEventListener('click', async () => {
  const value = question.value.trim();
  if (!value) return question.focus();
  resultPanel.innerHTML = '<div class="empty-state"><div class="empty-orbit">…</div><h3>Thinking through the schema</h3><p>Retrieving relevant tables and generating a safe query.</p></div>';
  try { renderResult(await postJson('/api/v1/chat', { question: value }), value); } catch (error) { showError(error.message); }
});

document.querySelector('#run-button').addEventListener('click', async () => {
  const editor = document.querySelector('#sql');
  try { renderResult(await postJson('/api/v1/query', { sql: editor.value }), 'SQL query result'); } catch (error) { showError(error.message); }
});

document.querySelector('#schema-nav').addEventListener('click', async () => {
  const search = question.value.trim() || 'tables columns';
  resultPanel.innerHTML = '<div class="empty-state"><div class="empty-orbit">…</div><h3>Loading schema</h3><p>Finding tables and columns that match your search.</p></div>';
  try { renderSchema(await postJson('/api/v1/schema/search', { question: search, limit: 20 })); } catch (error) { showError(error.message); }
});

document.querySelectorAll('.quick-card').forEach((card) => card.addEventListener('click', () => { question.value = card.dataset.question; question.focus(); }));
document.querySelector('#new-chat').addEventListener('click', () => { question.value = ''; resultPanel.innerHTML = '<div class="empty-state"><div class="empty-orbit">✦</div><h3>Your analysis will appear here</h3><p>Results, generated SQL, and source tables will be shown in one place.</p></div>'; });
