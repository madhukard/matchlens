"""Operator-only live synthetic publisher; no HTTP endpoint or automatic schedule."""

import argparse
import asyncio
import os
from contextlib import asynccontextmanager
from datetime import UTC, datetime
from time import perf_counter
from uuid import uuid4

from agents import OpenAIResponsesModel
from azure.identity import DefaultAzureCredential, ManagedIdentityCredential
from openai import AsyncOpenAI

from matchlens.live_agents import Budget, Workflow
from matchlens.live_domain import MatchState, scenario
from matchlens.live_store import acquire_worker_lease, publish


def timestamp():
    return datetime.now(UTC).isoformat()


@asynccontextmanager
async def model_client():
    credential = None
    endpoint = os.environ["AZURE_OPENAI_ENDPOINT"].rstrip("/")
    key = os.getenv("AZURE_OPENAI_API_KEY")
    if not key:
        credential = (
            ManagedIdentityCredential(client_id=os.environ["AZURE_CLIENT_ID"])
            if os.getenv("AZURE_CLIENT_ID")
            else DefaultAzureCredential()
        )
        key = (await asyncio.to_thread(credential.get_token, "https://ai.azure.com/.default")).token
    client = AsyncOpenAI(base_url=endpoint + "/openai/v1/", api_key=key, max_retries=0, timeout=45)
    try:
        yield OpenAIResponsesModel(
            model=os.getenv("MATCHLENS_MODEL", "gpt-6-sol"), openai_client=client
        )
    finally:
        await client.close()
        if credential:
            credential.close()


async def run_stream(model, seed: int = 7, interval: float = 2, publish_fn=publish):
    budget = Budget()
    state = MatchState()
    run = {
        "run_id": str(uuid4()),
        "status": "running",
        "started_at": timestamp(),
        "model": os.getenv("MATCHLENS_MODEL", "gpt-6-sol"),
        "frames": [],
        "budget": {
            "reserved_token_limit": 600_000,
            "model_call_limit": 48,
            "automatic_api_retries": 0,
            "rate_limit_retries_per_call": 1,
            "schedule": "manual_only",
        },
    }
    for clock, events in scenario(seed):
        for event in events:
            state.ingest(event)
        frame = {"snapshot": state.snapshot(clock), "status": "reviewing", "trace": []}
        run["frames"].append(frame)
        run["updated_at"] = timestamp()
        publish_fn(run)
        def progress(trace):
            frame["trace"] = trace
            run["updated_at"] = timestamp()
            publish_fn(run)

        workflow = Workflow(model, budget, on_progress=progress)
        start = perf_counter()
        try:
            package = await workflow.produce(frame["snapshot"])
            frame.update(package=package.model_dump(), status="approved")
        except Exception as error:
            frame.update(status="statistics_only", error_type=type(error).__name__)
        frame["trace"] = workflow.trace
        frame["latency_seconds"] = round(perf_counter() - start, 3)
        run["updated_at"] = timestamp()
        run["budget"]["reserved_tokens_used"] = budget.reserved
        publish_fn(run)
        print(
            f"frame={len(run['frames'])} revision={frame['snapshot']['revision']} "
            f"status={frame['status']} seconds={frame['latency_seconds']}",
            flush=True,
        )
        await asyncio.sleep(interval)
    run["status"] = "completed"
    run["updated_at"] = timestamp()
    publish_fn(run)
    publish_fn(run, archive=True)
    return run


async def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--seed", type=int, default=7)
    parser.add_argument("--interval", type=float, default=2)
    args = parser.parse_args()
    if not 0 <= args.interval <= 30:
        parser.error("interval must be 0–30 seconds")
    lease = None
    done = asyncio.Event()

    async def renew():
        while not done.is_set():
            try:
                await asyncio.wait_for(done.wait(), timeout=20)
            except TimeoutError:
                await asyncio.to_thread(lease.renew)

    async def stream():
        try:
            async with model_client() as model:
                await run_stream(model, args.seed, args.interval)
        finally:
            done.set()

    try:
        if os.getenv("MATCHLENS_STORAGE_URL"):
            lease = await asyncio.to_thread(acquire_worker_lease)
        async with asyncio.TaskGroup() as tasks:
            tasks.create_task(stream())
            if lease:
                tasks.create_task(renew())
    finally:
        if lease:
            await asyncio.to_thread(lease.release)


if __name__ == "__main__":
    asyncio.run(main())
