"use client";

import { FormEvent, useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";

export default function LoginPage() {
  const router = useRouter();

  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  async function handleLogin(event: FormEvent) {
    event.preventDefault();

    setError("");
    setLoading(true);

    try {
      const response = await fetch("http://127.0.0.1:8000/login", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          email,
          password,
        }),
      });

      const data = await response.json();

      if (!response.ok) {
        setError(data.detail || "Login failed");
        setLoading(false);
        return;
      }

      localStorage.setItem("access_token", data.access_token);

      router.push("/dashboard");
    } catch {
      setError("Could not connect to the backend.");
    } finally {
      setLoading(false);
    }
  }

  return (
    <main className="min-h-screen bg-[#08090b] text-white">
      <div className="grid min-h-screen lg:grid-cols-2">

        {/* Left side */}
        <div className="relative hidden overflow-hidden border-r border-white/10 lg:flex">
          <div className="absolute left-[-200px] top-[-150px] h-[600px] w-[600px] rounded-full bg-white/[0.04] blur-3xl" />

          <div className="relative flex w-full flex-col justify-between p-10">

            {/* Logo */}
            <Link href="/" className="flex items-center gap-3">
              <div className="flex h-9 w-9 items-center justify-center rounded-xl bg-white text-sm font-black text-black">
                AI
              </div>

              <span className="text-sm font-semibold">
                Career Intelligence
              </span>
            </Link>

            {/* Main message */}
            <div className="max-w-lg">
              <p className="text-xs font-semibold uppercase tracking-[0.2em] text-white/30">
                Your career, understood
              </p>

              <h1 className="mt-6 text-5xl font-semibold leading-[1.05] tracking-[-0.04em]">
                Turn your experience
                <br />
                into your next
                <br />
                <span className="text-white/35">opportunity.</span>
              </h1>

              <p className="mt-7 max-w-md text-sm leading-7 text-white/40">
                Analyze your resume, understand your skills, identify gaps,
                and prepare yourself for the roles you want.
              </p>
            </div>

            <p className="text-xs text-white/20">
              AI-powered career intelligence platform
            </p>
          </div>
        </div>

        {/* Right side */}
        <div className="flex items-center justify-center px-6 py-12">
          <div className="w-full max-w-md">

            {/* Mobile logo */}
            <Link
              href="/"
              className="mb-12 flex items-center gap-3 lg:hidden"
            >
              <div className="flex h-9 w-9 items-center justify-center rounded-xl bg-white text-sm font-black text-black">
                AI
              </div>

              <span className="text-sm font-semibold">
                Career Intelligence
              </span>
            </Link>

            <div>
              <p className="text-sm text-white/35">
                Welcome back
              </p>

              <h2 className="mt-2 text-3xl font-semibold tracking-tight">
                Sign in to your account
              </h2>

              <p className="mt-3 text-sm leading-6 text-white/35">
                Continue building your career intelligence profile.
              </p>
            </div>

            <form onSubmit={handleLogin} className="mt-10 space-y-5">

              {/* Email */}
              <div>
                <label className="text-xs font-medium text-white/60">
                  Email address
                </label>

                <input
                  type="email"
                  value={email}
                  onChange={(event) => setEmail(event.target.value)}
                  placeholder="you@example.com"
                  required
                  className="mt-2 w-full rounded-xl border border-white/10 bg-white/[0.04] px-4 py-3.5 text-sm text-white outline-none transition placeholder:text-white/20 focus:border-white/30 focus:bg-white/[0.06]"
                />
              </div>

              {/* Password */}
              <div>
                <div className="flex items-center justify-between">
                  <label className="text-xs font-medium text-white/60">
                    Password
                  </label>

                  <span className="text-xs text-white/20">
                    Forgot password?
                  </span>
                </div>

                <input
                  type="password"
                  value={password}
                  onChange={(event) => setPassword(event.target.value)}
                  placeholder="••••••••"
                  required
                  className="mt-2 w-full rounded-xl border border-white/10 bg-white/[0.04] px-4 py-3.5 text-sm text-white outline-none transition placeholder:text-white/20 focus:border-white/30 focus:bg-white/[0.06]"
                />
              </div>

              {/* Error */}
              {error && (
                <div className="rounded-xl border border-red-500/20 bg-red-500/5 px-4 py-3 text-sm text-red-400">
                  {error}
                </div>
              )}

              {/* Button */}
              <button
                type="submit"
                disabled={loading}
                className="w-full rounded-xl bg-white px-4 py-3.5 text-sm font-semibold text-black transition hover:bg-white/90 disabled:cursor-not-allowed disabled:opacity-50"
              >
                {loading ? "Signing in..." : "Sign in →"}
              </button>
            </form>

            {/* Register */}
            <div className="mt-8 border-t border-white/10 pt-8 text-center">
              <p className="text-sm text-white/30">
                Don't have an account?{" "}
                <Link
                  href="/register"
                  className="font-medium text-white transition hover:text-white/70"
                >
                  Create one
                </Link>
              </p>
            </div>

            <p className="mt-10 text-center text-[11px] leading-5 text-white/20">
              By continuing, you agree to use Career Intelligence for
              personal career analysis and development.
            </p>
          </div>
        </div>
      </div>
    </main>
  );
}