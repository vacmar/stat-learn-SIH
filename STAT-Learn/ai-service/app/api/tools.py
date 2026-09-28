from typing import Any

from fastapi import APIRouter

from app.tools.registry import ALL_TOOLS

router = APIRouter(prefix="/tools", tags=["Tools"])


@router.get("", response_model=list[dict[str, Any]])
def list_tools() -> list[dict[str, Any]]:
    """List all registered agent tools, their schemas, and descriptions."""
    manifest = []
    for tool_inst in ALL_TOOLS:
        args_schema: dict[str, Any] = {}
        if tool_inst.args_schema:
            try:
                args_schema = tool_inst.args_schema.model_json_schema()  # type: ignore
            except (AttributeError, ValueError):
                args_schema = getattr(tool_inst, "args", {})

        manifest.append(
            {
                "name": tool_inst.name,
                "description": tool_inst.description,
                "parameters": args_schema,
            }
        )
    return manifest
