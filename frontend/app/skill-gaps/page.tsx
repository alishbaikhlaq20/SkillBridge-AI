
"use client";

import { Suspense, useEffect, useState } from "react";
import Link from "next/link";
import { useSearchParams } from "next/navigation";

import { apiFetch } from "../../lib/api";

type SkillGap = {
  skill: string;
  category: string;
  priority: string;
  reason: string;
};

type SkillGapResponse = {
  match_id: number;
  job_id: number;
  overall_score: number;
  skill_gap_count: number;
  skill_gaps: SkillGap[];
};

function SkillGapsContent() {
  const searchParams = useSearchParams();
  const matchId = searchParams.get("match_id");

  const [data, setData] = useState<SkillGapResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    async function loadSkillGaps() {
      if (!matchId) {
        setError("No match result was selected.");
        setLoading(false);
        return;
      }

      try {
        const result = await apiFetch<SkillGapResponse>(
          `/skill-gaps/${matchId}`,
          { method: "POST" }
        );

        setData(result);
      } catch (err) {
        setError(
          err instanceof Error
            ? err.message
            : "Something went wrong."
        );
      } finally {
        setLoading(false);
      }
    }

    loadSkillGaps();
  }, [matchId]);

  if (loading) {
    return (
      <main className="min-h-screen bg-black px-6 py-12 text-white">
        <div className="mx-auto max-w-5xl">
          <p className="text-sm text-white/50">
            Analyzing your skill gaps...
          </p>
        </div>
      </main>
    );
  }

  if (error) {
    return (
      <main className="min-h-screen bg-black px-6 py-12 text-white">
        <div className="mx-auto max-w-5xl">
          <div className="rounded-3xl border border-red-500/20 bg-red-500/10 p-8">
            <h1 className="text-xl font-semibold">
              Skill gap analysis failed
            </h1>

            <p className="mt-3 text-sm text-red-200">
              {error}
            </p>

            <Link
              href="/dashboard"
              className="mt-6 inline-block rounded-xl bg-white px-5 py-3 text-sm font-semibold text-black"
            >
              Back to Dashboard
            </Link>
          </div>
        </div>
      </main>
    );
  }

  if (!data) {
    return null;
  }

  const highPriority = data.skill_gaps.filter(
    (gap) => gap.priority === "High"
  );

  const mediumPriority = data.skill_gaps.filter(
    (gap) => gap.priority === "Medium"
  );

  return (
    <main className="min-h-screen bg-black px-6 py-12 text-white">
      <div className="mx-auto max-w-5xl">

        {/* Header */}
        <div className="mb-10">
          <p className="text-sm uppercase tracking-[0.2em] text-white/40">
            AI Career Intelligence
          </p>

          <h1 className="mt-3 text-4xl font-semibold tracking-tight">
            Skill Gap Analysis
          </h1>

          <p className="mt-3 max-w-2xl text-white/60">
            Understand which skills you need to strengthen to
            become a stronger candidate for this position.
          </p>
        </div>

        {/* Summary */}
        <section className="grid gap-4 md:grid-cols-3">

          <SummaryCard
            title="Overall Match"
            value={`${data.overall_score}%`}
            description="Current resume match"
          />

          <SummaryCard
            title="Skill Gaps"
            value={String(data.skill_gap_count)}
            description="Skills to improve"
          />

          <SummaryCard
            title="High Priority"
            value={String(highPriority.length)}
            description="Important gaps"
          />

        </section>

        {/* High Priority Skills */}
        {highPriority.length > 0 && (
          <section className="mt-10">

            <div className="mb-5">
              <h2 className="text-2xl font-semibold">
                High Priority Skills
              </h2>

              <p className="mt-2 text-sm text-white/50">
                These skills have a strong impact on your
                suitability for this position.
              </p>
            </div>

            <div className="space-y-4">
              {highPriority.map((gap) => (
                <SkillGapCard
                  key={gap.skill}
                  gap={gap}
                />
              ))}
            </div>

          </section>
        )}

        {/* Medium Priority Skills */}
        {mediumPriority.length > 0 && (
          <section className="mt-10">

            <div className="mb-5">
              <h2 className="text-2xl font-semibold">
                Medium Priority Skills
              </h2>

              <p className="mt-2 text-sm text-white/50">
                These skills can further strengthen your
                profile.
              </p>
            </div>

            <div className="space-y-4">
              {mediumPriority.map((gap) => (
                <SkillGapCard
                  key={gap.skill}
                  gap={gap}
                />
              ))}
            </div>

          </section>
        )}

        {/* No Gaps */}
        {data.skill_gaps.length === 0 && (
          <section className="mt-10 rounded-3xl border border-white/10 bg-white/[0.04] p-8">
            <h2 className="text-xl font-semibold">
              Excellent match
            </h2>

            <p className="mt-3 text-sm text-white/50">
              No skill gaps were identified for this position.
            </p>
          </section>
        )}

        {/* Actions */}
        <div className="mt-10 flex flex-wrap gap-3">

          {/* Corrected: uses job_id, not match_id */}
          <Link
            href={`/match?job_id=${data.job_id}`}
            className="rounded-xl border border-white/10 px-5 py-3 text-sm font-semibold text-white/70 transition hover:bg-white/5"
          >
            ← Back to Match
          </Link>

          {data.skill_gaps.length > 0 && (
            <Link
              href={`/learning-plan?match_id=${data.match_id}`}
              className="rounded-xl bg-white px-5 py-3 text-sm font-semibold text-black transition hover:bg-white/90"
            >
              Create Learning Plan →
            </Link>
          )}

          <Link
            href="/dashboard"
            className="rounded-xl border border-white/10 px-5 py-3 text-sm font-semibold text-white/70 transition hover:bg-white/5"
          >
            Dashboard
          </Link>

        </div>

      </div>
    </main>
  );
}

export default function SkillGapsPage() {
  return (
    <Suspense
      fallback={
        <main className="min-h-screen bg-black px-6 py-12 text-white">
          <p className="text-sm text-white/50">Loading...</p>
        </main>
      }
    >
      <SkillGapsContent />
    </Suspense>
  );
}

/* ------------------------------------------------ */
/* Summary Card */
/* ------------------------------------------------ */

function SummaryCard({
  title,
  value,
  description,
}: {
  title: string;
  value: string;
  description: string;
}) {
  return (
    <div className="rounded-3xl border border-white/10 bg-white/[0.04] p-6">
      <p className="text-sm text-white/50">
        {title}
      </p>

      <p className="mt-3 text-3xl font-semibold">
        {value}
      </p>

      <p className="mt-2 text-xs text-white/40">
        {description}
      </p>
    </div>
  );
}

/* ------------------------------------------------ */
/* Skill Gap Card */
/* ------------------------------------------------ */

function SkillGapCard({
  gap,
}: {
  gap: SkillGap;
}) {
  return (
    <div className="rounded-3xl border border-white/10 bg-white/[0.04] p-7">

      <div className="flex flex-col gap-5 md:flex-row md:items-start md:justify-between">

        <div>
          <h3 className="text-xl font-semibold">
            {gap.skill}
          </h3>

          <p className="mt-2 text-sm text-white/50">
            {gap.category}
          </p>
        </div>

        <span
          className={`w-fit rounded-full px-3 py-1 text-xs font-semibold ${
            gap.priority === "High"
              ? "bg-white text-black"
              : "border border-white/10 bg-white/5 text-white/70"
          }`}
        >
          {gap.priority} Priority
        </span>

      </div>

      <div className="mt-5 border-t border-white/10 pt-5">
        <p className="text-sm leading-6 text-white/60">
          {gap.reason}
        </p>
      </div>

    </div>
  );
}
