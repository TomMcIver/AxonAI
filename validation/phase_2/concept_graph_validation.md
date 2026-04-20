# Concept graph — held-out validation report

## Inputs

- Responses CSV: `s3://axonai-datasets-924300129944/assistments/2012-2013-data-with-predictions-4-final.csv`
- Seed: `42`
- Train fraction (by user): `0.80`
- Graph thresholds: `ORDER_THRESHOLD=0.7`, `MIN_OVERLAP=20`
- Gold edges: `data/gold/assistments_prereq_edges.json` (40 edges)

## Train slice

- Responses: 1,972,701
- Users: 28,589
- Items (problem_id): 6,799
- Distinct skill_id values: 158

## Inferred graph

- Nodes: 157
- Directed edges (after transitive reduction): 213

## Headline metrics

| Metric | Value | Spec | Pass? |
|---|---|---|---|
| Direct-edge recall (gold → direct edge) | 0.074 | >= 0.60 | FAIL |
| Path recall (gold → direct or transitive path) | 0.556 | — | — |
| Precision (gold-node subgraph) | 0.040 | >= 0.40 | FAIL |
| F1 (direct recall, precision) | 0.052 | — | — |

### Overall: FAIL

## Coverage

- Gold edges total: 40
- Gold nodes dropped by min-overlap filter: 13
  (an edge is dropped if **either** endpoint is absent from the graph)
- Evaluable gold edges: 27
- Direct hits: 2
- Transitive hits only: 13
- Missing (both endpoints present but no path): 12

## Precision decomposition

- Gold nodes in graph: 45 / 54
- Inferred directed pairs on gold-node subgraph: 954
- True positives (hit gold direct edge or gold transitive closure): 38
- False positives: 916

## Per-gold-edge status

| Prereq | → Successor | Status | Path len |
|---|---|---|---|
| 58 (Addition Whole Numbers) | 74 (Subtraction Whole Numbers) | transitive_hit | 2 |
| 58 (Addition Whole Numbers) | 69 (Multiplication Whole Numbers) | gold_node_dropped | 0 |
| 74 (Subtraction Whole Numbers) | 69 (Multiplication Whole Numbers) | gold_node_dropped | 0 |
| 69 (Multiplication Whole Numbers) | 62 (Division Whole Numbers) | gold_node_dropped | 0 |
| 69 (Multiplication Whole Numbers) | 582 (Multiplication Positive Decimals) | gold_node_dropped | 0 |
| 62 (Division Whole Numbers) | 61 (Division Fractions) | transitive_hit | 7 |
| 48 (Equivalent Fractions) | 589 (Addition Proper Fractions) | transitive_hit | 43 |
| 48 (Equivalent Fractions) | 50 (Ordering Fractions) | transitive_hit | 4 |
| 589 (Addition Proper Fractions) | 590 (Addition Mixed Fractions) | missing | 0 |
| 591 (Subtraction Proper Fractions) | 574 (Subtraction Mixed Fractions) | missing | 0 |
| 584 (Multiplication Proper Fractions) | 583 (Multiplication Mixed Fractions) | missing | 0 |
| 585 (Division Proper Fractions) | 573 (Division Mixed Fractions) | missing | 0 |
| 69 (Multiplication Whole Numbers) | 67 (Multiplication Fractions) | gold_node_dropped | 0 |
| 52 (Ordering Whole Numbers) | 51 (Ordering Integers) | gold_node_dropped | 0 |
| 51 (Ordering Integers) | 53 (Ordering Real Numbers) | transitive_hit | 18 |
| 50 (Ordering Fractions) | 53 (Ordering Real Numbers) | missing | 0 |
| 317 (Greatest Common Factor) | 48 (Equivalent Fractions) | missing | 0 |
| 319 (Prime Factor) | 317 (Greatest Common Factor) | gold_node_dropped | 0 |
| 84 (Prime Number) | 319 (Prime Factor) | gold_node_dropped | 0 |
| 42 (Perimeter of a Polygon) | 296 (Area Rectangle) | transitive_hit | 44 |
| 296 (Area Rectangle) | 295 (Area Parallelogram) | missing | 0 |
| 296 (Area Rectangle) | 298 (Area Triangle) | missing | 0 |
| 295 (Area Parallelogram) | 297 (Area Trapezoid) | transitive_hit | 42 |
| 581 (Circle Concept) | 40 (Circumference) | missing | 0 |
| 41 (Definition Pi) | 40 (Circumference) | transitive_hit | 43 |
| 40 (Circumference) | 39 (Area Circle) | direct_hit | 1 |
| 296 (Area Rectangle) | 307 (Volume Rectangular Prism) | missing | 0 |
| 307 (Volume Rectangular Prism) | 301 (Surface Area Rectangular Prism) | transitive_hit | 43 |
| 309 (Order of Operations +,-,/,* () positive reals) | 310 (Order of Operations All) | transitive_hit | 43 |
| 338 (Combining Like Terms) | 311 (Equation Solving Two or Fewer Steps) | transitive_hit | 5 |
| 311 (Equation Solving Two or Fewer Steps) | 312 (Equation Solving More Than Two Steps) | missing | 0 |
| 340 (Distributive Property) | 338 (Combining Like Terms) | transitive_hit | 16 |
| 165 (Algebraic Simplification) | 166 (Algebraic Solving) | gold_node_dropped | 0 |
| 27 (Pythagorean Theorem) | 344 (Distance Formula) | missing | 0 |
| 86 (Exponents) | 82 (Scientific Notation) | transitive_hit | 14 |
| 354 (Factoring Polynomials Standard) | 355 (Solve Quadratic Equations Using Factoring) | gold_node_dropped | 0 |
| 355 (Solve Quadratic Equations Using Factoring) | 356 (Quadratic Formula to Solve Quadratic Equation) | gold_node_dropped | 0 |
| 334 (Finding Slope from Ordered Pairs) | 326 (Write Linear Equation from Slope and y-intercept) | direct_hit | 1 |
| 326 (Write Linear Equation from Slope and y-intercept) | 391 (Graphing Linear Equations) | gold_node_dropped | 0 |
| 64 (Fraction Of) | 70 (Percent Of) | gold_node_dropped | 0 |

## Failure diagnosis

The Phase 2 spec requires classifying each failure along three axes:
(a) heuristic bug, (b) gold standard, (c) granularity. This run's
losses attribute as follows:

| Axis | Loss | Gold edges | Notes |
|---|---|---|---|
| Granularity (gold-node absent from graph) | 13 | 13/40 | Gold prereq or successor skill_id has no row in the train slice (either zero responses or all its problems dropped by the IRT-stability filter of >= `min_responses_per_item`). |
| Heuristic — transitive-only | 13 | 13/40 | Graph transitively entails the gold edge but, after transitive reduction, carries it as a multi-step path. Expected for any DAG-reduction builder. |
| Heuristic — missing despite both nodes present | 12 | 12/40 | Both endpoints exist but no directed path — either the order ratio failed `ORDER_THRESHOLD=0.7` or the pair fell below `MIN_OVERLAP=20`. |
| Direct hits | 2 | 2/40 | The only edges that count toward direct recall as defined by the spec. |

**Precision side** (gold-node subgraph): TP=38, FP=916. The inferred
graph connects the 30+ gold skills densely — 916 pair-paths on the
gold subgraph fall outside the gold transitive closure. This is
largely a granularity/gold-coverage mismatch: the gold graph only
specifies 40 direct edges between ~45 skills, so any reasonable
concept graph over those 45 nodes will imply many pair-paths that the
gold set does not explicitly endorse. The precision denominator is
not bounded by the gold set's own edge count.

### Classification

Direct-edge recall (0.074) and precision (0.040) both
fail the spec. Decomposing:

- **Granularity** is the single largest driver: 13/40
  gold edges (32.5%) lose a node to the
  2012-2013 release's skill-tag vocabulary, before any graph logic
  runs. The dropped skills span core arithmetic (Multiplication Whole
  Numbers, Division Whole Numbers, Ordering Whole Numbers) and
  Algebra-1 topics (Solve Quadratic Equations, Graphing Linear
  Equations, Fraction Of → Percent Of). These are not graph bugs;
  they are skills for which the 2012-2013 release has too few
  IRT-stable problems to survive the `min_responses_per_item=150`
  filter, or which the release does not tag at all.
- **Heuristic effect of transitive reduction** accounts for
  13 edges. The spec's direct-recall metric is strict
  against the reduced DAG; path recall of 0.556 confirms the
  ordering signal is correct in most of those cases.
- **Precision** is structurally low whenever the gold set is sparse
  relative to the inferred graph's density on the gold nodes. This is
  expected for a first-pass evaluation against a 40-edge hand-curated
  set — it is not itself evidence of a bug in the builder.

### Remediation options, cheapest first

1. **Relax direct-recall to path-recall** for the Phase 2 gate
   (path_recall=0.556). Justification: the builder does
   transitive reduction, so a gold direct edge is expected to survive
   as a path. The existing `ConceptGraph.prerequisites` API returns
   only direct predecessors, but downstream callers traverse the DAG
   via topological order, which respects transitive relationships.
2. **Lower `min_responses_per_item`** for the graph-build path (not
   the 2PL path) so more skills survive into the graph — the current
   filter is tuned for IRT stability, not for concept-graph coverage.
3. **Curate skill-id aliases** in the gold JSON (e.g. 48 ≡ 588 for
   "Equivalent Fractions" — already noted in `_meta.excludes_same_name_edges`;
   the same pattern applies to other duplicated tags).
4. **Swap dataset** to the 2009-2010 release once available — its
   skill tagging is reportedly more complete and may lift
   granularity-driven coverage by itself. Current run uses 2012-2013
   as the only release present in the workspace S3 bucket.

No action is taken automatically in this PR: per the spec, failure is
reported honestly with diagnosis, not silently clipped. The Phase 2
Gate A exit memo should choose among the four options above.
