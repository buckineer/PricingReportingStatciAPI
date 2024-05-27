from aiohttp import ClientSession, ClientTimeout
from config import import_class
import os
config = import_class(os.environ['APP_SETTINGS'])


async def aiohttp_session():
    session: ClientSession = ClientSession(timeout=ClientTimeout(total=config.HTTP_CLIENT_TIMEOUT_SECONDS))
    try:
        yield session
    finally:
        await session.close()


async def get(session: ClientSession, url: str, headers: dict = None) -> tuple:
    async with session.get(url, headers=headers) as response:
        return (response.status, await response.json())


async def post(session: ClientSession, url: str, json: dict = None, headers: dict = None) -> tuple:
    async with session.post(url, json=json, headers=headers) as response:
        return (response.status, await response.json())


async def put(session: ClientSession, url: str, json: dict = None, headers: dict = None) -> tuple:
    async with session.put(url, json=json, headers=headers) as response:
        return (response.status, await response.json())


async def delete(session: ClientSession, url: str, headers: dict = None) -> tuple:
    async with session.delete(url, headers=headers) as response:
        return (response.status, await response.json())
