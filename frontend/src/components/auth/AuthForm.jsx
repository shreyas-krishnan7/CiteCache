import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { useAuth } from "../../context/AuthContext.jsx";
import { AlertIcon, Spinner } from "../icons.jsx";

const COPY = {
  login: {
    title: "Welcome back",
    subtitle: "Sign in to your document workspace.",
    submit: "Sign in",
    switchText: "New to CiteCache?",
    switchLink: "Create an account",
    switchTo: "/signup",
  },
  signup: {
    title: "Create your account",
    subtitle: "Upload documents and get answers backed by verified citations.",
    submit: "Create account",
    switchText: "Already have an account?",
    switchLink: "Sign in",
    switchTo: "/login",
  },
};

function Field({ id, label, hint, ...input }) {
  return (
    <div>
      <label htmlFor={id} className="block font-mono text-xs font-medium uppercase tracking-wider text-slate-600">
        {label}
      </label>
      <input
        id={id}
        {...input}
        className="mt-2 block w-full rounded-md border border-slate-300 bg-white px-3.5 py-2.5 text-[15px] text-slate-900 shadow-xs outline-none transition placeholder:text-slate-400 focus:border-blue-600 focus:ring-3 focus:ring-blue-600/15"
      />
      {hint && <p className="mt-1.5 text-xs text-slate-500">{hint}</p>}
    </div>
  );
}

export default function AuthForm({ mode }) {
  const copy = COPY[mode];
  const { signIn } = useAuth();
  const navigate = useNavigate();
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [confirm, setConfirm] = useState("");
  const [error, setError] = useState(null);
  const [busy, setBusy] = useState(false);

  async function onSubmit(e) {
    e.preventDefault();
    setError(null);
    if (mode === "signup" && password !== confirm) {
      setError("Passwords don't match.");
      return;
    }
    setBusy(true);
    try {
      await signIn(mode, username, password);
      navigate("/documents", { replace: true });
    } catch (err) {
      setError(err.message);
      setBusy(false);
    }
  }

  return (
    <div className="flex min-h-full items-center justify-center bg-slate-50 px-4 py-12">
      <div className="w-full max-w-md">
        <div className="mb-8 flex items-center justify-center gap-3">
          <div className="flex size-10 items-center justify-center rounded-lg bg-blue-700 text-lg font-semibold text-white">C</div>
          <div>
            <p className="text-xl font-semibold leading-tight tracking-tight">CiteCache</p>
            <p className="font-mono text-xs text-slate-500">Expert Utility</p>
          </div>
        </div>

        <div className="rounded-xl border border-slate-200 bg-white p-8 shadow-sm">
          <h1 className="text-2xl font-bold tracking-tight">{copy.title}</h1>
          <p className="mt-1.5 text-sm text-slate-500">{copy.subtitle}</p>

          <form onSubmit={onSubmit} className="mt-7 space-y-5" noValidate>
            <Field
              id="username" label="Username" autoComplete="username" required autoFocus
              value={username} onChange={(e) => setUsername(e.target.value)}
              hint={mode === "signup" ? "3–32 characters: letters, digits, _ . or -" : null}
            />
            <Field
              id="password" label="Password" type="password" required
              autoComplete={mode === "signup" ? "new-password" : "current-password"}
              value={password} onChange={(e) => setPassword(e.target.value)}
              hint={mode === "signup" ? "At least 8 characters." : null}
            />
            {mode === "signup" && (
              <Field
                id="confirm" label="Confirm password" type="password" required autoComplete="new-password"
                value={confirm} onChange={(e) => setConfirm(e.target.value)}
              />
            )}

            {error && (
              <div role="alert" className="flex items-start gap-2.5 rounded-md border border-red-200 bg-red-50 px-3.5 py-3 text-sm text-red-800">
                <AlertIcon className="mt-0.5 size-4 shrink-0" />
                {error}
              </div>
            )}

            <button
              type="submit"
              disabled={busy || !username || !password}
              className="flex w-full items-center justify-center gap-2 rounded-md bg-blue-700 px-4 py-3 font-mono text-sm font-medium text-white shadow-sm transition-colors hover:bg-blue-800 disabled:cursor-not-allowed disabled:opacity-50"
            >
              {busy && <Spinner className="size-4" />}
              {copy.submit}
            </button>
          </form>
        </div>

        <p className="mt-6 text-center text-sm text-slate-600">
          {copy.switchText}{" "}
          <Link to={copy.switchTo} className="font-medium text-blue-700 hover:underline">
            {copy.switchLink}
          </Link>
        </p>
      </div>
    </div>
  );
}
