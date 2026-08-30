
from __future__ import annotations

import requests
import streamlit as st

API_BASE = "http://localhost:8000"

st.set_page_config(page_title="CiteCache", page_icon="📚", layout="wide")
st.title("📚 CiteCache — Verified RAG with Semantic Cache")

with st.sidebar:
    st.header("Status")
    try:
        health = requests.get(f"{API_BASE}/health", timeout=5).json()
        st.success("Backend connected")
        st.metric("Documents indexed", health.get("documents_indexed", 0))
        st.caption(f"LLM provider: {health.get('llm_provider', 'unknown')}")
    except requests.exceptions.ConnectionError:
        st.error("Can't reach the API. Start it first:\n\n`uvicorn app.api.main:app --reload`")
        st.stop()

    st.divider()
    if st.button("🗑️ Reset all documents & cache", use_container_width=True):
        try:
            r = requests.post(f"{API_BASE}/reset", timeout=30)
            r.raise_for_status()
            data = r.json()
            st.success(
                f"Cleared {data['doc_chunks_deleted']} chunk(s) and "
                f"{data['cache_entries_deleted']} cache entry(ies)."
            )
            st.rerun()
        except requests.exceptions.RequestException as e:
            st.error(f"Reset failed: {e}")

tab_upload, tab_ask = st.tabs(["📤 Upload Documents", "💬 Ask a Question"])

with tab_upload:
    st.subheader("Upload support documents")
    st.caption("Markdown, plain text, PDF, or Word (.docx) files. Each is chunked, embedded, and indexed immediately.")
    uploaded_files = st.file_uploader("Choose files", accept_multiple_files=True, type=["md", "txt", "pdf", "docx"])

    if st.button("Index uploaded documents", disabled=not uploaded_files):
        _CONTENT_TYPES = {
            "md": "text/markdown",
            "txt": "text/plain",
            "pdf": "application/pdf",
            "docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        }
        files_payload = [
            ("files", (f.name, f.getvalue(), _CONTENT_TYPES.get(f.name.rsplit(".", 1)[-1].lower(), "application/octet-stream")))
            for f in uploaded_files
        ]
        with st.spinner("Chunking, embedding, and indexing..."):
            try:
                resp = requests.post(f"{API_BASE}/upload", files=files_payload, timeout=120)
                resp.raise_for_status()
                data = resp.json()
                st.success(f"Indexed {data['total_chunks_indexed']} chunks from {data['files_processed']} file(s).")
                for r in data["results"]:
                    st.write(f"- **{r['filename']}** → {r['chunks_indexed']} chunks (doc_type: `{r['doc_type']}`)")
                st.info(f"Total chunks now in collection: {data['total_chunks_in_collection']}")
            except requests.exceptions.RequestException as e:
                st.error(f"Upload failed: {e}")

with tab_ask:
    st.subheader("Ask a question")
    question = st.text_input("Your question", placeholder="How do I reset my password?")

    if st.button("Ask", disabled=not question):
        with st.spinner("Thinking..."):
            data = None
            try:
                resp = requests.post(f"{API_BASE}/ask", json={"question": question}, timeout=60)
                resp.raise_for_status()
                data = resp.json()
            except requests.exceptions.RequestException as e:
                st.error(f"Request failed: {e}")

        if data:
            source_badge = "🟢 served from cache" if data["source"] == "cache" else "🔵 freshly generated"
            st.markdown(
                f"**{source_badge}**  ·  confidence: `{data['confidence']:.2f}`  ·  "
                f"{data['latency_ms']:.0f}ms"
            )

            if data.get("insufficient_context"):
                st.warning("The model flagged this as insufficient context — answer may be incomplete.")

            st.markdown("### Answer")
            st.write(data["answer"])

            if data["citations"]:
                st.markdown("### Citations")
                for c in data["citations"]:
                    badge = ""
                    if c.get("supported") is True:
                        badge = "✅ verified"
                    elif c.get("supported") is False:
                        badge = "❌ not supported"
                    source_label = f" (source: `{c['source']}`)" if c.get("source") else ""
                    st.write(f"- `{c['chunk_id'][:8]}...`{source_label} {badge}")
                    if c.get("claim"):
                        st.caption(c["claim"])
            else:
                st.caption("No citations returned.")
