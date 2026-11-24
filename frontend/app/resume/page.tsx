"use client";

import { ChangeEvent, useEffect, useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";

type Resume = {
  id: number;
  file_name: string;
  file_type: string;
  file_size: number;
  extracted_text_length: number;
  uploaded_at: string;
};

type Education = {
  degree: string | null;
  university: string | null;
  location: string | null;
  cgpa: string | number | null;
  graduation_year: number | null;
};

type Experience = {
  job_title: string | null;
  company: string | null;
  start_date: string | null;
  end_date: string | null;
  description: string | null;
};

type Analysis = {
  resume_id: number;
  file_name: string;
  skills: string[];
  education: Education[];
  experience: Experience[];
};

export default function ResumePage() {
  const router = useRouter();

  const [resume, setResume] = useState<Resume | null>(null);
  const [analysis, setAnalysis] = useState<Analysis | null>(null);

  const [loading, setLoading] = useState(true);
  const [uploading, setUploading] = useState(false);
  const [analyzing, setAnalyzing] = useState(false);
  const [aiAnalyzing, setAiAnalyzing] = useState(false);

  const [error, setError] = useState("");
  const [success, setSuccess] = useState("");

  useEffect(() => {
    loadResume();
  }, []);

  async function loadResume() {
    const token = localStorage.getItem("access_token");

    if (!token) {
      router.push("/login");
      return;
    }

    try {
      const response = await fetch(
        "http://127.0.0.1:8000/resume",
        {
          headers: {
            Authorization: `Bearer ${token}`,
          },
        }
      );

      if (response.status === 401) {
        localStorage.removeItem("access_token");
        router.push("/login");
        return;
      }

      if (response.status === 404) {
        setResume(null);
        return;
      }

      if (!response.ok) {
        throw new Error("Could not load resume");
      }

      const data = await response.json();
      setResume(data);

      // Try loading existing analysis
      await loadAnalysis(token);
    } catch (error) {
      console.error(error);
      setError("Could not load your resume.");
    } finally {
      setLoading(false);
    }
  }

  async function loadAnalysis(token: string) {
    try {
      const response = await fetch(
        "http://127.0.0.1:8000/resume/analysis",
        {
          headers: {
            Authorization: `Bearer ${token}`,
          },
        }
      );

      if (!response.ok) {
        return;
      }

      const data = await response.json();
      setAnalysis(data);
    } catch {
      // Analysis may not exist yet.
    }
  }

  async function handleUpload(
    event: ChangeEvent<HTMLInputElement>
  ) {
    const file = event.target.files?.[0];

    if (!file) {
      return;
    }

    setError("");
    setSuccess("");

    if (file.type !== "application/pdf") {
      setError("Please upload a PDF file.");
      return;
    }

    setUploading(true);

    try {
      const token = localStorage.getItem("access_token");

      if (!token) {
        router.push("/login");
        return;
      }

      const formData = new FormData();
      formData.append("file", file);

      const response = await fetch(
        "http://127.0.0.1:8000/resume/upload",
        {
          method: "POST",
          headers: {
            Authorization: `Bearer ${token}`,
          },
          body: formData,
        }
      );

      const data = await response.json();

      if (!response.ok) {
        throw new Error(
          data.detail || "Resume upload failed."
        );
      }

      setSuccess("Resume uploaded successfully.");
      setAnalysis(null);

      await loadResume();
    } catch (error) {
      console.error(error);

      setError(
        error instanceof Error
          ? error.message
          : "Resume upload failed."
      );
    } finally {
      setUploading(false);

      // Allow selecting the same file again.
      event.target.value = "";
    }
  }

  async function handleAnalyze() {
    setError("");
    setSuccess("");
    setAnalyzing(true);

    try {
      const token = localStorage.getItem("access_token");

      if (!token) {
        router.push("/login");
        return;
      }

      const response = await fetch(
        "http://127.0.0.1:8000/resume/analyze",
        {
          method: "POST",
          headers: {
            Authorization: `Bearer ${token}`,
          },
        }
      );

      const data = await response.json();

      if (!response.ok) {
        throw new Error(
          data.detail || "Resume analysis failed."
        );
      }

      setSuccess("Resume analyzed successfully.");

      await loadAnalysis(token);
    } catch (error) {
      console.error(error);

      setError(
        error instanceof Error
          ? error.message
          : "Resume analysis failed."
      );
    } finally {
      setAnalyzing(false);
    }
  
  
  }
  async function handleAIAnalyze() {
  setError("");
  setSuccess("");
  setAiAnalyzing(true);

  try {
    const token = localStorage.getItem("access_token");

    if (!token) {
      router.push("/login");
      return;
    }

    const response = await fetch(
      "http://127.0.0.1:8000/resume/ai-analyze",
      {
        method: "POST",
        headers: {
          Authorization: `Bearer ${token}`,
        },
      }
    );

    const data = await response.json();

    if (!response.ok) {
      throw new Error(
        data.detail || "AI resume analysis failed."
      );
    }

    setSuccess(
      "AI resume analysis completed successfully."
    );

    await loadAnalysis(token);
  } catch (error) {
    console.error(error);

    setError(
      error instanceof Error
        ? error.message
        : "AI resume analysis failed."
    );
  } finally {
    setAiAnalyzing(false);
  }
}

  function formatFileSize(bytes: number) {
    if (bytes < 1024) {
      return `${bytes} B`;
    }

    if (bytes < 1024 * 1024) {
      return `${(bytes / 1024).toFixed(1)} KB`;
    }

    return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
  }

  if (loading) {
    return (
      <main className="flex min-h-screen items-center justify-center bg-[#08090b] text-white">
        <div className="text-center">
          <div className="mx-auto h-8 w-8 animate-spin rounded-full border-2 border-white/10 border-t-white" />

          <p className="mt-4 text-sm text-white/40">
            Loading resume intelligence...
          </p>
        </div>
      </main>
    );
  }

  return (
    <main className="min-h-screen bg-[#08090b] text-white">
      {/* Header */}
      <header className="border-b border-white/10 bg-[#08090b]/95">
        <div className="flex h-16 items-center justify-between px-5 md:px-8">
          <Link
            href="/dashboard"
            className="flex items-center gap-3"
          >
            <div className="flex h-9 w-9 items-center justify-center rounded-xl bg-white text-sm font-black text-black">
              AI
            </div>

            <div className="hidden sm:block">
              <p className="text-sm font-semibold">
                Career Intelligence
              </p>

              <p className="text-[10px] text-white/25">
                RESUME INTELLIGENCE
              </p>
            </div>
          </Link>

          <Link
            href="/dashboard"
            className="rounded-lg border border-white/10 px-3 py-2 text-xs text-white/50 transition hover:bg-white/5 hover:text-white"
          >
            ← Dashboard
          </Link>
        </div>
      </header>

      {/* Main */}
      <div className="mx-auto max-w-6xl px-5 py-8 md:px-8 md:py-12">
        <div>
          <p className="text-xs font-semibold uppercase tracking-[0.2em] text-white/25">
            Resume Intelligence
          </p>

          <h1 className="mt-3 text-3xl font-semibold tracking-tight md:text-4xl">
            Understand your resume.
          </h1>

          <p className="mt-3 max-w-2xl text-sm leading-6 text-white/35">
            Upload your resume and let Career Intelligence extract
            the information that will power your future career
            analysis.
          </p>
        </div>

        {/* Messages */}
        {error && (
          <div className="mt-6 rounded-xl border border-red-400/20 bg-red-400/5 px-4 py-3 text-sm text-red-300">
            {error}
          </div>
        )}

        {success && (
          <div className="mt-6 rounded-xl border border-emerald-400/20 bg-emerald-400/5 px-4 py-3 text-sm text-emerald-300">
            {success}
          </div>
        )}

        {!resume ? (
          /* Empty State */
          <section className="mt-10 rounded-2xl border border-white/10 bg-[#101216] p-8 md:p-12">
            <div className="mx-auto max-w-xl text-center">
              <div className="mx-auto flex h-16 w-16 items-center justify-center rounded-2xl border border-white/10 bg-white/[0.03]">
                <span className="text-2xl">↑</span>
              </div>

              <h2 className="mt-6 text-xl font-semibold">
                Upload your resume
              </h2>

              <p className="mt-3 text-sm leading-6 text-white/35">
                Upload a PDF version of your resume. We'll extract
                its text and prepare it for career intelligence
                analysis.
              </p>

              <label className="mt-7 inline-flex cursor-pointer items-center justify-center rounded-xl bg-white px-5 py-3 text-sm font-semibold text-black transition hover:bg-white/90">
                {uploading ? "Uploading..." : "Choose PDF"}

                <input
                  type="file"
                  accept="application/pdf"
                  className="hidden"
                  onChange={handleUpload}
                  disabled={uploading}
                />
              </label>

              <p className="mt-4 text-[10px] text-white/20">
                PDF files only
              </p>
            </div>
          </section>
        ) : (
          <>
            {/* Resume Card */}
            <section className="mt-10 rounded-2xl border border-white/10 bg-[#101216] p-6 md:p-7">
              <div className="flex flex-col justify-between gap-6 md:flex-row md:items-center">
                <div className="flex items-center gap-4">
                  <div className="flex h-12 w-12 shrink-0 items-center justify-center rounded-xl border border-white/10 bg-white/[0.03]">
                    <span className="text-xs font-bold">
                      PDF
                    </span>
                  </div>

                  <div>
                    <h2 className="text-sm font-semibold">
                      {resume.file_name}
                    </h2>

                    <p className="mt-1 text-xs text-white/30">
                      {formatFileSize(resume.file_size)} ·{" "}
                      {resume.extracted_text_length.toLocaleString()}{" "}
                      characters extracted
                    </p>
                  </div>
                </div>

                <div className="flex flex-wrap gap-3">
                  <label className="cursor-pointer rounded-xl border border-white/10 px-4 py-2.5 text-xs font-medium text-white/60 transition hover:bg-white/5 hover:text-white">
                    {uploading ? "Uploading..." : "Replace Resume"}

                    <input
                      type="file"
                      accept="application/pdf"
                      className="hidden"
                      onChange={handleUpload}
                      disabled={uploading}
                    />
                  </label>

                  <button
                    onClick={handleAnalyze}
                    disabled={analyzing}
                    className="rounded-xl bg-white px-4 py-2.5 text-xs font-semibold text-black transition hover:bg-white/90 disabled:cursor-not-allowed disabled:opacity-50"
                  >
                    {analyzing
                      ? "Analyzing..."
                      : analysis
                        ? "Re-analyze Resume"
                        : "Analyze Resume →"}
                  </button>
                  <button
  onClick={handleAIAnalyze}
  disabled={aiAnalyzing}
  className="rounded-xl border border-emerald-400/20 bg-emerald-400/10 px-4 py-2.5 text-xs font-semibold text-emerald-400 transition hover:bg-emerald-400/15 disabled:cursor-not-allowed disabled:opacity-50"
>
  {aiAnalyzing
    ? "AI Analyzing..."
    : "✨ AI Analyze"}
</button>
                </div>
              </div>
            </section>

            {/* Analysis */}
            {analysis && (
              <div className="mt-5 space-y-5">
                {/* Skills */}
                <section className="rounded-2xl border border-white/10 bg-[#101216] p-6 md:p-7">
                  <div className="flex items-start justify-between">
                    <div>
                      <p className="text-[10px] font-semibold uppercase tracking-[0.2em] text-white/25">
                        Skills
                      </p>

                      <h2 className="mt-2 text-xl font-semibold">
                        Detected technical skills
                      </h2>
                    </div>

                    <div className="rounded-lg border border-emerald-400/20 bg-emerald-400/5 px-3 py-1.5 text-[10px] font-medium text-emerald-400">
                      {analysis.skills.length} detected
                    </div>
                  </div>

                  {analysis.skills.length > 0 ? (
                    <div className="mt-7 flex flex-wrap gap-2">
                      {analysis.skills.map((skill) => (
                        <span
                          key={skill}
                          className="rounded-lg border border-white/10 bg-white/[0.03] px-3 py-2 text-xs text-white/70"
                        >
                          {skill}
                        </span>
                      ))}
                    </div>
                  ) : (
                    <p className="mt-6 text-sm text-white/30">
                      No technical skills were detected.
                    </p>
                  )}
                </section>

                {/* Education */}
                <section className="rounded-2xl border border-white/10 bg-[#101216] p-6 md:p-7">
                  <div className="flex items-start justify-between">
                    <div>
                      <p className="text-[10px] font-semibold uppercase tracking-[0.2em] text-white/25">
                        Education
                      </p>

                      <h2 className="mt-2 text-xl font-semibold">
                        Academic background
                      </h2>
                    </div>

                    <span className="rounded-full bg-emerald-400/10 px-2.5 py-1 text-[9px] text-emerald-400">
                      {analysis.education.length > 0
                        ? "Detected"
                        : "Not detected"}
                    </span>
                  </div>

                  <div className="mt-7 space-y-4">
                    {analysis.education.length > 0 ? (
                      analysis.education.map((item, index) => (
                        <div
                          key={index}
                          className="rounded-xl border border-white/10 bg-white/[0.02] p-5"
                        >
                          <p className="whitespace-pre-line text-sm leading-6 text-white/65">
                            {item.degree ||
                              "Education information detected"}
                          </p>
                          {item.university && (
  <p className="mt-2 text-xs text-white/30">
    {item.university}
  </p>
)}

{item.location && (
  <p className="mt-1 text-xs text-white/25">
    Location: {item.location}
  </p>
)}

{item.cgpa && (
  <p className="mt-1 text-xs text-white/25">
    CGPA: {item.cgpa}
  </p>
)}

{item.graduation_year && (
  <p className="mt-1 text-xs text-white/25">
    Graduation: {item.graduation_year}
  </p>
)}
                          

                          
                        </div>
                      ))
                    ) : (
                      <p className="text-sm text-white/30">
                        No education information was detected.
                      </p>
                    )}
                  </div>
                </section>

                {/* Experience */}
                <section className="rounded-2xl border border-white/10 bg-[#101216] p-6 md:p-7">
                  <div className="flex items-start justify-between">
                    <div>
                      <p className="text-[10px] font-semibold uppercase tracking-[0.2em] text-white/25">
                        Experience
                      </p>

                      <h2 className="mt-2 text-xl font-semibold">
                        Professional experience
                      </h2>
                    </div>

                    <span className="rounded-full bg-emerald-400/10 px-2.5 py-1 text-[9px] text-emerald-400">
                      {analysis.experience.length > 0
                        ? "Detected"
                        : "Not detected"}
                    </span>
                  </div>

                  <div className="mt-7 space-y-4">
                    {analysis.experience.length > 0 ? (
                      analysis.experience.map((item, index) => (
                        <div
                          key={index}
                          className="rounded-xl border border-white/10 bg-white/[0.02] p-5"
                        >
                          {item.job_title && (
                            <p className="text-sm font-semibold">
                              {item.job_title}
                            </p>
                          )}

                          {item.company && (
                            <p className="mt-1 text-xs text-white/40">
                              {item.company}
                            </p>
                          )}

                          {(item.start_date ||
                            item.end_date) && (
                            <p className="mt-1 text-[10px] text-white/25">
                              {item.start_date || ""}
                              {item.start_date &&
                              item.end_date
                                ? " — "
                                : ""}
                              {item.end_date || ""}
                            </p>
                          )}

                          {item.description && (
                            <p className="mt-4 whitespace-pre-line text-sm leading-6 text-white/50">
                              {item.description}
                            </p>
                          )}
                        </div>
                      ))
                    ) : (
                      <p className="text-sm text-white/30">
                        No experience information was detected.
                      </p>
                    )}
                  </div>
                </section>
              </div>
            )}
          </>
        )}
      </div>
    </main>
  );
}