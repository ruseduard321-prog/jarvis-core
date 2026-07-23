from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status

from backend.core.dependencies import get_prompt_library_service
from backend.core.prompt_models import PromptCategory
from backend.schemas.prompt import (
    PromptCreateRequest,
    PromptUpdateRequest,
    PromptResponse,
)

router = APIRouter(prefix="/prompts", tags=["prompts"])


# ============================================================
# PROMPT ENDPOINTS
# ============================================================

@router.get("", response_model=list[PromptResponse])
async def list_prompts(
    service=Depends(get_prompt_library_service),
) -> list[PromptResponse]:
    """List all prompts."""
    try:
        prompts = await service.list_prompts()
        return [
            PromptResponse(
                id=prompt.id,
                name=prompt.name,
                content=prompt.content,
                category=prompt.category.value,
                favorite=prompt.favorite,
                created_at=prompt.created_at,
                updated_at=prompt.updated_at,
            )
            for prompt in prompts
        ]
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e),
        )


@router.post("", response_model=PromptResponse, status_code=status.HTTP_201_CREATED)
async def create_prompt(
    request: PromptCreateRequest,
    service=Depends(get_prompt_library_service),
) -> PromptResponse:
    """Create a new prompt."""
    try:
        category = PromptCategory(request.category)
        prompt = await service.create_prompt(
            name=request.name,
            content=request.content,
            category=category,
        )
        return PromptResponse(
            id=prompt.id,
            name=prompt.name,
            content=prompt.content,
            category=prompt.category.value,
            favorite=prompt.favorite,
            created_at=prompt.created_at,
            updated_at=prompt.updated_at,
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid category: {request.category}",
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e),
        )


@router.get("/{prompt_id}", response_model=PromptResponse)
async def get_prompt(
    prompt_id: str,
    service=Depends(get_prompt_library_service),
) -> PromptResponse:
    """Get a prompt by ID."""
    try:
        prompt = await service.read_prompt(prompt_id)
        return PromptResponse(
            id=prompt.id,
            name=prompt.name,
            content=prompt.content,
            category=prompt.category.value,
            favorite=prompt.favorite,
            created_at=prompt.created_at,
            updated_at=prompt.updated_at,
        )
    except KeyError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Prompt not found: {prompt_id}",
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e),
        )


@router.patch("/{prompt_id}", response_model=PromptResponse)
async def update_prompt(
    prompt_id: str,
    request: PromptUpdateRequest,
    service=Depends(get_prompt_library_service),
) -> PromptResponse:
    """Update a prompt."""
    try:
        category = None
        if request.category:
            category = PromptCategory(request.category)
        
        prompt = await service.update_prompt(
            prompt_id=prompt_id,
            name=request.name,
            content=request.content,
            category=category,
            favorite=request.favorite,
        )
        return PromptResponse(
            id=prompt.id,
            name=prompt.name,
            content=prompt.content,
            category=prompt.category.value,
            favorite=prompt.favorite,
            created_at=prompt.created_at,
            updated_at=prompt.updated_at,
        )
    except KeyError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Prompt not found: {prompt_id}",
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid category: {request.category}",
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e),
        )


@router.delete("/{prompt_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_prompt(
    prompt_id: str,
    service=Depends(get_prompt_library_service),
) -> None:
    """Delete a prompt."""
    try:
        await service.delete_prompt(prompt_id)
    except KeyError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Prompt not found: {prompt_id}",
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e),
        )
