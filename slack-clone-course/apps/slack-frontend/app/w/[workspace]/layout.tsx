"use client";
// Protected layout: redirects to /login if there's no token, otherwise renders the
// two-pane app shell (sidebar + channel view).
import { useEffect, useState } from "react";
import { useRouter, useParams } from "next/navigation";
import { isAuthenticated } from "@/lib/auth";
import Sidebar from "@/components/Sidebar";

export default function WorkspaceLayout({ children }: { children: React.ReactNode }) {
  const router = useRouter();
  const params = useParams();
  const workspaceId = Number(params.workspace);
  const [ready, setReady] = useState(false);

  useEffect(() => {
    if (!isAuthenticated()) router.replace("/login");
    else setReady(true);
  }, [router]);

  if (!ready) return <div className="auth-wrap">Loading…</div>;

  return (
    <div className="app-shell">
      <Sidebar workspaceId={workspaceId} />
      <main>{children}</main>
    </div>
  );
}
