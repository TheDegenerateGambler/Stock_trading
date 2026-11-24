"""html_styles.py — CSS and JS for the day trade report."""

CSS = """
* { box-sizing: border-box; margin: 0; padding: 0; }
body { font-family: 'Segoe UI', Arial, sans-serif; background: #0d1117; color: #e6edf3; font-size: 13px; }
a { color: #58a6ff; text-decoration: none; }
a:hover { text-decoration: underline; }

.header {
    background: #161b22; border-bottom: 1px solid #30363d;
    padding: 12px 20px; display: flex; align-items: center; gap: 16px;
    position: sticky; top: 0; z-index: 100;
}
.header h1 { font-size: 16px; color: #f0f6fc; font-weight: 700; }
.header .meta { color: #8b949e; font-size: 12px; }
.badge { padding: 2px 8px; border-radius: 4px; font-size: 11px; font-weight: 600; }
.badge.bull { background: #1a4731; color: #3fb950; border: 1px solid #3fb950; }
.badge.bear { background: #4d1a1a; color: #f85149; border: 1px solid #f85149; }
.badge.choppy { background: #2d2d0a; color: #e3b341; border: 1px solid #e3b341; }
.badge.unknown { background: #21262d; color: #8b949e; border: 1px solid #30363d; }

.av-budget { margin-left: auto; font-size: 11px; color: #8b949e; }
.av-budget span { color: #58a6ff; }

.layout { display: flex; gap: 0; height: calc(100vh - 50px); overflow: hidden; }

/* Left picks panel */
.picks-panel {
    flex: 1; overflow-y: auto; padding: 16px;
    background: #0d1117;
}
.picks-panel h2 { font-size: 14px; color: #8b949e; margin-bottom: 12px; font-weight: 400; }

.pick-card {
    background: #161b22; border: 1px solid #30363d;
    border-radius: 8px; padding: 14px; margin-bottom: 10px;
    transition: border-color 0.2s;
}
.pick-card:hover { border-color: #58a6ff; }
.pick-card.long  { border-left: 4px solid #3fb950; }
.pick-card.short { border-left: 4px solid #f85149; }

.pick-top { display: flex; align-items: center; gap: 10px; margin-bottom: 8px; }
.pick-rank { color: #8b949e; font-size: 12px; min-width: 20px; }
.pick-ticker { font-size: 18px; font-weight: 700; color: #f0f6fc; }
.pick-dir { font-size: 14px; font-weight: 700; padding: 2px 10px; border-radius: 4px; }
.pick-dir.long  { background: #1a4731; color: #3fb950; }
.pick-dir.short { background: #4d1a1a; color: #f85149; }

.pick-levels { display: flex; gap: 20px; margin-bottom: 8px; }
.pick-level { text-align: center; }
.pick-level .lbl { font-size: 10px; color: #8b949e; text-transform: uppercase; }
.pick-level .val { font-size: 14px; font-weight: 600; }
.pick-level .val.entry { color: #f0f6fc; }
.pick-level .val.stop  { color: #f85149; }
.pick-level .val.target { color: #3fb950; }
.pick-level .pct { font-size: 11px; color: #8b949e; }

.pick-signals { font-size: 11px; color: #8b949e; margin-bottom: 6px; }
.sig-bull { color: #3fb950; }
.sig-bear { color: #f85149; }

.sentiment-row { display: flex; align-items: center; gap: 8px; margin-bottom: 6px; }
.sent-label { font-size: 11px; font-weight: 600; }
.sent-label.Bullish, .sent-label.Somewhat-Bullish { color: #3fb950; }
.sent-label.Bearish, .sent-label.Somewhat-Bearish { color: #f85149; }
.sent-label.Neutral { color: #8b949e; }
.sent-bar-bg { flex: 1; height: 6px; background: #21262d; border-radius: 3px; max-width: 120px; }
.sent-bar { height: 6px; border-radius: 3px; }
.sent-bar.bull { background: #3fb950; }
.sent-bar.bear { background: #f85149; }
.sent-bar.neutral { background: #e3b341; }
.sent-articles { font-size: 10px; color: #8b949e; }

.pick-headline {
    font-size: 11px; color: #8b949e; font-style: italic;
    border-left: 2px solid #30363d; padding-left: 8px;
    margin-top: 4px; overflow: hidden;
    display: -webkit-box; -webkit-line-clamp: 2; -webkit-box-orient: vertical;
}

.opts { font-size: 11px; padding: 1px 6px; border-radius: 3px; }
.opts.bull { background: #1a4731; color: #3fb950; }
.opts.bear { background: #4d1a1a; color: #f85149; }
.opts.neutral { background: #21262d; color: #8b949e; }

.no-picks {
    text-align: center; padding: 40px; color: #8b949e;
    background: #161b22; border-radius: 8px; border: 1px dashed #30363d;
}

/* Right Walter Bloomberg sidebar */
.wb-panel {
    width: 340px; min-width: 300px; border-left: 1px solid #30363d;
    background: #161b22; overflow-y: auto; padding: 14px;
    display: flex; flex-direction: column;
}
.wb-panel h3 {
    font-size: 13px; color: #f0f6fc; margin-bottom: 4px;
    display: flex; align-items: center; gap: 6px;
}
.wb-panel .wb-subtitle { font-size: 11px; color: #8b949e; margin-bottom: 10px; }
.wb-item {
    padding: 7px 0; border-bottom: 1px solid #21262d;
    font-size: 12px; line-height: 1.4;
}
.wb-item:last-child { border-bottom: none; }
.wb-age { color: #8b949e; font-size: 10px; display: inline-block; min-width: 45px; }
.wb-empty { color: #8b949e; font-size: 12px; text-align: center; padding: 20px; }

.regime-bar {
    background: #21262d; border-radius: 6px; padding: 10px 14px;
    margin-bottom: 12px; font-size: 12px;
}
.regime-bar .guidance { color: #8b949e; margin-top: 4px; font-size: 11px; }

.disclaimer {
    background: #161b22; border-top: 1px solid #30363d;
    padding: 8px 20px; font-size: 11px; color: #8b949e; text-align: center;
}

.refresh-note { font-size: 11px; color: #8b949e; margin-left: auto; }
"""

JS = """
let _lastUpdated = null;

async function pollUpdates() {
    try {
        const r = await fetch('live_data.json?t=' + Date.now());
        if (!r.ok) return;
        const data = await r.json();
        if (data.updated === _lastUpdated) return;
        _lastUpdated = data.updated;
        location.reload();
    } catch(e) {}
}

async function pollWalter() {
    try {
        const r = await fetch('live_walter.json?t=' + Date.now());
        if (!r.ok) return;
        const data = await r.json();
        const panel = document.getElementById('wb-feed');
        if (!panel) return;
        if (!data.items || data.items.length === 0) {
            panel.innerHTML = '<div class="wb-empty">No headlines yet...</div>';
            return;
        }
        panel.innerHTML = data.items.map(item =>
            `<div class="wb-item">
               <span class="wb-age">${item.age}</span>
               <a href="${item.url}" target="_blank">${item.title}</a>
             </div>`
        ).join('');
        const sub = document.getElementById('wb-subtitle');
        if (sub) sub.textContent = 'Updated ' + (data.fetched_ago || 'recently');
    } catch(e) {}
}

// Poll picks every 60s, Walter Bloomberg every 30s
setInterval(pollUpdates, 60000);
setInterval(pollWalter,  30000);
"""