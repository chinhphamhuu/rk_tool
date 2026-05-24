from __future__ import annotations

import argparse
import sys

try:
    from PySide6.QtWidgets import QApplication
except Exception:  # pragma: no cover
    QApplication = None

from core.app_paths import AppPaths


def main() -> int:
    parser = argparse.ArgumentParser(description="Rockchip Android ROM Repack GUI")
    parser.add_argument("--smoke-test", action="store_true")
    args = parser.parse_args()

    paths = AppPaths.detect()
    paths.ensure_workspace()

    if args.smoke_test:
        print("Smoke test OK")
        print(f"APP_ROOT={paths.app_root}")
        print(f"WORKSPACE={paths.workspace_dir}")
        return 0

    if QApplication is None:
        print("PySide6 chưa được cài. Hãy chạy: pip install -r requirements.txt", file=sys.stderr)
        return 1

    from gui.main_window import MainWindow
    from gui.theme import apply_theme

    app = QApplication(sys.argv)
    apply_theme(app)
    win = MainWindow(paths)
    win.show()
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
