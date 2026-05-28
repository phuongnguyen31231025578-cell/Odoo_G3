from . import models
from . import hooks

# Expose hooks at module level for Odoo
from .hooks import post_init_hook  # noqa: F401
