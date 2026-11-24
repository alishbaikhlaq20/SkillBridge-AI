"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";

type Profile = {
  user_id: number;
  email: string;
  full_name: string;
};

export default function DashboardPage() {
  const router = useRouter();

  const [profile, setProfile] = useState<Profile | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function loadProfile() {
      const token = localStorage.getItem("access_token");

      if (!token) {
        router.push("/login");
        return;
      }

      try {
        const response = await fetch(
          "http://127.0.0.1:8000/profile",
          {
            headers: {
              Authorization: `Bearer ${token}`,
            },
          }
        );

        if (!response.ok) {
          localStorage.removeItem("access_token");
          router.push("/login");
          return;
        }

        const data = await response.json();
        setProfile(data);
      } catch {
        console.error("Could not load profile");
      } finally {
        setLoading(false);
      }
    }

    loadProfile();
  }, [router]);

  function logout() {
    localStorage.removeItem("access_token");
    router.push("/login");
  }

  if (loading) {
    return (
      <main className="flex min-h-screen items-center justify-center bg-[#08090b] text-white">
        <div className="text-center">
          <div className="mx-auto h-8 w-8 animate-spin rounded-full border-2 border-white/10 border-t-white" />

          <p className="mt-4 text-sm text-white/40">
            Loading your workspace...
          </p>
        </div>
      </main>
    );
  }

  return (
    <main className="min-h-screen bg-[#08090b] text-white">

      {/* Top navigation */}
      <header className="border-b border-white/10 bg-[#08090b]/95">
        <div className="flex h-16 items-center justify-between px-5 md:px-8">

          <button
            onClick={() => router.push("/")}
            className="flex items-center gap-3 text-left"
          >
            <div className="flex h-9 w-9 items-center justify-center rounded-xl bg-white text-sm font-black text-black">
              AI
            </div>

            <div className="hidden sm:block">
              <p className="text-sm font-semibold">
                Career Intelligence
              </p>

              <p className="text-[10px] text-white/25">
                PERSONAL WORKSPACE
              </p>
            </div>
          </button>

          <div className="flex items-center gap-4">

            <div className="hidden text-right sm:block">
              <p className="text-xs font-medium">
                {profile?.full_name}
              </p>

              <p className="text-[10px] text-white/30">
                {profile?.email}
              </p>
            </div>

            <button
              onClick={logout}
              className="rounded-lg border border-white/10 px-3 py-2 text-xs text-white/50 transition hover:bg-white/5 hover:text-white"
            >
              Logout
            </button>

          </div>
        </div>
      </header>

      <div className="mx-auto max-w-7xl px-5 py-8 md:px-8 md:py-10">

        {/* Welcome */}
        <div className="flex flex-col justify-between gap-5 md:flex-row md:items-end">

          <div>
            <p className="text-xs font-semibold uppercase tracking-[0.2em] text-white/25">
              Overview
            </p>

            <h1 className="mt-3 text-3xl font-semibold tracking-tight md:text-4xl">
              Welcome back, {profile?.full_name?.split(" ")[0]}.
            </h1>

            <p className="mt-2 text-sm text-white/35">
              Here is an overview of your career intelligence workspace.
            </p>
          </div>

          <div className="text-xs text-white/25">
            Your personal career workspace
          </div>

        </div>

        {/* Main cards */}
        <div className="mt-10 grid gap-5 md:grid-cols-3">

          {/* Profile */}
          <DashboardCard
            number="01"
            title="Profile"
            description="Your career identity and professional information."
            status="Connected"
            active
            actionText="Manage your profile →"
            onClick={() => router.push("/profile")}
          />

          {/* Resume */}
          <DashboardCard
            number="02"
            title="Resume Intelligence"
            description="Analyze your resume and extract meaningful career insights."
            status="Available"
            active
            actionText="Analyze your resume →"
            onClick={() => router.push("/resume")}
          />

          {/* Job Analysis */}
          <DashboardCard
            number="03"
            title="Job Analysis"
            description="Paste a job description and let AI extract its skills, requirements, and responsibilities."
            status="Available"
            active
            actionText="Analyze a job →"
            onClick={() => router.push("/job")}
          />

        </div>

        {/* Workspace */}
        <div className="mt-5 grid gap-5 lg:grid-cols-[1.5fr_1fr]">

          {/* Career Intelligence */}
          <section className="rounded-2xl border border-white/10 bg-[#101216] p-6 md:p-7">

            <div className="flex items-start justify-between">

              <div>
                <p className="text-[10px] font-semibold uppercase tracking-[0.2em] text-white/25">
                  Career Intelligence
                </p>

                <h2 className="mt-2 text-xl font-semibold">
                  Your career snapshot
                </h2>
              </div>

              <div className="rounded-lg border border-white/10 px-3 py-1.5 text-[10px] text-white/30">
                AI READY
              </div>

            </div>

            <div className="mt-8 grid gap-3 sm:grid-cols-2">

              <Insight
                label="PROFILE"
                value="Ready"
                description="Account connected"
              />

              <Insight
                label="RESUME"
                value="Available"
                description="Resume intelligence ready"
              />

              <Insight
                label="SKILLS"
                value="Available"
                description="Extracted from resume"
              />

              <Insight
                label="JOB ANALYSIS"
                value="Available"
                description="AI job analysis ready"
              />

            </div>

          </section>

          {/* Next step */}
          <section className="relative overflow-hidden rounded-2xl border border-white/10 bg-white/[0.04] p-6 md:p-7">

            <div className="absolute right-[-100px] top-[-100px] h-64 w-64 rounded-full bg-white/[0.04] blur-3xl" />

            <div className="relative">

              <p className="text-[10px] font-semibold uppercase tracking-[0.2em] text-white/25">
                Recommended next step
              </p>

              <h2 className="mt-3 text-2xl font-semibold">
                Analyze a job
              </h2>

              <p className="mt-3 text-sm leading-6 text-white/35">
                Paste a real job description and let Career Intelligence
                identify the skills, education, experience, and
                responsibilities required for the role.
              </p>

              <button
                onClick={() => router.push("/job")}
                className="mt-7 rounded-xl bg-white px-5 py-3 text-sm font-semibold text-black transition hover:bg-white/90"
              >
                Analyze a Job →
              </button>

            </div>

          </section>

        </div>

        {/* Roadmap */}
        <section className="mt-5 rounded-2xl border border-white/10 bg-[#101216] p-6 md:p-7">

          <div>
            <p className="text-[10px] font-semibold uppercase tracking-[0.2em] text-white/25">
              Platform roadmap
            </p>

            <h2 className="mt-2 text-xl font-semibold">
              Your career intelligence journey
            </h2>
          </div>

          <div className="mt-8 grid gap-6 md:grid-cols-4">

            <RoadmapItem
              number="01"
              title="Profile"
              status="Available"
            />

            <RoadmapItem
              number="02"
              title="Resume Analysis"
              status="Available"
            />

            <RoadmapItem
              number="03"
              title="Job Analysis"
              status="Available"
            />

            <RoadmapItem
              number="04"
              title="Skill Gaps"
              status="Coming soon"
            />

          </div>

        </section>

      </div>
    </main>
  );
}


/* ------------------------------------------------ */
/* Dashboard Card */
/* ------------------------------------------------ */

function DashboardCard({
  number,
  title,
  description,
  status,
  active = false,
  actionText,
  onClick,
}: {
  number: string;
  title: string;
  description: string;
  status: string;
  active?: boolean;
  actionText?: string;
  onClick?: () => void;
}) {
  return (
    <div
      onClick={onClick}
      role={active ? "button" : undefined}
      tabIndex={active ? 0 : undefined}
      onKeyDown={(event) => {
        if (active && onClick && (event.key === "Enter" || event.key === " ")) {
          onClick();
        }
      }}
      className={`rounded-2xl border p-6 transition ${
        active
          ? "cursor-pointer border-white/20 bg-white/[0.06] hover:bg-white/[0.08]"
          : "border-white/10 bg-[#101216]"
      }`}
    >

      <div className="flex items-center justify-between">

        <span className="font-mono text-[10px] text-white/25">
          {number}
        </span>

        <span
          className={`rounded-full px-2.5 py-1 text-[9px] ${
            active
              ? "bg-emerald-400/10 text-emerald-400"
              : "bg-white/5 text-white/25"
          }`}
        >
          {status}
        </span>

      </div>

      <h3 className="mt-8 text-lg font-semibold">
        {title}
      </h3>

      <p className="mt-2 text-sm leading-6 text-white/35">
        {description}
      </p>

      {active && actionText && (
        <p className="mt-5 text-xs text-white/40">
          {actionText}
        </p>
      )}

    </div>
  );
}


/* ------------------------------------------------ */
/* Insight Card */
/* ------------------------------------------------ */

function Insight({
  label,
  value,
  description,
}: {
  label: string;
  value: string;
  description: string;
}) {
  return (
    <div className="rounded-xl border border-white/10 bg-white/[0.02] p-4">

      <p className="text-[9px] font-semibold tracking-[0.15em] text-white/25">
        {label}
      </p>

      <p className="mt-3 text-sm font-semibold">
        {value}
      </p>

      <p className="mt-1 text-[10px] text-white/25">
        {description}
      </p>

    </div>
  );
}


/* ------------------------------------------------ */
/* Roadmap Item */
/* ------------------------------------------------ */

function RoadmapItem({
  number,
  title,
  status,
}: {
  number: string;
  title: string;
  status: string;
}) {
  const isAvailable = status === "Available";

  return (
    <div className="border-l border-white/10 pl-4">

      <span className="font-mono text-[10px] text-white/20">
        {number}
      </span>

      <p className="mt-3 text-sm font-medium">
        {title}
      </p>

      <p
        className={`mt-1 text-[10px] ${
          isAvailable
            ? "text-emerald-400/70"
            : "text-white/25"
        }`}
      >
        {status}
      </p>

    </div>
  );
}