"use client";
import { useEffect, useState } from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { listChannels, logout } from "@/lib/api";
import styles from "./Sidebar.module.css";

type Channel = { id: number; name: string | null; kind: string };

export default function Sidebar({ workspaceId }: { workspaceId: number }) {
  const [channels, setChannels] = useState<Channel[]>([]);
  const pathname = usePathname();

  useEffect(() => {
    listChannels(workspaceId)
      .then((data) => setChannels(data.results ?? data))
      .catch(() => setChannels([]));
  }, [workspaceId]);

  return (
    <nav className={styles.sidebar}>
      <div className={styles.header}>Workspace</div>
      <div className={styles.section}>Channels</div>
      <ul className={styles.list}>
        {channels.map((c) => {
          const href = `/w/${workspaceId}/${c.id}`;
          const label = c.name ? `# ${c.name}` : "• direct message";
          return (
            <li key={c.id}>
              <Link
                href={href}
                className={`${styles.item} ${pathname === href ? styles.active : ""}`}
              >
                {label}
              </Link>
            </li>
          );
        })}
      </ul>
      <button className={styles.logout} onClick={() => logout().then(() => (location.href = "/login"))}>
        Sign out
      </button>
    </nav>
  );
}
