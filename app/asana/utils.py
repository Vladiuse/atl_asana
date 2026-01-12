def get_asana_profile_url_by_id(profile_id: str, workspace_id: str) -> str:
    return f"https://app.asana.com/1/{workspace_id}/profile/{profile_id}"
