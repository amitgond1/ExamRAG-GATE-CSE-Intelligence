export type Strategy = 'dense' | 'hybrid' | 'hybrid_rerank'

export interface SourceChunk {
  chunk_id: string; text: string; source: string; page: number | null
  subject: string; topic: string; difficulty: string; score: number
}

export interface MetricScores {
  faithfulness: number | null; answer_relevancy: number | null
  context_precision: number | null; context_recall: number | null
  hallucination_rate: number | null; mean_latency_ms: number | null
}

export interface EvaluationRun {
  run_id: string; run_name: string; started_at: string; status: string
  strategy: string | null; metrics: Record<string, number>
}

export interface EvaluationItem { question: string; ground_truth: string; expected_topic?: string }
