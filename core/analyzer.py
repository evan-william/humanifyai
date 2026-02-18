"""
HumanLikenessAnalyzer — extracts linguistic features from text and scores
how closely it resembles human writing versus typical AI output.

Uses only scikit-learn + standard library; no external LLM calls required.
"""

import re
import math
import logging
from dataclasses import dataclass, field
from typing import Dict, List, Tuple

import numpy as np
from sklearn.preprocessing import MinMaxScaler

logger = logging.getLogger(__name__)


@dataclass
class TextFeatures:
    """Raw linguistic measurements extracted from a text sample."""
    avg_sentence_length: float = 0.0
    sentence_length_variance: float = 0.0
    avg_word_length: float = 0.0
    lexical_diversity: float = 0.0          # type-token ratio
    punctuation_density: float = 0.0
    contraction_rate: float = 0.0
    passive_voice_rate: float = 0.0
    question_rate: float = 0.0
    exclamation_rate: float = 0.0
    paragraph_variation: float = 0.0
    avg_syllables_per_word: float = 0.0
    rare_word_rate: float = 0.0
    first_person_rate: float = 0.0
    conjunction_start_rate: float = 0.0
    hedge_word_rate: float = 0.0


@dataclass
class AnalysisResult:
    score: float                            # 0–100, higher = more human-like
    grade: str                              # A/B/C/D/F label
    features: Dict[str, float] = field(default_factory=dict)
    suggestions: List[str] = field(default_factory=list)
    word_count: int = 0
    sentence_count: int = 0


# Common English contractions used to detect informal, human-style writing
_CONTRACTIONS = re.compile(
    r"\b(i'm|you're|he's|she's|it's|we're|they're|i've|you've|we've|they've|"
    r"i'd|you'd|he'd|she'd|we'd|they'd|i'll|you'll|he'll|she'll|we'll|they'll|"
    r"isn't|aren't|wasn't|weren't|haven't|hasn't|hadn't|won't|wouldn't|don't|"
    r"doesn't|didn't|can't|couldn't|shouldn't|mustn't|let's|that's|who's|what's|"
    r"here's|there's|when's|where's|why's|how's)\b",
    re.IGNORECASE,
)

_PASSIVE_INDICATORS = re.compile(
    r"\b(was|were|is|are|been|being)\s+([\w]+ed|built|written|made|done|given|"
    r"taken|known|seen|found|used|called|considered|expected|required|provided)\b",
    re.IGNORECASE,
)

_HEDGE_WORDS = re.compile(
    r"\b(perhaps|maybe|possibly|probably|might|could|seems|appear|suggest|"
    r"indicate|generally|typically|usually|often|sometimes|somewhat|rather|"
    r"fairly|quite|relatively|apparently|presumably)\b",
    re.IGNORECASE,
)

_CONJUNCTIONS = re.compile(r"^(but|and|or|nor|so|yet|for)\b", re.IGNORECASE)

_FIRST_PERSON = re.compile(r"\b(i|me|my|mine|myself|we|us|our|ours|ourselves)\b", re.IGNORECASE)

# Very rough syllable counter — good enough for statistical scoring
def _count_syllables(word: str) -> int:
    word = word.lower().strip(".,!?;:")
    if len(word) <= 3:
        return 1
    word = re.sub(r"e$", "", word)
    vowels = re.findall(r"[aeiouy]+", word)
    return max(1, len(vowels))


# 1000 most common English words (abbreviated set used as "common word" reference)
_COMMON_WORDS = frozenset([
    "the","be","to","of","and","a","in","that","have","it","for","not","on","with",
    "he","as","you","do","at","this","but","his","by","from","they","we","say","her",
    "she","or","an","will","my","one","all","would","there","their","what","so","up",
    "out","if","about","who","get","which","go","me","when","make","can","like","time",
    "no","just","him","know","take","people","into","year","your","good","some","could",
    "them","see","other","than","then","now","look","only","come","its","over","think",
    "also","back","after","use","two","how","our","work","first","well","way","even",
    "new","want","because","any","these","give","day","most","us",
])


class HumanLikenessAnalyzer:
    """
    Extracts ~15 linguistic features and maps them to a weighted 0–100 score.
    The scoring weights are hand-tuned heuristics — not ML-trained weights —
    because we don't need a labelled dataset for this use case.
    """

    # Feature → (ideal_low, ideal_high, weight)
    # "ideal" ranges are empirical targets for human-like prose.
    _FEATURE_TARGETS: Dict[str, Tuple[float, float, float]] = {
        "avg_sentence_length":      (10.0, 22.0, 1.2),
        "sentence_length_variance": (20.0, 120.0, 1.5),
        "lexical_diversity":        (0.55, 1.0,  1.3),
        "contraction_rate":         (0.005, 0.08, 1.4),
        "punctuation_density":      (0.04, 0.12, 0.8),
        "question_rate":            (0.0,  0.2,  0.7),
        "hedge_word_rate":          (0.005, 0.06, 1.0),
        "first_person_rate":        (0.005, 0.08, 1.1),
        "conjunction_start_rate":   (0.0,  0.25, 0.9),
        "passive_voice_rate":       (0.0,  0.25, 0.8),  # some passive is fine
        "avg_syllables_per_word":   (1.3,  1.9,  0.7),
        "rare_word_rate":           (0.05, 0.3,  0.6),
    }

    def __init__(self) -> None:
        self._loaded = False

    def load(self) -> None:
        # Nothing heavy to load right now, but this keeps the interface
        # compatible if we swap to a real trained model later.
        self._loaded = True
        logger.info("HumanLikenessAnalyzer loaded.")

    def extract_features(self, text: str) -> Tuple[TextFeatures, int, int]:
        sentences = self._split_sentences(text)
        words = re.findall(r"\b[a-z']+\b", text.lower())
        n_words = len(words)
        n_sentences = max(1, len(sentences))

        if n_words == 0:
            return TextFeatures(), 0, 0

        sent_lengths = [len(re.findall(r"\b\w+\b", s)) for s in sentences]

        features = TextFeatures(
            avg_sentence_length=float(np.mean(sent_lengths)),
            sentence_length_variance=float(np.var(sent_lengths)),
            avg_word_length=float(np.mean([len(w.strip("'")) for w in words])),
            lexical_diversity=len(set(words)) / n_words,
            punctuation_density=len(re.findall(r"[.,;:!?\"'—–-]", text)) / max(1, len(text)),
            contraction_rate=len(_CONTRACTIONS.findall(text)) / n_words,
            passive_voice_rate=len(_PASSIVE_INDICATORS.findall(text)) / n_sentences,
            question_rate=sum(1 for s in sentences if s.strip().endswith("?")) / n_sentences,
            exclamation_rate=sum(1 for s in sentences if s.strip().endswith("!")) / n_sentences,
            avg_syllables_per_word=float(np.mean([_count_syllables(w) for w in words])),
            rare_word_rate=sum(1 for w in words if w not in _COMMON_WORDS) / n_words,
            first_person_rate=len(_FIRST_PERSON.findall(text)) / n_words,
            conjunction_start_rate=sum(1 for s in sentences if _CONJUNCTIONS.match(s.strip())) / n_sentences,
            hedge_word_rate=len(_HEDGE_WORDS.findall(text)) / n_words,
        )
        return features, n_words, n_sentences

    def score(self, text: str) -> AnalysisResult:
        if not self._loaded:
            raise RuntimeError("Analyzer not loaded. Call load() first.")

        features, n_words, n_sentences = self.extract_features(text)
        feature_dict = {k: getattr(features, k) for k in self._FEATURE_TARGETS}

        raw_scores: Dict[str, float] = {}
        weighted_sum = 0.0
        total_weight = 0.0

        for name, (lo, hi, weight) in self._FEATURE_TARGETS.items():
            value = feature_dict.get(name, 0.0)
            # Distance-to-ideal: 1.0 when inside range, falls off outside
            if lo <= value <= hi:
                component = 1.0
            else:
                distance = min(abs(value - lo), abs(value - hi))
                span = max(hi - lo, 1e-6)
                component = max(0.0, 1.0 - (distance / span))

            raw_scores[name] = round(component * 100, 2)
            weighted_sum += component * weight
            total_weight += weight

        final_score = round((weighted_sum / total_weight) * 100, 1)
        grade = self._grade(final_score)
        suggestions = self._generate_suggestions(features, final_score)

        return AnalysisResult(
            score=final_score,
            grade=grade,
            features=raw_scores,
            suggestions=suggestions,
            word_count=n_words,
            sentence_count=n_sentences,
        )

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _split_sentences(text: str) -> List[str]:
        # Simple but reliable sentence splitter
        parts = re.split(r"(?<=[.!?])\s+", text.strip())
        return [p for p in parts if p.strip()]

    @staticmethod
    def _grade(score: float) -> str:
        if score >= 85:
            return "A"
        elif score >= 70:
            return "B"
        elif score >= 55:
            return "C"
        elif score >= 40:
            return "D"
        return "F"

    @staticmethod
    def _generate_suggestions(features: TextFeatures, score: float) -> List[str]:
        tips: List[str] = []

        if features.sentence_length_variance < 20:
            tips.append("Vary your sentence lengths more — mix short punchy sentences with longer ones.")
        if features.contraction_rate < 0.005:
            tips.append("Add contractions (it's, don't, you'll) for a more conversational tone.")
        if features.avg_sentence_length > 25:
            tips.append("Break up long sentences to improve readability.")
        if features.avg_sentence_length < 8:
            tips.append("Some sentences feel too short. Try combining related thoughts.")
        if features.passive_voice_rate > 0.4:
            tips.append("Reduce passive voice — rewrite with the actor first (e.g. 'We found' not 'It was found').")
        if features.first_person_rate < 0.005:
            tips.append("Consider using first-person perspective where appropriate ('I think', 'We noticed').")
        if features.rare_word_rate < 0.05:
            tips.append("The vocabulary is quite simple. Occasional specific or domain terms add credibility.")
        if features.hedge_word_rate > 0.08:
            tips.append("Too many hedging words ('perhaps', 'maybe'). Be more direct where you can.")
        if features.conjunction_start_rate > 0.3:
            tips.append("Starting too many sentences with conjunctions (But, And) can feel repetitive.")

        if not tips:
            tips.append("The text already reads naturally. Minor tweaks only.")

        return tips[:5]  # cap at 5 suggestions