import { PhasePage } from "@/components/common/PhasePage";

export default function Evaluation() {
  return (
    <PhasePage
      phase={10}
      title="RAG evaluation"
      description="Measure how well retrieval and answer generation work."
      features={[
        "Evaluation dataset of questions, expected answers and relevant chunks",
        "Precision@K, Recall@K, hit rate and MRR",
        "Faithfulness, answer relevance and context metrics",
        "Compare dense, BM25, hybrid and reranked retrieval",
        "Failure analysis with a suggested fix for each failed case",
      ]}
    />
  );
}
