"""打包脚本 - 一键生成 Windows 可执行文件

用法：
    python build.py            # 默认 release 模式
    python build.py --debug    # debug 模式（含控制台 + 调试信息）
    python build.py --no-clean # 不清理旧的 build/dist

执行前请确保已安装依赖：
    pip install -r requirements.txt
"""
import argparse
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).parent
SPEC = ROOT / "novel_reader.spec"
BUILD_DIR = ROOT / "build"
DIST_DIR = ROOT / "dist"


def clean():
    """清理旧的构建产物"""
    for d in (BUILD_DIR, DIST_DIR):
        if d.exists():
            print(f"[clean] removing {d}")
            shutil.rmtree(d, ignore_errors=True)
    # 删除 PyInstaller 生成的 spec 同名 .pyz 等
    for f in ROOT.glob("*.pyz"):
        f.unlink()


def run_pyinstaller(debug: bool = False):
    """调用 PyInstaller（基于 spec 文件）

    注意：spec 文件中已固定打包模式（onefile），PyInstaller 不允许在命令行
    再传入 --onefile/--onedir 覆盖；如需切换，请修改 spec 文件。
    """
    if not SPEC.exists():
        print(f"[error] spec not found: {SPEC}", file=sys.stderr)
        sys.exit(1)

    cmd = [
        sys.executable, "-m", "PyInstaller",
        str(SPEC),
        "--clean",
        "--noconfirm",
    ]
    if debug:
        cmd.extend(["--console", "--log-level=DEBUG"])

    print(f"[build] running: {' '.join(cmd)}")
    result = subprocess.run(cmd, cwd=str(ROOT))
    if result.returncode != 0:
        print("[error] PyInstaller failed", file=sys.stderr)
        sys.exit(result.returncode)


def show_result():
    """展示产物"""
    print("\n=== Build finished ===")
    exe = DIST_DIR / ("NovelReader.exe" if sys.platform == "win32" else "NovelReader")
    if not exe.exists():
        alt = DIST_DIR / "NovelReader" / ("NovelReader.exe" if sys.platform == "win32" else "NovelReader")
        if alt.exists():
            exe = alt
    if exe.exists():
        size_mb = exe.stat().st_size / 1024 / 1024
        print(f"  [OK] Output: {exe}")
        print(f"  [OK] Size:   {size_mb:.1f} MB")
    else:
        print(f"  [!] Executable not found in {DIST_DIR}")


def main():
    parser = argparse.ArgumentParser(description="打包小说阅读器")
    parser.add_argument("--debug", action="store_true", help="Debug 模式（控制台 + 详细日志）")
    parser.add_argument("--no-clean", action="store_true", help="不清理旧构建")
    args = parser.parse_args()

    print(f"=== NovelReader Build ===")
    print(f"  Debug:  {args.debug}")
    print(f"  Python: {sys.version.split()[0]}")
    print(f"  Spec:   {SPEC.name}\n")

    if not args.no_clean:
        clean()

    run_pyinstaller(debug=args.debug)
    show_result()


if __name__ == "__main__":
    main()

