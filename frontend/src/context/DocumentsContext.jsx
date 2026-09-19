import { createContext, useCallback, useContext, useEffect, useMemo, useRef, useState } from "react";
import { api } from "../lib/api.js";

const DocumentsContext = createContext(null);
const POLL_MS = 700;

const isActive = (job) => job.status === "queued" || job.status === "processing";

export function DocumentsProvider({ children }) {
  const [documents, setDocuments] = useState([]);
  const [jobs, setJobs] = useState([]);
  const [loaded, setLoaded] = useState(false);
  const [uploadError, setUploadError] = useState(null);
  const finishedIds = useRef(new Set());

  const refresh = useCallback(async () => {
    const [docs, js] = await Promise.all([api.documents(), api.jobs()]);
    js.filter((j) => !isActive(j)).forEach((j) => finishedIds.current.add(j.id));
    setDocuments(docs);
    setJobs(js);
    setLoaded(true);
  }, []);

  useEffect(() => {
    refresh().catch(() => setLoaded(true));
  }, [refresh]);

  const hasActive = jobs.some(isActive);

  // Poll only while something is uploading; refresh the document list the
  // moment any job finishes so it appears as "Ready" without a reload.
  useEffect(() => {
    if (!hasActive) return undefined;
    const timer = setInterval(async () => {
      try {
        const js = await api.jobs();
        const newlyFinished = js.some((j) => !isActive(j) && !finishedIds.current.has(j.id));
        js.filter((j) => !isActive(j)).forEach((j) => finishedIds.current.add(j.id));
        setJobs(js);
        if (newlyFinished) setDocuments(await api.documents());
      } catch {
        /* transient poll failure: the next tick retries */
      }
    }, POLL_MS);
    return () => clearInterval(timer);
  }, [hasActive]);

  const upload = useCallback(async (fileList) => {
    const files = Array.from(fileList || []);
    if (!files.length) return;
    setUploadError(null);
    try {
      const created = await api.upload(files);
      setJobs((prev) => [...created, ...prev.filter((p) => !created.some((c) => c.id === p.id))]);
    } catch (e) {
      setUploadError(e.message);
    }
  }, []);

  const value = useMemo(
    () => ({ documents, jobs, loaded, upload, uploadError, clearUploadError: () => setUploadError(null), refresh }),
    [documents, jobs, loaded, upload, uploadError, refresh],
  );
  return <DocumentsContext.Provider value={value}>{children}</DocumentsContext.Provider>;
}

export function useDocuments() {
  return useContext(DocumentsContext);
}

export { isActive };
