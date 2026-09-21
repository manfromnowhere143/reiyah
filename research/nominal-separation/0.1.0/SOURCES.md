# Sources and limits

Document: reiyah.nominal-separation.sources, version 0.1.0.
Research cutoff: 21 September 2026. Exact bytes and capture times are in sources.json.

The numeric source is Haas, Solmaz, Reckenzaun and Genser, Virtual Vehicle
Research, [ViF-GTAD v2](https://doi.org/10.5281/zenodo.7808255), record 7808255,
published 7 April 2023, CC BY 4.0. The retained member identities and original
range receipts are in the [compact-motion packet](../../compact-motion/0.1.1/SOURCES.md).
The whole multi-gigabyte archive was not fetched or publisher-MD5 verified.
We reuse immutable numeric and documentation bytes; no sensor media is accessed.
Changes here consist of nominal mathematical reconstruction and derived summaries.

The [dataset paper](https://architect-eca2030.eu/images/pdfs/Online_Publishable_Version.pdf),
DOI 10.1177/02783649231188146, first online 11 July 2023, describes navigation
references and calibration. Its scenario summary and the retained scenario-3 PDF
differ in how they describe ego motion. Both are preserved. The scenario PDF
motivates increasing separation; neither source defines our exact Euclidean
reference-point monotonicity premise or supplies applicable residual uncertainty.
See the retained [clock source review](../../clock-alignment/0.1.1/SOURCES.md).

[Shewchuk's primary research page](https://www.cs.cmu.edu/~quake/robust.html)
explains how floating-point sign errors can undermine geometric predicates and
describes adaptive exact methods. It identifies the 1997 journal paper and
May 1996 technical report. This supports numerical discipline, not novelty or
an assertion that Reiyah implements those algorithms. Only the small HTML page
was newly captured; no third-party code is imported. Its code's public-domain
notice is not treated as a blanket license for the page or papers.

[Stout, arXiv:1507.02226v2](https://arxiv.org/abs/1507.02226v2), dated
22 June 2017, studies weighted L-infinity isotonic regression and pairwise/error
envelope feasibility, including linear-time results for linear orders. The
retained PDF's introduction and preliminaries make clear that monotone fitting
and error-bound constructions are established. We derive the simple unweighted
continuous scalar formula explicitly in METHOD.md; do not copy the extracted
PDF's displayed formulas or claim its full algorithms were reproduced here.
The university-host capture failed certificate verification. That zero-byte
failure is retained; the supported arXiv v2 route succeeded with TLS verification.

These two focused primary sources supplement the existing
[frontier review](../../frontier-expansion/0.1.0/SOURCES.md) and
[uncertainty review](../../continuous-envelope/0.1.0/SOURCES.md).
They do not establish superiority over NVIDIA, Mobileye, Tesla, SpaceX or any
competent research group, and reveal no company's private engineering process.
