
"use client";

import { Suspense, useEffect, useRef, useState } from "react";
import type { ReactNode } from "react";
import Link from "next/link";
import { useRouter, useSearchParams } from "next/navigation";

import { ApiError, apiFetch } from "../../lib/api";

/* ------------------------------------------------ */
/* Types                                            */
/* ------------------------------------------------ */

type Progress = {
  completed_tasks: number;
  total_tasks: number;
  percent: number;
};

type Resource = {
  title: string;
  type: string;
};

type PlanSkill = {
  skill: string;
  category: string;
  priority: string;
  difficulty: string;
  why_it_matters: string | null;
  starting_point: string | null;
  estimated_hours: number;
  prerequisites: string[];
  learning_objectives: string[];
  beginner_topics: string[];
  intermediate_topics: string[];
  advanced_topics: string[];
  practical_exercises: string[];
  mini_project: string | null;
  resources: Resource[];
  expected_outcome: string | null;
};

type PlanTask = {
  task_id: number;
  task_type: string;
  description: string;
  estimated_hours: number;
  is_completed: boolean;
  completed_at: string | null;
};

type PlanWeek = {
  week_id: number;
  week_number: number;
  skill: string;
  title: string;
  expected_outcome: string | null;
  tasks: PlanTask[];
};

type LearningPlan = {
  plan_id: number;
  match_id: number;
  job_id: number;
  title: string;
  overview: string | null;
  hours_per_week: number;
  total_weeks: number;
  total_hours: number;
  created_at: string;
  progress: Progress;
  skills: PlanSkill[];
  weeks: PlanWeek[];
  created?: boolean;
};

type PlanSummary = {
  plan_id: number;
  match_id: number;
  job_id: number;
  title: string;
  job_title: string | null;
  company: string | null;
  total_weeks: number;
  total_hours: number;
  created_at: string;
  progress: Progress;
};

type TaskUpdateResponse = {
  task_id: number;
  is_completed: boolean;
  completed_at: string | null;
  progress: Progress;
};

type SkillGapPreview = {
  skill_gap_count: number;
  skill_gaps: { skill: string; priority: string }[];
};

type ResumeSuggestion = {
  id: number;
  skill: string;
  evidence_level: "Learned" | "Practiced" | "Demonstrated";
  suggestion_text: string;
  source_task_ids: number[];
  is_selected: boolean;
  is_approved: boolean;
};

type ResumeSuggestionsResponse = {
  plan_id: number;
  suggestions: ResumeSuggestion[];
};

type ResumeApprovalResponse = {
  message: string;
  approved_additions: ResumeSuggestion[];
};

type Notice = {
  type: "success" | "error";
  text: string;
};

/* ------------------------------------------------ */
/* Small helpers                                    */
/* ------------------------------------------------ */

const HOUR_OPTIONS = [3, 5, 8, 10, 15, 20, 30];

function hourOptions(current: number): number[] {
  return HOUR_OPTIONS.includes(current)
    ? HOUR_OPTIONS
    : [...HOUR_OPTIONS, current].sort((a, b) => a - b);
}

function messageOf(error: unknown): string {
  return error instanceof Error
    ? error.message
    : "Something went wrong.";
}

function formatDate(value: string): string {
  const date = new Date(value);

  if (Number.isNaN(date.getTime())) {
    return "";
  }

  return date.toLocaleDateString(undefined, {
    year: "numeric",
    month: "short",
    day: "numeric",
  });
}

function searchUrl(title: string, skill: string): string {
  return `https://www.google.com/search?q=${encodeURIComponent(
    `${title} ${skill}`
  )}`;
}

/* ------------------------------------------------ */
/* Page                                             */
/* ------------------------------------------------ */

export default function LearningPlanPage() {
  return (
    <Suspense fallback={<FullPageMessage text="Loading..." />}>
      <LearningPlanContent />
    </Suspense>
  );
}

function LearningPlanContent() {
  const searchParams = useSearchParams();
  const matchParam = searchParams.get("match_id");

  if (matchParam === null) {
    return <PlanList />;
  }

  const matchId = Number(matchParam);

  if (!Number.isInteger(matchId) || matchId <= 0) {
    return (
      <PageShell backHref="/learning-plan" backLabel="← My plans">
        <ErrorCard text="This learning plan link is not valid." />
      </PageShell>
    );
  }

  return <PlanDetail matchId={matchId} />;
}

/* ------------------------------------------------ */
/* List of the user's plans                         */
/* ------------------------------------------------ */

function PlanList() {
  const [plans, setPlans] = useState<PlanSummary[] | null>(null);
  const [error, setError] = useState("");

  useEffect(() => {
    let cancelled = false;

    async function load() {
      try {
        const data = await apiFetch<{ plans: PlanSummary[] }>(
          "/learning-plans"
        );

        if (!cancelled) {
          setPlans(data.plans);
        }
      } catch (err) {
        if (!cancelled) {
          setError(messageOf(err));
        }
      }
    }

    load();

    return () => {
      cancelled = true;
    };
  }, []);

  return (
    <PageShell backHref="/dashboard" backLabel="← Dashboard">
      <Heading
        eyebrow="Learning Plans"
        title="Your learning plans"
        text="Continue a plan where you left off, or create a new one from the skill gaps of a job match."
      />

      <div className="mt-10">
        {error ? (
          <ErrorCard text={error} />
        ) : plans === null ? (
          <Spinner text="Loading your plans..." />
        ) : plans.length === 0 ? (
          <Card>
            <h2 className="text-xl font-semibold">
              No learning plans yet
            </h2>

            <p className="mt-3 text-sm leading-6 text-white/40">
              Analyze a job, calculate your match and open the Skill Gaps
              page. From there you can create a personalized plan.
            </p>

            <Link
              href="/job"
              className="mt-6 inline-block rounded-xl bg-white px-5 py-3 text-sm font-semibold text-black transition hover:bg-white/90"
            >
              Analyze a job →
            </Link>
          </Card>
        ) : (
          <div className="space-y-4">
            {plans.map((plan) => (
              <Link
                key={plan.plan_id}
                href={`/learning-plan?match_id=${plan.match_id}`}
                className="block rounded-2xl border border-white/10 bg-[#101216] p-6 transition hover:border-white/20"
              >
                <div className="flex flex-col gap-1 sm:flex-row sm:items-start sm:justify-between">
                  <div>
                    <h2 className="text-lg font-semibold">
                      {plan.job_title || plan.title}
                    </h2>

                    {plan.company && (
                      <p className="mt-1 text-sm text-white/40">
                        {plan.company}
                      </p>
                    )}
                  </div>

                  <p className="text-xs text-white/30">
                    Created {formatDate(plan.created_at)}
                  </p>
                </div>

                <div className="mt-5">
                  <ProgressBar percent={plan.progress.percent} />

                  <div className="mt-2 flex flex-wrap justify-between gap-2 text-xs text-white/40">
                    <span>
                      {plan.progress.completed_tasks} of{" "}
                      {plan.progress.total_tasks} tasks done
                    </span>

                    <span>
                      {plan.total_weeks} weeks · {plan.total_hours} hours
                    </span>
                  </div>
                </div>

                <p className="mt-4 text-sm font-semibold text-white/70">
                  Continue →
                </p>
              </Link>
            ))}
          </div>
        )}
      </div>
    </PageShell>
  );
}

/* ------------------------------------------------ */
/* One plan (or the "create plan" step)             */
/* ------------------------------------------------ */

type Status = "loading" | "ready" | "empty" | "error";

function PlanDetail({ matchId }: { matchId: number }) {
  const router = useRouter();

  const [status, setStatus] = useState<Status>("loading");
  const [error, setError] = useState("");

  const [plan, setPlan] = useState<LearningPlan | null>(null);
  const [gaps, setGaps] = useState<SkillGapPreview | null>(null);

  const [hours, setHours] = useState(8);
  const [view, setView] = useState<"roadmap" | "skills">("roadmap");

  const [generating, setGenerating] = useState(false);
  const [elapsed, setElapsed] = useState(0);
  const [deleting, setDeleting] = useState(false);
  const [pendingTasks, setPendingTasks] = useState<number[]>([]);
  const [notice, setNotice] = useState<Notice | null>(null);

  // Resume suggestions
  const [resumeSuggestions, setResumeSuggestions] = useState<
    ResumeSuggestion[]
  >([]);
  const [suggestionsLoading, setSuggestionsLoading] = useState(false);
  const [suggestionsSaving, setSuggestionsSaving] = useState(false);
  const [suggestionsGenerated, setSuggestionsGenerated] = useState(false);

  const generatingRef = useRef(false);

  /* Load the saved plan. The AI is NOT called here. */
  useEffect(() => {
    let cancelled = false;

    async function load() {
      setStatus("loading");
      setError("");

      try {
        const data = await apiFetch<LearningPlan>(
          `/learning-plans/by-match/${matchId}`
        );

        if (cancelled) return;

        setPlan(data);
        setHours(data.hours_per_week);
        setStatus("ready");

        // Load previously generated suggestions for completed plans.
        if (data.progress.percent === 100) {
          try {
            const suggestions =
              await apiFetch<ResumeSuggestionsResponse>(
                `/learning-plans/${data.plan_id}/resume-suggestions`
              );

            if (!cancelled) {
              setResumeSuggestions(suggestions.suggestions);
              setSuggestionsGenerated(
                suggestions.suggestions.length > 0
              );
            }
          } catch (suggestionError) {
            console.error(
              "Could not load saved resume suggestions:",
              suggestionError
            );
          }
        }
      } catch (err) {
        if (cancelled) return;

        if (err instanceof ApiError && err.status === 404) {
          try {
            const preview = await apiFetch<SkillGapPreview>(
              `/skill-gaps/${matchId}`,
              { method: "POST" }
            );

            if (!cancelled) {
              setGaps(preview);
              setStatus("empty");
            }
          } catch (gapError) {
            if (!cancelled) {
              setError(messageOf(gapError));
              setStatus("error");
            }
          }

          return;
        }

        setError(messageOf(err));
        setStatus("error");
      }
    }

    load();

    return () => {
      cancelled = true;
    };
  }, [matchId]);

  /* Seconds counter shown while the AI is working. */
  useEffect(() => {
    if (!generating) return;

    const timer = window.setInterval(() => {
      setElapsed((seconds) => seconds + 1);
    }, 1000);

    return () => window.clearInterval(timer);
  }, [generating]);

  /* Generate a learning plan. */
  async function generate(regenerate: boolean) {
    if (generatingRef.current) return;

    generatingRef.current = true;
    setElapsed(0);
    setGenerating(true);
    setNotice(null);

    try {
      const data = await apiFetch<LearningPlan>("/learning-plans", {
        method: "POST",
        body: JSON.stringify({
          match_id: matchId,
          hours_per_week: hours,
          regenerate,
        }),
      });

      setPlan(data);
      setStatus("ready");
      setView("roadmap");

      // A regenerated plan has new task evidence.
      if (regenerate) {
        setResumeSuggestions([]);
        setSuggestionsGenerated(false);
      }

      setNotice({
        type: "success",
        text:
          data.created === false
            ? "Your saved learning plan was opened."
            : regenerate
              ? "Your learning plan was regenerated."
              : "Your learning plan is ready.",
      });
    } catch (err) {
      setNotice({ type: "error", text: messageOf(err) });
    } finally {
      generatingRef.current = false;
      setGenerating(false);
    }
  }

  function handleRegenerate() {
    const confirmed = window.confirm(
      "Regenerate this plan? A new plan will replace the current one and your completed tasks will be reset."
    );

    if (confirmed) {
      generate(true);
    }
  }

  /* ------------------------------------------------ */
  /* Resume suggestion functions                      */
  /* ------------------------------------------------ */

  async function loadResumeSuggestions(planId: number) {
    try {
      const data = await apiFetch<ResumeSuggestionsResponse>(
        `/learning-plans/${planId}/resume-suggestions`
      );

      setResumeSuggestions(data.suggestions);
      setSuggestionsGenerated(data.suggestions.length > 0);
    } catch (err) {
      console.error("Could not load resume suggestions:", err);
    }
  }

  async function generateResumeSuggestions() {
    if (!plan || plan.progress.percent !== 100) return;

    setSuggestionsLoading(true);
    setNotice(null);

    try {
      const data = await apiFetch<ResumeSuggestionsResponse>(
        `/learning-plans/${plan.plan_id}/resume-suggestions`,
        { method: "POST" }
      );

      setResumeSuggestions(data.suggestions);
      setSuggestionsGenerated(true);

      setNotice({
        type: "success",
        text:
          "Your resume suggestions are ready. Review and edit them before approving.",
      });
    } catch (err) {
      setNotice({
        type: "error",
        text: messageOf(err),
      });
    } finally {
      setSuggestionsLoading(false);
    }
  }

  function updateSuggestion(
    id: number,
    changes: Partial<
      Pick<ResumeSuggestion, "suggestion_text" | "is_selected">
    >
  ) {
    setResumeSuggestions((current) =>
      current.map((item) =>
        item.id === id ? { ...item, ...changes } : item
      )
    );
  }

  async function approveResumeSuggestions() {
    if (!plan) return;

    const selected = resumeSuggestions.filter(
      (item) => item.is_selected && !item.is_approved
    );

    if (selected.length === 0) {
      setNotice({
        type: "error",
        text: "Select at least one suggestion before approving.",
      });
      return;
    }

    setSuggestionsSaving(true);
    setNotice(null);

    try {
      // Save the edited text and selection before approval.
      for (const item of selected) {
        await apiFetch<ResumeSuggestion>(
          `/learning-plans/resume-suggestions/${item.id}`,
          {
            method: "PATCH",
            body: JSON.stringify({
              suggestion_text: item.suggestion_text,
              is_selected: item.is_selected,
            }),
          }
        );
      }

      // Explicit approval is a separate action.
      const result = await apiFetch<ResumeApprovalResponse>(
        `/learning-plans/${plan.plan_id}/resume-suggestions/approve`,
        { method: "POST" }
      );

      setResumeSuggestions((current) =>
        current.map((item) => ({
          ...item,
          is_approved: result.approved_additions.some(
            (approved) => approved.id === item.id
          ),
        }))
      );

      setNotice({
        type: "success",
        text: `${result.approved_additions.length} resume suggestion(s) approved successfully.`,
      });
    } catch (err) {
      setNotice({
        type: "error",
        text: messageOf(err),
      });
    } finally {
      setSuggestionsSaving(false);
    }
  }

  /* ------------------------------------------------ */
  /* Task completion                                  */
  /* ------------------------------------------------ */

  async function toggleTask(task: PlanTask) {
    if (pendingTasks.includes(task.task_id)) return;

    setPendingTasks((ids) => [...ids, task.task_id]);

    try {
      const result = await apiFetch<TaskUpdateResponse>(
        `/learning-plans/tasks/${task.task_id}`,
        {
          method: "PATCH",
          body: JSON.stringify({ completed: !task.is_completed }),
        }
      );

      setPlan((current) =>
        current
          ? {
              ...current,
              progress: result.progress,
              weeks: current.weeks.map((week) => ({
                ...week,
                tasks: week.tasks.map((item) =>
                  item.task_id === result.task_id
                    ? {
                        ...item,
                        is_completed: result.is_completed,
                        completed_at: result.completed_at,
                      }
                    : item
                ),
              })),
            }
          : current
      );

      // If the final task was completed, load any existing suggestions.
      if (result.progress.percent === 100 && plan) {
        await loadResumeSuggestions(plan.plan_id);
      }
    } catch (err) {
      setNotice({
        type: "error",
        text: messageOf(err),
      });
    } finally {
      setPendingTasks((ids) =>
        ids.filter((id) => id !== task.task_id)
      );
    }
  }

  /* ------------------------------------------------ */
  /* Delete plan                                      */
  /* ------------------------------------------------ */

  async function deletePlan() {
    if (!plan) return;

    const confirmed = window.confirm(
      "Delete this learning plan and all of its progress? This cannot be undone."
    );

    if (!confirmed) return;

    setDeleting(true);

    try {
      await apiFetch<{ message: string }>(
        `/learning-plans/${plan.plan_id}`,
        { method: "DELETE" }
      );

      router.push("/learning-plan");
    } catch (err) {
      setNotice({
        type: "error",
        text: messageOf(err),
      });
      setDeleting(false);
    }
  }

  const backHref = `/skill-gaps?match_id=${matchId}`;

  /* ---------- loading / error ---------- */

  if (status === "loading") {
    return (
      <PageShell backHref={backHref} backLabel="← Skill Gaps">
        <Spinner text="Loading your learning plan..." />
      </PageShell>
    );
  }

  if (status === "error") {
    return (
      <PageShell backHref={backHref} backLabel="← Skill Gaps">
        <ErrorCard text={error} />
      </PageShell>
    );
  }

  /* ---------- no plan yet ---------- */

  if (status === "empty") {
    const total = gaps?.skill_gap_count ?? 0;

    const high = (gaps?.skill_gaps ?? []).filter(
      (gap) => gap.priority === "High"
    );

    return (
      <PageShell backHref={backHref} backLabel="← Skill Gaps">
        <Heading
          eyebrow="Learning Plan"
          title="Create your learning plan"
          text="A personalized roadmap built from your resume, the target job and your skill gaps."
        />

        <NoticeBanner notice={notice} />

        <div className="mt-10">
          <Card>
            {total === 0 ? (
              <>
                <h2 className="text-xl font-semibold">
                  No skill gaps to plan
                </h2>

                <p className="mt-3 text-sm leading-6 text-white/40">
                  Your resume already covers the skills this job asks for,
                  so there is nothing to learn for this match.
                </p>
              </>
            ) : (
              <>
                <p className="text-[10px] font-semibold uppercase tracking-[0.2em] text-white/25">
                  What the plan is based on
                </p>

                <h2 className="mt-2 text-xl font-semibold">
                  {total} skill {total === 1 ? "gap" : "gaps"} found
                </h2>

                <p className="mt-3 text-sm leading-6 text-white/40">
                  The plan covers the most important gaps (up to 6, high
                  priority first), and adapts to the skills, education and
                  experience on your resume.
                </p>

                {high.length > 0 && (
                  <div className="mt-5 flex flex-wrap gap-2">
                    {high.slice(0, 8).map((gap) => (
                      <span
                        key={gap.skill}
                        className="rounded-lg border border-white/10 bg-white/3 px-3 py-2 text-xs text-white/70"
                      >
                        {gap.skill}
                      </span>
                    ))}

                    {high.length > 8 && (
                      <span className="px-2 py-2 text-xs text-white/30">
                        +{high.length - 8} more
                      </span>
                    )}
                  </div>
                )}

                <div className="mt-8">
                  <label
                    htmlFor="hours-per-week"
                    className="text-sm text-white/60"
                  >
                    How many hours per week can you study?
                  </label>

                  <select
                    id="hours-per-week"
                    value={hours}
                    onChange={(event) =>
                      setHours(Number(event.target.value))
                    }
                    disabled={generating}
                    className="mt-2 block w-full rounded-xl border border-white/10 bg-[#08090b] px-4 py-3 text-sm text-white outline-none focus:border-white/20 sm:w-60"
                  >
                    {hourOptions(hours).map((option) => (
                      <option key={option} value={option}>
                        {option} hours per week
                      </option>
                    ))}
                  </select>
                </div>

                {generating && <GeneratingBanner seconds={elapsed} />}

                <button
                  onClick={() => generate(false)}
                  disabled={generating}
                  className="mt-6 rounded-xl bg-white px-5 py-3 text-sm font-semibold text-black transition hover:bg-white/90 disabled:cursor-not-allowed disabled:opacity-50"
                >
                  {generating
                    ? "✨ Creating your plan..."
                    : "Create learning plan →"}
                </button>
              </>
            )}
          </Card>
        </div>
      </PageShell>
    );
  }

  /* ---------- the plan ---------- */

  if (!plan) {
    return null;
  }

  const currentWeek = plan.weeks.find((week) =>
    week.tasks.some((task) => !task.is_completed)
  );

  return (
    <PageShell backHref={backHref} backLabel="← Skill Gaps">
      <Heading
        eyebrow="Learning Plan"
        title={plan.title}
        text={plan.overview || "Your personalized roadmap."}
      />

      <NoticeBanner notice={notice} />

      {/* Overview and progress */}
      <section className="mt-10 rounded-2xl border border-white/10 bg-[#101216] p-6 md:p-8">
        <div className="flex items-end justify-between gap-4">
          <div>
            <p className="text-[10px] font-semibold uppercase tracking-[0.2em] text-white/25">
              Overall progress
            </p>

            <p className="mt-2 text-4xl font-semibold tracking-tight">
              {plan.progress.percent}%
            </p>
          </div>

          <p className="text-sm text-white/40">
            {plan.progress.completed_tasks} of {plan.progress.total_tasks}{" "}
            tasks completed
          </p>
        </div>

        <div className="mt-5">
          <ProgressBar percent={plan.progress.percent} />
        </div>

        <div className="mt-8 grid gap-3 sm:grid-cols-3">
          <Stat label="Duration" value={`${plan.total_weeks} weeks`} />
          <Stat label="Total effort" value={`${plan.total_hours} hours`} />
          <Stat
            label="Pace"
            value={`${plan.hours_per_week} hours / week`}
          />
        </div>

        {generating && <GeneratingBanner seconds={elapsed} />}

        <div className="mt-8 flex flex-col gap-3 border-t border-white/10 pt-6 sm:flex-row sm:flex-wrap sm:items-center">
          <label htmlFor="hours-per-week" className="text-sm text-white/40">
            Hours per week
          </label>

          <select
            id="hours-per-week"
            value={hours}
            onChange={(event) => setHours(Number(event.target.value))}
            disabled={generating || deleting}
            className="rounded-xl border border-white/10 bg-[#08090b] px-3 py-2 text-sm text-white outline-none focus:border-white/20"
          >
            {hourOptions(hours).map((option) => (
              <option key={option} value={option}>
                {option}
              </option>
            ))}
          </select>

          <button
            onClick={handleRegenerate}
            disabled={generating || deleting}
            className="rounded-xl border border-white/10 px-4 py-2 text-sm text-white/60 transition hover:bg-white/5 hover:text-white disabled:cursor-not-allowed disabled:opacity-50"
          >
            {generating ? "Regenerating..." : "Regenerate plan"}
          </button>

          <button
            onClick={deletePlan}
            disabled={generating || deleting}
            className="rounded-xl border border-red-400/20 px-4 py-2 text-sm text-red-300 transition hover:bg-red-400/5 disabled:cursor-not-allowed disabled:opacity-50 sm:ml-auto"
          >
            {deleting ? "Deleting..." : "Delete plan"}
          </button>
        </div>
      </section>

      {/* Resume suggestions: only visible at 100% */}
      {plan.progress.percent === 100 && (
        <section className="mt-8 rounded-2xl border border-emerald-400/20 bg-[#101216] p-6 md:p-8">
          <p className="text-[10px] font-semibold uppercase tracking-[0.2em] text-emerald-300/60">
            Learning plan completed
          </p>

          <h2 className="mt-3 text-xl font-semibold">
            Add these skills to my resume
          </h2>

          <p className="mt-2 max-w-2xl text-sm leading-6 text-white/40">
            You have completed your learning roadmap. Review the
            suggestions below, edit their wording and approve only the
            statements that accurately describe what you accomplished.
            Your original uploaded resume will remain unchanged.
          </p>

          {!suggestionsGenerated && (
            <button
              onClick={generateResumeSuggestions}
              disabled={suggestionsLoading}
              className="mt-6 rounded-xl bg-white px-5 py-3 text-sm font-semibold text-black transition hover:bg-white/90 disabled:cursor-not-allowed disabled:opacity-50"
            >
              {suggestionsLoading
                ? "Generating suggestions..."
                : "Add these skills to my resume →"}
            </button>
          )}

          {suggestionsGenerated && (
            <div className="mt-6 space-y-6">
              {resumeSuggestions.length === 0 ? (
                <p className="rounded-xl border border-white/10 bg-white/3 p-4 text-sm text-white/50">
                  No completed task evidence was available to create
                  suggestions.
                </p>
              ) : (
                <>
                  {(
                    [
                      {
                        level: "Learned",
                        description:
                          "Knowledge gained through completed learning activities.",
                      },
                      {
                        level: "Practiced",
                        description:
                          "Skills practiced through completed exercises.",
                      },
                      {
                        level: "Demonstrated",
                        description:
                          "Skills applied in completed practical projects.",
                      },
                    ] as const
                  ).map((group) => {
                    const items = resumeSuggestions.filter(
                      (item) => item.evidence_level === group.level
                    );

                    if (items.length === 0) return null;

                    return (
                      <div key={group.level}>
                        <h3 className="text-sm font-semibold text-white/80">
                          {group.level}
                        </h3>

                        <p className="mt-1 text-xs text-white/35">
                          {group.description}
                        </p>

                        <div className="mt-3 space-y-3">
                          {items.map((item) => (
                            <div
                              key={item.id}
                              className="rounded-xl border border-white/10 bg-white/2 p-4"
                            >
                              <div className="flex items-start gap-3">
                                <input
                                  type="checkbox"
                                  checked={item.is_selected}
                                  disabled={
                                    item.is_approved || suggestionsSaving
                                  }
                                  onChange={(event) =>
                                    updateSuggestion(item.id, {
                                      is_selected: event.target.checked,
                                    })
                                  }
                                  className="mt-1 h-4 w-4 shrink-0 accent-white"
                                />

                                <div className="min-w-0 flex-1">
                                  <div className="flex flex-wrap items-center justify-between gap-2">
                                    <p className="text-sm font-semibold text-white/80">
                                      {item.skill}
                                    </p>

                                    {item.is_approved && (
                                      <span className="rounded-full border border-emerald-400/20 bg-emerald-400/5 px-2 py-1 text-[10px] text-emerald-300">
                                        Approved
                                      </span>
                                    )}
                                  </div>

                                  <textarea
                                    value={item.suggestion_text}
                                    disabled={
                                      item.is_approved || suggestionsSaving
                                    }
                                    onChange={(event) =>
                                      updateSuggestion(item.id, {
                                        suggestion_text: event.target.value,
                                      })
                                    }
                                    rows={3}
                                    maxLength={1000}
                                    className="mt-3 w-full resize-y rounded-lg border border-white/10 bg-[#08090b] px-3 py-3 text-sm leading-6 text-white/70 outline-none focus:border-white/30 disabled:opacity-50"
                                  />

                                  <p className="mt-2 text-[10px] text-white/25">
                                    Based on {item.source_task_ids.length}{" "}
                                    completed task(s)
                                  </p>
                                </div>
                              </div>
                            </div>
                          ))}
                        </div>
                      </div>
                    );
                  })}

                  <div className="border-t border-white/10 pt-5">
                    <p className="text-xs leading-5 text-white/35">
                      Only approve statements that accurately describe
                      what you completed. Learning and practice do not
                      automatically mean professional work experience.
                    </p>

                    <button
                      onClick={approveResumeSuggestions}
                      disabled={
                        suggestionsSaving ||
                        !resumeSuggestions.some(
                          (item) =>
                            item.is_selected && !item.is_approved
                        )
                      }
                      className="mt-5 rounded-xl bg-white px-5 py-3 text-sm font-semibold text-black transition hover:bg-white/90 disabled:cursor-not-allowed disabled:opacity-40"
                    >
                      {suggestionsSaving
                        ? "Saving approved suggestions..."
                        : "Approve selected suggestions"}
                    </button>
                  </div>
                </>
              )}
            </div>
          )}
        </section>
      )}

      {/* Tabs */}
      <div
        role="tablist"
        className="mt-8 inline-flex rounded-xl border border-white/10 bg-white/2 p-1"
      >
        <TabButton
          active={view === "roadmap"}
          onClick={() => setView("roadmap")}
        >
          Weekly roadmap
        </TabButton>

        <TabButton
          active={view === "skills"}
          onClick={() => setView("skills")}
        >
          Skills ({plan.skills.length})
        </TabButton>
      </div>

      {/* Weekly roadmap */}
      {view === "roadmap" && (
        <div className="mt-5 space-y-4">
          {!currentWeek && (
            <div className="rounded-2xl border border-emerald-400/20 bg-emerald-400/5 px-5 py-4 text-sm text-emerald-300">
              You completed every task in this plan.
            </div>
          )}

          {plan.weeks.map((week) => {
            const done = week.tasks.filter(
              (task) => task.is_completed
            ).length;

            const isCurrent = currentWeek?.week_id === week.week_id;

            return (
              <section
                key={week.week_id}
                className={`rounded-2xl border p-6 ${
                  isCurrent
                    ? "border-white/25 bg-[#12151a]"
                    : "border-white/10 bg-[#101216]"
                }`}
              >
                <div className="flex flex-wrap items-start justify-between gap-3">
                  <div>
                    <p className="text-[10px] font-semibold uppercase tracking-[0.2em] text-white/25">
                      Week {week.week_number}
                      {isCurrent && (
                        <span className="ml-2 rounded-full bg-white px-2 py-0.5 text-[10px] font-semibold tracking-normal text-black">
                          Current
                        </span>
                      )}
                    </p>

                    <h3 className="mt-2 text-lg font-semibold">
                      {week.title}
                    </h3>
                  </div>

                  <p className="text-xs text-white/40">
                    {done}/{week.tasks.length} done
                  </p>
                </div>

                <ul className="mt-5 space-y-2">
                  {week.tasks.map((task) => (
                    <li key={task.task_id}>
                      <label className="flex cursor-pointer items-start gap-3 rounded-xl border border-white/5 bg-white/2 px-4 py-3 transition hover:border-white/15">
                        <input
                          type="checkbox"
                          checked={task.is_completed}
                          disabled={pendingTasks.includes(task.task_id)}
                          onChange={() => toggleTask(task)}
                          className="mt-1 h-4 w-4 shrink-0 accent-white"
                        />

                        <span
                          className={`text-sm leading-6 ${
                            task.is_completed
                              ? "text-white/30 line-through"
                              : "text-white/70"
                          }`}
                        >
                          {task.description}
                        </span>

                        <span className="ml-auto shrink-0 text-xs text-white/25">
                          ~{task.estimated_hours}h
                        </span>
                      </label>
                    </li>
                  ))}
                </ul>

                {week.expected_outcome && (
                  <p className="mt-5 text-xs leading-5 text-white/35">
                    <span className="font-semibold text-white/50">
                      Expected outcome:{" "}
                    </span>
                    {week.expected_outcome}
                  </p>
                )}
              </section>
            );
          })}
        </div>
      )}

      {/* Skills */}
      {view === "skills" && (
        <div className="mt-5 space-y-4">
          {plan.skills.map((skill, index) => (
            <SkillCard
              key={skill.skill}
              skill={skill}
              defaultOpen={index === 0}
            />
          ))}
        </div>
      )}
    </PageShell>
  );
}

/* ------------------------------------------------ */
/* Skill card                                       */
/* ------------------------------------------------ */

function SkillCard({
  skill,
  defaultOpen,
}: {
  skill: PlanSkill;
  defaultOpen: boolean;
}) {
  return (
    <details
      open={defaultOpen}
      className="group rounded-2xl border border-white/10 bg-[#101216]"
    >
      <summary className="flex cursor-pointer list-none flex-wrap items-center justify-between gap-3 p-6">
        <div>
          <h3 className="text-lg font-semibold">{skill.skill}</h3>

          <p className="mt-1 text-xs text-white/40">
            {skill.category} · {skill.difficulty} ·{" "}
            ~{skill.estimated_hours} hours
          </p>
        </div>

        <span
          className={`rounded-full px-3 py-1 text-xs font-semibold ${
            skill.priority === "High"
              ? "bg-white text-black"
              : "border border-white/10 bg-white/5 text-white/70"
          }`}
        >
          {skill.priority} Priority
        </span>
      </summary>

      <div className="space-y-6 border-t border-white/10 p-6">
        {skill.why_it_matters && (
          <Block title="Why it matters for this job">
            <p className="text-sm leading-6 text-white/60">
              {skill.why_it_matters}
            </p>
          </Block>
        )}

        {skill.starting_point && (
          <Block title="Where to start">
            <p className="text-sm leading-6 text-white/60">
              {skill.starting_point}
            </p>
          </Block>
        )}

        {skill.prerequisites.length > 0 && (
          <Block title="Prerequisites">
            <div className="flex flex-wrap gap-2">
              {skill.prerequisites.map((item) => (
                <span
                  key={item}
                  className="rounded-lg border border-white/10 bg-white/3 px-3 py-2 text-xs text-white/60"
                >
                  {item}
                </span>
              ))}
            </div>
          </Block>
        )}

        {skill.learning_objectives.length > 0 && (
          <Block title="Learning objectives">
            <BulletList items={skill.learning_objectives} />
          </Block>
        )}

        <div className="grid gap-6 md:grid-cols-3">
          <TopicColumn title="Beginner" items={skill.beginner_topics} />
          <TopicColumn
            title="Intermediate"
            items={skill.intermediate_topics}
          />
          <TopicColumn title="Advanced" items={skill.advanced_topics} />
        </div>

        {skill.practical_exercises.length > 0 && (
          <Block title="Practical exercises">
            <BulletList items={skill.practical_exercises} />
          </Block>
        )}

        {skill.mini_project && (
          <Block title="Mini-project">
            <p className="text-sm leading-6 text-white/60">
              {skill.mini_project}
            </p>
          </Block>
        )}

        {skill.resources.length > 0 && (
          <Block title="Recommended resources">
            <ul className="space-y-2">
              {skill.resources.map((resource) => (
                <li
                  key={resource.title}
                  className="flex flex-wrap items-center gap-2 text-sm"
                >
                  <a
                    href={searchUrl(resource.title, skill.skill)}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="text-white/70 underline decoration-white/20 underline-offset-4 hover:text-white"
                  >
                    {resource.title}
                  </a>

                  <span className="rounded-md border border-white/10 px-2 py-0.5 text-[10px] text-white/40">
                    {resource.type}
                  </span>
                </li>
              ))}
            </ul>

            <p className="mt-3 text-xs text-white/25">
              Links open a web search so you always find the current version.
            </p>
          </Block>
        )}

        {skill.expected_outcome && (
          <Block title="Expected outcome">
            <p className="text-sm leading-6 text-white/60">
              {skill.expected_outcome}
            </p>
          </Block>
        )}
      </div>
    </details>
  );
}

/* ------------------------------------------------ */
/* Reusable pieces                                  */
/* ------------------------------------------------ */

function PageShell({
  backHref,
  backLabel,
  children,
}: {
  backHref: string;
  backLabel: string;
  children: ReactNode;
}) {
  return (
    <main className="min-h-screen bg-[#08090b] text-white">
      <header className="border-b border-white/10">
        <div className="flex h-16 items-center justify-between px-5 md:px-8">
          <Link href="/dashboard" className="flex items-center gap-3">
            <div className="flex h-9 w-9 items-center justify-center rounded-xl bg-white text-sm font-black text-black">
              AI
            </div>

            <div className="hidden sm:block">
              <p className="text-sm font-semibold">Career Intelligence</p>

              <p className="text-[10px] text-white/25">LEARNING PLANS</p>
            </div>
          </Link>

          <Link
            href={backHref}
            className="rounded-lg border border-white/10 px-3 py-2 text-xs text-white/50 transition hover:bg-white/5 hover:text-white"
          >
            {backLabel}
          </Link>
        </div>
      </header>

      <div className="mx-auto max-w-5xl px-5 py-10 md:px-8">
        {children}
      </div>
    </main>
  );
}

function Heading({
  eyebrow,
  title,
  text,
}: {
  eyebrow: string;
  title: string;
  text: string;
}) {
  return (
    <div>
      <p className="text-xs font-semibold uppercase tracking-[0.2em] text-white/25">
        {eyebrow}
      </p>

      <h1 className="mt-3 text-3xl font-semibold tracking-tight md:text-4xl">
        {title}
      </h1>

      <p className="mt-3 max-w-2xl text-sm leading-6 text-white/35">
        {text}
      </p>
    </div>
  );
}

function Card({ children }: { children: ReactNode }) {
  return (
    <section className="rounded-2xl border border-white/10 bg-[#101216] p-6 md:p-8">
      {children}
    </section>
  );
}

function Stat({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-xl border border-white/10 bg-white/2 p-4">
      <p className="text-[10px] font-semibold uppercase tracking-[0.15em] text-white/25">
        {label}
      </p>

      <p className="mt-2 text-lg font-semibold">{value}</p>
    </div>
  );
}

function ProgressBar({ percent }: { percent: number }) {
  return (
    <div
      role="progressbar"
      aria-valuenow={percent}
      aria-valuemin={0}
      aria-valuemax={100}
      className="h-2 w-full overflow-hidden rounded-full bg-white/10"
    >
      <div
        className="h-full rounded-full bg-white transition-all"
        style={{ width: `${percent}%` }}
      />
    </div>
  );
}

function TabButton({
  active,
  onClick,
  children,
}: {
  active: boolean;
  onClick: () => void;
  children: ReactNode;
}) {
  return (
    <button
      role="tab"
      aria-selected={active}
      onClick={onClick}
      className={`rounded-lg px-4 py-2 text-sm transition ${
        active
          ? "bg-white font-semibold text-black"
          : "text-white/50 hover:text-white"
      }`}
    >
      {children}
    </button>
  );
}

function Block({
  title,
  children,
}: {
  title: string;
  children: ReactNode;
}) {
  return (
    <div>
      <p className="mb-2 text-[10px] font-semibold uppercase tracking-[0.2em] text-white/25">
        {title}
      </p>

      {children}
    </div>
  );
}

function BulletList({ items }: { items: string[] }) {
  return (
    <ul className="space-y-2">
      {items.map((item) => (
        <li
          key={item}
          className="flex gap-3 text-sm leading-6 text-white/60"
        >
          <span className="mt-2 h-1.5 w-1.5 shrink-0 rounded-full bg-white/40" />
          <span>{item}</span>
        </li>
      ))}
    </ul>
  );
}

function TopicColumn({
  title,
  items,
}: {
  title: string;
  items: string[];
}) {
  return (
    <div>
      <p className="mb-2 text-[10px] font-semibold uppercase tracking-[0.2em] text-white/25">
        {title} topics
      </p>

      {items.length > 0 ? (
        <BulletList items={items} />
      ) : (
        <p className="text-sm text-white/25">
          Skipped. You already have the background.
        </p>
      )}
    </div>
  );
}

function NoticeBanner({ notice }: { notice: Notice | null }) {
  if (!notice) return null;

  const styles =
    notice.type === "success"
      ? "border-emerald-400/20 bg-emerald-400/5 text-emerald-300"
      : "border-red-400/20 bg-red-400/5 text-red-300";

  return (
    <div
      role={notice.type === "error" ? "alert" : "status"}
      className={`mt-6 rounded-xl border px-4 py-3 text-sm ${styles}`}
    >
      {notice.text}
    </div>
  );
}

function GeneratingBanner({ seconds }: { seconds: number }) {
  return (
    <div
      role="status"
      className="mt-6 flex items-center gap-4 rounded-xl border border-white/10 bg-white/3 px-4 py-4"
    >
      <div className="h-5 w-5 shrink-0 animate-spin rounded-full border-2 border-white/10 border-t-white" />

      <p className="text-sm text-white/60">
        Gemini is writing your plan ({seconds}s). This can take up to a
        minute, so please keep this page open.
      </p>
    </div>
  );
}

function Spinner({ text }: { text: string }) {
  return (
    <div className="py-16 text-center">
      <div className="mx-auto h-8 w-8 animate-spin rounded-full border-2 border-white/10 border-t-white" />

      <p className="mt-4 text-sm text-white/40">{text}</p>
    </div>
  );
}

function ErrorCard({ text }: { text: string }) {
  return (
    <div
      role="alert"
      className="rounded-2xl border border-red-400/20 bg-red-400/5 p-6"
    >
      <p className="text-sm text-red-300">{text}</p>
    </div>
  );
}

function FullPageMessage({ text }: { text: string }) {
  return (
    <main className="flex min-h-screen items-center justify-center bg-[#08090b] text-white">
      <p className="text-sm text-white/40">{text}</p>
    </main>
  );
}
