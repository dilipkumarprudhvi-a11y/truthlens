import asyncio
from backend.services.analyzer import TruthLensAnalyzer
from backend.services.linguistic import analyze_linguistic_signals
from backend.services.claims import extract_claims, build_search_query
from backend.services.evidence import CompositeEvidenceAggregator
from backend.services.scoring import evaluate_claim_against_evidence, compute_aggregate_verdict

TEST_CASES = [
    # ─── REAL / TRUE CASES ───
    {
        "category": "REAL_SCIENCE",
        "expected": "REAL",
        "text": "NASA's James Webb Space Telescope has captured detailed infrared images of a distant galaxy, revealing early star formation that occurred approximately 13 billion years ago. Scientists published these findings in the Astrophysical Journal."
    },
    {
        "category": "REAL_BREAKING_GOV",
        "expected": "REAL",
        "text": "BREAKING: The Federal Reserve announced a 0.25 percentage point interest rate cut following its two-day policy meeting, according to official statements released by the central bank."
    },
    {
        "category": "REAL_MEDICAL_TRIAL",
        "expected": "REAL",
        "text": "Researchers at Oxford University published peer-reviewed clinical trial results demonstrating that a new malaria vaccine reached 77 percent efficacy in children in West Africa."
    },
    {
        "category": "REAL_NEGATIVE_DISASTER",
        "expected": "REAL",
        "text": "A magnitude 6.8 earthquake struck central Japan, causing structural damage and prompting tsunami advisories along coastal regions. Emergency response agencies are assessing casualties."
    },
    {
        "category": "REAL_ENVIRONMENT",
        "expected": "REAL",
        "text": "The World Meteorological Organization published its annual greenhouse gas bulletin confirming atmospheric carbon dioxide levels reached record concentrations across global monitoring stations."
    },

    # ─── FAKE / DECEPTION CASES ───
    {
        "category": "FAKE_MEDICAL_HOAX",
        "expected": "FAKE",
        "text": "You WON'T BELIEVE what doctors are hiding from you! This ONE simple magic secret trick destroys all diseases overnight without any medication! Miracle cure revealed before the corrupt medical establishment bans it forever!"
    },
    {
        "category": "FAKE_CONSPIRACY_THEORY",
        "expected": "FAKE",
        "text": "URGENT: The illuminati and deep state operatives are executing a secret conspiracy to install a new world order globalist plot using mind control and chemtrails. Wake up sheeple!"
    },
    {
        "category": "FAKE_DEBUNKED_HOAX",
        "expected": "FAKE",
        "text": "BREAKING: Anonymous whistleblowers leak secret documents proving the government engineered a secret miracle energy device that mainstream media is completely censoring. Buy now before this video is banned forever!"
    },
    {
        "category": "FAKE_CLICKBAIT_EXTREME",
        "expected": "FAKE",
        "text": "SHOCKING HOAX: Secret laboratory admits that climate change was fabricated to install a world government order. Mind blowing truth they don't want you to know!"
    }
]

async def run_audit():
    analyzer = TruthLensAnalyzer()
    print("=" * 80)
    print("      TRUTHLENS ACCURACY & RELIABILITY PIPELINE AUDIT")
    print("=" * 80)
    
    passed = 0
    total = len(TEST_CASES)
    
    for i, tc in enumerate(TEST_CASES, start=1):
        text = tc["text"]
        expected = tc["expected"]
        category = tc["category"]
        
        # Run end-to-end analyzer
        res = await analyzer.analyze(text=text)
        
        pred_legacy = res.legacy_classification
        pred_verdict = res.primary_verdict
        cred = res.credibility_score
        fake_prob = res.fake_probability
        conf = res.confidence
        claims_count = len(res.claims)
        ev_count = sum(len(c.evidence) for c in res.claims)
        
        is_match = (expected == "REAL" and pred_legacy == "REAL" and cred >= 55.0) or \
                   (expected == "FAKE" and pred_legacy in ("FAKE", "SUSPICIOUS") and fake_prob >= 40.0)
        
        if is_match:
            passed += 1
            status_tag = "PASS"
        else:
            status_tag = "FAIL"
            
        print(f"\n[{i}/{total}] [{status_tag}] Category: {category} (Expected: {expected})")
        print(f"  Snippet: \"{text[:75]}...\"")
        print(f"  Primary Verdict   : {pred_verdict}")
        print(f"  Legacy Class      : {pred_legacy}")
        print(f"  Credibility Score : {cred}%")
        print(f"  Fake Probability  : {fake_prob}%")
        print(f"  Evidence Confidence: {conf}%")
        print(f"  Extracted Claims  : {claims_count} | Retrieved Evidence Items: {ev_count}")
        print(f"  Triggered Signals : {res.triggered_keywords}")
        print(f"  Message           : {res.message[:100]}...")

    print("\n" + "=" * 80)
    print(f"AUDIT SUMMARY: {passed}/{total} PASSED ({(passed/total)*100:.1f}%)")
    print("=" * 80)

if __name__ == "__main__":
    asyncio.run(run_audit())
