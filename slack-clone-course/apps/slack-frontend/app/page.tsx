"use client";
// Landing route: bounce to the first workspace if logged in, else to /login.
import { useEffect } from "react";
import { useRouter } from "next/navigation";
import { isAuthenticated, } from "@/lib/auth";
import { listWorkspaces } from "@/lib/api";

export default function Home() {
  const router = useRouter();
  useEffect(() => {
    if (!isAuthenticated()) {
      router.replace("/login");
      return;
    }
    listWorkspaces()
      .then((ws) => {
        if (ws.length) router.replace(`/w/${ws[0].id}`);
        else router.replace("/login"); // no workspace yet — could route to onboarding
      })
      .catch(() => router.replace("/login"));
  }, [router]);

  return <div className="auth-wrap">Loading…</div>;
}
