"""Sentence-level natural-language-inference hallucination detector."""

import re
from functools import lru_cache

import numpy as np
from sentence_transformers import CrossEncoder

from app.models.schemas import HallucinationClaim


SENTENCE_SPLIT = re.compile(r"(?<=[.!?])\s+(?=[A-Z0-9])")


class HallucinationDetector:
    """Classify whether each answer sentence is entailed by retrieved evidence."""

    def __init__(self, model_name: str) -> None:
        self.model_name = model_name

    @staticmethod
    @lru_cache(maxsize=1)
    def _load(model_name: str) -> CrossEncoder:
        return CrossEncoder(model_name)

    @staticmethod
    def _softmax(values: np.ndarray) -> np.ndarray:
        shifted = values - np.max(values, axis=-1, keepdims=True)
        exponent = np.exp(shifted)
        return exponent / exponent.sum(axis=-1, keepdims=True)

    def check(self, answer: str, contexts: list[str]) -> list[HallucinationClaim]:
        """Run NLI for each substantive sentence against the combined context."""
        sentences = [
            sentence.strip()
            for sentence in SENTENCE_SPLIT.split(answer.strip())
            if len(sentence.split()) >= 3
        ]
        if not sentences:
            return []
        premise = "\n".join(contexts)
        if not premise:
            return [
                HallucinationClaim(
                    sentence=sentence,
                    label="UNSUPPORTED",
                    entailment_score=0.0,
                    contradiction_score=0.0,
                    neutral_score=1.0,
                )
                for sentence in sentences
            ]

        model = self._load(self.model_name)
        logits = np.asarray(
            model.predict([(premise, sentence) for sentence in sentences], show_progress_bar=False)
        )
        probabilities = self._softmax(logits)
        id2label = {
            int(index): str(label).lower()
            for index, label in model.model.config.id2label.items()
        }

        def find_index(term: str, fallback: int) -> int:
            return next((index for index, label in id2label.items() if term in label), fallback)

        contradiction_index = find_index("contradiction", 0)
        entailment_index = find_index("entail", 1)
        neutral_index = find_index("neutral", 2)
        checks: list[HallucinationClaim] = []
        for sentence, scores in zip(sentences, probabilities, strict=False):
            entailment = float(scores[entailment_index])
            contradiction = float(scores[contradiction_index])
            neutral = float(scores[neutral_index])
            if entailment >= 0.65:
                label = "SUPPORTED"
            elif contradiction >= 0.55:
                label = "UNSUPPORTED"
            else:
                label = "POSSIBLE_HALLUCINATION"
            checks.append(
                HallucinationClaim(
                    sentence=sentence,
                    label=label,
                    entailment_score=round(entailment, 4),
                    contradiction_score=round(contradiction, 4),
                    neutral_score=round(neutral, 4),
                )
            )
        return checks

