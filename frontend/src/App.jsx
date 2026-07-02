import { useEffect, useState, useRef, useCallback } from "react";
import ReactMarkdown from "react-markdown";

const BASE_URL = "http://localhost:8000";

// ── Icons ──────────────────────────────────────────────────
const I = {
  Menu: () => <svg width="20" height="20" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="1.8" d="M4 6h16M4 12h16M4 18h16"/></svg>,
  Plus: () => <svg width="15" height="15" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2.2" d="M12 4v16m8-8H4"/></svg>,
  Msg: () => <svg width="14" height="14" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="1.6" d="M8 10h.01M12 10h.01M16 10h.01M9 16H5a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v8a2 2 0 01-2 2h-5l-5 5v-5z"/></svg>,
  Send: () => <svg width="15" height="15" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M12 19l9 2-9-18-9 18 9-2zm0 0v-8"/></svg>,
  Bot: () => <svg width="14" height="14" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="1.6" d="M9.75 17L9 20l-1 1h8l-1-1-.75-3M3 13h18M5 17h14a2 2 0 002-2V5a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z"/></svg>,
  User: () => <svg width="14" height="14" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="1.6" d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z"/></svg>,
  Sun: () => <svg width="15" height="15" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="1.6" d="M12 3v1m0 16v1m8.66-9H21M3 12H2m15.07-6.07l-.71.71M7.64 16.36l-.71.71M18.36 16.36l-.71-.71M7.05 7.64l-.71-.71M12 7a5 5 0 100 10A5 5 0 0012 7z"/></svg>,
  Moon: () => <svg width="15" height="15" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="1.6" d="M20.354 15.354A9 9 0 018.646 3.646 9.003 9.003 0 0012 21a9.003 9.003 0 008.354-5.646z"/></svg>,
  Upload: () => <svg width="24" height="24" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="1.5" d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12"/></svg>,
  File: () => <svg width="16" height="16" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="1.6" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"/></svg>,
  Spin: () => <svg className="spin" width="15" height="15" viewBox="0 0 24 24" fill="none"><circle cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" opacity="0.25"/><path fill="currentColor" opacity="0.75" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z"/></svg>,
  Warn: () => <svg width="14" height="14" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z"/></svg>,
  Check: () => <svg width="14" height="14" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"/></svg>,
  ChevR: () => <svg width="12" height="12" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M9 5l7 7-7 7"/></svg>,
  ChevL: () => <svg width="14" height="14" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M15 19l-7-7 7-7"/></svg>,
  ChevRn: () => <svg width="14" height="14" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M9 5l7 7-7 7"/></svg>,
  Download: () => <svg width="14" height="14" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4"/></svg>,
  Trash: () => <svg width="13" height="13" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="1.8" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16"/></svg>,
  Edit: () => <svg width="13" height="13" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="1.8" d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z"/></svg>,
  X: () => <svg width="12" height="12" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2.2" d="M6 18L18 6M6 6l12 12"/></svg>,
  Target: () => <svg width="13" height="13" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="1.8" d="M13 10V3L4 14h7v7l9-11h-7z"/></svg>,
  Clock: () => <svg width="13" height="13" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="1.8" d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z"/></svg>,
  Shield: () => <svg width="13" height="13" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="1.8" d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z"/></svg>,
  Alert: () => <svg width="13" height="13" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="1.8" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z"/></svg>,
  Pdf: () => <svg width="14" height="14" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="1.8" d="M7 21h10a2 2 0 002-2V9.414a1 1 0 00-.293-.707l-5.414-5.414A1 1 0 0012.586 3H7a2 2 0 00-2 2v14a2 2 0 002 2z"/><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="1.5" d="M9 13h1.5a1 1 0 010 2H9v-4h1.5m4 0h.5a1 1 0 010 2H13v2"/></svg>,
  Collapse: () => <svg width="13" height="13" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M11 19l-7-7 7-7m8 14l-7-7 7-7"/></svg>,
  Expand: () => <svg width="13" height="13" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M13 5l7 7-7 7M5 5l7 7-7 7"/></svg>,
  Text: () => <svg width="15" height="15" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="1.8" d="M4 6h16M4 10h16M4 14h10M4 18h6"/></svg>,
  Chat: () => <svg width="14" height="14" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="1.8" d="M21 15a2 2 0 01-2 2H7l-4 4V5a2 2 0 012-2h14a2 2 0 012 2z"/></svg>,
  ChevDown: () => <svg width="13" height="13" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M19 9l-7 7-7-7"/></svg>,
  ChevUp: () => <svg width="13" height="13" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M5 15l7-7 7 7"/></svg>,
};

const cx = (...a) => a.filter(Boolean).join(" ");

// ── PDF Report generator ────────────────────────────────────
function generatePDFReport(data, sessionTitle) {
  const itemStr = (item) => {
    if (typeof item === "string") return item;
    if (item.requirement) return `${item.requirement}${item.page_ref && item.page_ref !== "N/A" ? " <em>(" + item.page_ref + ")</em>" : ""}`;
    if (item.event) return `${item.event}${item.date ? " — " + item.date : ""}${item.page_ref && item.page_ref !== "N/A" ? " <em>(" + item.page_ref + ")</em>" : ""}`;
    if (item.role) return `<strong>${item.role}</strong>: ${item.details || ""}${item.page_ref && item.page_ref !== "N/A" ? " <em>(" + item.page_ref + ")</em>" : ""}`;
    if (item.item) return `${item.item}${item.page_ref && item.page_ref !== "N/A" ? " <em>(" + item.page_ref + ")</em>" : ""}`;
    return JSON.stringify(item);
  };
  const items = (arr) => arr?.length
    ? arr.map((s, i) => `<li style="margin:4px 0;font-size:12px;">${i + 1}. ${itemStr(s)}</li>`).join("")
    : "<li style='color:#999;font-size:12px;'>None detected</li>";
  const complianceTable = (arr) => {
    if (!arr?.length) return "<p style='color:#999;font-size:12px;'>None detected</p>";
    const rows = arr.map(c => {
      if (typeof c === "string") return `<tr><td>${c}</td><td>—</td><td>—</td><td>—</td></tr>`;
      return `<tr><td>${c.requirement || ""}</td><td>${c.category || ""}</td><td>${c.page_ref || "N/A"}</td><td>${c.mandatory === true ? "✅ Yes" : c.mandatory === false ? "No" : "—"}</td></tr>`;
    }).join("");
    return `<table style="width:100%;border-collapse:collapse;font-size:12px;margin-top:8px;"><thead><tr style="background:#f5f0ff;"><th style="padding:6px 10px;text-align:left;border:1px solid #ddd;">Requirement</th><th style="padding:6px 10px;text-align:left;border:1px solid #ddd;">Category</th><th style="padding:6px 10px;text-align:left;border:1px solid #ddd;">Page</th><th style="padding:6px 10px;text-align:left;border:1px solid #ddd;">Mandatory</th></tr></thead><tbody>${rows}</tbody></table>`;
  };

  const html = `<!DOCTYPE html><html><head><meta charset="utf-8"><title>AI Document Intelligence Report</title>
  <style>
    body{font-family:'Segoe UI',sans-serif;max-width:780px;margin:0 auto;padding:40px;color:#1a1512;}
    h1{font-size:28px;font-weight:800;color:#FF6B35;margin-bottom:4px;}
    .sub{color:#888;font-size:13px;margin-bottom:32px;}
    .section{margin-bottom:28px;page-break-inside:avoid;}
    .section-header{display:flex;align-items:center;gap:10px;padding:10px 16px;border-radius:10px;margin-bottom:12px;}
    .scope .section-header, .deliverables .section-header{background:rgba(255,107,53,0.1);}
    .deadline .section-header{background:rgba(78,205,196,0.1);}
    .staffing .section-header{background:rgba(96,165,250,0.1);}
    .compliance .section-header{background:rgba(167,139,250,0.1);}
    .highlights .section-header{background:rgba(245,158,11,0.1);}
    .objectives .section-header{background:rgba(34,197,94,0.1);}
    .technical .section-header{background:rgba(59,130,246,0.1);}
    .commercial .section-header{background:rgba(244,63,94,0.1);}
    .risks .section-header{background:rgba(239,68,68,0.1);}
    .section-header h2{margin:0;font-size:15px;font-weight:700;}
    .scope h2, .deliverables h2{color:#FF6B35;} .deadline h2{color:#4ECDC4;} .staffing h2{color:#60A5FA;}
    .compliance h2{color:#A78BFA;} .highlights h2{color:#F59E0B;} .objectives h2{color:#22c55e;}
    .technical h2{color:#3b82f6;} .commercial h2{color:#f43f5e;} .risks h2{color:#ef4444;}
    ul{margin:0;padding-left:20px;} li{margin:5px 0;font-size:12px;line-height:1.5;}
    .doctype{display:inline-block;padding:4px 12px;border-radius:999px;background:rgba(255,107,53,0.12);
      color:#FF6B35;font-size:12px;font-weight:700;margin-bottom:16px;}
    .exec-summary{font-size:13px;line-height:1.6;color:#333;margin-bottom:28px;
      padding:14px 16px;background:#faf9f7;border-radius:10px;border:1px solid #eee;}
    .risk-sev {display:inline-block;padding:1px 5px;font-size:10px;font-weight:bold;border-radius:3px;margin-left:5px;text-transform:uppercase;}
    .risk-sev-high {background:rgba(239,68,68,0.15);color:#ef4444;}
    .risk-sev-medium {background:rgba(245,158,11,0.15);color:#f59e0b;}
    .risk-sev-low {background:rgba(34,197,94,0.15);color:#22c55e;}
    .footer{margin-top:40px;padding-top:16px;border-top:1px solid #eee;font-size:11px;color:#aaa;text-align:center;}
    @media print{body{padding:20px;}}
  </style></head><body>
  <h1>📋 Document Intelligence Report</h1>
  <div class="sub">Session: ${sessionTitle || "Analysis"} &nbsp;·&nbsp; Generated: ${new Date().toLocaleString()}</div>
  ${data.document_type_label ? `<div class="doctype">${data.document_type_label}</div>` : ""}
  ${data.executive_summary ? `<div class="exec-summary">${data.executive_summary}</div>` : ""}
  <div class="section objectives"><div class="section-header"><span>🎯</span><h2>Objectives</h2></div><ul>${items(data.objectives)}</ul></div>
  <div class="section scope"><div class="section-header"><span>📐</span><h2>Scope of Work</h2></div><ul>${items(data.project_scope)}</ul></div>
  <div class="section deliverables"><div class="section-header"><span>📦</span><h2>Deliverables</h2></div><ul>${items(data.deliverables)}</ul></div>
  <div class="section technical"><div class="section-header"><span>💻</span><h2>Technical Requirements</h2></div><ul>${items(data.technical_requirements)}</ul></div>
  <div class="section commercial"><div class="section-header"><span>💰</span><h2>Commercial Requirements</h2></div><ul>${items(data.commercial_requirements)}</ul></div>
  <div class="section deadline"><div class="section-header"><span>⏰</span><h2>Key Deadlines</h2></div><ul>${items(data.deadlines)}</ul></div>
  <div class="section staffing"><div class="section-header"><span>👥</span><h2>Staffing Requirements</h2></div><ul>${items(data.staffing_requirements)}</ul></div>
  <div class="section risks"><div class="section-header"><span>⚠️</span><h2>Risks</h2></div><ul>${
    data.risks?.length ? data.risks.map((r, i) => {
      if (typeof r === "string") return `<li style="margin:4px 0;font-size:12px;">${i + 1}. ${r}</li>`;
      const sevClass = r.severity ? `risk-sev risk-sev-${r.severity.toLowerCase()}` : "";
      return `<li style="margin:4px 0;font-size:12px;">${i + 1}. ${r.risk || r.item || ""} ${r.severity ? `<span class="${sevClass}">${r.severity}</span>` : ""} ${r.type ? `[${r.type}]` : ""} ${r.page_ref && r.page_ref !== "N/A" ? `<em>(${r.page_ref})</em>` : ""}</li>`;
    }).join("") : "<li style='color:#999;font-size:12px;'>None detected</li>"
  }</ul></div>
  <div class="section compliance"><div class="section-header"><span>🛡️</span><h2>Compliance Requirements</h2></div>${complianceTable(data.compliance_requirements)}</div>
  <div class="section highlights"><div class="section-header"><span>💡</span><h2>Key Highlights</h2></div><ul>${items(data.key_highlights)}</ul></div>
  <div class="footer">Generated by Document Intelligence AI Workspace</div>
  </body></html>`;

  const blob = new Blob([html], { type: "text/html" });
  const url  = URL.createObjectURL(blob);
  const win  = window.open(url, "_blank");
  if (win) win.addEventListener("load", () => setTimeout(() => win.print(), 400));
}

// ── Main App ────────────────────────────────────────────────
export default function App() {
  // Upload state
  const [file, setFile]             = useState(null);
  const [manualText, setManualText] = useState("");
  const [inputMode, setInputMode]   = useState("file"); // "file" | "text"
  const [dragOver, setDragOver]     = useState(false);

  // Result + UI state
  const [result, setResult]         = useState(null);
  const [loading, setLoading]       = useState(false);
  const [loadingMsg, setLoadingMsg] = useState("Analyzing document…");
  const [chatOpen, setChatOpen]     = useState(false);

  // Chat state
  const [chatLoading, setChatLoading] = useState(false);
  const [sessions, setSessions]       = useState([]);
  const [activeSession, setActiveSession] = useState(null);
  const [messages, setMessages]         = useState([]);
  const [question, setQuestion]         = useState("");

  // Layout
  const [sidebarOpen, setSidebarOpen] = useState(true);
  const [mobileOpen, setMobileOpen]   = useState(false);
  const [toast, setToast]             = useState(null);
  const [theme, setTheme]             = useState(() => localStorage.getItem("theme") || "light");

  // Session management
  const [ctxMenu, setCtxMenu]     = useState(null);
  const [renaming, setRenaming]   = useState(null);
  const [renameVal, setRenameVal] = useState("");
  const [confirmDel, setConfirmDel] = useState(null);

  const msgEndRef = useRef(null);
  const renameRef = useRef(null);
  const fileRef   = useRef(null);
  const isDark    = theme === "dark";

  useEffect(() => {
    localStorage.setItem("theme", theme);
    document.documentElement.setAttribute("data-theme", theme);
    document.body.style.cssText = `background:${isDark ? "#0d0d10" : "#f0ede6"};color:${isDark ? "#f2ede8" : "#1a1512"};margin:0;padding:0;`;
  }, [theme, isDark]);

  const toast$ = useCallback((message, type = "error") => {
    setToast({ message, type });
    setTimeout(() => setToast(null), 4000);
  }, []);

  // ── API ────────────────────────────────────────────────────
  const loadSessions = useCallback(async () => {
    try {
      const r = await fetch(`${BASE_URL}/chat/sessions`);
      if (!r.ok) throw 0;
      const d = await r.json();
      setSessions(d.sessions || []);
    } catch { toast$("Server unreachable. Ensure backend is running.", "error"); }
  }, [toast$]);

  useEffect(() => { loadSessions(); }, [loadSessions]);
  useEffect(() => { msgEndRef.current?.scrollIntoView({ behavior: "smooth" }); }, [messages, chatLoading]);
  useEffect(() => { if (renaming && renameRef.current) renameRef.current.focus(); }, [renaming]);
  useEffect(() => {
    const fn = () => setCtxMenu(null);
    document.addEventListener("click", fn);
    return () => document.removeEventListener("click", fn);
  }, []);

  const createSession = async () => {
    try {
      const r = await fetch(`${BASE_URL}/chat/new-session`, { method: "POST" });
      if (!r.ok) throw 0;
      const d = await r.json();
      setActiveSession(d.session_id);
      setMessages([]);
      await loadSessions();
      setMobileOpen(false);
      return d.session_id;
    } catch { toast$("Failed to create session.", "error"); }
  };

  const loadHistory = async (sid) => {
    try {
      const r = await fetch(`${BASE_URL}/chat/history/${sid}`);
      if (!r.ok) throw 0;
      const d = await r.json();
      setActiveSession(sid);
      setMessages(d.messages || []);
      setResult(d.analysis ? { final_extracted_data: d.analysis } : null);
      setChatOpen(true);
      setMobileOpen(false);
    } catch { toast$("Failed to load history.", "error"); }
  };

  const renameSession = async (sid, newTitle) => {
    try {
      await fetch(`${BASE_URL}/chat/session/${sid}/rename?title=${encodeURIComponent(newTitle)}`, {
        method: "PATCH",
      });
      await loadSessions();
    } catch {
      toast$("Failed to rename session. Server unreachable.", "error");
    }
    setSessions(prev => prev.map(s => s.session_id === sid ? { ...s, title: newTitle } : s));
  };

  const deleteSession = async (sid) => {
    try {
      await fetch(`${BASE_URL}/chat/session/${sid}`, { method: "DELETE" });
    } catch {
      toast$("Failed to delete session on server; removed locally.", "error");
    }
    setSessions(prev => prev.filter(s => s.session_id !== sid));
    if (activeSession === sid) { setActiveSession(null); setMessages([]); setResult(null); setChatOpen(false); }
    setConfirmDel(null);
    toast$("Session deleted.", "success");
  };

  // ── Upload / Analyze ───────────────────────────────────────
  const handleUpload = async () => {
    if (inputMode === "file" && !file) return toast$("Please select a PDF or DOCX file.", "warning");
    if (inputMode === "text" && !manualText.trim()) return toast$("Please paste some text to analyze.", "warning");

    setLoading(true);
    setLoadingMsg("Reading your document…");
    try {
      const msgs = ["Reading your document…", "Extracting insights…", "Identifying deadlines…", "Detecting compliance needs…", "Almost done…"];
      let mi = 0;
      const timer = setInterval(() => { mi = (mi + 1) % msgs.length; setLoadingMsg(msgs[mi]); }, 1800);

      // Ensure a session exists so backend can auto-name it
      let sid = activeSession;
      if (!sid) { sid = await createSession(); }

      let r;
      if (inputMode === "file") {
        const fd = new FormData();
        fd.append("file", file);
        r = await fetch(`${BASE_URL}/rfp/upload?session_id=${sid}`, { method: "POST", body: fd });
      } else {
        r = await fetch(`${BASE_URL}/rfp/analyze-text`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ text: manualText, session_id: sid }),
        });
      }
      clearInterval(timer);
      if (!r.ok) throw 0;
      const data = await r.json();
      setResult(data);
      setChatOpen(false); // start fresh — user decides when to open chat
      if (!activeSession) await createSession();
      toast$("Document analyzed successfully!", "success");
    } catch { toast$("Failed to analyze document.", "error"); }
    finally { setLoading(false); }
  };

  const handleAsk = async () => {
    if (!activeSession) return toast$("Open a session first.", "warning");
    if (!question.trim()) return;
    const q = question;
    setMessages(p => [...p, { role: "user", content: q }]);
    setQuestion("");
    setChatLoading(true);
    try {
      const r = await fetch(`${BASE_URL}/chat/ask?question=${encodeURIComponent(q)}&session_id=${activeSession}`, { method: "POST" });
      if (!r.ok) throw 0;
      const d = await r.json();
      setMessages(p => [...p, { role: "assistant", content: d.answer }]);
    } catch {
      setMessages(p => [...p, { role: "assistant", content: "⚠️ Error communicating with server." }]);
    } finally { setChatLoading(false); }
  };

  const handleDrop = (e) => {
    e.preventDefault(); setDragOver(false);
    const f = e.dataTransfer.files[0];
    if (f && (f.name.endsWith(".pdf") || f.name.endsWith(".docx"))) { setFile(f); setInputMode("file"); }
    else toast$("Please drop a PDF or DOCX file.", "warning");
  };

  const activeTitle = sessions.find(s => s.session_id === activeSession)?.title || "Analysis Workspace";
  const flashData   = result?.final_extracted_data || null;

  const openCtx = (e, session) => {
    e.preventDefault(); e.stopPropagation();
    const rect = e.currentTarget.getBoundingClientRect();
    setCtxMenu({ sessionId: session.session_id, title: session.title, x: rect.right + 4, y: rect.top });
  };

  // ── Render ──────────────────────────────────────────────────
  return (
    <div className={cx("shell", isDark && "dark")}>
      <style>{CSS}</style>

      {/* Toast */}
      {toast && (
        <div className={cx("toast", "toast-" + toast.type)}>
          {toast.type === "error" ? <I.Warn /> : toast.type === "success" ? <I.Check /> : <I.Warn />}
          {toast.message}
        </div>
      )}

      {/* Delete confirm modal */}
      {confirmDel && (
        <div className="modal-bg" onClick={() => setConfirmDel(null)}>
          <div className="modal" onClick={e => e.stopPropagation()}>
            <div
  style={{
    width:48,
    height:48,
    borderRadius:"50%",
    background:"rgba(239,68,68,.12)",
    color:"#ef4444",
    display:"flex",
    alignItems:"center",
    justifyContent:"center",
    marginBottom:8
  }}
>
  <I.Trash />
</div>
            <div style={{ fontFamily: "var(--font-display)", fontWeight: 800, fontSize: 16, marginBottom: 6 }}>Delete session?</div>
            <div style={{ fontSize: 12, color: "var(--text-secondary)", marginBottom: 20, lineHeight: 1.6 }}>
              This will permanently remove the chat history. This cannot be undone.
            </div>
            <div style={{ display: "flex", gap: 10 }}>
              <button className="btn-ghost" onClick={() => setConfirmDel(null)}>Cancel</button>
              <button className="btn-danger" onClick={() => deleteSession(confirmDel)}>Delete</button>
            </div>
          </div>
        </div>
      )}

      {/* Context menu */}
      {ctxMenu && (
        <div className="ctx-menu" style={{ top: ctxMenu.y, left: ctxMenu.x }} onClick={e => e.stopPropagation()}>
          <button className="ctx-item" onClick={() => { setRenaming(ctxMenu.sessionId); setRenameVal(ctxMenu.title || ""); setCtxMenu(null); }}>
            <I.Edit /> Rename
          </button>
          <div className="ctx-sep" />
          <button className="ctx-item danger" onClick={() => { setConfirmDel(ctxMenu.sessionId); setCtxMenu(null); }}>
            <I.Trash /> Delete
          </button>
        </div>
      )}

      {mobileOpen && <div className="overlay" onClick={() => setMobileOpen(false)} />}

      {/* ── Sidebar ── */}
      <aside className={cx("sidebar", !sidebarOpen && "collapsed", mobileOpen && "mob-open")}>
        <div className="sb-logo">
          <div className="sb-logo-icon">
            <svg width="17" height="17" viewBox="0 0 24 24" fill="none" stroke="white" strokeWidth="2.2" strokeLinecap="round" strokeLinejoin="round">
              <path d="M14 2H6a2 2 0 00-2 2v16a2 2 0 002 2h12a2 2 0 002-2V8z"/>
              <polyline points="14 2 14 8 20 8"/>
              <line x1="16" y1="13" x2="8" y2="13"/>
              <line x1="16" y1="17" x2="8" y2="17"/>
            </svg>
          </div>
          {sidebarOpen && <div><div className="sb-name">AI Document Intelligence</div><div className="sb-sub">AI Workspace</div></div>}
        </div>

        <button className="sb-new" onClick={createSession}>
          <I.Plus />{sidebarOpen && <span>New Analysis</span>}
        </button>

        {sidebarOpen && sessions.length > 0 && <div className="sb-label">Recent</div>}
        <div className="sb-list">
          {sessions.length === 0 && sidebarOpen
            ? <div className="sb-empty">No sessions yet.<br />Start a new analysis.</div>
            : sessions.map(s => (
              <div key={s.session_id} className={cx("sb-item-wrap", activeSession === s.session_id && "active")}>
                {renaming === s.session_id
                  ? <form className="rename-form" onSubmit={e => {
                      e.preventDefault();
                      renameSession(s.session_id, renameVal || s.title || "Untitled");
                      setRenaming(null);
                    }}>
                      <input ref={renameRef} className="rename-input" value={renameVal}
                        onChange={e => setRenameVal(e.target.value)}
                        onBlur={() => { renameSession(s.session_id, renameVal || s.title || "Untitled"); setRenaming(null); }}
                        onKeyDown={e => e.key === "Escape" && setRenaming(null)} />
                    </form>
                  : <>
                      <button className="sb-item" onClick={() => loadHistory(s.session_id)}>
                        <div className="sb-item-icon"><I.Msg /></div>
                        {sidebarOpen && <span className="sb-item-title">{s.title || "Untitled Session"}</span>}
                      </button>
                      {sidebarOpen && (
                        <button className="sb-more" onClick={e => openCtx(e, s)} title="Options">
                          <svg width="14" height="14" fill="currentColor" viewBox="0 0 24 24">
                            <circle cx="5" cy="12" r="1.5" /><circle cx="12" cy="12" r="1.5" /><circle cx="19" cy="12" r="1.5" />
                          </svg>
                        </button>
                      )}
                    </>
                }
              </div>
            ))
          }
        </div>

        <div className="sb-footer">
          <button className="sb-collapse" onClick={() => setSidebarOpen(o => !o)}>
            {sidebarOpen ? <><I.Collapse /><span>Collapse</span></> : <I.Expand />}
          </button>
        </div>
      </aside>

      {/* ── Main ── */}
      <div className="main">
        {/* Header */}
        <header className="header">
          <div style={{ display: "flex", alignItems: "center", gap: 10 }}>
            <button className="mob-menu" onClick={() => setMobileOpen(true)}><I.Menu /></button>
            <div className="header-title">
              {activeSession
                ? <><span style={{ color: "var(--text-secondary)" }}>AI Document Intelligence</span>
                    <span style={{ color: "var(--border)", margin: "0 4px" }}><I.ChevR /></span>
                    <span>{activeTitle}</span></>
                : <>
                    <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="var(--accent)" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                      <path d="M14 2H6a2 2 0 00-2 2v16a2 2 0 002 2h12a2 2 0 002-2V8z"/>
                      <polyline points="14 2 14 8 20 8"/>
                    </svg>
                    AI Document Intelligence
                  </>
              }
            </div>
          </div>
          <div style={{ display: "flex", gap: 8, alignItems: "center" }}>
            {flashData && (
              <button className="btn-report" onClick={() => generatePDFReport(flashData, activeTitle)}>
                <I.Download /> Export PDF
              </button>
            )}
            <button className="theme-btn" onClick={() => setTheme(isDark ? "light" : "dark")}>
              {isDark ? <I.Sun /> : <I.Moon />}
            </button>
          </div>
        </header>

        {/* Content */}
        <div className="content">
          {!result ? (
            /* ── UPLOAD SCREEN ── */
            <div className="upload-wrap">
              <div className="upload-card">
                <div className="upload-blob b1" />
                <div className="upload-blob b2" />
                <div className="upload-inner">
                  <div className="upload-badge"><I.Target /> AI-Powered Analysis</div>
                  <h1 className="upload-title">AI Document Intelligence</h1>
                  <p className="upload-desc">
                    Upload a document or paste your text — we'll extract scope, deadlines, compliance needs &amp; risks instantly.
                  </p>

                  {/* Mode tabs */}
                  <div className="mode-tabs">
                    <button
                      className={cx("mode-tab", inputMode === "file" && "active")}
                      onClick={() => setInputMode("file")}
                    >
                      <I.Upload /> Upload File
                    </button>
                    <button
                      className={cx("mode-tab", inputMode === "text" && "active")}
                      onClick={() => setInputMode("text")}
                    >
                      <I.Text /> Paste Text
                    </button>
                  </div>

                  {/* File mode */}
                  {inputMode === "file" && (
                    <div
                      className={cx("dropzone", dragOver && "drag-over", file && "has-file")}
                      onDragOver={e => { e.preventDefault(); setDragOver(true); }}
                      onDragLeave={() => setDragOver(false)}
                      onDrop={handleDrop}
                      onClick={() => !file && fileRef.current?.click()}
                    >
                      <input ref={fileRef} type="file" accept=".pdf,.docx" style={{ display: "none" }}
                        onChange={e => setFile(e.target.files[0])} />
                      {!file ? (
                        <>
                          <div className="dz-icon"><I.Upload /></div>
                          <div className="dz-title">Drop your PDF or DOCX here</div>
                          <div className="dz-sub">or <span className="dz-browse">browse files</span></div>
                          <div className="dz-formats">
                            <span className="fmt-badge">PDF</span>
                            <span className="fmt-badge">DOCX</span>
                          </div>
                        </>
                      ) : (
                        <div className="file-preview">
                          <div className="file-preview-icon"> <I.File /></div>
                          <div className="file-preview-info">
                            <div className="file-preview-name">{file.name}</div>
                            <div className="file-preview-size">{(file.size / 1024).toFixed(1)} KB · Ready to analyze</div>
                          </div>
                          <button className="file-remove" onClick={e => { e.stopPropagation(); setFile(null); }}>
                            <I.X />
                          </button>
                        </div>
                      )}
                    </div>
                  )}

                  {/* Text mode */}
                  {inputMode === "text" && (
                    <div className="text-input-wrap">
                      <textarea
                        className="text-inp"
                        placeholder="Paste your document text, contract, or other content here…"
                        value={manualText}
                        onChange={e => setManualText(e.target.value)}
                        rows={8}
                      />
                      <div className="text-inp-meta">
                        {manualText.length > 0
                          ? <span className="text-count">{manualText.trim().split(/\s+/).length} words · {manualText.length} chars</span>
                          : <span className="text-hint">Minimum ~50 words recommended for good results</span>
                        }
                        {manualText.length > 0 && (
                          <button className="text-clear" onClick={() => setManualText("")}><I.X /> Clear</button>
                        )}
                      </div>
                    </div>
                  )}

                  {/* Analyze button */}
                  {((inputMode === "file" && file) || (inputMode === "text" && manualText.trim().length > 0)) && !loading && (
                    <button className="btn-analyze" onClick={handleUpload}>
                      Analyze Document →
                    </button>
                  )}

                  {loading && (
                    <div className="loading-state">
                      <div className="loading-bar"><div className="loading-fill" /></div>
                      <div className="loading-msg"><I.Spin />{loadingMsg}</div>
                    </div>
                  )}
                </div>
              </div>
            </div>
          ) : (
            /* ── RESULTS SCREEN ── */
            <div className="results-wrap">

              {/* Top bar */}
              <div className="results-topbar">
                <div className="results-meta">
                  <div className="results-title-row">
                    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="var(--accent)" strokeWidth="2.2" strokeLinecap="round" strokeLinejoin="round">
                      <path d="M14 2H6a2 2 0 00-2 2v16a2 2 0 002 2h12a2 2 0 002-2V8z"/>
                      <polyline points="14 2 14 8 20 8"/>
                    </svg>
                    <span className="results-title">
                      {file ? file.name : "Pasted Text"}
                    </span>
                    <span className="results-badge">Analyzed</span>
                    {/* Download button — right next to the Analyzed badge */}
                    {file && (
                      <a
                        href={`${BASE_URL}/rfp/download/${encodeURIComponent(file.name)}`}
                        download={file.name}
                        className="dl-inline-btn"
                        title="Download original file"
                      >
                        <I.Download /> Download Original
                      </a>
                    )}
                  </div>
                  {flashData?.document_type_label && (
                    <div className="results-doc-type-large">
                      Document Type: <strong>{flashData.document_type_label}</strong>
                    </div>
                  )}
                </div>
                <div style={{ display: "flex", gap: 8, alignItems: "center" }}>
                  {/* Re-upload strip */}
                  <div className={cx("strip-dropzone-sm", dragOver && "drag-over")}
                    onDragOver={e => { e.preventDefault(); setDragOver(true); }}
                    onDragLeave={() => setDragOver(false)}
                    onDrop={handleDrop}
                    onClick={() => fileRef.current?.click()}
                    title="Upload new document"
                  >
                    <input ref={fileRef} type="file" accept=".pdf,.docx" style={{ display: "none" }}
                      onChange={e => { setFile(e.target.files[0]); setInputMode("file"); }} />
                    {loading ? <><I.Spin /><span>Analyzing…</span></> : <><I.Upload /><span>New file</span></>}
                  </div>

                  <button className="btn-chat-toggle" onClick={() => setChatOpen(o => !o)}>
                    <I.Chat />
                    {chatOpen ? "Hide Chat" : "Chat with document"}
                    {chatOpen ? <I.ChevUp /> : <I.ChevDown />}
                  </button>
                </div>
              </div>

              {/* ── Document Report — clean text sections ── */}
              <div className="doc-report">

                {/* Summary */}
                {flashData?.executive_summary && (
                  <div className="doc-section">
                    <h2 className="doc-section-heading">Summary</h2>
                    <p className="doc-section-prose">{flashData.executive_summary}</p>
                  </div>
                )}

                {/* Objectives */}
                {flashData?.objectives?.length > 0 && (
                  <div className="doc-section">
                    <h2 className="doc-section-heading">Objectives</h2>
                    <ul className="doc-list">
                      {flashData.objectives.map((item, i) => (
                        <li key={i}>{typeof item === "string" ? item : item.item || JSON.stringify(item)}</li>
                      ))}
                    </ul>
                  </div>
                )}

                {/* Scope of Work */}
                {flashData?.project_scope?.length > 0 && (
                  <div className="doc-section">
                    <h2 className="doc-section-heading">Scope of Work</h2>
                    <ul className="doc-list">
                      {flashData.project_scope.map((item, i) => (
                        <li key={i}>
                          {typeof item === "string" ? item : item.item || JSON.stringify(item)}
                          {item.page_ref && item.page_ref !== "N/A" && <span className="pg-ref">{item.page_ref}</span>}
                        </li>
                      ))}
                    </ul>
                  </div>
                )}

                {/* Deliverables */}
                {flashData?.deliverables?.length > 0 && (
                  <div className="doc-section">
                    <h2 className="doc-section-heading">Deliverables</h2>
                    <ul className="doc-list">
                      {flashData.deliverables.map((item, i) => (
                        <li key={i}>
                          {typeof item === "string" ? item : item.item || JSON.stringify(item)}
                          {item.page_ref && item.page_ref !== "N/A" && <span className="pg-ref">{item.page_ref}</span>}
                        </li>
                      ))}
                    </ul>
                  </div>
                )}

                {/* Technical Requirements */}
                {flashData?.technical_requirements?.length > 0 && (
                  <div className="doc-section">
                    <h2 className="doc-section-heading">Technical Requirements</h2>
                    <ul className="doc-list">
                      {flashData.technical_requirements.map((item, i) => (
                        <li key={i}>
                          {typeof item === "string" ? item : item.item || JSON.stringify(item)}
                          {item.page_ref && item.page_ref !== "N/A" && <span className="pg-ref">{item.page_ref}</span>}
                        </li>
                      ))}
                    </ul>
                  </div>
                )}

                {/* Commercial Requirements */}
                {flashData?.commercial_requirements?.length > 0 && (
                  <div className="doc-section">
                    <h2 className="doc-section-heading">Commercial Requirements</h2>
                    <ul className="doc-list">
                      {flashData.commercial_requirements.map((item, i) => (
                        <li key={i}>
                          {typeof item === "string" ? item : item.item || JSON.stringify(item)}
                          {item.page_ref && item.page_ref !== "N/A" && <span className="pg-ref">{item.page_ref}</span>}
                        </li>
                      ))}
                    </ul>
                  </div>
                )}

                {/* Deadlines */}
                {flashData?.deadlines?.length > 0 && (
                  <div className="doc-section">
                    <h2 className="doc-section-heading">Key Deadlines &amp; Milestones</h2>
                    <ul className="doc-list">
                      {flashData.deadlines.map((item, i) => (
                        <li key={i}>
                          {typeof item === "string" ? item : (
                            <>{item.event}{item.date && <strong> — {item.date}</strong>}</>
                          )}
                          {item.page_ref && item.page_ref !== "N/A" && <span className="pg-ref">{item.page_ref}</span>}
                        </li>
                      ))}
                    </ul>
                  </div>
                )}

                {/* Staffing */}
                {flashData?.staffing_requirements?.length > 0 && (
                  <div className="doc-section">
                    <h2 className="doc-section-heading">Staffing Requirements</h2>
                    <ul className="doc-list">
                      {flashData.staffing_requirements.map((item, i) => (
                        <li key={i}>
                          {typeof item === "string" ? item : (
                            <>{item.role && <strong>{item.role}: </strong>}{item.details || item.item || ""}</>
                          )}
                          {item.page_ref && item.page_ref !== "N/A" && <span className="pg-ref">{item.page_ref}</span>}
                        </li>
                      ))}
                    </ul>
                  </div>
                )}

                {/* Risks */}
                {flashData?.risks?.length > 0 && (
                  <div className="doc-section">
                    <h2 className="doc-section-heading">Risks</h2>
                    <ul className="doc-list">
                      {flashData.risks.map((item, i) => (
                        <li key={i}>
                          {typeof item === "string" ? item : (
                            <>
                              {item.risk || item.item || ""}
                              {item.severity && (
                                <span className={`severity-badge sev-${(item.severity || "").toLowerCase()}`}>{item.severity}</span>
                              )}
                              {item.type && <span className="pg-ref">{item.type}</span>}
                              {item.source === "Inferred" && <span className="inferred-badge">Inferred</span>}
                            </>
                          )}
                          {item.page_ref && item.page_ref !== "N/A" && <span className="pg-ref">{item.page_ref}</span>}
                        </li>
                      ))}
                    </ul>
                  </div>
                )}

                {/* Compliance Table */}
                {flashData?.compliance_requirements?.length > 0 && (
                  <div className="doc-section">
                    <h2 className="doc-section-heading">Compliance Requirements</h2>
                    <div className="compliance-table-wrap">
                      <table className="compliance-table">
                        <thead>
                          <tr>
                            <th>#</th>
                            <th>Requirement</th>
                            <th>Category</th>
                            <th>Page</th>
                            <th>Mandatory</th>
                          </tr>
                        </thead>
                        <tbody>
                          {flashData.compliance_requirements.map((item, i) => (
                            <tr key={i}>
                              <td className="col-num">{i + 1}</td>
                              <td>{typeof item === "string" ? item : item.requirement || item.item || ""}</td>
                              <td>{item.category || "—"}</td>
                              <td>{item.page_ref && item.page_ref !== "N/A" ? item.page_ref : "—"}</td>
                              <td>
                                {item.mandatory === true
                                  ? <span className="mandatory-yes">✓ Yes</span>
                                  : item.mandatory === false
                                  ? <span className="mandatory-no">No</span>
                                  : "—"}
                              </td>
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    </div>
                  </div>
                )}

                {/* Key Highlights */}
                {flashData?.key_highlights?.length > 0 && (
                  <div className="doc-section">
                    <h2 className="doc-section-heading">Key Highlights</h2>
                    <ul className="doc-list">
                      {flashData.key_highlights.map((item, i) => (
                        <li key={i}>{typeof item === "string" ? item : item.item || JSON.stringify(item)}</li>
                      ))}
                    </ul>
                  </div>
                )}

              </div>{/* end doc-report */}

              {/* PDF report button */}
              <div className="report-row">
                <button className="report-btn-wide" onClick={() => generatePDFReport(flashData, activeTitle)}>
                  <I.Pdf /> Generate &amp; Download PDF Report
                </button>
              </div>

              {/* Chat panel — slides in when chatOpen */}
              {chatOpen && (
                <div className="chat-panel-inline">
                  <div className="chat-head">
                    <div style={{ display: "flex", alignItems: "center", gap: 10 }}>
                      <div className="chat-avatar"><I.Bot /></div>
                      <div>
                        <div className="chat-name">{activeTitle}</div>
                        <div className="chat-sub">AI-powered document Q&amp;A</div>
                      </div>
                    </div>
                    <div style={{ display: "flex", gap: 8, alignItems: "center" }}>
                      <div className="chat-status" title="Online" />
                      <button className="chat-close-btn" onClick={() => setChatOpen(false)} title="Close chat">
                        <I.X />
                      </button>
                    </div>
                  </div>

                  <div className="msgs">
                    {messages.length === 0
                      ? <div className="msgs-empty">
                          <div className="msgs-empty-icon"><I.Msg /></div>
                          <h4>Ask anything about this document</h4>
                          <p>Deadlines, compliance, scope, risks — ask away.</p>
                          <div className="chips">
                            {["Summarize key requirements", "What are the deadlines?", "List compliance needs", "Identify main risks"].map(q => (
                              <button key={q} className="chip" onClick={() => setQuestion(q)}>{q}</button>
                            ))}
                          </div>
                        </div>
                      : messages.map((m, i) => (
                          <div key={i} className={cx("msg-row", m.role === "user" && "user")}>
                            <div className={cx("msg-av", m.role === "assistant" ? "bot" : "usr")}>
                              {m.role === "assistant" ? <I.Bot /> : <I.User />}
                            </div>
                            <div className={cx("bubble", m.role === "user" ? "ubub" : "bbub")}>
                              {m.role === "assistant"
                                ? <div className="prose"><ReactMarkdown>{m.content}</ReactMarkdown></div>
                                : m.content}
                            </div>
                          </div>
                        ))
                    }
                    {chatLoading && (
                      <div className="typing-row">
                        <div className="msg-av bot"><I.Bot /></div>
                        <div className="typing-dots"><span /><span /><span /></div>
                      </div>
                    )}
                    <div ref={msgEndRef} />
                  </div>

                  <div className="chat-input-area">
                    <div className="chat-box">
                      <input className="chat-inp" type="text" value={question}
                        onChange={e => setQuestion(e.target.value)}
                        onKeyDown={e => e.key === "Enter" && !e.shiftKey && handleAsk()}
                        disabled={chatLoading}
                        placeholder="Ask about compliance, deadlines, scope, risks…" />
                      <button className="send-btn" onClick={handleAsk} disabled={!question.trim() || chatLoading}>
                        <I.Send />
                      </button>
                    </div>
                  </div>
                </div>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

// ── CSS ─────────────────────────────────────────────────────
const CSS = `
@import url('https://fonts.googleapis.com/css2?family=Playfair+Display:wght@600;700&family=Plus+Jakarta+Sans:wght@400;500;600;700&display=swap');

*,*::before,*::after{box-sizing:border-box;margin:0;padding:0;}

:root{
  --bg:#f0ede6;--bg-card:#fff;--bg-sidebar:#ffffff;
  --bg-si:rgba(0,0,0,0.04);--bg-sa:rgba(255,107,53,0.16);
  --border:#e0ddd6;--border-sb:#ece7de;
  --text-primary:#1a1512;--text-secondary:#7a7065;
  --text-sb:#6b7280;--text-sba:#1a1512;
  --accent:#FF6B35;--accent2:#4ECDC4;--accent3:#A78BFA;
  --accent-h:#e5521c;--accent-l:rgba(255,107,53,0.09);--accent-r:rgba(255,107,53,0.22);
  --header-bg:rgba(240,237,230,0.9);
  --msg-user:#1a1512;--msg-user-t:#fff;--msg-bot:#fff;--msg-bot-b:#e0ddd6;
  --inp-bg:#fff;--inp-b:#d4cfc8;
  --sh-sm:0 1px 4px rgba(0,0,0,0.07);--sh-md:0 4px 20px rgba(0,0,0,0.09);
  --sh-lg:0 12px 48px rgba(0,0,0,0.11);
  --r:16px;--rsm:10px;--rfull:9999px;
  --font-display:'Playfair Display',serif;--font-body:'Plus Jakarta Sans',sans-serif;
}
.dark{
  --bg:#0d0d10;--bg-card:#16161e;--bg-sidebar:#0a0a0e;
  --bg-si:rgba(255,255,255,0.04);--bg-sa:rgba(255,107,53,0.14);
  --border:rgba(255,255,255,0.08);--border-sb:rgba(255,255,255,0.05);
  --text-primary:#f2ede8;--text-secondary:#8a8075;
  --text-sb:rgba(255,255,255,0.5);
  --accent:#FF7A4D;--accent-h:#ff6b35;
  --accent-l:rgba(255,122,77,0.1);--accent-r:rgba(255,122,77,0.25);
  --header-bg:rgba(13,13,16,0.92);
  --msg-user:#FF7A4D;--msg-bot:#1c1c26;--msg-bot-b:rgba(255,255,255,0.08);
  --inp-bg:#1c1c26;--inp-b:rgba(255,255,255,0.1);
  --sh-sm:0 1px 3px rgba(0,0,0,0.35);--sh-md:0 4px 20px rgba(0,0,0,0.45);
  --sh-lg:0 12px 48px rgba(0,0,0,0.55);
}

.shell{display:flex;height:100vh;width:100%;overflow:hidden;background:var(--bg);
  color:var(--text-primary);font-family:var(--font-body);font-size:14px;line-height:1.6;
  transition:background .3s,color .3s;}

/* Sidebar */
.sidebar{width:258px;min-width:258px;background:var(--bg-sidebar);
  border-right:1px solid var(--border-sb);display:flex;flex-direction:column;
  transition:width .25s,min-width .25s;z-index:30;overflow:hidden;}
.sidebar.collapsed{width:62px;min-width:62px;}
.sb-logo{display:flex;align-items:center;gap:10px;padding:17px 15px;
  border-bottom:1px solid var(--border-sb);min-height:60px;}
.sb-logo-icon{width:33px;height:33px;border-radius:9px;flex-shrink:0;
  background:linear-gradient(135deg,#FF6B35,#FF9F5A);
  display:flex;align-items:center;justify-content:center;
  box-shadow:0 4px 12px rgba(255,107,53,0.35);}
  .sb-name{
  font-family:var(--font-display);
  font-weight:800;
  font-size:14px;
  color:var(--text-sba);
  white-space:nowrap;
  }
.sb-sub{font-size:10px;color:var(--text-sb);font-weight:400;letter-spacing:.1em;text-transform:uppercase;white-space:nowrap;}
.sb-new{margin:11px;background:linear-gradient(135deg,#FF6B35,#FF9F5A);color:#fff;border:none;
  border-radius:var(--rsm);padding:10px 13px;cursor:pointer;font-family:var(--font-body);
  font-size:13px;font-weight:600;display:flex;align-items:center;justify-content:center;
  gap:7px;transition:opacity .2s,transform .15s;white-space:nowrap;overflow:hidden;
  box-shadow:0 4px 14px rgba(255,107,53,0.32);}
.sb-new:hover{opacity:.88;transform:translateY(-1px);}
.sb-label{padding:8px 15px 5px;font-size:10px;font-weight:700;letter-spacing:.12em;
  text-transform:uppercase;color:rgba(255,255,255,0.2);white-space:nowrap;}
.sb-list{flex:1;overflow-y:auto;padding:4px 7px;}
.sb-list::-webkit-scrollbar{width:3px;}
.sb-list::-webkit-scrollbar-thumb{background:rgba(255,255,255,0.07);border-radius:3px;}
.sb-empty{margin:6px;padding:18px 10px;text-align:center;border:1px dashed rgba(255,255,255,0.1);
  border-radius:var(--rsm);color:rgba(255,255,255,0.22);font-size:12px;line-height:1.6;}
.sb-item-wrap{position:relative;display:flex;align-items:center;border-radius:var(--rsm);transition:background .15s;}
.sb-item-wrap:hover,.sb-item-wrap.active{background:var(--bg-si);}
.sb-item-wrap.active{background:var(--bg-sa);}
.sb-item{display:flex;align-items:center;gap:9px;padding:8px 9px;flex:1;
  border:none;background:transparent;cursor:pointer;color:var(--text-sb);
  font-family:var(--font-body);font-size:12.5px;text-align:left;overflow:hidden;border-radius:var(--rsm);}
.sb-item-wrap.active .sb-item{color:var(--text-sba);}
.sb-item-icon{width:26px;height:26px;border-radius:7px;background:rgba(255,255,255,0.06);
  display:flex;align-items:center;justify-content:center;flex-shrink:0;}
.sb-item-wrap.active .sb-item-icon{background:rgba(255,107,53,0.2);}
.sb-item-title{overflow:hidden;text-overflow:ellipsis;white-space:nowrap;flex:1;}
.sb-more{width:26px;height:26px;border:none;background:transparent;cursor:pointer;
  color:var(--text-sb);display:flex;align-items:center;justify-content:center;
  border-radius:6px;flex-shrink:0;margin-right:4px;transition:color .15s,background .15s;}
.sb-more:hover{ color:var(--text-primary);
  background:rgba(0,0,0,0.05);}
.rename-form{flex:1;padding:4px 6px;}
.rename-input{width:100%;background:rgba(255,255,255,0.08);border:1px solid rgba(255,255,255,0.15);
  border-radius:6px;padding:5px 8px;color:#fff;font-family:var(--font-body);font-size:12.5px;outline:none;}
.rename-input:focus{border-color:var(--accent);}
.sb-footer{padding:11px;border-top:1px solid var(--border-sb);}
.sb-collapse{width:100%;display:flex;align-items:center;justify-content:flex-start;gap:7px;
  padding:7px 9px;border-radius:var(--rsm);border:none;background:transparent;cursor:pointer;
  color:var(--text-sb);font-size:12px;font-family:var(--font-body);transition:color .2s;}
.sidebar.collapsed .sb-collapse{justify-content:center;}
.sb-collapse:hover{color:var(--text-primary);}

/* Context menu */
.ctx-menu{position:fixed;z-index:999;background:var(--bg-card);border:1px solid var(--border);
  border-radius:var(--rsm);box-shadow:var(--sh-lg);padding:5px;min-width:130px;
  animation:ctxIn .15s ease-out;}
@keyframes ctxIn{from{opacity:0;transform:scale(.95) translateY(-4px)}to{opacity:1;transform:scale(1)}}
.ctx-item{width:100%;display:flex;align-items:center;gap:8px;padding:7px 10px;
  border:none;background:transparent;cursor:pointer;color:var(--text-primary);
  font-family:var(--font-body);font-size:12.5px;border-radius:7px;transition:background .15s;}
.ctx-item:hover{background:var(--accent-l);color:var(--accent);}
.ctx-item.danger{color:#ef4444;}
.ctx-item.danger:hover{background:rgba(239,68,68,0.09);}
.ctx-sep{height:1px;background:var(--border);margin:4px 0;}

/* Modal */
.modal-bg{position:fixed;inset:0;background:rgba(0,0,0,0.55);z-index:998;
  backdrop-filter:blur(4px);display:flex;align-items:center;justify-content:center;}
.modal{background:var(--bg-card);border:1px solid var(--border);border-radius:var(--r);
  padding:28px 24px;max-width:340px;width:90%;display:flex;flex-direction:column;
  align-items:center;text-align:center;box-shadow:var(--sh-lg);}
.btn-ghost{padding:9px 18px;border:1px solid var(--border);border-radius:var(--rsm);
  background:transparent;color:var(--text-secondary);font-family:var(--font-body);
  font-size:13px;font-weight:600;cursor:pointer;transition:all .2s;}
.btn-ghost:hover{border-color:var(--text-secondary);}
.btn-danger{padding:9px 18px;border:none;border-radius:var(--rsm);
  background:linear-gradient(135deg,#ef4444,#dc2626);color:#fff;
  font-family:var(--font-body);font-size:13px;font-weight:700;cursor:pointer;
  box-shadow:0 4px 12px rgba(239,68,68,0.35);transition:opacity .2s,transform .15s;}
.btn-danger:hover{opacity:.88;transform:translateY(-1px);}

/* Header */
.main{flex:1;display:flex;flex-direction:column;overflow:hidden;min-width:0;}
.header{height:55px;background:var(--header-bg);backdrop-filter:blur(16px);
  border-bottom:1px solid var(--border);display:flex;align-items:center;
  justify-content:space-between;padding:0 22px;flex-shrink:0;
  transition:background .3s,border-color .3s;}
.header-title{font-family:var(--font-display);font-weight:700;font-size:14.5px;
  color:var(--text-primary);display:flex;align-items:center;gap:6px;}
.mob-menu{display:none;width:34px;height:34px;align-items:center;justify-content:center;
  border-radius:var(--rsm);border:1px solid var(--border);background:var(--bg-card);
  cursor:pointer;color:var(--text-secondary);}
.theme-btn{width:34px;height:34px;border-radius:var(--rsm);border:1px solid var(--border);
  background:var(--bg-card);cursor:pointer;display:flex;align-items:center;
  justify-content:center;color:var(--text-secondary);transition:all .2s;}
.theme-btn:hover{background:var(--accent-l);border-color:var(--accent);color:var(--accent);}
.btn-report{display:flex;align-items:center;gap:7px;padding:8px 14px;
  background:linear-gradient(135deg,#FF6B35,#FF9F5A);color:#fff;border:none;
  border-radius:var(--rsm);font-family:var(--font-body);font-size:12px;font-weight:700;
  cursor:pointer;box-shadow:0 3px 12px rgba(255,107,53,0.32);transition:opacity .2s,transform .15s;}
.btn-report:hover{opacity:.88;transform:translateY(-1px);}

/* Toast */
.toast{position:fixed;top:18px;left:50%;transform:translateX(-50%);z-index:9999;
  display:flex;align-items:center;gap:9px;padding:9px 18px;border-radius:var(--rfull);
  font-size:13px;font-weight:600;box-shadow:var(--sh-lg);white-space:nowrap;
  animation:toastIn .3s cubic-bezier(.34,1.56,.64,1);}
@keyframes toastIn{from{opacity:0;transform:translateX(-50%) translateY(-14px) scale(.9)}
  to{opacity:1;transform:translateX(-50%) translateY(0) scale(1)}}
.toast-error{background:#fff0ee;color:#c0392b;border:1px solid #ffccc7;}
.toast-success{background:#edfff9;color:#0d6e4e;border:1px solid #9effd5;}
.toast-warning{background:#fffbec;color:#8a5d00;border:1px solid #ffe58f;}
.dark .toast-error{background:#2d1010;color:#ff8a80;border-color:#7f1d1d;}
.dark .toast-success{background:#0b2e1f;color:#6ee7b7;border-color:#064e3b;}
.dark .toast-warning{background:#2d1f00;color:#fcd34d;border-color:#78350f;}

/* Upload screen */
.content{flex:1;overflow-y:auto;padding:16px;}
.upload-wrap{height:100%;display:flex;align-items:center;justify-content:center;padding:16px;}
.upload-card{width:100%;max-width:580px;background:var(--bg-card);border:1px solid var(--border);
  border-radius:22px;overflow:hidden;box-shadow:var(--sh-lg);position:relative;
  transition:background .3s,border-color .3s;}
.upload-blob{position:absolute;border-radius:50%;filter:blur(60px);pointer-events:none;}
.b1{width:220px;height:220px;top:-70px;right:-60px;
  background:linear-gradient(135deg,#FF6B35,#FF9F5A);opacity:.07;}
.b2{width:180px;height:180px;bottom:-60px;left:-40px;
  background:linear-gradient(135deg,#4ECDC4,#A78BFA);opacity:.06;}
.upload-inner{padding:36px 34px;position:relative;}
.upload-badge{display:inline-flex;align-items:center;gap:6px;padding:4px 12px;
  background:var(--accent-l);color:var(--accent);border-radius:var(--rfull);
  font-size:11px;font-weight:700;letter-spacing:.07em;text-transform:uppercase;
  margin-bottom:14px;border:1px solid var(--accent-r);}
.upload-title{font-family:var(--font-display);font-size:26px;font-weight:800;
  color:var(--text-primary);margin-bottom:8px;line-height:1.15;}
.upload-desc{font-size:13px;color:var(--text-secondary);line-height:1.65;margin-bottom:20px;}

/* Mode tabs */
.mode-tabs{display:flex;gap:6px;margin-bottom:16px;background:var(--bg);
  border-radius:var(--rsm);padding:4px;border:1px solid var(--border);}
.mode-tab{flex:1;display:flex;align-items:center;justify-content:center;gap:6px;
  padding:8px 12px;border-radius:7px;border:none;background:transparent;
  font-family:var(--font-body);font-size:12.5px;font-weight:600;cursor:pointer;
  color:var(--text-secondary);transition:all .2s;}
.mode-tab.active{background:var(--bg-card);color:var(--accent);
  box-shadow:0 2px 8px rgba(0,0,0,0.08);border:1px solid var(--accent-r);}

/* Text input */
.text-input-wrap{border:2px solid var(--border);border-radius:var(--r);
  overflow:hidden;transition:border-color .2s;background:var(--bg);}
.text-input-wrap:focus-within{border-color:var(--accent);}
.text-inp{width:100%;border:none;background:transparent;padding:14px 16px;
  font-family:var(--font-body);font-size:13px;color:var(--text-primary);
  resize:none;outline:none;line-height:1.65;}
.text-inp::placeholder{color:var(--text-secondary);}
.text-inp-meta{display:flex;align-items:center;justify-content:space-between;
  padding:7px 12px;border-top:1px solid var(--border);background:var(--bg-card);}
.text-count{font-size:11px;color:var(--accent);font-weight:600;}
.text-hint{font-size:11px;color:var(--text-secondary);font-style:italic;}
.text-clear{display:flex;align-items:center;gap:4px;border:none;background:transparent;
  font-family:var(--font-body);font-size:11px;color:var(--text-secondary);cursor:pointer;
  padding:3px 7px;border-radius:5px;transition:all .15s;}
.text-clear:hover{color:#ef4444;background:rgba(239,68,68,0.08);}

/* Dropzone */
.dropzone{border:2px dashed var(--border);border-radius:var(--r);padding:28px 24px;
  display:flex;flex-direction:column;align-items:center;justify-content:center;
  text-align:center;cursor:pointer;transition:all .2s;background:var(--bg);}
.dropzone:hover,.dropzone.drag-over{border-color:var(--accent);background:var(--accent-l);}
.dropzone.has-file{border-style:solid;border-color:var(--accent);background:var(--accent-l);}
.dz-icon{color:var(--accent);margin-bottom:10px;opacity:.85;}
.dz-title{font-weight:700;font-size:14.5px;color:var(--text-primary);margin-bottom:4px;}
.dz-sub{font-size:12.5px;color:var(--text-secondary);margin-bottom:12px;}
.dz-browse{color:var(--accent);font-weight:600;text-decoration:underline;text-underline-offset:2px;}
.dz-formats{display:flex;gap:8px;}
.fmt-badge{padding:3px 10px;border-radius:var(--rfull);border:1px solid var(--border);
  font-size:10.5px;font-weight:700;color:var(--text-secondary);letter-spacing:.06em;}
.file-preview{display:flex;align-items:center;gap:12px;width:100%;}
.file-preview-icon{font-size:28px;flex-shrink:0;}
.file-preview-info{flex:1;text-align:left;overflow:hidden;}
.file-preview-name{font-weight:700;font-size:13.5px;color:var(--text-primary);
  overflow:hidden;text-overflow:ellipsis;white-space:nowrap;}
.file-preview-size{font-size:11px;color:var(--text-secondary);margin-top:2px;}
.file-remove{width:28px;height:28px;border-radius:50%;border:1px solid var(--border);
  background:var(--bg-card);cursor:pointer;display:flex;align-items:center;
  justify-content:center;color:var(--text-secondary);flex-shrink:0;transition:all .2s;}
.file-remove:hover{border-color:#ef4444;color:#ef4444;}

.btn-analyze{width:100%;margin-top:16px;padding:13px 20px;
  background:linear-gradient(135deg,#FF6B35,#FF9F5A);color:#fff;border:none;
  border-radius:var(--rsm);font-family:var(--font-body);font-size:14.5px;font-weight:700;
  cursor:pointer;box-shadow:0 4px 20px rgba(255,107,53,0.38);transition:opacity .2s,transform .15s;}
.btn-analyze:hover{opacity:.9;transform:translateY(-1px);}

.loading-state{margin-top:16px;}
.loading-bar{height:4px;background:var(--border);border-radius:2px;overflow:hidden;margin-bottom:10px;}
.loading-fill{height:100%;width:60%;background:linear-gradient(90deg,#FF6B35,#FF9F5A,#4ECDC4);
  border-radius:2px;animation:loadBar 1.8s ease-in-out infinite;}
@keyframes loadBar{0%{transform:translateX(-100%)}100%{transform:translateX(250%)}}
.loading-msg{display:flex;align-items:center;gap:8px;font-size:13px;color:var(--text-secondary);
  font-weight:500;justify-content:center;}

/* Results screen */
.results-wrap{display:flex;flex-direction:column;gap:14px;max-width:960px;margin:0 auto;width:100%;}
.results-topbar{display:flex;align-items:center;justify-content:space-between;
  background:var(--bg-card);border:1px solid var(--border);border-radius:var(--rsm);
  padding:11px 16px;flex-wrap:wrap;gap:10px;}
.results-meta{flex:1;min-width:0;}
.results-title-row{display:flex;align-items:center;gap:8px;}
.results-title{font-family:var(--font-display);font-size:13.5px;font-weight:700;
  color:var(--text-primary);overflow:hidden;text-overflow:ellipsis;white-space:nowrap;max-width:280px;}
.results-badge{padding:2px 9px;border-radius:var(--rfull);
  background:rgba(34,211,162,0.12);color:#0d9e6e;border:1px solid rgba(34,211,162,0.25);
  font-size:10px;font-weight:700;letter-spacing:.06em;text-transform:uppercase;flex-shrink:0;}
.dark .results-badge{color:#34d399;background:rgba(52,211,153,0.1);}
.results-doc-type-large{display:inline-flex;align-items:center;gap:6px;margin-top:8px;
  font-size:13.5px;font-weight:600;color:var(--text-secondary);background:var(--accent-l);
  border:1px solid var(--accent-r);padding:5px 12px;border-radius:var(--rsm);margin-bottom:4px;}
.results-doc-type-large strong{color:var(--accent);font-size:16px;font-weight:800;text-transform:uppercase;}

/* Compact re-upload in topbar */
.strip-dropzone-sm{display:inline-flex;align-items:center;gap:6px;padding:7px 12px;
  border:1.5px dashed var(--border);border-radius:var(--rsm);
  background:var(--bg);color:var(--text-secondary);font-size:12px;font-weight:500;
  cursor:pointer;transition:all .2s;}
.strip-dropzone-sm:hover,.strip-dropzone-sm.drag-over{border-color:var(--accent);
  color:var(--accent);background:var(--accent-l);}

/* Chat toggle button */
.btn-chat-toggle{display:flex;align-items:center;gap:7px;padding:8px 14px;
  background:linear-gradient(135deg,#FF6B35,#FF9F5A);color:#fff;border:none;
  border-radius:var(--rsm);font-family:var(--font-body);font-size:12.5px;font-weight:700;
  cursor:pointer;box-shadow:0 3px 12px rgba(255,107,53,0.28);transition:opacity .2s,transform .15s;}
.btn-chat-toggle:hover{opacity:.88;transform:translateY(-1px);}

/* Cards grid */
.cards-grid{display:grid;grid-template-columns:repeat(2,1fr);gap:12px;}

/* Report row */
.report-row{display:flex;justify-content:flex-start;}
.report-btn-wide{display:inline-flex;align-items:center;gap:7px;padding:9px 18px;
  background:transparent;border:1.5px solid var(--accent);color:var(--accent);
  border-radius:var(--rsm);font-family:var(--font-body);font-size:12.5px;font-weight:700;
  cursor:pointer;transition:all .2s;}
.report-btn-wide:hover{background:var(--accent);color:#fff;box-shadow:0 4px 14px rgba(255,107,53,0.35);}

/* Chat panel inline */
.chat-panel-inline{background:var(--bg-card);border:1px solid var(--border);
  border-radius:var(--r);display:flex;flex-direction:column;
  box-shadow:var(--sh-md);min-height:420px;max-height:520px;
  animation:slideDown .25s cubic-bezier(.34,1.16,.64,1);}
@keyframes slideDown{from{opacity:0;transform:translateY(-12px)}to{opacity:1;transform:translateY(0)}}

.chat-head{padding:13px 18px;border-bottom:1px solid var(--border);flex-shrink:0;
  display:flex;align-items:center;justify-content:space-between;}
.chat-avatar{width:32px;height:32px;border-radius:9px;
  background:linear-gradient(135deg,#FF6B35,#FF9F5A);
  display:flex;align-items:center;justify-content:center;color:#fff;
  box-shadow:0 3px 10px rgba(255,107,53,0.28);}
.chat-name{font-family:var(--font-display);font-size:13.5px;font-weight:800;color:var(--text-primary);}
.chat-sub{font-size:11px;color:var(--text-secondary);}
.chat-status{width:8px;height:8px;border-radius:50%;background:#22d3a2;
  box-shadow:0 0 0 3px rgba(34,211,162,0.2);animation:pulse 2s infinite;}
@keyframes pulse{0%,100%{box-shadow:0 0 0 3px rgba(34,211,162,0.18)}
  50%{box-shadow:0 0 0 5px rgba(34,211,162,0.08)}}
.chat-close-btn{width:28px;height:28px;border-radius:7px;border:1px solid var(--border);
  background:transparent;cursor:pointer;display:flex;align-items:center;justify-content:center;
  color:var(--text-secondary);transition:all .2s;}
.chat-close-btn:hover{border-color:#ef4444;color:#ef4444;}

.msgs{flex:1;overflow-y:auto;padding:14px;display:flex;flex-direction:column;gap:11px;}
.msgs::-webkit-scrollbar{width:4px;}
.msgs::-webkit-scrollbar-thumb{background:var(--border);border-radius:4px;}
.msgs-empty{flex:1;display:flex;flex-direction:column;align-items:center;
  justify-content:center;text-align:center;color:var(--text-secondary);gap:9px;}
.msgs-empty-icon{width:48px;height:48px;border-radius:14px;
  background:linear-gradient(135deg,rgba(255,107,53,.1),rgba(255,159,90,.06));
  border:1px solid rgba(255,107,53,.18);
  display:flex;align-items:center;justify-content:center;color:var(--accent);}
.msgs-empty h4{font-size:13.5px;font-weight:700;color:var(--text-primary);font-family:var(--font-display);}
.msgs-empty p{font-size:12px;max-width:220px;line-height:1.6;}
.chips{display:flex;flex-wrap:wrap;gap:6px;justify-content:center;margin-top:4px;}
.chip{padding:6px 12px;border:1px solid var(--border);border-radius:var(--rfull);
  font-size:11.5px;cursor:pointer;background:var(--bg);color:var(--text-secondary);
  transition:all .2s;font-family:var(--font-body);font-weight:500;}
.chip:hover{border-color:var(--accent);color:var(--accent);background:var(--accent-l);transform:translateY(-1px);}
.msg-row{display:flex;gap:9px;}
.msg-row.user{flex-direction:row-reverse;}
.msg-av{width:27px;height:27px;border-radius:8px;display:flex;align-items:center;
  justify-content:center;flex-shrink:0;margin-top:2px;}
.msg-av.bot{background:linear-gradient(135deg,#FF6B35,#FF9F5A);color:#fff;}
.msg-av.usr{background:var(--bg);border:1px solid var(--border);color:var(--text-secondary);}
.bubble{max-width:76%;padding:10px 13px;border-radius:12px;font-size:13px;line-height:1.65;box-shadow:var(--sh-sm);}
.ubub{background:var(--msg-user);color:var(--msg-user-t);border-radius:12px 4px 12px 12px;}
.bbub{background:var(--msg-bot);border:1px solid var(--msg-bot-b);
  color:var(--text-primary);border-radius:4px 12px 12px 12px;transition:background .3s;}
.prose p{margin:0 0 8px}.prose p:last-child{margin:0}
.prose ul{padding-left:16px;margin:5px 0}.prose li{margin-bottom:3px}
.prose code{background:var(--bg);padding:1px 5px;border-radius:4px;font-size:12px;border:1px solid var(--border);}
.typing-row{display:flex;gap:9px;}
.typing-dots{display:flex;align-items:center;gap:4px;padding:11px 13px;
  background:var(--msg-bot);border:1px solid var(--msg-bot-b);
  border-radius:4px 12px 12px 12px;box-shadow:var(--sh-sm);}
.typing-dots span{width:6px;height:6px;border-radius:50%;background:var(--accent);
  display:block;animation:bounce 1.2s ease-in-out infinite;}
.typing-dots span:nth-child(2){animation-delay:.15s}
.typing-dots span:nth-child(3){animation-delay:.3s}
@keyframes bounce{0%,60%,100%{transform:translateY(0);opacity:.4}30%{transform:translateY(-6px);opacity:1}}
.chat-input-area{padding:10px 12px;border-top:1px solid var(--border);flex-shrink:0;}
.chat-box{display:flex;align-items:center;gap:9px;background:var(--inp-bg);
  border:1.5px solid var(--inp-b);border-radius:11px;padding:7px 7px 7px 13px;
  transition:border-color .2s,box-shadow .2s;}
.chat-box:focus-within{border-color:var(--accent);box-shadow:0 0 0 3px var(--accent-r);}
.chat-inp{flex:1;border:none;background:transparent;outline:none;
  font-family:var(--font-body);font-size:13px;color:var(--text-primary);min-width:0;}
.chat-inp::placeholder{color:var(--text-secondary);}
.send-btn{width:32px;height:32px;border-radius:8px;
  background:linear-gradient(135deg,#FF6B35,#FF9F5A);color:#fff;border:none;
  cursor:pointer;display:flex;align-items:center;justify-content:center;
  transition:opacity .2s,transform .15s;flex-shrink:0;
  box-shadow:0 3px 10px rgba(255,107,53,0.28);}
.send-btn:hover:not(:disabled){opacity:.88;transform:scale(1.06);}
.send-btn:disabled{background:var(--border);color:var(--text-secondary);cursor:not-allowed;box-shadow:none;}

.overlay{display:none;position:fixed;inset:0;background:rgba(0,0,0,0.52);z-index:25;backdrop-filter:blur(4px);}
.spin{animation:spin .8s linear infinite;}
@keyframes spin{to{transform:rotate(360deg)}}
::-webkit-scrollbar{width:5px;height:5px}
::-webkit-scrollbar-track{background:transparent}
::-webkit-scrollbar-thumb{background:var(--border);border-radius:6px}

@media(max-width:768px){
  .sidebar{position:fixed;top:0;left:0;bottom:0;transform:translateX(-100%);
    width:280px!important;min-width:280px!important;}
  .sidebar.mob-open{transform:translateX(0);}
  .overlay{display:block;}
  .mob-menu{display:flex;}
  .cards-grid{grid-template-columns:1fr;}
  .content{padding:10px;}
  .header{padding:0 13px;}
  .results-topbar{flex-direction:column;align-items:flex-start;}
}
@media(max-width:480px){.bubble{max-width:88%;}.upload-inner{padding:24px 20px;}}

/* ── Document Report Layout styles ── */
.dl-inline-btn {
  display: inline-flex;
  align-items: center;
  gap: 5px;
  padding: 4px 10px;
  border-radius: 6px;
  background: var(--bg);
  border: 1px solid var(--border);
  color: var(--text-secondary);
  font-size: 11px;
  font-weight: 600;
  text-decoration: none;
  transition: all 0.2s ease;
  margin-left: 8px;
}
.dl-inline-btn:hover {
  border-color: var(--accent);
  color: var(--accent);
  background: var(--accent-l);
  transform: translateY(-1px);
}
.doc-report {
  display: flex;
  flex-direction: column;
  gap: 20px;
  background: var(--bg-card);
  border: 1px solid var(--border);
  border-radius: var(--r);
  padding: 24px;
  box-shadow: var(--sh-sm);
}
.doc-section {
  padding-bottom: 20px;
  border-bottom: 1px solid var(--border);
}
.doc-section:last-child {
  border-bottom: none;
  padding-bottom: 0;
}
.doc-section-heading {
  font-family: var(--font-display);
  font-size: 18px;
  font-weight: 700;
  color: var(--text-primary);
  margin-bottom: 12px;
  border-left: 3px solid var(--accent);
  padding-left: 10px;
}
.doc-section-prose {
  font-size: 14px;
  line-height: 1.7;
  color: var(--text-secondary);
  white-space: pre-wrap;
}
.doc-list {
  list-style: none;
  padding-left: 0;
  display: flex;
  flex-direction: column;
  gap: 8px;
}
.doc-list li {
  position: relative;
  padding-left: 20px;
  font-size: 13.5px;
  color: var(--text-secondary);
  line-height: 1.6;
}
.doc-list li::before {
  content: "•";
  position: absolute;
  left: 5px;
  color: var(--accent);
  font-weight: bold;
}
.pg-ref {
  display: inline-block;
  font-size: 10px;
  font-weight: 700;
  background: var(--accent-l);
  color: var(--accent);
  padding: 1px 6px;
  border-radius: 4px;
  margin-left: 8px;
  white-space: nowrap;
}
.severity-badge {
  display: inline-block;
  font-size: 9px;
  font-weight: 800;
  padding: 1px 6px;
  border-radius: 4px;
  text-transform: uppercase;
  margin-left: 8px;
}
.sev-high {
  background: rgba(239, 68, 68, 0.12);
  color: #ef4444;
}
.sev-medium {
  background: rgba(245, 158, 11, 0.12);
  color: #f59e0b;
}
.sev-low {
  background: rgba(34, 197, 94, 0.12);
  color: #22c55e;
}
.inferred-badge {
  display: inline-block;
  font-size: 9px;
  font-weight: 800;
  padding: 1px 6px;
  border-radius: 4px;
  background: rgba(167, 139, 250, 0.12);
  color: #a78bfa;
  text-transform: uppercase;
  margin-left: 8px;
}
.compliance-table-wrap {
  width: 100%;
  overflow-x: auto;
  border: 1px solid var(--border);
  border-radius: var(--rsm);
  margin-top: 10px;
}
.compliance-table {
  width: 100%;
  border-collapse: collapse;
  font-size: 13px;
  text-align: left;
}
.compliance-table th {
  background: var(--bg);
  color: var(--text-primary);
  font-weight: 600;
  padding: 10px 14px;
  border-bottom: 1.5px solid var(--border);
}
.compliance-table td {
  padding: 10px 14px;
  border-bottom: 1px solid var(--border);
  color: var(--text-secondary);
  line-height: 1.5;
}
.compliance-table tr:last-child td {
  border-bottom: none;
}
.compliance-table .col-num {
  font-weight: 700;
  color: var(--text-primary);
  width: 40px;
}
.compliance-table .mandatory-yes {
  color: #22c55e;
  font-weight: 700;
}
.compliance-table .mandatory-no {
  color: var(--text-secondary);
}
`;