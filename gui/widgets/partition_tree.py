from __future__ import annotations

from PySide6.QtWidgets import QTreeWidget, QTreeWidgetItem


class EditablePartitionTree(QTreeWidget):
    def __init__(self) -> None:
        super().__init__()
        self.setHeaderLabels(("Cấu trúc ROM (Editable)",))
        self.setMinimumHeight(360)
        for partition in ("odm_a", "product_a", "system_a", "system_ext_a", "vendor_a"):
            parent = QTreeWidgetItem([f"📁 {partition}"])
            self.addTopLevelItem(parent)
            if partition == "system_a":
                parent.setExpanded(True)
                for child in ("product", "system", "vendor", "odm", "etc", "bin", "sbin", "xbin", "lib", "lib64"):
                    parent.addChild(QTreeWidgetItem([f"📁 {child}"]))


class OutputEditableTree(QTreeWidget):
    def __init__(self) -> None:
        super().__init__()
        self.setHeaderLabels(("Cây thư mục editable sẽ tạo ra",))
        self.setMinimumHeight(280)
        root = QTreeWidgetItem(["📁 workspace/projects/rk3318_android11/editable/"])
        self.addTopLevelItem(root)
        root.setExpanded(True)
        for partition in ("odm_a", "product_a", "system_a", "system_ext_a", "vendor_a"):
            root.addChild(QTreeWidgetItem([f"📁 {partition}"]))
