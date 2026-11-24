"use client";

import { Suspense, useEffect, useState } from "react";
import Link from "next/link";
import { useSearchParams } from "next/navigation";

type MatchResult = {
  match_id: number;
  job_id: number;
  overall_score: number;
  skills_score: number;
  experience_score: number;
  education_score: number;
  matching_skills: string[];
  missing_skills: string[];
};

function MatchContent() {
  const searchParams = useSearchParams();

  const jobId = searchParams.get("job_id");

  const [result, setResult] = useState<MatchResult | null>(null);

  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    async function loadMatch() {
      const token = localStorage.getItem("access_token");

      if (!token) {
        window.location.href = "/login";
        return;
      }

      if (!jobId) {
        setError("No job was selected for matching.");
        setLoading(false);
        return;
      }

      try {
        const response = await fetch(
          `http://127.0.0.1:8000/match/${jobId}`,
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
            data.detail || "Could not calculate match."
          );
        }

        setResult(data);
      } catch (error) {
        setError(
          error instanceof Error
            ? error.message
            : "Something went wrong."
        );
      } finally {
        setLoading(false);
      }
    }

    loadMatch();
  }, [jobId]);

  if (loading) {
    return (
      <main className="flex min-h-screen items-center justify-center bg-[#08090b] text-white">
        <div className="text-center">
          <div className="mx-auto h-8 w-8 animate-spin rounded-full border-2 border-white/10 border-t-white" />

          <p className="mt-4 text-sm text-white/40">
            Calculating your match...
          </p>
        </div>
      </main>
    );
  }

  if (error) {
    return (
      <main className="min-h-screen bg-[#08090b] px-5 py-10 text-white">
        <div className="mx-auto max-w-4xl">
          <Link
            href="/dashboard"
            className="text-sm text-white/40 hover:text-white"
          >
            ← Dashboard
          </Link>

          <div className="mt-8 rounded-2xl border border-red-400/20 bg-red-400/5 p-6">
            <p className="text-sm text-red-300">
              {error}
            </p>
          </div>
        </div>
      </main>
    );
  }

  if (!result) {
    return null;
  }

  return (
    <main className="min-h-screen bg-[#08090b] text-white">

      {/* Header */}
      <header className="border-b border-white/10">
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
                MATCH ANALYSIS
              </p>
            </div>
          </Link>

          <Link
            href="/job"
            className="rounded-lg border border-white/10 px-3 py-2 text-xs text-white/50 transition hover:bg-white/5 hover:text-white"
          >
            Analyze another job
          </Link>

        </div>
      </header>

      <div className="mx-auto max-w-5xl px-5 py-10 md:px-8">

        {/* Page Heading */}
        <div>
          <p className="text-xs font-semibold uppercase tracking-[0.2em] text-white/25">
            Match Analysis
          </p>

          <h1 className="mt-3 text-3xl font-semibold tracking-tight md:text-4xl">
            How well does your resume fit?
          </h1>

          <p className="mt-3 text-sm leading-6 text-white/35">
            This analysis compares your structured resume information
            against the requirements extracted from the job description.
          </p>
        </div>

        {/* Overall Score */}
        <section className="mt-10 rounded-2xl border border-white/10 bg-[#101216] p-7 md:p-10">

          <div className="text-center">

            <p className="text-[10px] font-semibold uppercase tracking-[0.2em] text-white/25">
              Overall Match
            </p>

            <div className="mt-5">
              <span className="text-6xl font-semibold tracking-tight">
                {result.overall_score}%
              </span>
            </div>

            <p className="mt-3 text-sm text-white/35">
              Based on skills, experience, and education
            </p>

          </div>

          <div className="mt-10 grid gap-3 sm:grid-cols-3">

            <ScoreCard
              label="Skills"
              score={result.skills_score}
            />

            <ScoreCard
              label="Experience"
              score={result.experience_score}
            />

            <ScoreCard
              label="Education"
              score={result.education_score}
            />

          </div>

        </section>

        {/* Skills */}
        <div className="mt-5 grid gap-5 md:grid-cols-2">

          {/* Matching Skills */}
          <section className="rounded-2xl border border-white/10 bg-[#101216] p-6 md:p-7">

            <p className="text-[10px] font-semibold uppercase tracking-[0.2em] text-white/25">
              Matching Skills
            </p>

            <h2 className="mt-2 text-xl font-semibold">
              Skills you already have
            </h2>

            <div className="mt-6 flex flex-wrap gap-2">

              {result.matching_skills.length > 0 ? (
                result.matching_skills.map((skill) => (
                  <span
                    key={skill}
                    className="rounded-lg border border-emerald-400/20 bg-emerald-400/5 px-3 py-2 text-xs text-emerald-300"
                  >
                    ✓ {skill}
                  </span>
                ))
              ) : (
                <p className="text-sm text-white/30">
                  No matching skills detected.
                </p>
              )}

            </div>

          </section>

          {/* Missing Skills */}
          <section className="rounded-2xl border border-white/10 bg-[#101216] p-6 md:p-7">

            <p className="text-[10px] font-semibold uppercase tracking-[0.2em] text-white/25">
              Skill Gaps
            </p>

            <h2 className="mt-2 text-xl font-semibold">
              Skills to consider developing
            </h2>

            <div className="mt-6 flex flex-wrap gap-2">

              {result.missing_skills.length > 0 ? (
                result.missing_skills.map((skill) => (
                  <span
                    key={skill}
                    className="rounded-lg border border-red-400/20 bg-red-400/5 px-3 py-2 text-xs text-red-300"
                  >
                    × {skill}
                  </span>
                ))
              ) : (
                <p className="text-sm text-white/30">
                  No skill gaps detected.
                </p>
              )}

            </div>

          </section>

        </div>

        {/* Explanation */}
        <section className="mt-5 rounded-2xl border border-white/10 bg-[#101216] p-6 md:p-7">

          <p className="text-[10px] font-semibold uppercase tracking-[0.2em] text-white/25">
            How this score works
          </p>

          <h2 className="mt-2 text-xl font-semibold">
            Explainable matching
          </h2>

          <div className="mt-6 grid gap-4 md:grid-cols-3">

            <Explanation
              title="Skills"
              text="50% of the overall score is based on how your skills match the job requirements."
            />

            <Explanation
              title="Experience"
              text="30% considers the experience requirements extracted from the job description."
            />

            <Explanation
              title="Education"
              text="20% considers compatibility between your education and the job requirements."
            />

          </div>

        </section>

        {/* Actions */}
        <section className="mt-5 flex flex-col gap-3 sm:flex-row sm:flex-wrap">

          {/* NEW: Skill Gap Analysis */}
          <Link
            href={`/skill-gaps?match_id=${result.match_id}`}
            className="rounded-xl bg-white px-5 py-3 text-center text-sm font-semibold text-black transition hover:bg-white/90"
          >
            View Skill Gaps →
          </Link>

          {/* Dashboard */}
          <Link
            href="/dashboard"
            className="rounded-xl border border-white/10 px-5 py-3 text-center text-sm text-white/60 transition hover:bg-white/5 hover:text-white"
          >
            ← Dashboard
          </Link>

          {/* Analyze another job */}
          <Link
            href="/job"
            className="rounded-xl border border-white/10 px-5 py-3 text-center text-sm text-white/60 transition hover:bg-white/5 hover:text-white"
          >
            Analyze Another Job
          </Link>

        </section>

      </div>
    </main>
  );
}


export default function MatchPage() {
  // useSearchParams needs a Suspense boundary for production builds.
  return (
    <Suspense
      fallback={
        <main className="flex min-h-screen items-center justify-center bg-[#08090b] text-white">
          <p className="text-sm text-white/40">Loading...</p>
        </main>
      }
    >
      <MatchContent />
    </Suspense>
  );
}

/* ------------------------------------------------ */
/* Score Card */
/* ------------------------------------------------ */

function ScoreCard({
  label,
  score,
}: {
  label: string;
  score: number;
}) {
  return (
    <div className="rounded-xl border border-white/10 bg-white/[0.02] p-5 text-center">

      <p className="text-[10px] font-semibold uppercase tracking-[0.15em] text-white/25">
        {label}
      </p>

      <p className="mt-3 text-2xl font-semibold">
        {score}%
      </p>

    </div>
  );
}


/* ------------------------------------------------ */
/* Explanation */
/* ------------------------------------------------ */

function Explanation({
  title,
  text,
}: {
  title: string;
  text: string;
}) {
  return (
    <div className="rounded-xl border border-white/10 bg-white/[0.02] p-5">

      <p className="text-sm font-semibold">
        {title}
      </p>

      <p className="mt-2 text-xs leading-5 text-white/30">
        {text}
      </p>

    </div>
  );
}