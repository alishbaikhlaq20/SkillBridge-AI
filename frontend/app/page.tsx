import Link from "next/link";

const features = [
  {
    number: "01",
    title: "Resume Intelligence",
    description:
      "Turn your resume into structured career insights, skills, experience, and opportunities.",
  },
  {
    number: "02",
    title: "Job Match Analysis",
    description:
      "Understand how your profile compares with the requirements of the roles you want.",
  },
  {
    number: "03",
    title: "Skill Gap Detection",
    description:
      "Identify the skills you are missing and discover what to focus on next.",
  },
];

export default function Home() {
  return (
    <main className="min-h-screen overflow-hidden bg-[#08090b] text-white">
      {/* Navigation */}
      <nav className="border-b border-white/10">
        <div className="mx-auto flex max-w-7xl items-center justify-between px-6 py-5">
          <Link href="/" className="flex items-center gap-3">
            <div className="flex h-9 w-9 items-center justify-center rounded-xl bg-white text-sm font-black text-black">
              AI
            </div>

            <span className="text-sm font-semibold tracking-tight">
              Career Intelligence
            </span>
          </Link>

          <div className="hidden items-center gap-8 text-sm text-white/60 md:flex">
            <a href="#features" className="transition hover:text-white">
              Features
            </a>
            <a href="#how-it-works" className="transition hover:text-white">
              How it works
            </a>
          </div>

          <div className="flex items-center gap-3">
            <Link
              href="/login"
              className="hidden rounded-lg px-4 py-2 text-sm text-white/70 transition hover:bg-white/5 hover:text-white sm:block"
            >
              Sign in
            </Link>

            <Link
              href="/register"
              className="rounded-lg bg-white px-4 py-2.5 text-sm font-semibold text-black transition hover:bg-white/90"
            >
              Get started
            </Link>
          </div>
        </div>
      </nav>

      {/* Hero */}
      <section className="relative">
        <div className="absolute left-1/2 top-0 h-[600px] w-[900px] -translate-x-1/2 rounded-full bg-white/[0.04] blur-3xl" />

        <div className="relative mx-auto max-w-6xl px-6 pb-24 pt-28 text-center md:pb-32 md:pt-36">
          <div className="mx-auto inline-flex items-center gap-2 rounded-full border border-white/10 bg-white/[0.04] px-4 py-2 text-xs font-medium text-white/60">
            <span className="h-1.5 w-1.5 rounded-full bg-emerald-400" />
            AI-powered career intelligence
          </div>

          <h1 className="mx-auto mt-8 max-w-5xl text-5xl font-semibold tracking-[-0.04em] md:text-7xl lg:text-8xl">
            Your career,
            <br />
            <span className="text-white/40">understood.</span>
          </h1>

          <p className="mx-auto mt-8 max-w-2xl text-base leading-7 text-white/50 md:text-lg">
            Analyze your experience, understand your skills, discover career
            gaps, and prepare for the opportunities that matter to you.
          </p>

          <div className="mt-10 flex flex-col items-center justify-center gap-3 sm:flex-row">
            <Link
              href="/register"
              className="w-full rounded-xl bg-white px-7 py-3.5 text-sm font-semibold text-black transition hover:scale-[1.02] hover:bg-white/90 sm:w-auto"
            >
              Start your career analysis →
            </Link>

            <Link
              href="/login"
              className="w-full rounded-xl border border-white/10 bg-white/[0.03] px-7 py-3.5 text-sm font-medium text-white/70 transition hover:bg-white/[0.07] hover:text-white sm:w-auto"
            >
              I already have an account
            </Link>
          </div>
        </div>
      </section>

      {/* Product Preview */}
      <section className="mx-auto max-w-6xl px-6">
        <div className="relative overflow-hidden rounded-2xl border border-white/10 bg-[#101216] shadow-2xl shadow-black/40">
          <div className="flex items-center gap-2 border-b border-white/10 px-5 py-4">
            <span className="h-2.5 w-2.5 rounded-full bg-white/20" />
            <span className="h-2.5 w-2.5 rounded-full bg-white/20" />
            <span className="h-2.5 w-2.5 rounded-full bg-white/20" />

            <div className="ml-4 rounded-md bg-white/[0.04] px-4 py-1.5 text-[10px] text-white/30">
              app.career-intelligence
            </div>
          </div>

          <div className="grid min-h-[380px] md:grid-cols-[200px_1fr]">
            <aside className="hidden border-r border-white/10 p-5 md:block">
              <div className="mb-8 text-xs font-semibold text-white/80">
                Career Intelligence
              </div>

              <div className="space-y-2 text-xs text-white/35">
                <div className="rounded-lg bg-white/[0.07] px-3 py-2 text-white/80">
                  Overview
                </div>
                <div className="px-3 py-2">My Profile</div>
                <div className="px-3 py-2">Resume</div>
                <div className="px-3 py-2">Job Analysis</div>
                <div className="px-3 py-2">Skill Gaps</div>
                <div className="px-3 py-2">Interview Prep</div>
              </div>
            </aside>

            <div className="p-6 md:p-8">
              <div className="text-xs text-white/30">
                CAREER OVERVIEW
              </div>

              <h3 className="mt-2 text-2xl font-semibold">
                Welcome back.
              </h3>

              <div className="mt-7 grid gap-4 sm:grid-cols-3">
                <PreviewCard
                  label="PROFILE"
                  value="Complete"
                  detail="Build your profile"
                />

                <PreviewCard
                  label="RESUME"
                  value="Ready"
                  detail="Upload your resume"
                />

                <PreviewCard
                  label="JOB MATCH"
                  value="AI"
                  detail="Coming soon"
                />
              </div>

              <div className="mt-4 rounded-xl border border-white/10 bg-white/[0.02] p-5">
                <div className="text-xs text-white/30">
                  RESUME INTELLIGENCE
                </div>

                <div className="mt-3 flex flex-col justify-between gap-4 sm:flex-row sm:items-center">
                  <div>
                    <p className="font-medium">Unlock your career insights</p>
                    <p className="mt-1 text-xs text-white/35">
                      Upload your resume to begin your analysis.
                    </p>
                  </div>

                  <div className="rounded-lg bg-white px-4 py-2 text-center text-xs font-semibold text-black">
                    Upload resume
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* Features */}
      <section id="features" className="mx-auto max-w-6xl px-6 py-28">
        <div className="max-w-xl">
          <p className="text-xs font-semibold uppercase tracking-[0.2em] text-white/30">
            Built around you
          </p>

          <h2 className="mt-4 text-3xl font-semibold tracking-tight md:text-5xl">
            From resume to career strategy.
          </h2>

          <p className="mt-5 leading-7 text-white/40">
            One place to understand where you are, where you want to go, and
            what stands between the two.
          </p>
        </div>

        <div className="mt-14 grid gap-px overflow-hidden rounded-2xl border border-white/10 bg-white/10 md:grid-cols-3">
          {features.map((feature) => (
            <div
              key={feature.number}
              className="bg-[#101216] p-7 transition hover:bg-[#14161a]"
            >
              <span className="text-xs font-mono text-white/25">
                {feature.number}
              </span>

              <h3 className="mt-12 text-lg font-semibold">
                {feature.title}
              </h3>

              <p className="mt-3 text-sm leading-6 text-white/40">
                {feature.description}
              </p>
            </div>
          ))}
        </div>
      </section>

      {/* How it works */}
      <section
        id="how-it-works"
        className="border-y border-white/10 bg-white/[0.02]"
      >
        <div className="mx-auto max-w-6xl px-6 py-24">
          <p className="text-xs font-semibold uppercase tracking-[0.2em] text-white/30">
            How it works
          </p>

          <div className="mt-12 grid gap-10 md:grid-cols-3">
            <Step
              number="01"
              title="Build your profile"
              text="Tell the platform about your education, experience and career goals."
            />

            <Step
              number="02"
              title="Add your resume"
              text="Your resume becomes the foundation for your career intelligence."
            />

            <Step
              number="03"
              title="Understand your gaps"
              text="Discover skills, opportunities and areas to focus on next."
            />
          </div>
        </div>
      </section>

      {/* CTA */}
      <section className="mx-auto max-w-4xl px-6 py-28 text-center">
        <h2 className="text-4xl font-semibold tracking-tight md:text-6xl">
          Your next opportunity
          <br />
          starts with understanding.
        </h2>

        <p className="mx-auto mt-6 max-w-xl text-white/40">
          Build your career profile today and start turning your experience
          into actionable intelligence.
        </p>

        <Link
          href="/register"
          className="mt-8 inline-flex rounded-xl bg-white px-7 py-3.5 text-sm font-semibold text-black transition hover:scale-[1.02]"
        >
          Create your account →
        </Link>
      </section>

      {/* Footer */}
      <footer className="border-t border-white/10">
        <div className="mx-auto flex max-w-6xl flex-col justify-between gap-4 px-6 py-8 text-xs text-white/30 sm:flex-row">
          <span>© 2026 AI Career Intelligence</span>
          <span>Understand. Improve. Advance.</span>
        </div>
      </footer>
    </main>
  );
}

function PreviewCard({
  label,
  value,
  detail,
}: {
  label: string;
  value: string;
  detail: string;
}) {
  return (
    <div className="rounded-xl border border-white/10 bg-white/[0.02] p-4">
      <div className="text-[9px] font-semibold tracking-wider text-white/25">
        {label}
      </div>

      <div className="mt-3 text-xl font-semibold">{value}</div>

      <div className="mt-1 text-[10px] text-white/30">{detail}</div>
    </div>
  );
}

function Step({
  number,
  title,
  text,
}: {
  number: string;
  title: string;
  text: string;
}) {
  return (
    <div>
      <span className="font-mono text-xs text-white/25">{number}</span>

      <h3 className="mt-5 text-lg font-semibold">{title}</h3>

      <p className="mt-3 max-w-sm text-sm leading-6 text-white/40">
        {text}
      </p>
    </div>
  );
}