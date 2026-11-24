"use client";

import { FormEvent, useEffect, useState } from "react";
import { useRouter } from "next/navigation";

type Profile = {
  phone: string;
  location: string;
  education: string;
  university: string;
  degree: string;
  graduation_year: string;
  experience_years: string;
  bio: string;
  linkedin_url: string;
  github_url: string;
  portfolio_url: string;
};

const emptyProfile: Profile = {
  phone: "",
  location: "",
  education: "",
  university: "",
  degree: "",
  graduation_year: "",
  experience_years: "",
  bio: "",
  linkedin_url: "",
  github_url: "",
  portfolio_url: "",
};

export default function ProfilePage() {
  const router = useRouter();

  const [profileExists, setProfileExists] = useState(false);
  const [profile, setProfile] = useState<Profile>(emptyProfile);

  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);

  const [message, setMessage] = useState("");
  const [error, setError] = useState("");

  useEffect(() => {
    loadProfile();
  }, []);

  async function loadProfile() {
    const token = localStorage.getItem("access_token");

    if (!token) {
      router.push("/login");
      return;
    }

    try {
      const response = await fetch(
        "http://127.0.0.1:8000/profile/details",
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
        setProfile(emptyProfile);
        setProfileExists(false);
        setLoading(false);
        return;
      }

      if (!response.ok) {
        setError("Could not load your profile.");
        setLoading(false);
        return;
      }

      const data = await response.json();

      setProfileExists(true);

      setProfile({
        phone: data.phone || "",
        location: data.location || "",
        education: data.education || "",
        university: data.university || "",
        degree: data.degree || "",
        graduation_year: data.graduation_year?.toString() || "",
        experience_years: data.experience_years?.toString() || "",
        bio: data.bio || "",
        linkedin_url: data.linkedin_url || "",
        github_url: data.github_url || "",
        portfolio_url: data.portfolio_url || "",
      });
    } catch {
      setError("Could not connect to the backend.");
    } finally {
      setLoading(false);
    }
  }

  function handleChange(
    event: React.ChangeEvent<
      HTMLInputElement | HTMLTextAreaElement | HTMLSelectElement
    >
  ) {
    const { name, value } = event.target;

    setProfile((previous) => ({
      ...previous,
      [name]: value,
    }));
  }

  async function handleSave(event: FormEvent) {
    event.preventDefault();

    setSaving(true);
    setMessage("");
    setError("");

    const token = localStorage.getItem("access_token");

    if (!token) {
      router.push("/login");
      return;
    }

    const payload = {
      phone: profile.phone || null,
      location: profile.location || null,
      education: profile.education || null,
      university: profile.university || null,
      degree: profile.degree || null,

      graduation_year: profile.graduation_year
        ? Number(profile.graduation_year)
        : null,

      experience_years: profile.experience_years
        ? Number(profile.experience_years)
        : null,

      bio: profile.bio || null,
      linkedin_url: profile.linkedin_url || null,
      github_url: profile.github_url || null,
      portfolio_url: profile.portfolio_url || null,
    };

    try {
      const response = await fetch(
        "http://127.0.0.1:8000/profile",
        {
          method: profileExists ? "PUT" : "POST",

          headers: {
            "Content-Type": "application/json",
            Authorization: `Bearer ${token}`,
          },

          body: JSON.stringify(payload),
        }
      );

      const data = await response.json();

      if (!response.ok) {
        setError(data.detail || "Failed to save profile.");
        return;
      }

      setProfileExists(true);

      setMessage(
        profileExists
          ? "Profile updated successfully!"
          : "Profile created successfully!"
      );
    } catch {
      setError("Could not connect to the backend.");
    } finally {
      setSaving(false);
    }
  }

  if (loading) {
    return (
      <main className="min-h-screen bg-[#08090b] text-white">
        <div className="flex min-h-screen items-center justify-center">
          <p className="text-sm text-white/40">
            Loading your profile...
          </p>
        </div>
      </main>
    );
  }

  return (
    <main className="min-h-screen bg-[#08090b] text-white">
      <div className="mx-auto max-w-4xl px-6 py-10">

        {/* Header */}
        <div className="mb-10 flex items-center justify-between">
          <div>

            <button
              onClick={() => router.push("/dashboard")}
              className="mb-5 text-sm text-white/40 transition hover:text-white"
            >
              ← Back to dashboard
            </button>

            <h1 className="text-3xl font-semibold tracking-tight">
              Your Profile
            </h1>

            <p className="mt-2 text-sm text-white/35">
              Build your professional profile so the platform can
              understand your career.
            </p>

          </div>
        </div>

        <form
          onSubmit={handleSave}
          className="space-y-6"
        >

          {/* Personal Information */}
          <section className="rounded-2xl border border-white/10 bg-white/[0.03] p-6">

            <h2 className="text-lg font-semibold">
              Personal Information
            </h2>

            <p className="mt-1 text-sm text-white/30">
              Basic information about you.
            </p>

            <div className="mt-6 grid gap-5 md:grid-cols-2">

              <div>
                <label className="text-xs text-white/50">
                  Phone
                </label>

                <input
                  name="phone"
                  value={profile.phone}
                  onChange={handleChange}
                  placeholder="+92 300 1234567"
                  className="mt-2 w-full rounded-xl border border-white/10 bg-white/[0.04] px-4 py-3 text-sm outline-none transition focus:border-white/30"
                />
              </div>

              <div>
                <label className="text-xs text-white/50">
                  Location
                </label>

                <input
                  name="location"
                  value={profile.location}
                  onChange={handleChange}
                  placeholder="Karachi, Pakistan"
                  className="mt-2 w-full rounded-xl border border-white/10 bg-white/[0.04] px-4 py-3 text-sm outline-none transition focus:border-white/30"
                />
              </div>

            </div>
          </section>

          {/* Education */}
          <section className="rounded-2xl border border-white/10 bg-white/[0.03] p-6">

            <h2 className="text-lg font-semibold">
              Education
            </h2>

            <p className="mt-1 text-sm text-white/30">
              Tell us about your academic background.
            </p>

            <div className="mt-6 grid gap-5 md:grid-cols-2">

              <div>
                <label className="text-xs text-white/50">
                  Education Level
                </label>

                <select
                  name="education"
                  value={profile.education}
                  onChange={handleChange}
                  className="mt-2 w-full rounded-xl border border-white/10 bg-[#111216] px-4 py-3 text-sm outline-none focus:border-white/30"
                >
                  <option value="">
                    Select education level
                  </option>

                  <option value="High School">
                    High School
                  </option>

                  <option value="Diploma">
                    Diploma
                  </option>

                  <option value="Bachelor's">
                    Bachelor's
                  </option>

                  <option value="Master's">
                    Master's
                  </option>

                  <option value="PhD">
                    PhD
                  </option>
                </select>
              </div>

              <div>
                <label className="text-xs text-white/50">
                  University
                </label>

                <input
                  name="university"
                  value={profile.university}
                  onChange={handleChange}
                  placeholder="University name"
                  className="mt-2 w-full rounded-xl border border-white/10 bg-white/[0.04] px-4 py-3 text-sm outline-none focus:border-white/30"
                />
              </div>

              <div>
                <label className="text-xs text-white/50">
                  Degree
                </label>

                <input
                  name="degree"
                  value={profile.degree}
                  onChange={handleChange}
                  placeholder="Software Engineering"
                  className="mt-2 w-full rounded-xl border border-white/10 bg-white/[0.04] px-4 py-3 text-sm outline-none focus:border-white/30"
                />
              </div>

              <div>
                <label className="text-xs text-white/50">
                  Graduation Year
                </label>

                <input
                  type="number"
                  name="graduation_year"
                  value={profile.graduation_year}
                  onChange={handleChange}
                  placeholder="2026"
                  min="1950"
                  max="2100"
                  className="mt-2 w-full rounded-xl border border-white/10 bg-white/[0.04] px-4 py-3 text-sm outline-none focus:border-white/30"
                />
              </div>

            </div>
          </section>

          {/* Experience */}
          <section className="rounded-2xl border border-white/10 bg-white/[0.03] p-6">

            <h2 className="text-lg font-semibold">
              Experience
            </h2>

            <p className="mt-1 text-sm text-white/30">
              Give the system some context about your professional
              experience.
            </p>

            <div className="mt-6 space-y-5">

              <div>
                <label className="text-xs text-white/50">
                  Years of Experience
                </label>

                <input
                  type="number"
                  name="experience_years"
                  value={profile.experience_years}
                  onChange={handleChange}
                  placeholder="0"
                  min="0"
                  max="50"
                  className="mt-2 w-full rounded-xl border border-white/10 bg-white/[0.04] px-4 py-3 text-sm outline-none focus:border-white/30"
                />
              </div>

              <div>
                <label className="text-xs text-white/50">
                  Professional Bio
                </label>

                <textarea
                  name="bio"
                  value={profile.bio}
                  onChange={handleChange}
                  rows={5}
                  placeholder="Tell us about your experience, interests, and career goals..."
                  className="mt-2 w-full resize-none rounded-xl border border-white/10 bg-white/[0.04] px-4 py-3 text-sm outline-none focus:border-white/30"
                />
              </div>

            </div>
          </section>

          {/* Professional Links */}
          <section className="rounded-2xl border border-white/10 bg-white/[0.03] p-6">

            <h2 className="text-lg font-semibold">
              Professional Links
            </h2>

            <p className="mt-1 text-sm text-white/30">
              Connect your professional profiles.
            </p>

            <div className="mt-6 space-y-5">

              <div>
                <label className="text-xs text-white/50">
                  LinkedIn
                </label>

                <input
                  name="linkedin_url"
                  value={profile.linkedin_url}
                  onChange={handleChange}
                  placeholder="https://linkedin.com/in/yourname"
                  className="mt-2 w-full rounded-xl border border-white/10 bg-white/[0.04] px-4 py-3 text-sm outline-none focus:border-white/30"
                />
              </div>

              <div>
                <label className="text-xs text-white/50">
                  GitHub
                </label>

                <input
                  name="github_url"
                  value={profile.github_url}
                  onChange={handleChange}
                  placeholder="https://github.com/yourusername"
                  className="mt-2 w-full rounded-xl border border-white/10 bg-white/[0.04] px-4 py-3 text-sm outline-none focus:border-white/30"
                />
              </div>

              <div>
                <label className="text-xs text-white/50">
                  Portfolio
                </label>

                <input
                  name="portfolio_url"
                  value={profile.portfolio_url}
                  onChange={handleChange}
                  placeholder="https://yourportfolio.com"
                  className="mt-2 w-full rounded-xl border border-white/10 bg-white/[0.04] px-4 py-3 text-sm outline-none focus:border-white/30"
                />
              </div>

            </div>
          </section>

          {/* Error Message */}
          {error && (
            <div className="rounded-xl border border-red-500/20 bg-red-500/5 px-4 py-3 text-sm text-red-400">
              {error}
            </div>
          )}

          {/* Success Message */}
          {message && (
            <div className="rounded-xl border border-emerald-500/20 bg-emerald-500/5 px-4 py-3 text-sm text-emerald-400">
              {message}
            </div>
          )}

          {/* Save Button */}
          <div className="flex justify-end pb-10">

            <button
              type="submit"
              disabled={saving}
              className="rounded-xl bg-white px-6 py-3 text-sm font-semibold text-black transition hover:bg-white/90 disabled:cursor-not-allowed disabled:opacity-40"
            >
              {saving
                ? "Saving..."
                : profileExists
                ? "Update Profile →"
                : "Create Profile →"}
            </button>

          </div>

        </form>
      </div>
    </main>
  );
}