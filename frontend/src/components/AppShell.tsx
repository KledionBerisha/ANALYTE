"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useEffect, useState } from "react";

import { useAuth } from "@/lib/auth";

export function Logo() {
  return (
    <span className="flex items-center gap-2 font-semibold tracking-tight text-slate-900">
      <span className="grid size-7 place-items-center rounded-lg bg-cyan-700 text-sm font-bold text-white">
        A
      </span>
      ANALYTE
    </span>
  );
}

/** Faqet e mbrojtura: pa seancë, drejt hyrjes. */
export function AppShell({ children }: { children: React.ReactNode }) {
  const { user, logout, logoutEverywhere } = useAuth();
  const router = useRouter();
  const [signOutError, setSignOutError] = useState(false);

  async function everywhere() {
    setSignOutError(false);
    try {
      await logoutEverywhere();
    } catch {
      setSignOutError(true);
    }
  }

  useEffect(() => {
    if (user === null) router.replace("/login");
  }, [user, router]);

  if (!user) {
    return <div className="grid flex-1 place-items-center text-sm text-slate-500">Duke u ngarkuar…</div>;
  }

  return (
    <div className="flex flex-1 flex-col">
      <header className="border-b border-slate-200 bg-white">
        <div className="mx-auto flex h-14 max-w-7xl items-center justify-between px-4 sm:px-6">
          <Link href="/documents">
            <Logo />
          </Link>
          <div className="flex items-center gap-4 text-sm">
            <span className="hidden text-slate-500 sm:inline">{user.email}</span>
            {signOutError && (
              <span role="alert" className="text-xs text-rose-700">
                Seancat nuk u mbyllën. Provoni sërish.
              </span>
            )}
            <button
              onClick={everywhere}
              className="rounded-md px-3 py-1.5 text-slate-600 hover:bg-slate-100 hover:text-slate-900"
            >
              Dil kudo
            </button>
            <button
              onClick={logout}
              className="rounded-md px-3 py-1.5 text-slate-600 hover:bg-slate-100 hover:text-slate-900"
            >
              Dil
            </button>
          </div>
        </div>
      </header>
      <main className="mx-auto w-full max-w-7xl flex-1 px-4 py-8 sm:px-6">{children}</main>
    </div>
  );
}
