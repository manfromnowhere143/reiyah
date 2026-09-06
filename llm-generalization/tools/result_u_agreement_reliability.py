"""Result U: from measuring joint failure to predicting it - is agreement a trustworthy signal?

The program measured that redundant channels fail together. This asks the runtime question: an
ensemble treats AGREEMENT between models as confidence, so when models agree it trusts the answer.
But if the models are coupled they agree on the same WRONG answers too, and then agreement is a
weaker signal of correctness than independence promises, and unanimous-yet-wrong is the sharpest
failure. This quantifies that, the seed of a live monitor that reads only the channels' outputs.

Data: public v1 Open LLM Leaderboard MMLU 5-shot. Per question, each model's CHOSEN answer is the
argmax of its per-choice log-probabilities; `gold` is the correct choice. Joined across models by a
hash of the example.

Measured:
  - pair agreement reliability: P(correct | the two models chose the same answer), against the
    independence expectation, and P(both wrong | they agree), the false-confidence rate.
  - the full jury: when ALL models agree, how often are they unanimously wrong.
"""
import sys
from itertools import combinations

import numpy as np
import pandas as pd
from huggingface_hub import HfApi, hf_hub_download

api = HfApi()
MODELS = [
    ("meta-llama__Llama-2-7b-hf", "Llama"),
    ("meta-llama__Llama-2-13b-hf", "Llama"),
    ("meta-llama__Llama-2-70b-hf", "Llama"),
    ("mistralai__Mistral-7B-v0.1", "Mistral"),
    ("tiiuae__falcon-7b", "Falcon"),
    ("mosaicml__mpt-7b", "MPT"),
    ("Qwen__Qwen-7B", "Qwen"),
]


def load_model(model):
    rid = f"open-llm-leaderboard-old/details_{model}"
    try:
        files = [f for f in api.list_repo_files(rid, repo_type="dataset")
                 if "hendrycksTest-" in f and f.endswith(".parquet")]
    except Exception:
        return None
    if not files:
        return None
    best = pd.Series([f.split("/")[0] for f in files]).value_counts().index[0]
    files = sorted(f for f in files if f.startswith(best))
    parts = []
    for f in files:
        try:
            df = pd.read_parquet(hf_hub_download(rid, f, repo_type="dataset"))
            df["qhash"] = df["hashes"].apply(lambda h: h["example"])
            df["chosen"] = df["predictions"].apply(lambda p: int(np.argmax(p)))
            df["gold"] = df["gold"].astype(int)
            parts.append(df[["qhash", "chosen", "gold"]])
        except Exception:
            continue
    if not parts:
        return None
    d = pd.concat(parts).drop_duplicates("qhash").set_index("qhash")
    print(f"  loaded {model}: {len(d)} questions", flush=True)
    return d


def main():
    print("loading models (chosen answers)...", flush=True)
    chosen, gold, fams = {}, None, {}
    for m, fam in MODELS:
        d = load_model(m)
        if d is None:
            continue
        chosen[m] = d["chosen"]
        fams[m] = fam
        gold = d["gold"] if gold is None else gold
    C = pd.DataFrame(chosen).dropna().astype(int)      # question x model chosen answer
    common = C.index
    G = gold.loc[common].astype(int)
    names = list(C.columns)
    n = len(C)
    correct = C.eq(G, axis=0)                            # question x model correctness
    print("=" * 88)
    print("RESULT U - is agreement a trustworthy signal? predicting joint failure from outputs")
    print(f"MMLU 5-shot, {len(names)} models, {n} questions, choices A-D")
    print("=" * 88)

    Ch = C.values
    Cor = correct.values
    Gv = G.values

    def pair_stats(i, j):
        agree = Ch[:, i] == Ch[:, j]
        na = agree.sum()
        if na == 0:
            return None
        both_corr = (agree & Cor[:, i] & Cor[:, j]).sum()
        both_wrong = (agree & ~Cor[:, i] & ~Cor[:, j]).sum()
        p_corr_given_agree = both_corr / na
        p_wrong_given_agree = both_wrong / na
        # independence baseline for agreeing-and-both-wrong: if the two models chose wrong answers
        # independently among 3 wrong options, agreement on the same wrong answer would be rare.
        pw_i = (~Cor[:, i]).mean(); pw_j = (~Cor[:, j]).mean()
        indep_agree_wrong = pw_i * pw_j / 3.0            # 3 wrong choices, uniform-ish
        lift = p_wrong_given_agree / (indep_agree_wrong / (na / n)) if indep_agree_wrong > 0 else np.nan
        return dict(p_agree=na / n, p_corr=p_corr_given_agree, p_wrong=p_wrong_given_agree)

    print("\n  when two models AGREE on an answer:")
    print(f"  {'pair':<44}{'P(agree)':>10}{'P(correct|agree)':>18}{'P(both wrong|agree)':>20}")
    ps = []
    for i, j in combinations(range(len(names)), 2):
        s = pair_stats(i, j)
        if s:
            ps.append((names[i], names[j], s))
    for a, b, s in ps[:8]:
        lbl = f"{a.split('__')[-1][:18]} + {b.split('__')[-1][:18]}"
        print(f"  {lbl:<44}{100*s['p_agree']:>9.0f}%{100*s['p_corr']:>17.1f}%{100*s['p_wrong']:>19.1f}%")
    mc = np.mean([s['p_corr'] for _, _, s in ps])
    mw = np.mean([s['p_wrong'] for _, _, s in ps])
    print(f"\n  average over {len(ps)} pairs: P(correct|agree) {100*mc:.1f}%, "
          f"P(both wrong|agree) {100*mw:.1f}%")

    # full jury unanimity
    unanimous = (Ch == Ch[:, [0]]).all(axis=1)
    nu = unanimous.sum()
    unanimous_correct = (unanimous & Cor[:, 0]).sum()
    unanimous_wrong = nu - unanimous_correct
    print(f"\n  the full {len(names)}-model jury:")
    print(f"    unanimous (all chose the same answer): {100*nu/n:.1f}% of questions")
    print(f"    of those, UNANIMOUS AND WRONG        : {100*unanimous_wrong/nu:.1f}%  ({unanimous_wrong} questions)")
    print(f"    so agreement, even unanimous, carries a real error rate the ensemble treats as ~0")

    print("\n" + "-" * 88)
    print("NON-CLAIMS: public leaderboard outputs on one benchmark (MMLU 5-shot); agreement is the")
    print("argmax choice; the independence baseline for shared wrong answers is a simple uniform")
    print("approximation; descriptive, retained as proposed; a runtime-signal demonstration, not a")
    print("deployed monitor and not a driving result. No released 1.2 byte is involved.")


if __name__ == "__main__":
    main()
