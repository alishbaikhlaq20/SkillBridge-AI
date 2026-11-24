"use client";

import { useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";

type JobAnalysis = {
  job_id: number;
  job_title: string | null;
  company: string | null;
  required_skills: string[];
  preferred_skills: string[];
  education_requirements: string[];
  experience_requirements: string[];
  responsibilities: string[];
};

export default function JobPage() {
  const router = useRouter();

  const [description, setDescription] = useState("");
  const [analysis, setAnalysis] = useState<JobAnalysis | null>(null);

  const [saving, setSaving] = useState(false);
  const [analyzing, setAnalyzing] = useState(false);

  const [error, setError] = useState("");
  const [success, setSuccess] = useState("");

  async function handleAnalyze() {
    setError("");
    setSuccess("");

    if (description.trim().length < 50) {
      setError(
        "Please enter a job description with at least 50 characters."
      );
      return;
    }

    const token = localStorage.getItem("access_token");

    if (!token) {
      router.push("/login");
      return;
    }

    setSaving(true);

    try {
      // Step 1: Save job description
      const saveResponse = await fetch(
        "http://127.0.0.1:8000/jobs",
        {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
            Authorization: `Bearer ${token}`,
          },
          body: JSON.stringify({
            description,
          }),
        }
      );

      const saveData = await saveResponse.json();

      if (!saveResponse.ok) {
        throw new Error(
          saveData.detail || "Could not save job description."
        );
      }

      const jobId = saveData.job_id;

      setSaving(false);
      setAnalyzing(true);

      // Step 2: Analyze with AI
      const analyzeResponse = await fetch(
        `http://127.0.0.1:8000/jobs/${jobId}/analyze`,
        {
          method: "POST",
          headers: {
            Authorization: `Bearer ${token}`,
          },
        }
      );

      const analyzeData = await analyzeResponse.json();

      if (!analyzeResponse.ok) {
        throw new Error(
          analyzeData.detail || "AI job analysis failed."
        );
      }

      setAnalysis(analyzeData);

      setSuccess(
        "Job description analyzed successfully."
      );
    } catch (error) {
      console.error(error);

      setError(
        error instanceof Error
          ? error.message
          : "Something went wrong."
      );
    } finally {
      setSaving(false);
      setAnalyzing(false);
    }
  }

  function renderList(items: string[]) {
    if (items.length === 0) {
      return (
        <p className="text-sm text-white/30">
          No information detected.
        </p>
      );
    }

    return (
      <ul className="space-y-2">
        {items.map((item, index) => (
          <li
            key={index}
            className="flex gap-3 text-sm leading-6 text-white/60"
          >
            <span className="mt-2 h-1.5 w-1.5 shrink-0 rounded-full bg-white/40" />
            <span>{item}</span>
          </li>
        ))}
      </ul>
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
                JOB INTELLIGENCE
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

        {/* Heading */}
        <div>
          <p className="text-xs font-semibold uppercase tracking-[0.2em] text-white/25">
            Job Intelligence
          </p>

          <h1 className="mt-3 text-3xl font-semibold tracking-tight md:text-4xl">
            Understand the job.
          </h1>

          <p className="mt-3 max-w-2xl text-sm leading-6 text-white/35">
            Paste a job description and let Career Intelligence
            extract the skills, requirements, and responsibilities
            that matter.
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

        {/* Input */}
        <section className="mt-10 rounded-2xl border border-white/10 bg-[#101216] p-6 md:p-7">

          <div>
            <p className="text-[10px] font-semibold uppercase tracking-[0.2em] text-white/25">
              Job Description
            </p>

            <h2 className="mt-2 text-xl font-semibold">
              Paste the complete job posting
            </h2>
          </div>

          <textarea
            value={description}
            onChange={(event) =>
              setDescription(event.target.value)
            }
            placeholder="Paste the job title, requirements, responsibilities, skills, education and experience requirements here..."
            className="mt-6 min-h-[280px] w-full resize-y rounded-xl border border-white/10 bg-white/[0.02] p-4 text-sm leading-6 text-white outline-none placeholder:text-white/20 focus:border-white/20"
          />

          <div className="mt-5 flex flex-col justify-between gap-4 sm:flex-row sm:items-center">

            <p className="text-xs text-white/25">
              {description.length.toLocaleString()} characters
            </p>

            <button
              onClick={handleAnalyze}
              disabled={saving || analyzing}
              className="rounded-xl bg-white px-5 py-3 text-sm font-semibold text-black transition hover:bg-white/90 disabled:cursor-not-allowed disabled:opacity-50"
            >
              {saving
                ? "Saving..."
                : analyzing
                  ? "✨ AI Analyzing..."
                  : "Analyze Job →"}
            </button>

          </div>
        </section>

        {/* Results */}
        {analysis && (
          <div className="mt-5 space-y-5">

            {/* Overview */}
            <section className="rounded-2xl border border-white/10 bg-[#101216] p-6 md:p-7">

              <p className="text-[10px] font-semibold uppercase tracking-[0.2em] text-white/25">
                Overview
              </p>

              <h2 className="mt-2 text-2xl font-semibold">
                {analysis.job_title || "Job opportunity"}
              </h2>

              {analysis.company && (
                <p className="mt-2 text-sm text-white/40">
                  {analysis.company}
                </p>
              )}

            </section>
            <div className="mt-5 flex justify-end">
  <Link
    href={`/match?job_id=${analysis.job_id}`}
    className="rounded-xl bg-white px-5 py-3 text-sm font-semibold text-black transition hover:bg-white/90"
  >
    Analyze Resume Match →
  </Link>
</div>

            {/* Required Skills */}
            <section className="rounded-2xl border border-white/10 bg-[#101216] p-6 md:p-7">

              <p className="text-[10px] font-semibold uppercase tracking-[0.2em] text-white/25">
                Required Skills
              </p>

              <h2 className="mt-2 text-xl font-semibold">
                What the employer is looking for
              </h2>

              <div className="mt-6">
                {analysis.required_skills.length > 0 ? (
                  <div className="flex flex-wrap gap-2">
                    {analysis.required_skills.map(
                      (skill) => (
                        <span
                          key={skill}
                          className="rounded-lg border border-white/10 bg-white/[0.03] px-3 py-2 text-xs text-white/70"
                        >
                          {skill}
                        </span>
                      )
                    )}
                  </div>
                ) : (
                  renderList(
                    analysis.required_skills
                  )
                )}
              </div>

            </section>

            {/* Preferred Skills */}
            <section className="rounded-2xl border border-white/10 bg-[#101216] p-6 md:p-7">

              <p className="text-[10px] font-semibold uppercase tracking-[0.2em] text-white/25">
                Preferred Skills
              </p>

              <h2 className="mt-2 text-xl font-semibold">
                Additional skills
              </h2>

              <div className="mt-6">
                {renderList(
                  analysis.preferred_skills
                )}
              </div>

            </section>

            {/* Education */}
            <section className="rounded-2xl border border-white/10 bg-[#101216] p-6 md:p-7">

              <p className="text-[10px] font-semibold uppercase tracking-[0.2em] text-white/25">
                Education
              </p>

              <h2 className="mt-2 text-xl font-semibold">
                Education requirements
              </h2>

              <div className="mt-6">
                {renderList(
                  analysis.education_requirements
                )}
              </div>

            </section>

            {/* Experience */}
            <section className="rounded-2xl border border-white/10 bg-[#101216] p-6 md:p-7">

              <p className="text-[10px] font-semibold uppercase tracking-[0.2em] text-white/25">
                Experience
              </p>

              <h2 className="mt-2 text-xl font-semibold">
                Experience requirements
              </h2>

              <div className="mt-6">
                {renderList(
                  analysis.experience_requirements
                )}
              </div>

            </section>

            {/* Responsibilities */}
            <section className="rounded-2xl border border-white/10 bg-[#101216] p-6 md:p-7">

              <p className="text-[10px] font-semibold uppercase tracking-[0.2em] text-white/25">
                Responsibilities
              </p>

              <h2 className="mt-2 text-xl font-semibold">
                What you would work on
              </h2>

              <div className="mt-6">
                {renderList(
                  analysis.responsibilities
                )}
              </div>

            </section>

          </div>
        )}

      </div>
    </main>
  );
}