"use client";
import { FormEvent, useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { login, register } from "@/lib/api";

export default function RegisterPage() {
  const router = useRouter();
  const [email, setEmail] = useState("");
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);

  async function onSubmit(e: FormEvent) {
    e.preventDefault();
    setBusy(true);
    setError("");
    try {
      await register(email, username, password);
      await login(email, password); // auto-login after sign-up
      router.replace("/");
    } catch {
      setError("Could not register. Try a different email or a stronger password.");
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="auth-wrap">
      <form className="auth-card" onSubmit={onSubmit}>
        <h1>Create account</h1>
        {error && <div className="error">{error}</div>}
        <input className="field" type="email" placeholder="you@example.com"
          value={email} onChange={(e) => setEmail(e.target.value)} required />
        <input className="field" placeholder="username"
          value={username} onChange={(e) => setUsername(e.target.value)} required />
        <input className="field" type="password" placeholder="Password (8+ chars)"
          value={password} onChange={(e) => setPassword(e.target.value)} required />
        <button className="btn" disabled={busy}>
          {busy ? "Creating…" : "Create account"}
        </button>
        <p style={{ marginTop: 16, fontSize: 13 }}>
          Already have an account? <Link href="/login">Sign in</Link>
        </p>
      </form>
    </div>
  );
}
