"""
Debug script -- runs RAGAS on ONE question with raise_exceptions=True,
so whatever is actually failing inside context_recall/factual_correctness/
response_relevancy shows up as a real traceback instead of being
silently swallowed.

Run this from inside ragas_eval/ (same venv as run_ragas_metrics.py):
    python debug_single_question.py
    python debug_single_question.py q05     # pick a specific question id
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

from dotenv import load_dotenv

_THIS_DIR = Path(__file__).resolve().parent
_PROJECT_ROOT = _THIS_DIR.parent
load_dotenv(_THIS_DIR / ".env")

import os

GEMINI_MODEL = os.getenv("RAGAS_GEMINI_MODEL", "gemini-3.5-flash-lite")
LOCAL_EMBEDDING_MODEL = os.getenv("RAGAS_EMBEDDING_MODEL", "BAAI/bge-small-en-v1.5")

DATASET_PATH = _PROJECT_ROOT / "data" / "ragas_dataset.json"


def main() -> None:
    dataset = json.loads(DATASET_PATH.read_text())
    qid = sys.argv[1] if len(sys.argv) > 1 else next(iter(dataset))
    entry = dataset[qid]

    print(f"Debugging question: {qid}")
    print(f"  question: {entry['question']}")
    print(f"  ground_truth: {entry['ground_truth']}")
    print(f"  num contexts: {len(entry['contexts'])}")
    print(f"  answer: {entry['answer'][:150]}...")
    print()

    from langchain_google_genai import ChatGoogleGenerativeAI
    from langchain_huggingface import HuggingFaceEmbeddings
    from ragas.llms import LangchainLLMWrapper
    from ragas.embeddings import LangchainEmbeddingsWrapper
    from ragas import EvaluationDataset, SingleTurnSample, evaluate
    from ragas.metrics import LLMContextRecall, FactualCorrectness
    from ragas.run_config import RunConfig

    api_key = os.getenv("GEMINI_API_KEY")
    llm = LangchainLLMWrapper(ChatGoogleGenerativeAI(model=GEMINI_MODEL, google_api_key=api_key, temperature=0))
    embeddings = LangchainEmbeddingsWrapper(HuggingFaceEmbeddings(model_name=LOCAL_EMBEDDING_MODEL))

    sample = SingleTurnSample(
        user_input=entry["question"],
        response=entry["answer"],
        retrieved_contexts=entry["contexts"] or ["(no context retrieved)"],
        reference=entry["ground_truth"],
    )
    eval_dataset = EvaluationDataset(samples=[sample])

    metric_name = sys.argv[2] if len(sys.argv) > 2 else "factual_correctness"
    metric = FactualCorrectness() if metric_name == "factual_correctness" else LLMContextRecall()

    print(f"--- Running {metric.__class__.__name__} with raise_exceptions=True ---\n")
    try:
        result = evaluate(
            dataset=eval_dataset,
            metrics=[metric],
            llm=llm,
            embeddings=embeddings,
            run_config=RunConfig(max_workers=1, timeout=180),
            raise_exceptions=True,  # <-- the difference: let it actually crash so we see why
        )
        print("Result:", result.to_pandas().to_dict())
    except Exception as e:
        print(f"REAL EXCEPTION SURFACED:\n{type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
