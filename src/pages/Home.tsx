import React, { useState, useRef } from "react";
import MonacoEditor from "@monaco-editor/react";
import StatusDisplay from "../components/StatusDisplay";
import Spinner from "../components/Spinner";
import { pasteSchema, zipSchema, githubSchema } from "../utils/validation";

const TABS = ["Paste Code", "Upload ZIP", "GitHub Repo"] as const;
type Tab = typeof TABS[number];

type Status = {
  status: string;
  download_url?: string;
  [key: string]: any;
};

const API_BASE = "http://localhost:5000";

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

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-gray-100 flex flex-col items-center py-8">
      <div className="w-full max-w-2xl bg-white rounded-lg shadow-xl p-8">
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
      </div>
      <footer className="mt-8 text-gray-400 text-sm">AI Code Reviewer &copy; {new Date().getFullYear()}</footer>
    </div>
  );
};

export default Home; 