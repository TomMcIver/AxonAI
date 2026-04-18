"""ConceptGraph built from the ASSISTments skill hierarchy.

Implemented in PR 6. Backed by networkx.

Planned API:
    class ConceptGraph:
        prerequisites(concept_id)       -> list[concept_id]
        successors(concept_id)          -> list[concept_id]
        topological_next(mastered_set)  -> concept_id | None

Serialisation: pickled under data/processed/concept_graph.pkl.
"""
