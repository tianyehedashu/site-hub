"""Google Flow (labs.google) / Imagen / Nano Banana site plugin.

All JSON presets under this directory share the ``images[]`` media contract:

.. code-block:: jsonc

   {
     "images": [
       { "encodedImage": "<base64>", "seed": 1 },
       { "fifeUrl":      "https://...", "seed": 2 }
     ]
   }

This contract is declared **inside each preset JSON** (top-level
``media_contract`` key), so ``--save-images`` works through the default
:meth:`SitePlugin.media_contract` implementation without a Python override
— the JSON declaration is the single source of truth.

The plugin below exists for **future** Python-only needs (injecting
dynamic session tokens, response post-processing, conditional contract
synthesis, …).  Today it only sets :attr:`site_id` so ``ziniao site show``
can report a stable identifier; ``media_contract`` falls through to the
base implementation, which compiles the preset's JSON rules.
"""

from __future__ import annotations

from ziniao_mcp.sites import SitePlugin


class GoogleFlowPlugin(SitePlugin):
    """Plugin for labs.google / aisandbox media generation endpoints."""

    site_id = "google-flow"


SITE_PLUGIN = GoogleFlowPlugin
