"""
Attendance Console – premium dark UI v2 (sidebar + glassmorphism + animations).
Imported by app/main.py as:  from app.ui import UI_HTML
"""

UI_HTML = """<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Attendance Console</title>
<meta name="description" content="Employee attendance tracking, analytics, and management console.">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800;900&family=JetBrains+Mono:wght@400;500&display=swap" rel="stylesheet">
<style>
:root {
  /* Backgrounds */
  --bg:    #04080f;
  --bg2:   #080f1c;
  --bg3:   #0c1526;
  --bg-sidebar: rgba(4,8,15,0.96);

  /* Glass */
  --glass:        rgba(255,255,255,0.027);
  --glass2:       rgba(255,255,255,0.055);
  --glass3:       rgba(255,255,255,0.085);
  --glass-border: rgba(255,255,255,0.075);
  --glass-border-h: rgba(99,102,241,0.4);

  /* Text */
  --ink:  #cdd6f4;
  --ink2: #e8eeff;
  --ink3: #f5f7ff;
  --mute:  #5c6b8a;
  --mute2: #7d90b3;
  --mute3: #9badd0;

  /* Brand */
  --acc:    #6366f1;
  --acc2:   #818cf8;
  --acc3:   #a5b4fc;
  --violet: #8b5cf6;
  --violet2:#a78bfa;
  --cyan:   #06b6d4;
  --cyan2:  #22d3ee;
  --pink:   #ec4899;

  /* Status */
  --ok:    #10b981;
  --ok2:   #34d399;
  --bad:   #f43f5e;
  --bad2:  #fb7185;
  --warn:  #f59e0b;
  --warn2: #fbbf24;

  /* Glows */
  --glow-acc:    rgba(99,102,241,0.45);
  --glow-violet: rgba(139,92,246,0.4);
  --glow-ok:     rgba(16,185,129,0.4);

  /* Layout */
  --sidebar-w: 240px;
  --r:    12px;
  --r-sm: 8px;
  --r-lg: 18px;

  /* Transitions */
  --ease: cubic-bezier(.4,0,.2,1);
}

*, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }
html { scroll-behavior: smooth; }

body {
  background: var(--bg);
  color: var(--ink);
  font: 13.5px/1.65 'Inter', system-ui, sans-serif;
  min-height: 100vh;
  overflow-x: hidden;
  -webkit-font-smoothing: antialiased;
  display: flex;
}

/* ── Mesh gradient background ── */
#bg-mesh {
  position: fixed; inset: 0; z-index: -3; pointer-events: none;
  background:
    radial-gradient(ellipse 1100px 700px at 10% 5%,  rgba(99,102,241,0.12) 0%, transparent 60%),
    radial-gradient(ellipse  800px 600px at 88% 90%, rgba(139,92,246,0.10) 0%, transparent 55%),
    radial-gradient(ellipse  700px 500px at 55% 35%, rgba(6,182,212,0.06) 0%, transparent 50%),
    radial-gradient(ellipse  500px 350px at 30% 75%, rgba(16,185,129,0.05) 0%, transparent 45%),
    var(--bg);
  animation: meshDrift 22s ease-in-out infinite alternate;
}
@keyframes meshDrift {
  0%   { transform: scale(1)    rotate(0deg); }
  50%  { transform: scale(1.05) rotate(.6deg); }
  100% { transform: scale(1)    rotate(0deg); }
}

/* Grid overlay */
#bg-grid {
  position: fixed; inset: 0; z-index: -2; pointer-events: none;
  background-image:
    linear-gradient(rgba(255,255,255,0.016) 1px, transparent 1px),
    linear-gradient(90deg, rgba(255,255,255,0.016) 1px, transparent 1px);
  background-size: 52px 52px;
  mask-image: radial-gradient(ellipse 85% 85% at 50% 50%, black 20%, transparent 100%);
}

/* ── Floating orbs ── */
#orbs { position: fixed; inset: 0; z-index: -1; pointer-events: none; overflow: hidden; }
.orb {
  position: absolute; border-radius: 50%;
  animation: orbFloat linear infinite;
  opacity: 0;
}
@keyframes orbFloat {
  0%   { transform: translateY(110vh) scale(0); opacity: 0; }
  8%   { opacity: 1; }
  92%  { opacity: 0.5; }
  100% { transform: translateY(-12vh) scale(1.3); opacity: 0; }
}

/* ══════════════════════════════════════════
   SIDEBAR
══════════════════════════════════════════ */
#sidebar {
  width: var(--sidebar-w);
  min-height: 100vh;
  background: var(--bg-sidebar);
  border-right: 1px solid var(--glass-border);
  backdrop-filter: blur(40px) saturate(180%);
  -webkit-backdrop-filter: blur(40px) saturate(180%);
  display: flex;
  flex-direction: column;
  position: fixed;
  left: 0; top: 0; bottom: 0;
  z-index: 300;
  overflow: hidden;
}

/* Sidebar accent line */
#sidebar::before {
  content: '';
  position: absolute; top: 0; left: 0; width: 1px; height: 100%;
  background: linear-gradient(180deg, transparent 0%, rgba(99,102,241,0.5) 40%, rgba(139,92,246,0.4) 70%, transparent 100%);
}

.sb-logo {
  display: flex; align-items: center; gap: 12px;
  padding: 22px 20px 18px;
  border-bottom: 1px solid var(--glass-border);
}
.sb-logo-mark {
  width: 38px; height: 38px; border-radius: 12px; flex-shrink: 0;
  background: linear-gradient(135deg, var(--acc) 0%, var(--violet) 100%);
  display: flex; align-items: center; justify-content: center; font-size: 19px;
  box-shadow: 0 0 0 1px rgba(255,255,255,0.12), 0 4px 24px var(--glow-acc);
  animation: markPulse 4s ease-in-out infinite;
}
@keyframes markPulse {
  0%,100% { box-shadow: 0 0 0 1px rgba(255,255,255,0.12), 0 4px 24px var(--glow-acc); }
  50%      { box-shadow: 0 0 0 1px rgba(255,255,255,0.2), 0 6px 36px rgba(99,102,241,0.65); }
}
.sb-logo-text h1 {
  font-size: 14px; font-weight: 800; color: var(--ink3);
  letter-spacing: -.5px; line-height: 1.2;
}
.sb-logo-text h1 span { color: var(--acc3); }
.sb-logo-text p { font-size: 10.5px; color: var(--mute2); font-weight: 400; margin-top: 1px; }

/* Clock */
#sb-clock {
  margin: 12px 16px 4px;
  background: var(--glass);
  border: 1px solid var(--glass-border);
  border-radius: var(--r-sm);
  padding: 9px 13px;
  display: flex; flex-direction: column; gap: 1px;
}
#sb-clock .clock-time {
  font: 700 19px/1 'JetBrains Mono', monospace;
  color: var(--ink2);
  letter-spacing: 1px;
}
#sb-clock .clock-date {
  font-size: 10.5px; color: var(--mute2); font-weight: 500;
  margin-top: 3px;
}

/* Live badge in sidebar */
.sb-live {
  display: inline-flex; align-items: center; gap: 5px;
  margin: 4px 16px 12px;
  padding: 4px 10px; border-radius: 99px;
  font-size: 10px; font-weight: 600; color: var(--ok2); letter-spacing: .6px;
  background: rgba(16,185,129,0.09);
  border: 1px solid rgba(16,185,129,0.22);
  align-self: flex-start;
}
.live-dot {
  width: 6px; height: 6px; border-radius: 50%;
  background: var(--ok); box-shadow: 0 0 8px var(--ok);
  animation: livePulse 2s ease-in-out infinite;
}
@keyframes livePulse { 0%,100%{opacity:1;transform:scale(1)} 50%{opacity:.5;transform:scale(.8)} }

/* Sidebar nav */
.sb-section-label {
  font-size: 10px; font-weight: 700; color: var(--mute);
  letter-spacing: 1.2px; text-transform: uppercase;
  padding: 10px 20px 4px;
}
.sb-nav { flex: 1; overflow-y: auto; padding: 4px 10px; }
.sb-nav::-webkit-scrollbar { width: 3px; }
.sb-nav::-webkit-scrollbar-thumb { background: rgba(255,255,255,0.08); border-radius: 99px; }

.sb-btn {
  display: flex; align-items: center; gap: 11px;
  width: 100%; padding: 10px 12px; border-radius: 10px;
  border: 0; background: none; cursor: pointer;
  color: var(--mute2); font: 500 13px 'Inter', inherit;
  transition: all .2s var(--ease);
  position: relative; overflow: hidden; text-align: left;
  margin-bottom: 2px;
}
.sb-btn .sb-icon {
  width: 30px; height: 30px; border-radius: 8px;
  display: flex; align-items: center; justify-content: center;
  font-size: 14px; flex-shrink: 0;
  background: var(--glass); border: 1px solid var(--glass-border);
  transition: all .2s var(--ease);
}
.sb-btn:hover { color: var(--ink2); background: var(--glass2); }
.sb-btn:hover .sb-icon { border-color: rgba(99,102,241,0.25); background: rgba(99,102,241,0.1); }
.sb-btn.on {
  color: var(--ink3);
  background: linear-gradient(135deg, rgba(99,102,241,0.22) 0%, rgba(139,92,246,0.14) 100%);
  box-shadow: inset 0 1px 0 rgba(255,255,255,0.07);
}
.sb-btn.on .sb-icon {
  background: linear-gradient(135deg, rgba(99,102,241,0.3), rgba(139,92,246,0.2));
  border-color: rgba(99,102,241,0.35);
  box-shadow: 0 2px 12px rgba(99,102,241,0.3);
}
.sb-btn.on::before {
  content: '';
  position: absolute; left: 0; top: 20%; bottom: 20%;
  width: 3px; border-radius: 0 3px 3px 0;
  background: linear-gradient(180deg, var(--acc), var(--violet));
  box-shadow: 2px 0 10px var(--glow-acc);
}

/* Sidebar footer */
.sb-footer {
  padding: 14px 14px;
  border-top: 1px solid var(--glass-border);
  display: flex; flex-direction: column; gap: 8px;
}
.sb-api-link {
  display: flex; align-items: center; justify-content: center; gap: 7px;
  padding: 9px 16px; border-radius: 10px;
  font-size: 12px; font-weight: 600; letter-spacing: .15px;
  color: var(--acc2); text-decoration: none;
  border: 1px solid rgba(99,102,241,0.28);
  background: rgba(99,102,241,0.07);
  transition: all .22s;
}
.sb-api-link:hover {
  background: rgba(99,102,241,0.16); border-color: rgba(99,102,241,0.5);
  box-shadow: 0 0 20px rgba(99,102,241,0.28);
  transform: translateY(-1px);
}

/* ══════════════════════════════════════════
   MAIN CONTENT
══════════════════════════════════════════ */
#content {
  margin-left: var(--sidebar-w);
  flex: 1;
  min-height: 100vh;
  display: flex; flex-direction: column;
}

/* Topbar */
#topbar {
  position: sticky; top: 0; z-index: 200;
  height: 58px;
  background: rgba(4,8,15,0.88);
  backdrop-filter: blur(32px) saturate(180%);
  -webkit-backdrop-filter: blur(32px) saturate(180%);
  border-bottom: 1px solid var(--glass-border);
  display: flex; align-items: center; gap: 16px;
  padding: 0 28px;
  box-shadow: 0 1px 0 rgba(255,255,255,0.04), 0 4px 32px rgba(0,0,0,0.4);
}
#topbar-title { font-size: 16px; font-weight: 800; color: var(--ink3); letter-spacing: -.5px; flex: 1; }
#topbar-sub   { font-size: 12px; color: var(--mute2); margin-top: 1px; font-weight: 400; }

/* ── KPI strip ── */
#kpi-strip {
  display: flex; gap: 14px;
  padding: 20px 28px 0;
  overflow-x: auto;
}
#kpi-strip::-webkit-scrollbar { height: 3px; }
#kpi-strip::-webkit-scrollbar-thumb { background: rgba(255,255,255,0.1); border-radius: 99px; }

.kpi {
  flex: 1; min-width: 130px;
  background: var(--glass);
  border: 1px solid var(--glass-border);
  border-radius: var(--r);
  padding: 14px 18px;
  position: relative; overflow: hidden;
  transition: border-color .25s, box-shadow .25s, transform .22s;
  cursor: default;
}
.kpi::after {
  content: ''; position: absolute; inset: 0;
  background: radial-gradient(circle at 80% 20%, var(--kpi-glow, rgba(99,102,241,0.12)) 0%, transparent 65%);
  pointer-events: none;
}
.kpi-bar {
  position: absolute; top: 0; left: 0; right: 0; height: 2px;
  background: linear-gradient(90deg, var(--kpi-c1, var(--acc)), var(--kpi-c2, var(--violet)));
}
.kpi:hover { border-color: var(--glass-border-h); transform: translateY(-2px); box-shadow: 0 8px 32px rgba(0,0,0,0.35); }
.kpi-val {
  font: 800 26px/1 'Inter', sans-serif;
  color: var(--ink3); letter-spacing: -1px;
  margin-bottom: 4px;
}
.kpi-label { font-size: 10.5px; font-weight: 600; color: var(--mute2); letter-spacing: .5px; text-transform: uppercase; }
.kpi-sub   { font-size: 10px; color: var(--mute); margin-top: 4px; }

/* ── Main area ── */
main {
  flex: 1;
  padding: 20px 28px 80px;
  max-width: 1180px;
  width: 100%;
}
section { display: none; }
section.on { display: block; animation: secIn .35s var(--ease); }
@keyframes secIn { from { opacity:0; transform: translateY(14px); } to { opacity:1; transform: translateY(0); } }

/* ── Section header ── */
.sec-head { margin-bottom: 22px; display: flex; align-items: flex-start; justify-content: space-between; gap: 12px; }
.sec-head-text h2 { font-size: 21px; font-weight: 800; color: var(--ink3); letter-spacing: -.6px; }
.sec-head-text p  { color: var(--mute2); font-size: 12.5px; margin-top: 4px; }

/* ── Cards ── */
.card {
  background: var(--glass);
  border: 1px solid var(--glass-border);
  border-radius: var(--r-lg);
  padding: 20px 22px;
  margin-bottom: 16px;
  backdrop-filter: blur(24px) saturate(160%);
  -webkit-backdrop-filter: blur(24px) saturate(160%);
  position: relative; overflow: hidden;
  transition: border-color .28s, box-shadow .28s, transform .22s;
}
.card::before {
  content: '';
  position: absolute; top: 0; left: 0; right: 0; height: 1px;
  background: linear-gradient(90deg, transparent 0%, rgba(255,255,255,0.1) 50%, transparent 100%);
}
.card:hover {
  border-color: var(--glass-border-h);
  box-shadow: 0 6px 40px rgba(0,0,0,0.38), 0 0 0 1px rgba(99,102,241,0.1);
}

/* Card grid */
.card-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 16px; margin-bottom: 16px; }
@media (max-width: 900px) { .card-grid { grid-template-columns: 1fr; } }

/* Card header */
.ch { display: flex; align-items: center; gap: 10px; margin-bottom: 16px; }
.ci {
  width: 32px; height: 32px; border-radius: 9px;
  display: flex; align-items: center; justify-content: center; font-size: 15px; flex-shrink: 0;
}
.ci-v { background: rgba(99,102,241,0.16); }
.ci-c { background: rgba(6,182,212,0.16); }
.ci-g { background: rgba(16,185,129,0.16); }
.ci-o { background: rgba(245,158,11,0.16); }
.ci-r { background: rgba(244,63,94,0.16); }
.ci-p { background: rgba(139,92,246,0.16); }
.ch-label { flex: 1; }
.ch-label h3 { font-size: 11px; font-weight: 700; color: var(--mute2); letter-spacing: .7px; text-transform: uppercase; }
.ch-label p  { font-size: 11px; color: var(--mute); margin-top: 1px; }

/* ── Form ── */
.row { display: flex; gap: 10px; flex-wrap: wrap; align-items: flex-end; margin-bottom: 14px; }
.col { display: flex; flex-direction: column; gap: 5px; }
label { display: flex; flex-direction: column; gap: 5px; font-size: 10.5px; font-weight: 600; color: var(--mute); letter-spacing: .4px; text-transform: uppercase; }
input, select {
  font: 13px 'Inter', inherit; color: var(--ink2);
  background: rgba(255,255,255,0.04);
  border: 1px solid rgba(255,255,255,0.08);
  border-radius: 9px; padding: 9px 12px; min-width: 130px;
  transition: border-color .2s, box-shadow .2s, background .2s;
  outline: none; -webkit-appearance: none; appearance: none;
}
input:hover, select:hover { border-color: rgba(255,255,255,0.15); }
input:focus, select:focus {
  border-color: var(--acc);
  background: rgba(99,102,241,0.07);
  box-shadow: 0 0 0 3px rgba(99,102,241,0.16);
}
input::placeholder { color: var(--mute); opacity: 1; }
select option { background: #0d1627; color: var(--ink); }

/* ── Buttons ── */
button.act {
  position: relative; overflow: hidden;
  background: linear-gradient(135deg, var(--acc) 0%, var(--violet) 100%);
  color: #fff; border: 0; border-radius: 9px;
  padding: 10px 20px; cursor: pointer;
  font: 600 13px 'Inter', inherit; letter-spacing: -.1px;
  box-shadow: 0 3px 18px rgba(99,102,241,0.38), inset 0 1px 0 rgba(255,255,255,0.15);
  transition: all .22s var(--ease);
  white-space: nowrap;
}
button.act:hover { transform: translateY(-2px); box-shadow: 0 8px 28px rgba(99,102,241,0.55), inset 0 1px 0 rgba(255,255,255,0.15); }
button.act:active { transform: translateY(0); }

button.ghost {
  position: relative; overflow: hidden;
  background: rgba(255,255,255,0.04); color: var(--acc2);
  border: 1px solid rgba(99,102,241,0.28);
  border-radius: 9px; padding: 9px 16px; cursor: pointer;
  font: 500 13px 'Inter', inherit;
  transition: all .22s; white-space: nowrap;
}
button.ghost:hover { background: rgba(99,102,241,0.12); border-color: var(--acc); box-shadow: 0 0 20px rgba(99,102,241,0.22); transform: translateY(-1px); }
button.ghost:disabled { opacity: .32; cursor: not-allowed; transform: none !important; }

button.danger {
  background: rgba(244,63,94,0.09); color: var(--bad2);
  border: 1px solid rgba(244,63,94,0.28);
  border-radius: 9px; padding: 9px 16px; cursor: pointer;
  font: 500 13px 'Inter', inherit;
  transition: all .22s;
}
button.danger:hover { background: rgba(244,63,94,0.18); border-color: var(--bad); }

/* Ripple */
.ripple {
  position: absolute; border-radius: 50%;
  background: rgba(255,255,255,0.22);
  transform: scale(0); pointer-events: none;
  animation: rippleAnim .55s linear;
}
@keyframes rippleAnim { to { transform: scale(5); opacity: 0; } }

/* ── Tables ── */
.scroll { overflow-x: auto; border-radius: 10px; }
.scroll::-webkit-scrollbar { height: 4px; }
.scroll::-webkit-scrollbar-thumb { background: rgba(255,255,255,0.1); border-radius: 99px; }
table { width: 100%; border-collapse: collapse; font-size: 12.5px; }
thead tr { background: rgba(255,255,255,0.02); }
th {
  text-align: left; padding: 10px 14px;
  color: var(--mute); font-weight: 700; font-size: 10.5px;
  letter-spacing: .7px; text-transform: uppercase;
  border-bottom: 1px solid var(--glass-border); white-space: nowrap;
}
td {
  text-align: left; padding: 11px 14px;
  border-bottom: 1px solid rgba(255,255,255,0.04); white-space: nowrap;
  transition: background .1s;
}
tr:last-child td { border-bottom: 0; }
tbody tr { transition: background .1s; }
tbody tr:hover td { background: rgba(99,102,241,0.06); }
tbody tr:hover td:first-child { box-shadow: inset 3px 0 0 var(--acc); }

/* ── Status pills ── */
.pill {
  display: inline-flex; align-items: center; gap: 4px;
  padding: 3px 9px; border-radius: 99px;
  font-size: 10.5px; font-weight: 700; letter-spacing: .25px;
}
.p-present { background: rgba(16,185,129,0.13);  color: #34d399; border: 1px solid rgba(16,185,129,0.28); }
.p-absent   { background: rgba(244,63,94,0.13);   color: #fb7185; border: 1px solid rgba(244,63,94,0.28); }
.p-wfh      { background: rgba(6,182,212,0.13);   color: #22d3ee; border: 1px solid rgba(6,182,212,0.28); }
.p-leave    { background: rgba(245,158,11,0.13);  color: #fcd34d; border: 1px solid rgba(245,158,11,0.28); }
.p-on_duty  { background: rgba(99,102,241,0.13);  color: #a5b4fc; border: 1px solid rgba(99,102,241,0.28); }
.p-dept     { background: rgba(139,92,246,0.11);  color: #c4b5fd; border: 1px solid rgba(139,92,246,0.26); }
.p-edits    { background: rgba(245,158,11,0.11);  color: #fcd34d; border: 1px solid rgba(245,158,11,0.22); }

/* ── Stat grid ── */
.stats { display: grid; grid-template-columns: repeat(auto-fit, minmax(140px, 1fr)); gap: 12px; margin-top: 2px; }
.stat {
  background: rgba(255,255,255,0.025);
  border: 1px solid rgba(255,255,255,0.06);
  border-radius: var(--r); padding: 16px 18px;
  position: relative; overflow: hidden;
  transition: transform .22s, border-color .22s, box-shadow .22s;
  cursor: default;
}
.stat::before {
  content: ''; position: absolute; top: 0; left: 0; right: 0; height: 2px;
  background: linear-gradient(90deg, var(--acc), var(--violet));
}
.stat:hover { transform: translateY(-3px); border-color: rgba(99,102,241,0.3); box-shadow: 0 8px 28px rgba(0,0,0,0.3); }
.stat b { display: block; font-size: 28px; font-weight: 800; letter-spacing: -1.5px; color: var(--ink3); line-height: 1.1; }
.stat span { color: var(--mute2); font-size: 10.5px; font-weight: 600; letter-spacing: .5px; text-transform: uppercase; margin-top: 5px; display: block; }

/* ── Toast notifications ── */
#toast-container {
  position: fixed; bottom: 24px; right: 24px; z-index: 9999;
  display: flex; flex-direction: column; gap: 10px; pointer-events: none;
}
.toast {
  display: flex; align-items: center; gap: 10px;
  padding: 13px 18px; border-radius: var(--r); min-width: 260px; max-width: 400px;
  backdrop-filter: blur(28px) saturate(180%);
  -webkit-backdrop-filter: blur(28px) saturate(180%);
  box-shadow: 0 8px 40px rgba(0,0,0,0.45), 0 1px 0 rgba(255,255,255,0.05);
  font-size: 13px; font-weight: 500;
  pointer-events: all;
  animation: toastIn .35s var(--ease);
  transition: opacity .3s, transform .3s;
}
.toast.hiding { opacity: 0; transform: translateX(16px); }
.toast.ok  { background: rgba(10,32,26,0.92); color: var(--ok2);  border: 1px solid rgba(16,185,129,0.28); }
.toast.err { background: rgba(35,10,15,0.92); color: var(--bad2); border: 1px solid rgba(244,63,94,0.28); }
.toast.warn{ background: rgba(30,22,8,0.92);  color: var(--warn2);border: 1px solid rgba(245,158,11,0.28); }
.toast-icon { font-size: 18px; flex-shrink: 0; }
.toast-body { flex: 1; }
.toast-close { cursor: pointer; opacity: .5; font-size: 16px; flex-shrink: 0; }
.toast-close:hover { opacity: 1; }
@keyframes toastIn { from { opacity:0; transform: translateX(20px); } to { opacity:1; transform: translateX(0); } }

/* Inline msg (used in some cards) */
.msg {
  margin: 8px 0; padding: 10px 15px; border-radius: 9px;
  font-size: 12.5px; font-weight: 500; display: flex; align-items: center; gap: 9px;
  animation: msgIn .28s ease;
}
@keyframes msgIn { from { opacity:0; transform: translateY(-5px); } to { opacity:1; transform: translateY(0); } }
.msg.ok  { background: rgba(16,185,129,0.09); color: var(--ok2); border: 1px solid rgba(16,185,129,0.22); }
.msg.err { background: rgba(244,63,94,0.09);  color: var(--bad2);  border: 1px solid rgba(244,63,94,0.22); }
.msg-icon { font-size: 17px; line-height: 1; }

/* ── Empty state ── */
.empty { color: var(--mute); padding: 52px 0; text-align: center; }
.ei { font-size: 40px; margin-bottom: 14px; opacity: .3; display: block; animation: floatEmoji 3s ease-in-out infinite; }
@keyframes floatEmoji { 0%,100%{transform:translateY(0)} 50%{transform:translateY(-6px)} }
.empty p { font-size: 12.5px; color: var(--mute2); }
.empty small { font-size: 11px; color: var(--mute); display: block; margin-top: 4px; }

/* ── Pager ── */
.pager { display: flex; align-items: center; justify-content: center; gap: 12px; margin-top: 14px; }
.pager span { color: var(--mute2); font-size: 12px; font-weight: 500; }

/* ── Rank medals ── */
.r1 { color: #fbbf24; font-weight: 800; font-size: 13px; }
.r2 { color: #a1a1aa; font-weight: 700; font-size: 13px; }
.r3 { color: #cd7c3a; font-weight: 700; font-size: 13px; }

/* ── Skeleton ── */
.sk {
  height: 13px; border-radius: 6px; margin: 9px 0;
  background: linear-gradient(90deg,
    rgba(255,255,255,0.035) 25%,
    rgba(255,255,255,0.08) 50%,
    rgba(255,255,255,0.035) 75%);
  background-size: 200% 100%;
  animation: shimmer 1.5s infinite;
}
@keyframes shimmer { 0%{background-position:200% 0} 100%{background-position:-200% 0} }

/* ── Chart ── */
svg text { fill: var(--mute); font-size: 9.5px; font-family: Inter, sans-serif; }
.chart-legend {
  display: flex; flex-wrap: wrap; gap: 16px; margin-top: 12px;
  font-size: 11.5px; color: var(--mute2); align-items: center;
}
.chart-legend span { display: flex; align-items: center; gap: 6px; font-weight: 500; }

/* ── Progress bar ── */
.prog-bar {
  height: 5px; border-radius: 99px; background: rgba(255,255,255,0.06);
  overflow: hidden; margin-top: 6px;
}
.prog-fill {
  height: 100%; border-radius: 99px;
  background: linear-gradient(90deg, var(--acc), var(--violet));
  transition: width 1s var(--ease);
}

/* ── Divider ── */
.divider { height: 1px; background: var(--glass-border); margin: 16px 0; }

/* ── Scrollbar (global) ── */
::-webkit-scrollbar { width: 5px; height: 5px; }
::-webkit-scrollbar-track { background: rgba(255,255,255,0.02); }
::-webkit-scrollbar-thumb { background: rgba(255,255,255,0.1); border-radius: 99px; }
::-webkit-scrollbar-thumb:hover { background: rgba(255,255,255,0.18); }

/* ── Responsive: hide sidebar on small screens ── */
@media (max-width: 720px) {
  #sidebar { transform: translateX(-100%); transition: transform .3s var(--ease); }
  #sidebar.open { transform: translateX(0); }
  #content { margin-left: 0; }
  .card-grid { grid-template-columns: 1fr; }
  #kpi-strip { padding: 14px 16px 0; }
  main { padding: 16px 16px 80px; }
}
</style>
</head>
<body>

<!-- Backgrounds -->
<div id="bg-mesh"></div>
<div id="bg-grid"></div>
<div id="orbs"></div>

<!-- ═══════════════════════════════════
     SIDEBAR
═══════════════════════════════════ -->
<aside id="sidebar">
  <div class="sb-logo">
    <div class="sb-logo-mark">📋</div>
    <div class="sb-logo-text">
      <h1>Attendance <span>Console</span></h1>
      <p>Employee Analytics</p>
    </div>
  </div>

  <div id="sb-clock">
    <div class="clock-time" id="clock-time">--:--:--</div>
    <div class="clock-date" id="clock-date">Loading...</div>
  </div>

  <div class="sb-live"><div class="live-dot"></div>SYSTEM LIVE</div>

  <div class="sb-nav" id="sb-nav">
    <div class="sb-section-label">Main</div>
  </div>

  <div class="sb-footer">
    <a class="sb-api-link" href="/docs" target="_blank">⚡ Swagger API Docs</a>
  </div>
</aside>

<!-- ═══════════════════════════════════
     CONTENT
═══════════════════════════════════ -->
<div id="content">

  <!-- Top bar -->
  <div id="topbar">
    <div style="flex:1">
      <div id="topbar-title">Analytics Dashboard</div>
      <div id="topbar-sub">Department summaries, leaderboard and attendance trends</div>
    </div>
    <div style="display:flex;align-items:center;gap:10px">
      <div id="topbar-kpi-today" style="font-size:12px;color:var(--mute2);text-align:right"></div>
    </div>
  </div>

  <!-- KPI strip (analytics only) -->
  <div id="kpi-strip" style="display:none"></div>

  <main id="main-area">

  <!-- ─────────── ANALYTICS ─────────── -->
  <section id="analytics">
    <div class="sec-head">
      <div class="sec-head-text">
        <h2>📊 Analytics Dashboard</h2>
        <p>Department summaries, late leaderboard, employee stats and attendance trends.</p>
      </div>
    </div>

    <div class="card">
      <div class="ch"><div class="ci ci-v">🗓</div><div class="ch-label"><h3>Filter Controls</h3><p>Select month and department</p></div></div>
      <div class="row">
        <label>Month<input id="a_month" type="month"></label>
        <label>Department<input id="a_dept" placeholder="all departments"></label>
        <button class="act" onclick="loadAnalytics()">Load Analytics</button>
      </div>
    </div>

    <div class="card-grid">
      <div class="card" style="margin-bottom:0">
        <div class="ch"><div class="ci ci-c">🏢</div><div class="ch-label"><h3>Department Summary</h3></div></div>
        <div class="scroll" id="a_sum">
          <div class="empty"><span class="ei">🏢</span><p>Select a month and click Load Analytics.</p></div>
        </div>
      </div>
      <div class="card" style="margin-bottom:0">
        <div class="ch"><div class="ci ci-r">🏆</div><div class="ch-label"><h3>Late Leaderboard</h3></div></div>
        <div class="row">
          <label>Top N<input id="a_limit" type="number" min="1" max="50" value="10" style="min-width:72px"></label>
        </div>
        <div class="scroll" id="a_lb">
          <div class="empty"><span class="ei">🏆</span><p>Load analytics to see the leaderboard.</p></div>
        </div>
      </div>
    </div>

    <div class="card" style="margin-top:16px">
      <div class="ch"><div class="ci ci-g">👤</div><div class="ch-label"><h3>Employee Monthly Stats</h3></div></div>
      <div class="row">
        <label>Employee Code<input id="a_emp" placeholder="EMP0001"></label>
        <button class="ghost" onclick="loadEmp()">Show Stats</button>
      </div>
      <div id="a_emp_out"></div>
    </div>

    <div class="card">
      <div class="ch"><div class="ci ci-p">📈</div><div class="ch-label"><h3>Department Attendance Trend</h3><p>Daily attendance rate with 7-day moving average</p></div></div>
      <div class="row">
        <label>Department<input id="t_dept" placeholder="Engineering"></label>
        <label>From<input id="t_from" type="date"></label>
        <label>To<input id="t_to" type="date"></label>
        <button class="ghost" onclick="loadTrend()">Plot Trend</button>
      </div>
      <div id="t_out">
        <div class="empty"><span class="ei">📈</span><p>Enter a department and date range to visualize the trend.</p></div>
      </div>
    </div>
  </section>

  <!-- ─────────── ATTENDANCE ─────────── -->
  <section id="attendance">
    <div class="sec-head">
      <div class="sec-head-text">
        <h2>⏱ Attendance</h2>
        <p>Punch in/out, view attendance records and apply corrections.</p>
      </div>
    </div>

    <div class="card">
      <div class="ch"><div class="ci ci-g">✅</div><div class="ch-label"><h3>Punch In / Out</h3><p>Record employee attendance for today or a specific time</p></div></div>
      <div class="row">
        <label>Employee Code<input id="p_emp" placeholder="EMP0001"></label>
        <label>Status<select id="p_status"><option>PRESENT</option><option>WFH</option><option>ON_DUTY</option></select></label>
        <label>Time (blank = now)<input id="p_time" type="datetime-local" step="1"></label>
        <button class="act" id="btn-punch-in" onclick="punch('in')">Punch In</button>
        <button class="ghost" id="btn-punch-out" onclick="punch('out')">Punch Out</button>
      </div>
      <div id="p_msg"></div>
    </div>

    <div class="card">
      <div class="ch"><div class="ci ci-c">📋</div><div class="ch-label"><h3>Attendance Records</h3><p>Search and filter all attendance logs</p></div></div>
      <div class="row">
        <label>Employee<input id="l_emp" placeholder="any"></label>
        <label>From<input id="l_from" type="date"></label>
        <label>To<input id="l_to" type="date"></label>
        <label>Status
          <select id="l_status">
            <option value="">any</option><option>PRESENT</option><option>WFH</option>
            <option>ON_DUTY</option><option>ABSENT</option><option>LEAVE</option>
          </select>
        </label>
        <button class="act" onclick="loadLogs(1)">Search</button>
      </div>
      <div id="l_msg"></div>
      <div class="scroll" id="l_out"></div>
      <div class="pager" id="l_pg"></div>
    </div>

    <div class="card">
      <div class="ch"><div class="ci ci-o">✏️</div><div class="ch-label"><h3>Correct a Record</h3><p>Regularize and fix attendance discrepancies</p></div></div>
      <div class="row">
        <label>Employee<input id="r_emp"></label>
        <label>Date<input id="r_date" type="date"></label>
        <label>Status
          <select id="r_status">
            <option value="">unchanged</option><option>PRESENT</option><option>WFH</option>
            <option>ON_DUTY</option><option>ABSENT</option><option>LEAVE</option>
          </select>
        </label>
        <label>Punch In<input id="r_in" type="datetime-local" step="1"></label>
        <label>Punch Out<input id="r_out" type="datetime-local" step="1"></label>
      </div>
      <div class="row">
        <label>Reason<input id="r_reason" style="min-width:280px" placeholder="Minimum 5 characters"></label>
        <label>Authorized By<input id="r_by" value="hr.admin"></label>
        <button class="act" onclick="regularize()">Apply Correction</button>
      </div>
      <div id="r_msg"></div>
    </div>
  </section>

  <!-- ─────────── EMPLOYEES ─────────── -->
  <section id="employees">
    <div class="sec-head">
      <div class="sec-head-text">
        <h2>👥 Employees</h2>
        <p>Manage employee records and onboard new team members.</p>
      </div>
    </div>

    <div class="card">
      <div class="ch"><div class="ci ci-g">➕</div><div class="ch-label"><h3>New Employee</h3><p>Register a new team member</p></div></div>
      <div class="row">
        <label>Code<input id="e_code" placeholder="EMP0042"></label>
        <label>Full Name<input id="e_name"></label>
        <label>Email<input id="e_email" type="email"></label>
        <label>Department<input id="e_dept"></label>
        <label>Shift Start<input id="e_ss" value="09:30" style="min-width:90px"></label>
        <label>Shift End<input id="e_se" value="18:30" style="min-width:90px"></label>
        <label>Joined On<input id="e_join" type="date"></label>
        <button class="act" onclick="addEmp()">Create Employee</button>
      </div>
      <div id="e_msg"></div>
    </div>

    <div class="card">
      <div class="ch"><div class="ci ci-c">🔍</div><div class="ch-label"><h3>Employee Directory</h3><p>Browse and filter all employees</p></div></div>
      <div class="row">
        <label>Filter by Department<input id="f_dept" placeholder="all departments"></label>
        <button class="act" onclick="loadEmps(1)">Filter</button>
      </div>
      <div class="scroll" id="f_out"></div>
      <div class="pager" id="f_pg"></div>
    </div>
  </section>

  </main>
</div><!-- /content -->

<!-- Toast container -->
<div id="toast-container"></div>

<script>
// ── Floating orbs ──────────────────────────────────────────
(function () {
  const c = document.getElementById('orbs');
  const cols = ['rgba(99,102,241,0.6)','rgba(139,92,246,0.55)','rgba(6,182,212,0.5)','rgba(255,255,255,0.3)','rgba(16,185,129,0.45)'];
  for (let i = 0; i < 36; i++) {
    const d = document.createElement('div');
    d.className = 'orb';
    const sz = Math.random() * 5 + 1;
    d.style.cssText = `width:${sz}px;height:${sz}px;left:${Math.random()*100}%;` +
      `background:${cols[Math.floor(Math.random()*cols.length)]};border-radius:50%;filter:blur(${Math.random()*1}px);` +
      `animation-duration:${10+Math.random()*18}s;animation-delay:${Math.random()*16}s`;
    c.appendChild(d);
  }
})();

// ── Ripple effect ──────────────────────────────────────────
document.addEventListener('click', e => {
  const btn = e.target.closest('button.act, button.ghost');
  if (!btn) return;
  const r = document.createElement('span');
  r.className = 'ripple';
  const rect = btn.getBoundingClientRect();
  const sz = Math.max(rect.width, rect.height);
  r.style.width = r.style.height = sz + 'px';
  r.style.top  = (e.clientY - rect.top  - sz / 2) + 'px';
  r.style.left = (e.clientX - rect.left - sz / 2) + 'px';
  btn.appendChild(r);
  setTimeout(() => r.remove(), 600);
});

// ── Live IST clock ─────────────────────────────────────────
(function tickClock() {
  const IST_MS = 5.5 * 3600000;
  const now = new Date(Date.now() + IST_MS - new Date().getTimezoneOffset() * 60000);
  const pad = n => String(n).padStart(2, '0');
  document.getElementById('clock-time').textContent =
    `${pad(now.getUTCHours())}:${pad(now.getUTCMinutes())}:${pad(now.getUTCSeconds())}`;
  document.getElementById('clock-date').textContent =
    now.toUTCString().slice(0, 16);
  setTimeout(tickClock, 1000);
})();

// ── Core helpers ───────────────────────────────────────────
const $ = id => document.getElementById(id);
const IST = 330 * 60000;
const fmt = ms => ms == null ? '—' : new Date(ms + IST).toISOString().slice(0,19).replace('T',' ');
const toMs = v => v ? Date.parse(v + (v.length === 16 ? ':00' : '') + '+05:30') : undefined;
const esc = s => String(s ?? '').replace(/[&<>"]/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c]));
const qs = o => Object.entries(o).filter(([,v]) => v !== '' && v != null).map(([k,v]) => k+'='+encodeURIComponent(v)).join('&');

async function api(path, opt) {
  const r = await fetch(path, opt);
  let b = null;
  try { b = await r.json(); } catch (e) {}
  if (!r.ok) {
    const d = b && b.detail;
    throw new Error(Array.isArray(d) ? d.map(x => (x.loc||[]).slice(1).join('.')+' '+x.msg).join('; ') : (d || r.statusText));
  }
  return b;
}
const send = (m, body) => ({ method: m, headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(body) });

// ── Toast notifications ────────────────────────────────────
function toast(msg, type = 'ok') {
  const icons = { ok: '✓', err: '✕', warn: '⚠' };
  const t = document.createElement('div');
  t.className = `toast ${type}`;
  t.innerHTML = `<span class="toast-icon">${icons[type]||'ℹ'}</span><span class="toast-body">${esc(msg)}</span><span class="toast-close" onclick="dismissToast(this.parentNode)">✕</span>`;
  $('toast-container').appendChild(t);
  setTimeout(() => dismissToast(t), 4500);
}
function dismissToast(el) {
  if (!el || el._gone) return;
  el._gone = true;
  el.classList.add('hiding');
  setTimeout(() => el.remove(), 320);
}

// ── Inline message (for forms) ─────────────────────────────
function say(id, text, ok) {
  $(id).innerHTML = text ? `<div class="msg ${ok?'ok':'err'}"><span class="msg-icon">${ok?'✓':'✕'}</span>${esc(text)}</div>` : '';
}

// ── Status pills ───────────────────────────────────────────
const STATUS_ICONS = { PRESENT:'🟢', ABSENT:'🔴', WFH:'🏠', LEAVE:'🌴', ON_DUTY:'🔵' };
function pill(s) {
  const cls = { PRESENT:'p-present', ABSENT:'p-absent', WFH:'p-wfh', LEAVE:'p-leave', ON_DUTY:'p-on_duty' };
  return `<span class="pill ${cls[s]||''}">${STATUS_ICONS[s]||''} ${esc(s)}</span>`;
}

// ── Animated counter ───────────────────────────────────────
function countUp(el, target) {
  if (isNaN(+target)) { el.textContent = target; return; }
  const end = +target, steps = 26, dur = 700;
  let step = 0;
  const id = setInterval(() => {
    step++;
    el.textContent = step >= steps ? target : Math.round(end * step / steps);
    if (step >= steps) clearInterval(id);
  }, dur / steps);
}

// ── Skeleton ───────────────────────────────────────────────
function sk(id) {
  $(id).innerHTML = '<div class="sk" style="width:78%"></div><div class="sk" style="width:52%"></div><div class="sk" style="width:65%"></div><div class="sk" style="width:82%"></div>';
}

// ── Table builder ──────────────────────────────────────────
function table(cols, rows) {
  if (!rows.length) return '<div class="empty"><span class="ei">📭</span><p>No records found.</p><small>Try adjusting your filters.</small></div>';
  const head = cols.map(c => `<th>${esc(c[0])}</th>`).join('');
  const body = rows.map(r => `<tr>${cols.map(c => `<td>${c[1](r)}</td>`).join('')}</tr>`).join('');
  return `<table><thead><tr>${head}</tr></thead><tbody>${body}</tbody></table>`;
}

// ── Pager ──────────────────────────────────────────────────
function pager(id, page, size, total, fn) {
  const last = Math.max(1, Math.ceil(total / size));
  $(id).innerHTML = `<button class="ghost" ${page<=1?'disabled':''} onclick="${fn}(${page-1})">← Prev</button>`
    + `<span>Page ${page} / ${last} &nbsp;·&nbsp; ${total} rows</span>`
    + `<button class="ghost" ${page>=last?'disabled':''} onclick="${fn}(${page+1})">Next →</button>`;
}

// ── KPI strip ──────────────────────────────────────────────
function buildKPI(label, val, sub, c1, c2, glow) {
  return `<div class="kpi" style="--kpi-c1:${c1};--kpi-c2:${c2};--kpi-glow:${glow}">
    <div class="kpi-bar"></div>
    <div class="kpi-val" id="kv-${label.replace(/\s/g,'')}">${val}</div>
    <div class="kpi-label">${label}</div>
    ${sub ? `<div class="kpi-sub">${sub}</div>` : ''}
  </div>`;
}

// ── Analytics ──────────────────────────────────────────────
async function loadAnalytics() {
  try {
    sk('a_sum'); sk('a_lb');
    const m = $('a_month').value, d = $('a_dept').value;

    const s = await api('/analytics/departments/summary?' + qs({ month: m, department: d }));
    $('a_sum').innerHTML = table([
      ['Department', r => `<span class="pill p-dept">${esc(r.department)}</span>`],
      ['Headcount',  r => `<b style="color:var(--acc2);font-weight:800">${r.headcount}</b>`],
      ['Present Days',r => r.present_days],
      ['Avg Hours',  r => r.avg_work_hours ?? '—'],
      ['Late Count', r => r.late_count > 0
        ? `<span style="color:var(--bad2);font-weight:700">${r.late_count}</span>`
        : `<span style="color:var(--ok2)">${r.late_count}</span>`],
      ['Late Min',   r => r.total_late_minutes],
      ['Leave',      r => r.leave_count],
      ['On Duty',    r => r.on_duty_count],
    ], s.items);

    const l = await api('/analytics/leaderboard/late?' + qs({ month: m, department: d, limit: $('a_limit').value }));
    const rankLabel = n => n===1 ? `<span class="r1">🥇 1</span>` : n===2 ? `<span class="r2">🥈 2</span>` : n===3 ? `<span class="r3">🥉 3</span>` : n;
    $('a_lb').innerHTML = table([
      ['Rank',       r => rankLabel(r.rank)],
      ['Code',       r => `<span style="color:var(--acc3);font-weight:600;font-family:'JetBrains Mono',monospace">${esc(r.emp_code)}</span>`],
      ['Name',       r => esc(r.name)],
      ['Department', r => `<span class="pill p-dept">${esc(r.department)}</span>`],
      ['Late Min',   r => `<span style="color:var(--bad2);font-weight:700">${r.total_late_minutes}</span>`],
      ['Late Days',  r => r.late_count],
    ], l.items);

    // Build KPI strip from summary totals
    if (s.items.length > 0) {
      const totalHead = s.items.reduce((a,x) => a + x.headcount, 0);
      const totalLate = s.items.reduce((a,x) => a + x.late_count, 0);
      const totalLeave = s.items.reduce((a,x) => a + x.leave_count, 0);
      const totalOnDuty = s.items.reduce((a,x) => a + x.on_duty_count, 0);
      const strip = $('kpi-strip');
      strip.style.display = 'flex';
      strip.innerHTML =
        buildKPI('Total Staff', totalHead, `${s.items.length} departments`, 'var(--acc)','var(--violet)','rgba(99,102,241,0.14)') +
        buildKPI('Late Arrivals', totalLate, m || 'this month', 'var(--bad)','var(--pink)','rgba(244,63,94,0.13)') +
        buildKPI('On Leave', totalLeave, m || 'this month', 'var(--warn)','#f97316','rgba(245,158,11,0.13)') +
        buildKPI('On Duty', totalOnDuty, m || 'this month', 'var(--cyan)','var(--acc2)','rgba(6,182,212,0.12)') +
        buildKPI('Departments', s.items.length, 'loaded', 'var(--ok)','var(--cyan)','rgba(16,185,129,0.12)');
      // Animate KPI numbers
      ['Total Staff','Late Arrivals','On Leave','On Duty','Departments'].forEach((lbl, i) => {
        const vals = [totalHead, totalLate, totalLeave, totalOnDuty, s.items.length];
        const el = document.getElementById('kv-' + lbl.replace(/\s/g,''));
        if (el) countUp(el, vals[i]);
      });
    }

    toast('Analytics loaded successfully', 'ok');
  } catch (e) { toast(e.message, 'err'); }
}

async function loadEmp() {
  try {
    const e = $('a_emp').value.trim(), m = $('a_month').value;
    if (!e) { toast('Enter an employee code first', 'warn'); return; }
    $('a_emp_out').innerHTML = '<div class="sk"></div><div class="sk" style="width:55%"></div>';
    const r = await api('/analytics/employees/' + encodeURIComponent(e) + '/monthly?month=' + m);
    const st = [
      ['Working Days', r.working_days], ['Present Days', r.present_days],
      ['Attendance %', r.attendance_pct ?? 'n/a'], ['Late Count', r.late_count],
      ['Late Min', r.total_late_minutes], ['Overtime Min', r.total_overtime_minutes],
      ['Leave Days', r.leave_days],
    ];
    $('a_emp_out').innerHTML = '<div class="stats">' + st.map((x,i) =>
      `<div class="stat"><b id="sc${i}">${esc(x[1])}</b><span>${x[0]}</span></div>`
    ).join('') + '</div>';
    // Add a progress bar for attendance %
    if (r.attendance_pct != null) {
      const pct = Math.min(100, Math.max(0, parseFloat(r.attendance_pct)));
      $('a_emp_out').innerHTML += `<div style="margin-top:14px"><div style="font-size:11px;color:var(--mute2);margin-bottom:4px">Attendance Rate: <b style="color:var(--ink2)">${r.attendance_pct}%</b></div><div class="prog-bar"><div class="prog-fill" style="width:${pct}%"></div></div></div>`;
    }
    st.forEach((x,i) => { const el = $('sc'+i); if (el) countUp(el, x[1]); });
  } catch (e) { $('a_emp_out').innerHTML = `<div class="msg err"><span class="msg-icon">✕</span>${esc(e.message)}</div>`; }
}

async function loadTrend() {
  try {
    const dept = $('t_dept').value.trim();
    if (!dept) { toast('Enter a department name', 'warn'); return; }
    $('t_out').innerHTML = '<div class="sk"></div><div class="sk" style="width:60%"></div>';
    const r = await api('/analytics/departments/' + encodeURIComponent(dept) + '/trend?' + qs({ from: $('t_from').value, to: $('t_to').value }));
    const W=1060, H=280, PX=52, PY=36, n=r.items.length;
    const x = i => PX + i * (W - PX - 28) / Math.max(1, n-1);
    const y = v => H - PY - v * (H - PY - PY*0.65);

    function pathStr(key) {
      let s='', pen=false;
      r.items.forEach((it,i) => {
        const v = it[key];
        if (v==null) { pen=false; return; }
        s += (pen?'L':'M') + x(i).toFixed(1) + ' ' + y(v).toFixed(1);
        pen=true;
      });
      return s;
    }
    function areaStr(key) {
      let pts='', first=-1, last=-1, pen=false;
      r.items.forEach((it,i) => { if (it[key]!=null) { if (first<0) first=i; last=i; } });
      if (first<0) return '';
      r.items.forEach((it,i) => {
        const v=it[key]; if (v==null){pen=false;return;}
        pts += (pen?'L':'M') + x(i).toFixed(1) + ' ' + y(v).toFixed(1); pen=true;
      });
      return pts + `L${x(last).toFixed(1)} ${y(0)} L${x(first).toFixed(1)} ${y(0)} Z`;
    }

    const gridLines = [0,.25,.5,.75,1].map(v =>
      `<line x1="${PX}" x2="${W-28}" y1="${y(v)}" y2="${y(v)}" stroke="rgba(255,255,255,0.05)" stroke-dasharray="4 5"/>` +
      `<text x="4" y="${y(v)+4}" fill="var(--mute)" font-size="10">${(v*100).toFixed(0)}%</text>`
    ).join('');

    const dots = r.items.map((it,i) => it.attendance_rate==null
      ? `<rect x="${x(i)-3}" y="${H-PY-6}" width="6" height="6" fill="rgba(255,255,255,0.07)" rx="2"><title>${it.date} (non-working)</title></rect>`
      : `<circle cx="${x(i)}" cy="${y(it.attendance_rate)}" r="5" fill="var(--acc)" stroke="var(--bg)" stroke-width="2.5" style="cursor:pointer"><title>${it.date}: ${(it.attendance_rate*100).toFixed(1)}%</title></circle>`
    ).join('');

    const step = Math.max(1, Math.floor(n / 8));
    const labels = r.items.map((it,i) => (i%step===0||i===n-1)
      ? `<text x="${x(i)}" y="${H-6}" text-anchor="middle" font-size="9" fill="var(--mute)">${it.date.slice(5)}</text>`
      : ''
    ).join('');

    const defs = `<defs>
      <linearGradient id="gAcc" x1="0" y1="0" x2="0" y2="1">
        <stop offset="0%" stop-color="rgba(99,102,241,0.45)"/>
        <stop offset="100%" stop-color="rgba(99,102,241,0.01)"/>
      </linearGradient>
      <linearGradient id="gOk" x1="0" y1="0" x2="0" y2="1">
        <stop offset="0%" stop-color="rgba(16,185,129,0.25)"/>
        <stop offset="100%" stop-color="rgba(16,185,129,0.0)"/>
      </linearGradient>
      <filter id="glow"><feGaussianBlur stdDeviation="2.5" result="blur"/><feMerge><feMergeNode in="blur"/><feMergeNode in="SourceGraphic"/></feMerge></filter>
    </defs>`;

    $('t_out').innerHTML = `
      <div class="scroll">
        <svg viewBox="0 0 ${W} ${H}" width="100%" style="min-width:560px">
          ${defs}${gridLines}
          <path d="${areaStr('attendance_rate')}" fill="url(#gAcc)"/>
          <path d="${pathStr('attendance_rate')}" fill="none" stroke="var(--acc)" stroke-width="2.5" stroke-linejoin="round" filter="url(#glow)"/>
          <path d="${pathStr('moving_avg_7d')}" fill="none" stroke="var(--ok)" stroke-width="2" stroke-linejoin="round" stroke-dasharray="7 4" opacity="0.85"/>
          ${dots}${labels}
        </svg>
      </div>
      <div class="chart-legend">
        <span><svg width="20" height="4"><line x1="0" y1="2" x2="20" y2="2" stroke="var(--acc)" stroke-width="2.5"/></svg>Daily attendance rate</span>
        <span><svg width="20" height="4"><line x1="0" y1="2" x2="20" y2="2" stroke="var(--ok)" stroke-width="2" stroke-dasharray="5 3"/></svg>7-day moving avg</span>
        <span style="font-size:11px;color:var(--mute)">Weekends/holidays excluded · Hover dots for values</span>
      </div>`;
    toast(`Trend loaded for ${dept}`, 'ok');
  } catch (e) { $('t_out').innerHTML = `<div class="msg err"><span class="msg-icon">✕</span>${esc(e.message)}</div>`; }
}

// ── Punch ──────────────────────────────────────────────────
async function punch(kind) {
  const btn = kind==='in' ? $('btn-punch-in') : $('btn-punch-out');
  const origText = btn.textContent;
  btn.textContent = '…'; btn.disabled = true;
  try {
    const b = { emp_code: $('p_emp').value.trim() };
    const t = toMs($('p_time').value);
    if (t) b.punched_at = t;
    if (kind==='in') b.status = $('p_status').value;
    const r = await api('/attendance/punch-' + kind, send('POST', b));
    const msg = kind==='in'
      ? `Punched in for ${r.date} — ${r.late_minutes} min late`
      : `Punched out — ${r.work_hours}h worked, ${r.overtime_minutes} min OT${r.half_day?', half day':''}`;
    toast(msg, 'ok');
    say('p_msg', msg, true);
    loadLogs(1);
  } catch (e) { toast(e.message, 'err'); say('p_msg', e.message); }
  finally { btn.textContent = origText; btn.disabled = false; }
}

async function loadLogs(p) {
  try {
    const page = p||1, size=15;
    if (page===1) sk('l_out');
    const r = await api('/attendance?' + qs({ emp_code:$('l_emp').value.trim(), date_from:$('l_from').value, date_to:$('l_to').value, status:$('l_status').value, page, page_size:size }));
    say('l_msg','');
    $('l_out').innerHTML = table([
      ['Date',     r => `<b style="color:var(--mute2);font-family:'JetBrains Mono',monospace;font-size:12px">${esc(r.date)}</b>`],
      ['Employee', r => `<span style="color:var(--acc3);font-weight:600;font-family:'JetBrains Mono',monospace">${esc(r.emp_code)}</span>`],
      ['Status',   r => pill(r.status)],
      ['In',       r => fmt(r.punch_in)],
      ['Out',      r => fmt(r.punch_out)],
      ['Hours',    r => r.work_hours ?? '—'],
      ['Late',     r => r.late_minutes>0 ? `<span style="color:var(--bad2);font-weight:700">${r.late_minutes}</span>` : `<span style="color:var(--mute)">${r.late_minutes}</span>`],
      ['OT',       r => r.overtime_minutes>0 ? `<span style="color:var(--ok2);font-weight:700">${r.overtime_minutes}</span>` : `<span style="color:var(--mute)">${r.overtime_minutes}</span>`],
      ['Half',     r => r.half_day ? '<span style="color:var(--warn)">½ day</span>' : ''],
      ['Edits',    r => r.history.length>0 ? `<span class="pill p-edits">${r.history.length}</span>` : ''],
    ], r.items);
    pager('l_pg', r.page, r.page_size, r.total, 'loadLogs');
  } catch (e) { say('l_msg', e.message); }
}

async function regularize() {
  try {
    const b = { reason:$('r_reason').value, regularized_by:$('r_by').value };
    if ($('r_status').value) b.status = $('r_status').value;
    const a=toMs($('r_in').value), c=toMs($('r_out').value);
    if (a) b.punch_in=a; if (c) b.punch_out=c;
    const r = await api('/attendance/'+encodeURIComponent($('r_emp').value.trim())+'/'+$('r_date').value, send('PATCH', b));
    const msg = `Saved. ${r.history.length} history entries. Changed: ${Object.keys(r.history[r.history.length-1].changes).join(', ')}`;
    toast(msg, 'ok');
    say('r_msg', msg, true);
    loadLogs(1);
  } catch (e) { toast(e.message, 'err'); say('r_msg', e.message); }
}

// ── Employees ─────────────────────────────────────────────
async function addEmp() {
  try {
    const r = await api('/employees', send('POST', {
      emp_code:$('e_code').value.trim(), name:$('e_name').value, email:$('e_email').value,
      department:$('e_dept').value, shift_start:$('e_ss').value, shift_end:$('e_se').value,
      joined_on:$('e_join').value
    }));
    toast('Created employee ' + r.emp_code, 'ok');
    say('e_msg','Created ' + r.emp_code, true);
    loadEmps(1);
  } catch (e) { toast(e.message,'err'); say('e_msg', e.message); }
}

async function loadEmps(p) {
  try {
    const page=p||1, size=15;
    if (page===1) sk('f_out');
    const r = await api('/employees?' + qs({ department:$('f_dept').value, page, page_size:size }));
    $('f_out').innerHTML = table([
      ['Code',       r => `<b style="color:var(--acc3);font-family:'JetBrains Mono',monospace">${esc(r.emp_code)}</b>`],
      ['Name',       r => esc(r.name)],
      ['Department', r => `<span class="pill p-dept">${esc(r.department)}</span>`],
      ['Shift',      r => `<span style="color:var(--mute2);font-family:'JetBrains Mono',monospace;font-size:12px">${esc(r.shift_start)} – ${esc(r.shift_end)}</span>`],
      ['Joined',     r => esc(r.joined_on)],
      ['Email',      r => `<a href="mailto:${esc(r.email)}" style="color:var(--acc2);text-decoration:none">${esc(r.email)}</a>`],
    ], r.items);
    pager('f_pg', r.page, r.page_size, r.total, 'loadEmps');
  } catch (e) { $('f_out').innerHTML = `<div class="msg err"><span class="msg-icon">✕</span>${esc(e.message)}</div>`; }
}

// ── Navigation ────────────────────────────────────────────
const TABS = [
  ['analytics',  '📊', 'Analytics', 'Analytics Dashboard', 'Department summaries, leaderboard and attendance trends'],
  ['attendance', '⏱', 'Attendance', 'Attendance', 'Punch in/out, records and corrections'],
  ['employees',  '👥', 'Employees',  'Employees', 'Manage employee records and onboarding'],
];
function show(id) {
  TABS.forEach(t => {
    $(t[0]).classList.toggle('on', t[0]===id);
  });
  [...$('sb-nav').querySelectorAll('.sb-btn')].forEach((b,i) => b.classList.toggle('on', TABS[i][0]===id));
  // Update topbar
  const tab = TABS.find(t => t[0]===id);
  if (tab) {
    $('topbar-title').textContent = tab[3];
    $('topbar-sub').textContent   = tab[4];
  }
  // Show/hide KPI strip
  $('kpi-strip').style.display = id==='analytics' ? 'flex' : 'none';
  location.hash = id;
}

// Build sidebar nav
$('sb-nav').innerHTML += TABS.map(t =>
  `<button class="sb-btn" onclick="show('${t[0]}')">
    <div class="sb-icon">${t[1]}</div>
    <span>${t[2]}</span>
  </button>`
).join('');

// ── Bootstrap ─────────────────────────────────────────────
const today = new Date(Date.now() + IST).toISOString().slice(0, 10);
$('a_month').value = today.slice(0, 7);
$('t_from').value  = today.slice(0, 8) + '01';
$('t_to').value    = today;
show(location.hash.slice(1) || 'analytics');
loadLogs(1);
loadEmps(1);
</script>
</body>
</html>"""
