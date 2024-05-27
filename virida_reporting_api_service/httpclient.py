from aiohttp import ClientSession
from fastapi import status

async def get(session: ClientSession, url: str, headers: dict=None) -> tuple:
    async with session.get(url, headers=headers) as response:
        if response.status == status.HTTP_500_INTERNAL_SERVER_ERROR:
            return (response.status, None)
        return (response.status, await response.json())

async def post(session: ClientSession, url: str, json: dict=None, headers: dict=None) -> tuple:
    async with session.post(url, json=json, headers=headers) as response:
        if response.status == status.HTTP_500_INTERNAL_SERVER_ERROR:
            return (response.status, None)
        return (response.status, await response.json())

async def put(session: ClientSession, url: str, json: dict=None, headers: dict=None) -> tuple:
    async with session.put(url, json=json, headers=headers) as response:
        if response.status == status.HTTP_500_INTERNAL_SERVER_ERROR:
            return (response.status, None)
        return (response.status, await response.json())

async def delete(session: ClientSession, url: str, headers: dict=None) -> tuple:
    async with session.delete(url, headers=headers) as response:
        if response.status == status.HTTP_500_INTERNAL_SERVER_ERROR:
            return (response.status, None)
        return (response.status, await response.json())