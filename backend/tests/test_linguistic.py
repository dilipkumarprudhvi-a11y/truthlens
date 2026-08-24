"""
Unit tests for deterministic linguistic engine.
Verifies that outputs are 100% deterministic (no randomness).
"""

import pytest
from backend.services.linguistic import (
    compute_sentiment,
    compute_clickbait,
    compute_bias,
    compute_readability,
    compute_writing_style,
    compute_virality_proxy,
    analyze_linguistic_signals
)


def test_sentiment_deterministic_consistency():
    text = "Scientists published a remarkable breakthrough demonstrating positive growth and innovative sustainable energy solutions."
    s1 = compute_sentiment(text)
    s2 = compute_sentiment(text)
    
    assert s1.tone == s2.tone
    assert s1.positive_pct == s2.positive_pct
    assert s1.polarity_score == s2.polarity_score
    assert s1.tone == "Positive / Optimistic"
    assert s1.polarity_score > 0.0


def test_sentiment_alarmist_fear():
    text = "WARNING: Terrifying disaster and deadly catastrophe causes panic, chaos, and existential threat across the nation!"
    res = compute_sentiment(text)
    assert res.fear_pct > 0
    assert res.negative_pct > 0
    assert "Alarmist" in res.tone or "Negative" in res.tone


def test_clickbait_scoring():
    text_normal = "The Federal Reserve released its quarterly macroeconomic summary regarding interest rates."
    text_clickbait = "You WON'T BELIEVE what happened next! Doctors are STUNNED by this ONE simple trick that destroys everything!"
    
    cb_normal = compute_clickbait(text_normal)
    cb_clickbait = compute_clickbait(text_clickbait)
    
    assert cb_normal.score < cb_clickbait.score
    assert cb_clickbait.score >= 40
    assert cb_clickbait.caps_word_count >= 2
    assert cb_clickbait.exclamation_count >= 2
    assert "you won't believe" in cb_clickbait.triggers


def test_political_bias_spectrum():
    text_left = "Progressive grassroots movements advocate for wealth tax and universal healthcare to fight corporate greed."
    text_right = "Patriot citizens oppose the socialist agenda, deep state bureaucrats, and attacks on freedom of speech."
    text_neutral = "The committee reviewed the statutory guidelines during the morning session."

    b_left = compute_bias(text_left)
    b_right = compute_bias(text_right)
    b_neutral = compute_bias(text_neutral)

    assert "Left" in b_left.leaning
    assert "Right" in b_right.leaning
    assert b_neutral.leaning == "Center / Balanced"


def test_readability_flesch_index():
    easy_text = "The cat sat on the mat. The sun was hot. Dogs can run fast."
    complex_text = "The epistemological underpinnings of contemporaneous socio-political discourse necessitate multidimensional hermeneutics."

    r_easy = compute_readability(easy_text)
    r_complex = compute_readability(complex_text)

    assert r_easy.score > r_complex.score
    assert r_easy.sentence_count == 3


def test_writing_style_formality():
    informal = "Hey guys, what's up? Click here right now to see this cool thing!"
    formal = "The empirical investigation was conducted over a five-year period; 45% of respondents confirmed the hypothesis."

    s_informal = compute_writing_style(informal)
    s_formal = compute_writing_style(formal)

    assert s_formal.formality in ("Standard Editorial", "Formal / Academic")
    assert s_formal.number_count >= 1
