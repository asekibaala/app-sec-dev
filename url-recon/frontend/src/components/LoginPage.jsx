import { useState } from "react";

/**
 * Dedicated login screen for the application.
 * It presents the product as a security workspace rather than a generic form.
 */
export default function LoginPage({ onLogin, isSubmitting, error }) {
  const [username, setUsername] = useState("admin");
  const [password, setPassword] = useState("admin");

  async function handleSubmit(event) {
    event.preventDefault();
    await onLogin(username.trim(), password);
  }

  return (
    <div className="min-h-screen overflow-hidden bg-[linear-gradient(180deg,_#08111d_0%,_#0f172a_45%,_#111827_100%)] px-6 py-10 text-slate-100">
      <div className="pointer-events-none absolute inset-0 bg-[radial-gradient(circle_at_top_left,_rgba(249,115,22,0.16),_transparent_30%),radial-gradient(circle_at_80%_20%,_rgba(14,165,233,0.18),_transparent_28%),radial-gradient(circle_at_bottom,_rgba(148,163,184,0.12),_transparent_40%)]" />

      <div className="relative mx-auto flex min-h-[82vh] max-w-6xl items-center">
        <div className="grid w-full gap-6 lg:grid-cols-[1.2fr_0.8fr]">
          <section className="rounded-[2rem] border border-white/10 bg-white/5 p-8 shadow-2xl shadow-black/30 backdrop-blur-xl">
            <div className="flex items-center gap-3">
              <div className="flex h-12 w-12 items-center justify-center rounded-2xl border border-orange-400/30 bg-orange-500/10 text-lg font-bold text-orange-300">
                BH
              </div>
              <div>
                <p className="text-xs uppercase tracking-[0.28em] text-orange-300">Bugbounty hut</p>
                <h1 className="mt-1 text-3xl font-semibold text-white sm:text-5xl">
                  Secure recon workspace.
                </h1>
              </div>
            </div>

            <p className="mt-6 max-w-2xl text-sm leading-7 text-slate-300 sm:text-base">
              Sign in to access scans, history, and reports.
            </p>

            <div className="mt-8 grid gap-4 sm:grid-cols-3">
              <div className="rounded-2xl border border-white/10 bg-slate-950/35 p-4">
                <p className="text-[11px] uppercase tracking-[0.22em] text-slate-400">Default User</p>
                <p className="mt-2 text-xl font-semibold text-white">admin</p>
              </div>
              <div className="rounded-2xl border border-white/10 bg-slate-950/35 p-4">
                <p className="text-[11px] uppercase tracking-[0.22em] text-slate-400">Default Pass</p>
                <p className="mt-2 text-xl font-semibold text-white">admin</p>
              </div>
              <div className="rounded-2xl border border-white/10 bg-slate-950/35 p-4">
                <p className="text-[11px] uppercase tracking-[0.22em] text-slate-400">Access</p>
                <p className="mt-2 text-xl font-semibold text-white">Scans and reports</p>
              </div>
            </div>
          </section>

          <section className="rounded-[2rem] border border-white/10 bg-slate-950/80 p-8 shadow-2xl shadow-black/40 backdrop-blur-xl">
            <p className="text-xs uppercase tracking-[0.22em] text-slate-400">Operator Access</p>
            <h2 className="mt-3 text-3xl font-semibold text-white">Sign in</h2>
            <p className="mt-3 text-sm leading-6 text-slate-400">
              Use the seeded admin account for local development, then replace it for real deployments.
            </p>

            <form onSubmit={handleSubmit} className="mt-8 flex flex-col gap-4">
              <label className="flex flex-col gap-2 text-sm">
                <span className="font-medium text-slate-300">Username</span>
                <input
                  type="text"
                  value={username}
                  onChange={(event) => setUsername(event.target.value)}
                  autoComplete="username"
                  disabled={isSubmitting}
                  className="rounded-xl border border-slate-700 bg-slate-900 px-4 py-3 text-slate-100 outline-none transition focus:border-cyan-400"
                />
              </label>

              <label className="flex flex-col gap-2 text-sm">
                <span className="font-medium text-slate-300">Password</span>
                <input
                  type="password"
                  value={password}
                  onChange={(event) => setPassword(event.target.value)}
                  autoComplete="current-password"
                  disabled={isSubmitting}
                  className="rounded-xl border border-slate-700 bg-slate-900 px-4 py-3 text-slate-100 outline-none transition focus:border-cyan-400"
                />
              </label>

              {error && (
                <div className="rounded-xl border border-red-900/70 bg-red-950/40 px-4 py-3 text-sm text-red-300">
                  {error}
                </div>
              )}

              <button
                type="submit"
                disabled={isSubmitting || !username.trim() || !password}
                className="mt-2 rounded-xl bg-gradient-to-r from-orange-500 to-amber-500 px-5 py-3 text-sm font-semibold text-slate-950 transition hover:from-orange-400 hover:to-amber-400 disabled:cursor-not-allowed disabled:opacity-60"
              >
                {isSubmitting ? "Authenticating..." : "Enter Bugbounty hut"}
              </button>
            </form>
          </section>
        </div>
      </div>
    </div>
  );
}
