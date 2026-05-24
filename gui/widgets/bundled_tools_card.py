from __future__ import annotations

from core.tool_config import BundledToolConfig
from gui.widgets.info_card import Card, muted_label
from gui.widgets.status_badge import StatusBadge


class BundledToolsCard(Card):
    def __init__(self, tool_config: BundledToolConfig | None = None) -> None:
        super().__init__("🛠  Bundled tools")

        if tool_config is None:
            self.layout.addWidget(muted_label("Tool paths are read-only and resolved from APP_ROOT/tools/."))
            self.layout.addWidget(StatusBadge("READ ONLY", "info"))
            return

        for tool in tool_config.tools:
            variant = "ok" if tool.is_ok else "error"
            self.layout.addWidget(
                muted_label(f"{tool.name}: {tool.path} [{tool.status}]", small=True)
            )
            self.layout.addWidget(StatusBadge(tool.status, variant))

        summary = "All bundled tools OK" if tool_config.all_ok else "Some bundled tools are missing"
        self.layout.addWidget(muted_label(summary, small=True))
