"use client";
// Workspace root with no channel selected: jump to the first channel, or show a hint.
import { useEffect, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import { listChannels } from "@/lib/api";

export default function WorkspaceHome() {
  const params = useParams();
  const router = useRouter();
  const workspaceId = Number(params.workspace);
  const [empty, setEmpty] = useState(false);

  useEffect(() => {
    listChannels(workspaceId).then((data) => {
      const channels = data.results ?? data;
      if (channels.length) router.replace(`/w/${workspaceId}/${channels[0].id}`);
      else setEmpty(true);
    });
  }, [workspaceId, router]);

  return (
    <div style={{ padding: 24 }}>
      {empty ? "No channels yet — create one in the admin or via the API." : "Opening…"}
    </div>
  );
}
