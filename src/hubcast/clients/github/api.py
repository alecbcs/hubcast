from collections.abc import Mapping
from functools import partial

from gidgethub import aiohttp as gh_aiohttp

from hubcast.clients.utils import Response, with_retries


class GitHubAPI(gh_aiohttp.GitHubAPI):
    """gidgethub's GitHubAPI with retried requests."""

    async def _request(
        self, method: str, url: str, headers: Mapping[str, str], body: bytes = b""
    ) -> Response:
        send = partial(super()._request, method, url, headers, body)
        return await with_retries(send, method, url)
