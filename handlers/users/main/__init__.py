# handlers/users/main/__init__.py
from .start import router as start_router

# from .callbacks import router as callbacks_router  # Hozircha commentga olib turamiz

__all__ = ["start_router"]
