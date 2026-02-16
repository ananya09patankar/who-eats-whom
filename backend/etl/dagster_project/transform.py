from dataclasses import dataclass

@dataclass(frozen=True)
class Interaction:
    predator_taxon_id: int
    prey_taxon_id: int
    evidence_obs_id: int

def to_interactions(refined_obs: list[dict]) -> list[Interaction]:
    """TODO: implement once you confirm how predator/prey is encoded in iNat raw."""
    return []
