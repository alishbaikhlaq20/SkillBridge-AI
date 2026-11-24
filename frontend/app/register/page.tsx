"use client";

import { FormEvent, useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";

function PasswordRequirement({
  met,
  children,
}: {
  met: boolean;
  children: React.ReactNode;
}) {
  return (
    <div
      className={`flex items-center gap-2 text-xs ${
        met ? "text-emerald-400" : "text-white/25"
      }`}
    >
      <span
        className={`flex h-4 w-4 items-center justify-center rounded-full text-[9px] ${
          met ? "bg-emerald-400/10" : "bg-white/5"
        }`}
      >
        {met ? "✓" : ""}
      </span>

      {children}
    </div>
  );
}

export default function RegisterPage() {
  const router = useRouter();

  const [fullName, setFullName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  const passwordRules = {
    length: password.length >= 8,
    uppercase: /[A-Z]/.test(password),
    lowercase: /[a-z]/.test(password),
    number: /\d/.test(password),
    special: /[^\w\s]/.test(password),
  };

  const passwordIsStrong =
    passwordRules.length &&
    passwordRules.uppercase &&
    passwordRules.lowercase &&
    passwordRules.number &&
    passwordRules.special;

  async function handleRegister(event: FormEvent) {
    event.preventDefault();

    setError("");

    // Extra frontend protection
    if (!passwordIsStrong) {
      setError("Please create a strong password.");
      return;
    }

    setLoading(true);

    try {
      const response = await fetch("http://127.0.0.1:8000/register", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          full_name: fullName,
          email,
          password,
        }),
      });

      const data = await response.json();

      if (!response.ok) {
        // FastAPI validation errors can sometimes be an array
        if (Array.isArray(data.detail)) {
          setError(data.detail[0]?.msg || "Registration failed");
        } else {
          setError(data.detail || "Registration failed");
        }

        return;
      }

      router.push("/login");
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
          <div className="absolute bottom-[-200px] right-[-200px] h-[600px] w-[600px] rounded-full bg-white/[0.04] blur-3xl" />

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
                Start your journey
              </p>

              <h1 className="mt-6 text-5xl font-semibold leading-[1.05] tracking-[-0.04em]">
                Know where you
                <br />
                stand.
                <br />

                <span className="text-white/35">
                  Know what's next.
                </span>
              </h1>

              <p className="mt-7 max-w-md text-sm leading-7 text-white/40">
                Create your profile and let AI help you understand your
                experience, skills, opportunities, and career gaps.
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

            {/* Heading */}
            <div>
              <p className="text-sm text-white/35">
                Create your account
              </p>

              <h2 className="mt-2 text-3xl font-semibold tracking-tight">
                Start your career journey
              </h2>

              <p className="mt-3 text-sm leading-6 text-white/35">
                Build your profile and unlock your career intelligence
                dashboard.
              </p>
            </div>

            {/* Form */}
            <form onSubmit={handleRegister} className="mt-10 space-y-5">

              {/* Full name */}
              <div>
                <label className="text-xs font-medium text-white/60">
                  Full name
                </label>

                <input
                  type="text"
                  value={fullName}
                  onChange={(event) => setFullName(event.target.value)}
                  placeholder="Your full name"
                  required
                  className="mt-2 w-full rounded-xl border border-white/10 bg-white/[0.04] px-4 py-3.5 text-sm text-white outline-none transition placeholder:text-white/20 focus:border-white/30 focus:bg-white/[0.06]"
                />
              </div>

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
                <label className="text-xs font-medium text-white/60">
                  Password
                </label>

                <input
                  type="password"
                  value={password}
                  onChange={(event) => setPassword(event.target.value)}
                  placeholder="Create a strong password"
                  required
                  className="mt-2 w-full rounded-xl border border-white/10 bg-white/[0.04] px-4 py-3.5 text-sm text-white outline-none transition placeholder:text-white/20 focus:border-white/30 focus:bg-white/[0.06]"
                />

                {/* Password requirements */}
                <div className="mt-4 space-y-2">
                  <PasswordRequirement met={passwordRules.length}>
                    At least 8 characters
                  </PasswordRequirement>

                  <PasswordRequirement met={passwordRules.uppercase}>
                    One uppercase letter
                  </PasswordRequirement>

                  <PasswordRequirement met={passwordRules.lowercase}>
                    One lowercase letter
                  </PasswordRequirement>

                  <PasswordRequirement met={passwordRules.number}>
                    One number
                  </PasswordRequirement>

                  <PasswordRequirement met={passwordRules.special}>
                    One special character
                  </PasswordRequirement>
                </div>
              </div>

              {/* Error */}
              {error && (
                <div className="rounded-xl border border-red-500/20 bg-red-500/5 px-4 py-3 text-sm text-red-400">
                  {error}
                </div>
              )}

              {/* Submit */}
              <button
                type="submit"
                disabled={loading || !passwordIsStrong}
                className="w-full rounded-xl bg-white px-4 py-3.5 text-sm font-semibold text-black transition hover:bg-white/90 disabled:cursor-not-allowed disabled:opacity-40"
              >
                {loading ? "Creating account..." : "Create account →"}
              </button>
            </form>

            {/* Login link */}
            <div className="mt-8 border-t border-white/10 pt-8 text-center">
              <p className="text-sm text-white/30">
                Already have an account?{" "}
                <Link
                  href="/login"
                  className="font-medium text-white transition hover:text-white/70"
                >
                  Sign in
                </Link>
              </p>
            </div>

          </div>
        </div>
      </div>
    </main>
  );
}