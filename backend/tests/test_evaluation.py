"""
Labeled Evaluation Benchmark Test Suite
Measures and reports scientific evaluation metrics:
Precision, Recall, F1 Score, and Confusion Matrix across a labeled test dataset.
"""

import pytest
from backend.services.linguistic import analyze_linguistic_signals
from backend.services.claims import extract_claims
from backend.services.scoring import compute_aggregate_verdict

# Evaluated Labeled Dataset
EVALUATION_DATASET = [
    # REAL SAMPLES
    {
        "text": "The European Space Agency launched the Euclid space telescope to map the geometry of the dark universe over a six-year mission. The telescope will observe billions of galaxies out to 10 billion light-years.",
        "label": "REAL"
    },
    {
        "text": "Researchers at Oxford University published peer-reviewed trial results demonstrating that a new malaria vaccine reached 77 percent efficacy in clinical trials with children in West Africa.",
        "label": "REAL"
    },
    {
        "text": "The Department of Energy announced 45 million dollars in funding for solar and battery integration projects to support the national electrical grid infrastructure.",
        "label": "REAL"
    },
    {
        "text": "Astronomers using the James Webb Space Telescope identified water vapor in the inner disk of a young planetary system where rocky planets are forming.",
        "label": "REAL"
    },
    {
        "text": "The World Meteorological Organization published its annual greenhouse gas bulletin confirming atmospheric carbon dioxide levels reached record concentrations.",
        "label": "REAL"
    },

    # FAKE / DECEPTION SAMPLES
    {
        "text": "BREAKING: Anonymous whistleblowers leak secret documents proving the government engineered a miracle energy cure that mainstream media is completely censoring! Click here before this video is banned forever by the deep state cabal!",
        "label": "FAKE"
    },
    {
        "text": "You WON'T BELIEVE what doctors are hiding from you! This ONE simple magic secret trick destroys all diseases overnight without any medication! The shocking truth exposed!",
        "label": "FAKE"
    },
    {
        "text": "URGENT WARNING: Globalist tyrants and deep state operatives are executing a treasonous secret conspiracy to destroy the constitutional fabric of the country. Traitors unmasked!",
        "label": "FAKE"
    },
    {
        "text": "SHOCKING HOAX: Secret laboratory admits that climate change was fabricated to install a world government order. Mind blowing truth they don't want you to know!",
        "label": "FAKE"
    },
    {
        "text": "Miracle cure revealed! Buy now before the corrupt medical establishment bans this secret natural remedy forever. 100 percent proven by anonymous experts!",
        "label": "FAKE"
    }
]


def test_labeled_dataset_benchmark():
    tp = 0  # True Positive (Actual FAKE, Predicted FAKE/SUSPICIOUS)
    fp = 0  # False Positive (Actual REAL, Predicted FAKE/SUSPICIOUS)
    tn = 0  # True Negative (Actual REAL, Predicted REAL)
    fn = 0  # False Negative (Actual FAKE, Predicted REAL)

    print("\n=======================================================")
    print("      TRUTHLENS LABELED BENCHMARK EVALUATION           ")
    print("=======================================================")

    for item in EVALUATION_DATASET:
        text = item["text"]
        ground_truth = item["label"]

        linguistic, entities, doc = analyze_linguistic_signals(text)
        claims = extract_claims(text)
        primary_verdict, legacy_class, cred, fake_prob, conf, msg = compute_aggregate_verdict(claims, linguistic)

        predicted_fake = legacy_class in ("FAKE", "SUSPICIOUS") or fake_prob >= 50.0

        if ground_truth == "FAKE":
            if predicted_fake:
                tp += 1
            else:
                fn += 1
        elif ground_truth == "REAL":
            if predicted_fake:
                fp += 1
            else:
                tn += 1

    total_samples = len(EVALUATION_DATASET)
    accuracy = (tp + tn) / total_samples
    precision = tp / max(1, (tp + fp))
    recall = tp / max(1, (tp + fn))
    f1 = (2 * precision * recall) / max(1e-6, (precision + recall))

    print(f"Total Benchmark Samples: {total_samples}")
    print(f"Accuracy:                {accuracy:.2%}")
    print(f"Precision (Deception):   {precision:.2%}")
    print(f"Recall (Deception):      {recall:.2%}")
    print(f"F1 Score:                {f1:.3f}")
    print("-------------------------------------------------------")
    print(f"Confusion Matrix:")
    print(f"  [ True FAKE (TP): {tp} ]  [ False FAKE (FP): {fp} ]")
    print(f"  [ False REAL (FN): {fn} ] [ True REAL (TN):  {tn} ]")
    print("=======================================================\n")

    assert accuracy >= 0.80, f"Accuracy {accuracy} below minimum benchmark threshold"
    assert f1 >= 0.80, f"F1 Score {f1} below minimum benchmark threshold"
