from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status

from backend.core.dependencies import get_tool_registry
from backend.schemas.tool import ToolResponse

router = APIRouter(tags=["tools"])


@router.get("/tools", response_model=list[ToolResponse])
async def list_tools(tool_registry=Depends(get_tool_registry)) -> list[ToolResponse]:
    """List available tools."""
    tools = tool_registry.list_tools()
    return [
        ToolResponse(
            slug=tool.slug,
            name=tool.name,
            description=tool.description,
            capabilities=tool.capabilities,
        )
        for tool in tools
    ]


@router.get("/tools/{slug}", response_model=ToolResponse)
async def get_tool(slug: str, tool_registry=Depends(get_tool_registry)) -> ToolResponse:
    """Get tool metadata by slug."""
    try:
        tool = tool_registry.get(slug)
    except ValueError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Tool not found: {slug}")

    return ToolResponse(
        slug=tool.slug,
        name=tool.name,
        description=tool.description,
        capabilities=tool.capabilities,
    )
