from typing import Final, cast

import yaml
from cachetools import TTLCache

from hubcast.clients.github import GitHubClient
from hubcast.exceptions import HubcastError
from hubcast.repos.config import RepoConfig

# sentinel to distinguish "config not found" from cache miss
_CONFIG_NOT_FOUND: Final = object()

# cache stores RepoConfig on success, _CONFIG_NOT_FOUND when file doesn't exist
config_cache: TTLCache[str, RepoConfig | object] = TTLCache(maxsize=1000, ttl=1800)

_CONFIG_NOT_FOUND_MSG = "Repo config file not found at .github/hubcast.yml"


async def get_repo_config(
    gh: GitHubClient, fullname: str, refresh: bool = False
) -> tuple[RepoConfig, bool]:
    """Get repository configuration from cache or fetch from GitHub.

    Args:
        gh: GitHub client instance
        fullname: Full repository name (e.g., "owner/repo")
        refresh: Whether to force refresh from GitHub

    Returns:
        Tuple of (RepoConfig instance, whether it was freshly fetched)

    Raises:
        HubcastError: If config file contains invalid YAML, is missing required keys,
            or has validation errors
    """
    if not refresh and (cached_value := config_cache.get(fullname)) is not None:
        if cached_value is _CONFIG_NOT_FOUND:
            raise HubcastError(
                _CONFIG_NOT_FOUND_MSG,
                log_level="INFO",
                repo=fullname,
            )
        # cached_value must be RepoConfig (only other option was sentinel, now ruled out)
        return cast(RepoConfig, cached_value), False

    try:
        config_str = await gh.get_repo_config()
    except HubcastError as e:
        # cache 404 errors to avoid repeated API calls
        if _CONFIG_NOT_FOUND_MSG in str(e):
            config_cache[fullname] = _CONFIG_NOT_FOUND
        raise

    try:
        config_yaml = yaml.safe_load(config_str)
    except yaml.YAMLError as e:
        raise HubcastError(
            f"Invalid YAML in repo config for {fullname}: {e}",
            log_level="INFO",
            repo=fullname,
        ) from None

    if config_yaml is None:
        raise HubcastError(
            f"Empty config file for {fullname}",
            log_level="INFO",
            repo=fullname,
        )

    try:
        config = RepoConfig.model_validate(config_yaml)
    except ValueError as e:
        raise HubcastError(
            f"Invalid repo config for {fullname}: {e}",
            log_level="INFO",
            repo=fullname,
        ) from None

    config_cache[fullname] = config
    return config, True
