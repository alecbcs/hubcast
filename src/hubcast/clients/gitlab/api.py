from collections.abc import Mapping
from functools import partial

from gidgetlab import aiohttp as gl_aiohttp

from hubcast.clients.utils import Response, with_retries


class GitLabAPI(gl_aiohttp.GitLabAPI):
    """gidgetlab's GitLabAPI with retried requests."""

    async def _request(
        self, method: str, url: str, headers: Mapping[str, str], body: bytes = b""
    ) -> Response:
        send = partial(super()._request, method, url, headers, body)
        return await with_retries(send, method, url)
