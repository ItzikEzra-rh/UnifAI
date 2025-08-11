"""
IEM Messenger Factory

Factory functions for creating InterMessenger instances with dependency injection.
"""

from typing import Optional, Callable
from graph.step_context import StepContext
from graph.state.state_view import StateView
from .models import ElementAddress
from .messenger import DefaultInterMessenger
from .interfaces import MessengerMiddleware


def create_messenger(
        state: StateView,
        identity: ElementAddress,
        *,
        enforce_adjacency: bool = True,
        adjacent_check: Optional[Callable[[str], bool]] = None,
        middleware: list[MessengerMiddleware] = None
) -> DefaultInterMessenger:
    """
    Create a messenger with explicit configuration.
    
    Args:
        state: StateView for channel access
        identity: Element address/identity
        enforce_adjacency: Whether to enforce adjacency checks
        adjacent_check: Custom adjacency check function
        middleware: List of middleware to apply
        
    Returns:
        Configured DefaultInterMessenger
    """
    return DefaultInterMessenger(
        state=state,
        identity=identity,
        is_adjacent=adjacent_check if enforce_adjacency else None,
        middleware=middleware or []
    )


def messenger_from_ctx(
        state: StateView,
        ctx: StepContext,
        *,
        middleware: list[MessengerMiddleware] = None,
        enforce_adjacency: bool = True
) -> DefaultInterMessenger:
    """
    Create a messenger from StepContext (convenience for nodes).
    
    Args:
        state: StateView for channel access
        ctx: StepContext containing element identity and adjacency info
        middleware: List of middleware to apply
        enforce_adjacency: Whether to enforce adjacency checks
        
    Returns:
        Configured DefaultInterMessenger with adjacency checks based on ctx
    """
    identity = ElementAddress(
        uid=ctx.uid,
        name=getattr(ctx.metadata, 'display_name', None),
        type_key=getattr(ctx.metadata, 'type_key', None)
    )

    # Create adjacency check function from context
    adjacent_check = None
    if enforce_adjacency:
        adjacent_check = lambda uid: uid in ctx.adjacent_nodes

    return DefaultInterMessenger(
        state=state,
        identity=identity,
        is_adjacent=adjacent_check,
        middleware=middleware or [],
        context=ctx
    )


def messenger_for_testing(
        state: StateView,
        uid: str,
        *,
        name: str = None,
        middleware: list[MessengerMiddleware] = None
) -> DefaultInterMessenger:
    """
    Create a messenger for testing (no adjacency enforcement).
    
    Args:
        state: StateView for channel access
        uid: Element UID
        name: Optional element name
        middleware: List of middleware to apply
        
    Returns:
        Configured DefaultInterMessenger with no adjacency checks
    """
    identity = ElementAddress(uid=uid, name=name)

    return create_messenger(
        state=state,
        identity=identity,
        enforce_adjacency=False,
        middleware=middleware
    )
