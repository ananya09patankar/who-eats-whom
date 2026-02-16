def refine_observations(raw_obs: list[dict]) -> list[dict]:
    """Placeholder refinement hook. Replace with the team's filtering later."""
    return [o for o in raw_obs if o.get("id") is not None]
