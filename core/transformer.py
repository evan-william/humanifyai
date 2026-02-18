"""
TextTransformer — applies rule-based and statistical transformations to make
AI-generated text sound more natural. This is the main processing engine.

Passes (in order):
  1. passive_rewrites  — "it can be seen that" → "we can see that"
  2. formal_simplify   — verbose phrases, formal verbs/nouns → casual
  3. contractions      — "do not" → "don't", "it is" → "it's", etc.
  4. sentence_variety  — inject casual openers into monotonous sentences
"""

import re
import random
import logging
from typing import List, Tuple

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Contraction map
# ---------------------------------------------------------------------------
_CONTRACTION_EXPAND = {
    # to be
    r"\bit is\b":       "it's",
    r"\bIt is\b":       "It's",
    r"\bthat is\b":     "that's",
    r"\bThat is\b":     "That's",
    r"\bwhat is\b":     "what's",
    r"\bWhat is\b":     "What's",
    r"\bwho is\b":      "who's",
    r"\bWho is\b":      "Who's",
    r"\bhere is\b":     "here's",
    r"\bHere is\b":     "Here's",
    r"\bthere is\b":    "there's",
    r"\bThere is\b":    "There's",
    r"\bwhere is\b":    "where's",
    r"\bWhere is\b":    "Where's",
    r"\bhow is\b":      "how's",
    r"\bHow is\b":      "How's",
    # I
    r"\bI am\b":        "I'm",
    r"\bI will\b":      "I'll",
    r"\bI would\b":     "I'd",
    r"\bI have\b":      "I've",
    r"\bI had\b":       "I'd",
    # we
    r"\bwe are\b":      "we're",
    r"\bWe are\b":      "We're",
    r"\bwe will\b":     "we'll",
    r"\bWe will\b":     "We'll",
    r"\bwe have\b":     "we've",
    r"\bWe have\b":     "We've",
    r"\bwe would\b":    "we'd",
    r"\bWe would\b":    "We'd",
    # you
    r"\byou are\b":     "you're",
    r"\bYou are\b":     "You're",
    r"\byou will\b":    "you'll",
    r"\bYou will\b":    "You'll",
    r"\byou have\b":    "you've",
    r"\bYou have\b":    "You've",
    r"\byou would\b":   "you'd",
    r"\bYou would\b":   "You'd",
    # they
    r"\bthey are\b":    "they're",
    r"\bThey are\b":    "They're",
    r"\bthey will\b":   "they'll",
    r"\bThey will\b":   "They'll",
    r"\bthey have\b":   "they've",
    r"\bThey have\b":   "They've",
    r"\bthey would\b":  "they'd",
    r"\bThey would\b":  "They'd",
    # he / she
    r"\bhe is\b":       "he's",
    r"\bHe is\b":       "He's",
    r"\bhe will\b":     "he'll",
    r"\bHe will\b":     "He'll",
    r"\bhe would\b":    "he'd",
    r"\bHe would\b":    "He'd",
    r"\bhe has\b":      "he's",
    r"\bHe has\b":      "He's",
    r"\bshe is\b":      "she's",
    r"\bShe is\b":      "She's",
    r"\bshe will\b":    "she'll",
    r"\bShe will\b":    "She'll",
    r"\bshe would\b":   "she'd",
    r"\bShe would\b":   "She'd",
    r"\bshe has\b":     "she's",
    r"\bShe has\b":     "She's",
    # negatives
    r"\bdo not\b":      "don't",
    r"\bDo not\b":      "Don't",
    r"\bdoes not\b":    "doesn't",
    r"\bDoes not\b":    "Doesn't",
    r"\bdid not\b":     "didn't",
    r"\bDid not\b":     "Didn't",
    r"\bcannot\b":      "can't",
    r"\bCannot\b":      "Can't",
    r"\bcould not\b":   "couldn't",
    r"\bCould not\b":   "Couldn't",
    r"\bwould not\b":   "wouldn't",
    r"\bWould not\b":   "Wouldn't",
    r"\bshould not\b":  "shouldn't",
    r"\bShould not\b":  "Shouldn't",
    r"\bwill not\b":    "won't",
    r"\bWill not\b":    "Won't",
    r"\bmust not\b":    "mustn't",
    r"\bMust not\b":    "Mustn't",
    r"\bneed not\b":    "needn't",
    r"\bNeed not\b":    "Needn't",
    r"\bis not\b":      "isn't",
    r"\bIs not\b":      "Isn't",
    r"\bare not\b":     "aren't",
    r"\bAre not\b":     "Aren't",
    r"\bwas not\b":     "wasn't",
    r"\bWas not\b":     "Wasn't",
    r"\bwere not\b":    "weren't",
    r"\bWere not\b":    "Weren't",
    r"\bhave not\b":    "haven't",
    r"\bHave not\b":    "Haven't",
    r"\bhas not\b":     "hasn't",
    r"\bHas not\b":     "Hasn't",
    r"\bhad not\b":     "hadn't",
    r"\bHad not\b":     "Hadn't",
    # misc
    r"\blet us\b":      "let's",
    r"\bLet us\b":      "Let's",
}

# ---------------------------------------------------------------------------
# Formal → casual phrase substitutions
# Longer / more specific patterns come first to avoid partial matches.
# ---------------------------------------------------------------------------
_FORMAL_TO_CASUAL: List[Tuple[str, str]] = [
    # Transition words
    (r"\bIn conclusion,?\b",                    "To wrap up,"),
    (r"\bTo summarize,?\b",                     "In short,"),
    (r"\bTo conclude,?\b",                      "To wrap up,"),
    (r"\bIn summary,?\b",                       "In short,"),
    (r"\bFurthermore,?\b",                      "On top of that,"),
    (r"\bMoreover,?\b",                         "Plus,"),
    (r"\bIn addition,?\b",                      "Also,"),
    (r"\bAdditionally,?\b",                     "Also,"),
    (r"\bSubsequently,?\b",                     "Then,"),
    (r"\bConversely,?\b",                       "On the flip side,"),
    (r"\bNevertheless,?\b",                     "Still,"),
    (r"\bNonetheless,?\b",                      "Still,"),
    (r"\bHowever,?\b",                          "That said,"),
    (r"\bConsequently,?\b",                     "So,"),
    (r"\bTherefore,?\b",                        "So,"),
    (r"\bThus,?\b",                             "So,"),
    (r"\bHence,?\b",                            "Which is why"),
    (r"\bAccordingly,?\b",                      "So,"),

    # Filler openings
    (r"\bIt is important to note that\b",       "Worth noting:"),
    (r"\bIt is worth noting that\b",            "Worth noting:"),
    (r"\bIt should be noted that\b",            "Note that"),
    (r"\bIt is worth mentioning that\b",        "Interestingly,"),
    (r"\bIt is crucial to understand that\b",   "The key thing is"),
    (r"\bIt is essential to recognize that\b",  "Keep in mind that"),
    (r"\bIt is evident that\b",                 "Clearly,"),
    (r"\bIt is clear that\b",                   "Clearly,"),
    (r"\bIt is obvious that\b",                 "Obviously,"),
    (r"\bIt is widely known that\b",            "Most people know that"),
    (r"\bIt goes without saying that\b",        "Obviously,"),
    (r"\bNeedless to say,?\b",                  "Obviously,"),
    (r"\bAs previously mentioned,?\b",          "As I said,"),
    (r"\bAs mentioned above,?\b",               "As I said,"),
    (r"\bAs stated earlier,?\b",                "As I said,"),
    (r"\bAs we can see,?\b",                    "Clearly,"),

    # Verbose constructions
    (r"\bIn order to\b",                        "To"),
    (r"\bin order to\b",                        "to"),
    (r"\bdue to the fact that\b",               "because"),
    (r"\bDue to the fact that\b",               "Because"),
    (r"\bin light of the fact that\b",          "since"),
    (r"\bIn light of the fact that\b",          "Since"),
    (r"\bfor the purpose of\b",                 "to"),
    (r"\bFor the purpose of\b",                 "To"),
    (r"\bwith the intention of\b",              "to"),
    (r"\bWith the intention of\b",              "To"),
    (r"\bat this point in time\b",              "now"),
    (r"\bAt this point in time\b",              "Now"),
    (r"\bat the present time\b",                "currently"),
    (r"\bAt the present time\b",                "Currently"),
    (r"\bin the near future\b",                 "soon"),
    (r"\bIn the near future\b",                 "Soon"),
    (r"\bon a daily basis\b",                   "every day"),
    (r"\bOn a daily basis\b",                   "Every day"),
    (r"\bprior to\b",                           "before"),
    (r"\bPrior to\b",                           "Before"),
    (r"\bsubsequent to\b",                      "after"),
    (r"\bSubsequent to\b",                      "After"),
    (r"\bwith regard to\b",                     "about"),
    (r"\bWith regard to\b",                     "About"),
    (r"\bwith respect to\b",                    "about"),
    (r"\bWith respect to\b",                    "About"),
    (r"\bin terms of\b",                        "for"),
    (r"\bIn terms of\b",                        "For"),
    (r"\bfor the most part\b",                  "mostly"),
    (r"\bFor the most part\b",                  "Mostly"),
    (r"\bto a certain extent\b",                "somewhat"),
    (r"\bTo a certain extent\b",                "Somewhat"),
    (r"\ba large number of\b",                  "many"),
    (r"\bA large number of\b",                  "Many"),
    (r"\ba majority of\b",                      "most"),
    (r"\bA majority of\b",                      "Most"),
    (r"\bthe majority of\b",                    "most"),
    (r"\bThe majority of\b",                    "Most"),
    (r"\ba wide variety of\b",                  "many kinds of"),
    (r"\bA wide variety of\b",                  "Many kinds of"),
    (r"\bplay a crucial role in\b",             "directly affect"),
    (r"\bplay an important role in\b",          "matter for"),
    (r"\bplay a role in\b",                     "affect"),

    # Formal verbs → casual
    (r"\bUtilize\b",        "use"),
    (r"\butilize\b",        "use"),
    (r"\bFacilitate\b",     "help"),
    (r"\bfacilitate\b",     "help"),
    (r"\bDemonstrate\b",    "show"),
    (r"\bdemonstrate\b",    "show"),
    (r"\bAssist\b",         "help"),
    (r"\bassist\b",         "help"),
    (r"\bObtain\b",         "get"),
    (r"\bobtain\b",         "get"),
    (r"\bPurchase\b",       "buy"),
    (r"\bpurchase\b",       "buy"),
    (r"\bProvide\b",        "give"),
    (r"\bprovide\b",        "give"),
    (r"\bRequire\b",        "need"),
    (r"\brequire\b",        "need"),
    (r"\bAttempt\b",        "try"),
    (r"\battempt\b",        "try"),
    (r"\bCommence\b",       "start"),
    (r"\bcommence\b",       "start"),
    (r"\bTerminate\b",      "end"),
    (r"\bterminate\b",      "end"),
    (r"\bAscertain\b",      "find out"),
    (r"\bascertain\b",      "find out"),
    (r"\bEnhance\b",        "improve"),
    (r"\benhance\b",        "improve"),
    (r"\bImplement\b",      "use"),
    (r"\bimplement\b",      "use"),
    (r"\bLeverage\b",       "use"),
    (r"\bleverage\b",       "use"),
    (r"\bMaximize\b",       "get the most out of"),
    (r"\bmaximize\b",       "get the most out of"),
    (r"\bMinimize\b",       "reduce"),
    (r"\bminimize\b",       "reduce"),
    (r"\bOptimize\b",       "improve"),
    (r"\boptimize\b",       "improve"),
    (r"\bPrioritize\b",     "focus on"),
    (r"\bprioritize\b",     "focus on"),

    # Formal nouns → casual
    (r"\bindividuals\b",    "people"),
    (r"\bIndividuals\b",    "People"),
    (r"\bresidence\b",      "home"),
    (r"\bResidence\b",      "Home"),
    (r"\bemployment\b",     "work"),
    (r"\bEmployment\b",     "Work"),
    (r"\bcompensation\b",   "pay"),
    (r"\bCompensation\b",   "Pay"),

    # Redundant qualifiers AI loves
    (r"\bvery unique\b",            "unique"),
    (r"\bVery unique\b",            "Unique"),
    (r"\babsolutely essential\b",   "essential"),
    (r"\bAbsolutely essential\b",   "Essential"),
    (r"\bcompletely eliminate\b",   "eliminate"),
    (r"\bCompletely eliminate\b",   "Eliminate"),
    (r"\bbasically\b",              ""),
    (r"\bessentially\b",            ""),
    (r"\bfundamentally\b",          ""),
    (r"\bultimately\b",             "in the end"),
    (r"\bUltimately\b",             "In the end"),
]

# ---------------------------------------------------------------------------
# Passive voice → active rewrites
# ---------------------------------------------------------------------------
_PASSIVE_REWRITES: List[Tuple[str, str]] = [
    (r"\bit can be seen that\b",        "we can see that"),
    (r"\bIt can be seen that\b",        "We can see that"),
    (r"\bit can be argued that\b",      "you could argue that"),
    (r"\bIt can be argued that\b",      "You could argue that"),
    (r"\bit can be said that\b",        "you could say that"),
    (r"\bIt can be said that\b",        "You could say that"),
    (r"\bit has been shown that\b",     "research shows that"),
    (r"\bIt has been shown that\b",     "Research shows that"),
    (r"\bit has been found that\b",     "studies found that"),
    (r"\bIt has been found that\b",     "Studies found that"),
    (r"\bit is believed that\b",        "many believe that"),
    (r"\bIt is believed that\b",        "Many believe that"),
    (r"\bit is suggested that\b",       "the data suggests that"),
    (r"\bIt is suggested that\b",       "The data suggests that"),
    (r"\bit is recommended that\b",     "we recommend that"),
    (r"\bIt is recommended that\b",     "We recommend that"),
    (r"\bit is expected that\b",        "we expect that"),
    (r"\bIt is expected that\b",        "We expect that"),
    (r"\bit is assumed that\b",         "we assume that"),
    (r"\bIt is assumed that\b",         "We assume that"),
    (r"\bit is acknowledged that\b",    "we acknowledge that"),
    (r"\bIt is acknowledged that\b",    "We acknowledge that"),
    (r"\bshould be noted\b",            "worth noting"),
    (r"\bshould be mentioned\b",        "worth mentioning"),
    (r"\bmust be considered\b",         "we need to consider"),
]

_HUMAN_OPENERS = [
    "Honestly,",
    "Here's the thing —",
    "Think about it:",
    "To be fair,",
    "The short answer is",
    "Interestingly enough,",
    "You might be surprised, but",
    "Real talk —",
    "And honestly?",
    "Here's what matters:",
    "Worth saying:",
    "Look —",
]


class TextTransformer:
    """
    Applies a configurable pipeline of transformations to a text string.
    Each pass is isolated and toggleable. Transforms run in order so
    later passes do not undo earlier ones.
    """

    def __init__(
        self,
        use_contractions: bool = True,
        simplify_formal: bool = True,
        vary_sentences: bool = True,
        rewrite_passive: bool = True,
        seed: int | None = None,
    ):
        self.use_contractions = use_contractions
        self.simplify_formal = simplify_formal
        self.vary_sentences = vary_sentences
        self.rewrite_passive = rewrite_passive
        self._rng = random.Random(seed)

    def transform(self, text: str) -> str:
        if not text or not text.strip():
            return text

        result = text

        if self.rewrite_passive:
            result = self._apply_passive_rewrites(result)

        if self.simplify_formal:
            result = self._apply_formal_simplification(result)

        if self.use_contractions:
            result = self._apply_contractions(result)

        if self.vary_sentences:
            result = self._apply_sentence_variation(result)

        result = self._clean_up(result)
        return result

    # ------------------------------------------------------------------
    # Transformation passes
    # ------------------------------------------------------------------

    def _apply_contractions(self, text: str) -> str:
        for pattern, replacement in _CONTRACTION_EXPAND.items():
            text = re.sub(pattern, replacement, text)
        return text

    def _apply_formal_simplification(self, text: str) -> str:
        for pattern, replacement in _FORMAL_TO_CASUAL:
            text = re.sub(pattern, replacement, text)
        return text

    def _apply_passive_rewrites(self, text: str) -> str:
        for pattern, replacement in _PASSIVE_REWRITES:
            text = re.sub(pattern, replacement, text)
        return text

    def _apply_sentence_variation(self, text: str) -> str:
        sentences = re.split(r"(?<=[.!?])\s+", text)
        if len(sentences) < 4:
            return text

        result_parts = []
        for i, sent in enumerate(sentences):
            if i > 0 and i % 5 == 0 and re.match(r"^(The|This)\b", sent):
                opener = self._rng.choice(_HUMAN_OPENERS)
                sent = f"{opener} {sent[0].lower()}{sent[1:]}"
            result_parts.append(sent)

        return " ".join(result_parts)

    @staticmethod
    def _clean_up(text: str) -> str:
        # Fix double spaces from empty-string replacements (e.g. "basically" → "")
        text = re.sub(r" {2,}", " ", text)
        # Fix artifact commas like "So, ,"
        text = re.sub(r",\s*,", ",", text)
        # Fix space before period
        text = re.sub(r"\s+\.", ".", text)
        # Fix leading space after newlines
        text = re.sub(r"\n ", "\n", text)
        return text.strip()