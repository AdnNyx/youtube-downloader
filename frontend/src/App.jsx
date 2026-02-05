import { useEffect, useMemo, useState } from "react";
import { api } from "./lib/api";
import {
  Youtube,
  Link2,
  Wand2,
  Download,
  Music2,
  Video,
  Loader2,
  CheckCircle2,
  XCircle,
} from "lucide-react";

export default function App() {
  const [url, setUrl] = useState("");
  const [loadingParse, setLoadingParse] = useState(false);
  const [video, setVideo] = useState(null);

  const [type, setType] = useState("mp3");
  const [quality, setQuality] = useState("720p");
  const [bitrate, setBitrate] = useState(192);

  const [jobId, setJobId] = useState(null);
  const [job, setJob] = useState(null);
  const [loadingJob, setLoadingJob] = useState(false);

  const mp4Options = useMemo(() => video?.formats?.mp4 || [], [video]);

  // ===== Convert: Parse + Create Job (1 klik) =====
  async function handleConvert() {
    if (!url.trim()) return;

    setLoadingParse(true);
    setLoadingJob(true);

    setVideo(null);
    setJobId(null);
    setJob(null);

    try {
      // 1) PARSE
      const parseRes = await api.post("/youtube/parse", { url });
      const parsedVideo = parseRes.data.data;
      setVideo(parsedVideo);

      // 2) Default quality kalau mp4 (ambil highest)
      let selectedQuality = quality;
      if (type === "mp4") {
        const mp4List = parsedVideo?.formats?.mp4 || [];
        if (mp4List.length) {
          selectedQuality = mp4List.slice(-1)[0].label;
          setQuality(selectedQuality);
        }
      }

      // 3) CREATE JOB
      const payload =
        type === "mp4"
          ? { url, type: "mp4", quality: selectedQuality }
          : { url, type: "mp3", bitrate };

      const jobRes = await api.post("/youtube/jobs", payload);
      const id = jobRes.data.data.jobId;
      setJobId(id);
    } catch (err) {
      console.log("Convert error:", err?.response || err);

      alert(
        err?.response?.data?.detail ||
          err?.response?.data?.message ||
          JSON.stringify(err?.response?.data) ||
          err.message ||
          "Convert failed",
      );
    } finally {
      setLoadingParse(false);
      setLoadingJob(false);
    }
  }

  // Polling job status
  useEffect(() => {
    if (!jobId) return;

    let timer = null;
    let stopped = false;

    async function poll() {
      try {
        const res = await api.get(`/youtube/jobs/${jobId}`);
        setJob(res.data.data);

        if (
          res.data.data?.status === "finished" ||
          res.data.data?.status === "failed"
        ) {
          stopped = true;
          return;
        }
      } catch (err) {
        // silent fail
      }

      if (!stopped) timer = setTimeout(poll, 1000);
    }

    poll();

    return () => {
      if (timer) clearTimeout(timer);
    };
  }, [jobId]);

  const progress = job?.progress ?? 0;
  const stage = job?.stage ?? "-";
  const status = job?.status ?? "-";

  const API_BASE = import.meta.env.VITE_API_BASE_URL || "http://127.0.0.1:8000";
  const downloadUrl =
    job?.status === "finished" ? `${API_BASE}${job.downloadUrl}` : null;

  const busy = loadingParse || loadingJob;

  const StatusBadge = () => {
    const s = job?.status;

    if (!jobId) return null;

    if (s === "finished") {
      return (
        <span className="inline-flex items-center gap-2 rounded-full border border-emerald-500/30 bg-emerald-500/10 px-3 py-1 text-xs text-emerald-300">
          <CheckCircle2 className="w-4 h-4" />
          Finished
        </span>
      );
    }

    if (s === "failed") {
      return (
        <span className="inline-flex items-center gap-2 rounded-full border border-red-500/30 bg-red-500/10 px-3 py-1 text-xs text-red-300">
          <XCircle className="w-4 h-4" />
          Failed
        </span>
      );
    }

    return (
      <span className="inline-flex items-center gap-2 rounded-full border border-indigo-500/30 bg-indigo-500/10 px-3 py-1 text-xs text-indigo-300">
        <Loader2 className="w-4 h-4 animate-spin" />
        {s || "processing"}
      </span>
    );
  };

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100">
      {/* Background glow */}
      <div className="pointer-events-none fixed inset-0 overflow-hidden">
        <div className="absolute -top-40 left-1/2 h-[500px] w-[900px] -translate-x-1/2 rounded-full bg-indigo-600/10 blur-3xl" />
        <div className="absolute -bottom-40 left-1/2 h-[400px] w-[800px] -translate-x-1/2 rounded-full bg-emerald-600/10 blur-3xl" />
      </div>

      <div className="relative max-w-3xl mx-auto px-4 py-10">
        {/* Header */}
        <div className="flex items-center gap-3">
          <div className="h-12 w-12 rounded-2xl bg-gradient-to-br from-red-500/20 to-indigo-500/20 border border-slate-800 flex items-center justify-center">
            <Youtube className="w-7 h-7 text-red-400" />
          </div>

          <div className="flex-1">
            <h1 className="text-2xl font-bold tracking-tight">
              YouTube Downloader
            </h1>
            <p className="text-slate-400 text-sm mt-1">
              Paste link → pilih format → Convert → Download.
            </p>
          </div>
        </div>

        {/* Main Card */}
        <div className="mt-8 rounded-3xl border border-slate-800 bg-slate-900/40 backdrop-blur-xl shadow-[0_0_0_1px_rgba(255,255,255,0.02)]">
          <div className="p-5 md:p-6">
            {/* URL input */}
            <label className="text-sm text-slate-300">YouTube URL</label>
            <div className="mt-2 flex gap-2">
              <div className="relative flex-1">
                <Link2 className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-500" />
                <input
                  className="w-full bg-slate-950/70 border border-slate-800 rounded-2xl pl-10 pr-3 py-3 outline-none focus:border-slate-600 transition"
                  placeholder="https://www.youtube.com/watch?v=..."
                  value={url}
                  onChange={(e) => setUrl(e.target.value)}
                />
              </div>

              <button
                onClick={handleConvert}
                disabled={busy || !url.trim()}
                className="px-4 md:px-5 py-3 rounded-2xl bg-emerald-600 hover:bg-emerald-500 disabled:opacity-50 font-semibold transition inline-flex items-center gap-2"
              >
                {busy ? (
                  <>
                    <Loader2 className="w-5 h-5 animate-spin" />
                    Converting
                  </>
                ) : (
                  <>
                    <Wand2 className="w-5 h-5" />
                    Convert
                  </>
                )}
              </button>
            </div>

            {/* Options */}
            <div className="mt-5 grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label className="text-sm text-slate-300">Format</label>
                <div className="relative mt-2">
                  {type === "mp3" ? (
                    <Music2 className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-500" />
                  ) : (
                    <Video className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-500" />
                  )}

                  <select
                    value={type}
                    onChange={(e) => setType(e.target.value)}
                    className="w-full appearance-none bg-slate-950/70 border border-slate-800 rounded-2xl pl-10 pr-10 py-3 outline-none focus:border-slate-600 transition"
                  >
                    <option value="mp3">MP3 (Audio)</option>
                    <option value="mp4">MP4 (Video)</option>
                  </select>

                  <div className="pointer-events-none absolute right-3 top-1/2 -translate-y-1/2 text-slate-500">
                    ▾
                  </div>
                </div>
              </div>

              {type === "mp4" ? (
                <div>
                  <label className="text-sm text-slate-300">Quality</label>
                  <div className="relative mt-2">
                    <select
                      value={quality}
                      onChange={(e) => setQuality(e.target.value)}
                      className="w-full appearance-none bg-slate-950/70 border border-slate-800 rounded-2xl px-3 pr-10 py-3 outline-none focus:border-slate-600 transition"
                    >
                      {/* Kalau belum parse, pakai default */}
                      {!mp4Options.length && (
                        <>
                          <option value="360p">360p</option>
                          <option value="480p">480p</option>
                          <option value="720p">720p</option>
                          <option value="1080p">1080p</option>
                        </>
                      )}

                      {mp4Options.length
                        ? mp4Options.map((f) => (
                            <option key={f.label} value={f.label}>
                              {f.label} {f.hasAudio ? "(with audio)" : ""}
                            </option>
                          ))
                        : null}
                    </select>
                    <div className="pointer-events-none absolute right-3 top-1/2 -translate-y-1/2 text-slate-500">
                      ▾
                    </div>
                  </div>

                  <div className="text-xs text-slate-500 mt-2">
                    * Saat convert, otomatis ambil kualitas tertinggi jika
                    tersedia.
                  </div>
                </div>
              ) : (
                <div>
                  <label className="text-sm text-slate-300">Bitrate</label>
                  <div className="relative mt-2">
                    <select
                      value={bitrate}
                      onChange={(e) => setBitrate(parseInt(e.target.value))}
                      className="w-full appearance-none bg-slate-950/70 border border-slate-800 rounded-2xl px-3 pr-10 py-3 outline-none focus:border-slate-600 transition"
                    >
                      <option value={128}>128 kbps</option>
                      <option value={192}>192 kbps</option>
                      <option value={320}>320 kbps</option>
                    </select>
                    <div className="pointer-events-none absolute right-3 top-1/2 -translate-y-1/2 text-slate-500">
                      ▾
                    </div>
                  </div>
                </div>
              )}
            </div>

            {/* Video metadata card */}
            {video && (
              <div className="mt-6 rounded-3xl border border-slate-800 bg-slate-950/50 p-4">
                <div className="flex gap-4">
                  <img
                    src={video.thumbnail}
                    alt="thumbnail"
                    className="w-40 h-24 object-cover rounded-2xl border border-slate-800"
                  />
                  <div className="flex-1">
                    <div className="font-semibold leading-snug">
                      {video.title}
                    </div>
                    <div className="text-sm text-slate-400 mt-2">
                      {video.channel || "-"} •{" "}
                      {video.duration ? `${video.duration}s` : "-"}
                    </div>
                  </div>
                </div>
              </div>
            )}
          </div>

          {/* Job status footer */}
          {jobId && (
            <div className="border-t border-slate-800 p-5 md:p-6">
              <div className="flex items-center justify-between gap-4 flex-wrap">
                <div className="text-sm text-slate-400">
                  Job ID:{" "}
                  <span className="text-slate-200 font-medium">{jobId}</span>
                </div>
                <StatusBadge />
              </div>

              <div className="mt-3 text-sm text-slate-400">
                Stage: <span className="text-slate-200">{stage}</span>
              </div>

              {/* Progress bar */}
              <div className="mt-4 w-full bg-slate-950 border border-slate-800 rounded-2xl overflow-hidden">
                <div
                  className="h-3 bg-gradient-to-r from-indigo-500 to-emerald-500 transition-all"
                  style={{ width: `${progress}%` }}
                />
              </div>

              <div className="mt-2 text-xs text-slate-400">{progress}%</div>

              {/* Error */}
              {job?.status === "failed" && (
                <div className="mt-4 text-sm text-red-300 border border-red-500/20 bg-red-500/10 rounded-2xl p-3">
                  {job?.error || "Unknown error"}
                </div>
              )}

              {/* Download */}
              {downloadUrl && (
                <a
                  href={downloadUrl}
                  className="mt-5 inline-flex items-center justify-center gap-2 w-full px-4 py-3 rounded-2xl bg-indigo-600 hover:bg-indigo-500 font-semibold transition"
                >
                  <Download className="w-5 h-5" />
                  Download File
                </a>
              )}
            </div>
          )}
        </div>

        <div className="mt-10 text-xs text-slate-500 text-center">
          Gunakan hanya untuk konten yang kamu punya izin/hak unduh.
        </div>
      </div>
    </div>
  );
}
