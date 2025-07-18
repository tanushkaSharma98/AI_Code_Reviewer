import React, { useState, useRef, useEffect } from "react";
import MonacoEditor from "@monaco-editor/react";
import StatusDisplay from "../components/StatusDisplay";
import Spinner from "../components/Spinner";
import { pasteSchema, zipSchema, githubSchema } from "../utils/validation";

function getLanguageFromFilename(filename: string) {
  if (filename.endsWith('.py')) return 'python';
  if (filename.endsWith('.js')) return 'javascript';
  if (filename.endsWith('.java')) return 'java';
  if (filename.endsWith('.c')) return 'c';
  if (filename.endsWith('.cpp')) return 'cpp';
  if (filename.endsWith('.md')) return 'markdown';
  if (filename.endsWith('.ts')) return 'typescript';
  return 'plaintext';
}

const TABS = ["Paste Code", "Upload ZIP", "GitHub Repo"] as const;
type Tab = typeof TABS[number];

type Status = {
  status: string;
  download_url?: string;
  [key: string]: any;
};

const API_BASE = import.meta.env.VITE_API_BASE || "http://localhost:5000";

const Home: React.FC = () => {
  const [tab, setTab] = useState<Tab>("Paste Code");
  const [code, setCode] = useState("");
  const [filename, setFilename] = useState("main.py");
  const [zipFile, setZipFile] = useState<File | null>(null);
  const [githubUrl, setGithubUrl] = useState("");
  const [errors, setErrors] = useState<string[]>([]);
  const [sessionId, setSessionId] = useState<string | null>(null);
  const [status, setStatus] = useState<Status | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [isPolling, setIsPolling] = useState(false);
  const statusInterval = useRef<NodeJS.Timeout | null>(null);
  const [maxZipSizeMB, setMaxZipSizeMB] = useState(5);
  const [maxZipSizeBytes, setMaxZipSizeBytes] = useState(5 * 1024 * 1024);
  const [review, setReview] = useState<any>(null);
  const [copyMsg, setCopyMsg] = useState<string | null>(null);
  const [showLinter, setShowLinter] = useState(false);
  const [expandedIssue, setExpandedIssue] = useState<number | null>(null);
  const chatFeedRef = useRef<HTMLDivElement>(null);

  React.useEffect(() => {
    fetch(`${API_BASE}/config`).then(async (res) => {
      if (res.ok) {
        const data = await res.json();
        setMaxZipSizeMB(data.max_zip_size_mb || 5);
        setMaxZipSizeBytes(data.max_zip_size_bytes || 5 * 1024 * 1024);
      }
    }).catch(() => {
      setMaxZipSizeMB(5);
      setMaxZipSizeBytes(5 * 1024 * 1024);
    });
  }, []);

  React.useEffect(() => {
    if (sessionId && status?.status === "complete") {
      fetch(`${API_BASE}/review/${sessionId}`)
        .then((res) => res.json())
        .then((data) => setReview(data));
    }
  }, [sessionId, status]);

  useEffect(() => {
    if (chatFeedRef.current) {
      chatFeedRef.current.scrollTop = chatFeedRef.current.scrollHeight;
    }
  }, [review]);

  const handleTab = (t: Tab) => {
    setTab(t);
    setErrors([]);
    setSessionId(null);
    setStatus(null);
    setIsPolling(false);
  };

  const validate = () => {
    try {
      if (tab === "Paste Code") {
        pasteSchema.parse({ code, filename });
      } else if (tab === "Upload ZIP") {
        if (!zipFile) throw new Error("ZIP file is required");
        if (zipFile.size > maxZipSizeBytes) throw new Error(`ZIP file too large (max ${maxZipSizeMB}MB).`);
        zipSchema.parse({ zip: zipFile });
      } else if (tab === "GitHub Repo") {
        githubSchema.parse({ github_url: githubUrl });
      }
      setErrors([]);
      return true;
    } catch (e: any) {
      setErrors([e.errors?.[0]?.message || e.message]);
      return false;
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!validate()) return;
    setIsSubmitting(true);
    setErrors([]);
    setSessionId(null);
    setStatus(null);
    setIsPolling(false);
    try {
      let formData = new FormData();
      if (tab === "Paste Code") {
        formData.append("code", code);
        formData.append("filename", filename);
      } else if (tab === "Upload ZIP" && zipFile) {
        formData.append("zip", zipFile);
      } else if (tab === "GitHub Repo") {
        formData.append("github_url", githubUrl);
      }
      const res = await fetch(`${API_BASE}/submit`, {
        method: "POST",
        body: formData,
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.error || "Submission failed");
      setSessionId(data.session_id);
      setIsPolling(true);
      pollStatus(data.session_id);
    } catch (err: any) {
      setErrors([err.message]);
    } finally {
      setIsSubmitting(false);
    }
  };

  const pollStatus = (id: string) => {
    if (statusInterval.current) clearInterval(statusInterval.current);
    statusInterval.current = setInterval(async () => {
      try {
        const res = await fetch(`${API_BASE}/status/${id}`);
        const data = await res.json();
        setStatus(data);
        if (data.status === "complete" || data.status === "not found") {
          setIsPolling(false);
          if (statusInterval.current) clearInterval(statusInterval.current);
        }
      } catch {
        // ignore
      }
    }, 2000);
  };

  const handleDownload = () => {
    if (!sessionId || !status?.download_url) return;
    window.open(`${API_BASE}${status.download_url}`, "_blank");
  };

  const handleCopy = async (text: string) => {
    await navigator.clipboard.writeText(text);
    setCopyMsg("Copied!");
    setTimeout(() => setCopyMsg(null), 1200);
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-gray-100 flex flex-col items-center py-8">
      <div className="w-full max-w-screen-2xl bg-white rounded-lg shadow-xl p-8 px-12">
        <h1 className="text-3xl font-bold mb-2 text-center text-blue-700">AI Code Reviewer</h1>
        <p className="text-center text-gray-500 mb-6">Paste code, upload a ZIP, or enter a GitHub repo to get an instant AI-powered review and patch!</p>
        <div className="flex space-x-2 mb-6 justify-center">
          {TABS.map((t) => (
            <button
              key={t}
              className={`px-4 py-2 rounded-t font-semibold border-b-2 transition-all ${
                tab === t
                  ? "border-blue-500 text-blue-600 bg-blue-50"
                  : "border-transparent text-gray-500 bg-gray-100 hover:bg-gray-200"
              }`}
              onClick={() => handleTab(t)}
            >
              {t}
            </button>
          ))}
        </div>
        <form onSubmit={handleSubmit} className="space-y-4">
          {tab === "Paste Code" && (
            <>
              <label className="block font-medium mb-1">Filename <span className="text-gray-400 text-xs">(e.g. main.py, app.js)</span></label>
              <input
                className="w-full border rounded px-3 py-2 mb-2"
                value={filename}
                onChange={(e) => setFilename(e.target.value)}
                placeholder="main.py"
                required
              />
              <label className="block font-medium mb-1">Code</label>
              <div className="h-48 border rounded mb-2">
                <MonacoEditor
                  height="100%"
                  defaultLanguage="python"
                  value={code}
                  onChange={(v) => setCode(v || "")}
                  options={{ fontSize: 14, minimap: { enabled: false } }}
                />
              </div>
              <p className="text-xs text-gray-400 mb-2">Supports Python, JS, Java, C, C++ and more.</p>
            </>
          )}
          {tab === "Upload ZIP" && (
            <>
              <label className="block font-medium mb-1">ZIP File</label>
              <input
                type="file"
                accept=".zip"
                className="w-full border rounded px-3 py-2"
                onChange={(e) => setZipFile(e.target.files?.[0] || null)}
                required
              />
              <p className="text-xs text-gray-400 mb-2">Max size: {maxZipSizeMB}MB (configurable).</p>
            </>
          )}
          {tab === "GitHub Repo" && (
            <>
              <label className="block font-medium mb-1">GitHub Repository URL</label>
              <input
                className="w-full border rounded px-3 py-2"
                value={githubUrl}
                onChange={(e) => setGithubUrl(e.target.value)}
                placeholder="https://github.com/user/repo"
                required
              />
              <p className="text-xs text-gray-400 mb-2">Only public repositories are supported.</p>
            </>
          )}
          {errors.length > 0 && (
            <div className="bg-red-100 text-red-700 px-4 py-2 rounded">
              {errors.map((err, i) => (
                <div key={i}>{err}</div>
              ))}
            </div>
          )}
          <button
            type="submit"
            className="w-full bg-blue-600 text-white py-2 rounded font-semibold hover:bg-blue-700 transition"
            disabled={isSubmitting}
          >
            {isSubmitting ? <Spinner /> : "Submit"}
          </button>
        </form>
        {isPolling && (
          <div className="mt-4 flex items-center justify-center">
            <Spinner />
            <span className="ml-2 text-blue-500 font-medium">Review in progress...</span>
          </div>
        )}
        {sessionId && !isPolling && (
          <StatusDisplay
            status={status?.status || "Checking..."}
            downloadUrl={status?.download_url}
            onDownload={handleDownload}
          />
        )}
        {sessionId && !isPolling && review && (
          <div className="mt-8">
            <h2 className="text-2xl font-bold mb-2 text-blue-700">AI Review Results</h2>
            {/* Summary Card */}
            <div className="mb-4 p-4 rounded bg-blue-50 flex flex-wrap gap-4 items-center shadow">
              <span className="font-semibold text-blue-700">Summary:</span>
              <span className="text-sm">Total Issues: <b>{Array.isArray(review.ai_log) ? review.ai_log.length : 0}</b></span>
              <span className="text-sm">Files Affected: <b>{Array.isArray(review.ai_log) ? [...new Set(review.ai_log.map((i:any)=>i.file))].length : 0}</b></span>
              {typeof review.code_quality_score === 'number' && (
                <span className="text-sm">Code Quality Score: <b className="text-green-700">{review.code_quality_score}/100</b></span>
              )}
            </div>
            {/* Collapsible Linter Results */}
            <div className="mb-4">
              <button
                className="text-xs text-blue-600 underline mb-2"
                onClick={() => setShowLinter((v) => !v)}
                type="button"
              >{showLinter ? 'Hide' : 'Show'} Linter Results</button>
              {showLinter && (
                <div className="bg-gray-100 rounded p-2 mt-2 max-h-48 overflow-auto text-xs">
                  {review.linter_results && Object.keys(review.linter_results).length > 0 ? (
                    Object.entries(review.linter_results).map(([file, issues]: any, idx) => (
                      <div key={idx} className="mb-2">
                        <div className="font-mono text-xs text-blue-700">{file}</div>
                        <ul className="ml-4 list-disc">
                          {issues.map((iss: any, i: number) => (
                            <li key={i}>{iss.message || JSON.stringify(iss)}</li>
                          ))}
                        </ul>
                      </div>
                    ))
                  ) : (
                    <div className="text-gray-500">No linter issues found.</div>
                  )}
                </div>
              )}
            </div>
            {review.pr_comments && (
              <div className="mb-6">
                <h3 className="text-xl font-bold mb-2 text-blue-700">PR-Style Comments</h3>
                <pre className="bg-gray-100 rounded p-4 text-sm overflow-x-auto whitespace-pre-wrap">{review.pr_comments}</pre>
              </div>
            )}
            {/* Chat Feed */}
            <div ref={chatFeedRef} className="space-y-6 max-h-[400px] overflow-y-auto transition-all">
              {Array.isArray(review.ai_log) && review.ai_log.length > 0 ? (
                review.ai_log.map((issue: any, idx: number) => (
                  <div key={idx} className="flex items-start gap-3 animate-fadein">
                    <div className="flex-shrink-0 text-2xl">🤖</div>
                    <div className="bg-blue-50 border border-blue-100 rounded-xl p-4 shadow w-full">
                      <div className="flex flex-wrap gap-4 items-center mb-2">
                        <span className="font-mono text-xs bg-blue-100 px-2 py-1 rounded">{issue.file}</span>
                        <span className="font-mono text-xs bg-gray-200 px-2 py-1 rounded">Line {issue.line}</span>
                        <button
                          className="ml-auto px-2 py-1 text-xs bg-gray-200 rounded hover:bg-blue-200"
                          onClick={() => setExpandedIssue(expandedIssue === idx ? null : idx)}
                          type="button"
                        >{expandedIssue === idx ? 'Collapse' : 'Expand'}</button>
                      </div>
                      <div className="mb-1"><span className="font-semibold text-red-600">Issue:</span> {typeof issue.issue === 'string' ? issue.issue : issue.issue?.message}</div>
                      <div className="mb-1"><span className="font-semibold text-blue-700">Suggestion:</span> {issue.suggestion}</div>
                      {expandedIssue === idx ? (
                        <div className="grid grid-cols-1 md:grid-cols-2 gap-2 mt-2">
                          <div>
                            <div className="text-xs text-gray-500 mb-1">Current Code</div>
                            <MonacoEditor
                              height="80"
                              language={getLanguageFromFilename(issue.file)}
                              value={issue.current_code}
                              options={{ readOnly: true, fontSize: 13, minimap: { enabled: false } }}
                            />
                          </div>
                          <div>
                            <div className="text-xs text-gray-500 mb-1 flex items-center">Recommended Fix
                              <button
                                className="ml-2 px-2 py-1 text-xs bg-blue-500 text-white rounded hover:bg-blue-600"
                                onClick={() => handleCopy(issue.recommended_code)}
                                type="button"
                              >Copy</button>
                              {copyMsg && <span className="ml-2 text-green-600 text-xs">{copyMsg}</span>}
                            </div>
                            <MonacoEditor
                              height="80"
                              language={getLanguageFromFilename(issue.file)}
                              value={issue.recommended_code}
                              options={{ readOnly: true, fontSize: 13, minimap: { enabled: false } }}
                            />
                          </div>
                        </div>
                      ) : (
                        <div className="grid grid-cols-1 md:grid-cols-2 gap-2 mt-2">
                          <div>
                            <div className="text-xs text-gray-500 mb-1">Current Code</div>
                            <pre className="bg-gray-200 rounded p-2 text-xs overflow-x-auto"><code>{issue.current_code}</code></pre>
                          </div>
                          <div>
                            <div className="text-xs text-gray-500 mb-1 flex items-center">Recommended Fix
                              <button
                                className="ml-2 px-2 py-1 text-xs bg-blue-500 text-white rounded hover:bg-blue-600"
                                onClick={() => handleCopy(issue.recommended_code)}
                                type="button"
                              >Copy</button>
                              {copyMsg && <span className="ml-2 text-green-600 text-xs">{copyMsg}</span>}
                            </div>
                            <pre className="bg-gray-200 rounded p-2 text-xs overflow-x-auto"><code>{issue.recommended_code}</code></pre>
                          </div>
                        </div>
                      )}
                      {issue.patch && (
                        <div className="mt-2">
                          <div className="text-xs text-gray-500 mb-1">Patch Snippet</div>
                          <pre className="bg-gray-200 rounded p-2 text-xs overflow-x-auto">{issue.patch}</pre>
                        </div>
                      )}
                    </div>
                  </div>
                ))
              ) : (
                <div className="text-gray-500">No issues found by AI review.</div>
              )}
            </div>
            {/* Unified Patch & Copy */}
            {review.patch && (
              <div className="mt-8">
                <h3 className="font-semibold mb-1">Unified Patch (all fixes)</h3>
                <div className="flex items-center gap-2 mb-2">
                  <button
                    className="px-2 py-1 text-xs bg-blue-500 text-white rounded hover:bg-blue-600"
                    onClick={() => handleCopy(review.patch)}
                    type="button"
                  >Copy Patch</button>
                  {copyMsg && <span className="text-green-600 text-xs">{copyMsg}</span>}
                </div>
                <pre className="bg-gray-100 rounded p-2 text-xs overflow-x-auto">{review.patch}</pre>
              </div>
            )}
            <button
              className="mt-6 w-full bg-blue-600 text-white py-2 rounded font-semibold hover:bg-blue-700 transition"
              onClick={handleDownload}
              type="button"
            >Download Full ZIP</button>
          </div>
        )}
        {sessionId && !isPolling && !review && (
          <div className="mt-8 text-gray-500">Loading review results...</div>
        )}
      </div>
      <footer className="mt-8 text-gray-400 text-sm">AI Code Reviewer &copy; {new Date().getFullYear()}</footer>
    </div>
  );
};

export default Home; 