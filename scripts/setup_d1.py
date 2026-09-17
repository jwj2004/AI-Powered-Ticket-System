"""
D1 一键初始化脚本
功能：建表 + 灌数据 + 构建FAISS向量索引
用法：python scripts/setup_d1.py
"""
import subprocess
import sys
import os

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_DIR = os.path.dirname(SCRIPT_DIR)
PYTHON = sys.executable


def run_script(script_name, description):
    print(f"\n{'='*60}")
    print(f"▶ 开始: {description}")
    print(f"{'='*60}\n")
    result = subprocess.run(
        [PYTHON, os.path.join(SCRIPT_DIR, script_name)],
        cwd=PROJECT_DIR,
    )
    if result.returncode != 0:
        print(f"\n❌ {description} 失败，退出码: {result.returncode}")
        sys.exit(1)
    print(f"\n✅ {description} 完成")


def main():
    print("=" * 60)
    print("  知答 MVP - D1 一键初始化")
    print("  建表 + 灌数据 + FAISS向量索引")
    print("=" * 60)

    run_script("init_db.py", "建表 + 灌CSV数据")
    run_script("build_faiss_index.py", "构建FAISS向量索引")

    print("\n" + "=" * 60)
    print("🎉 D1 全部完成！")
    print("=" * 60)
    print("")
    print("📁 产出物：")
    print("  db/zhida.db            - SQLite 数据库（5张表）")
    print("  db/ticket_index.faiss  - FAISS 向量索引")
    print("  db/ticket_id_mapping.json - 索引ID→工单ID映射")
    print("")
    print("📅 D2 可以开始写接口了！")
    print("  /api/lookup           - 错误码秒查")
    print("  /api/retrieve         - 内部向量检索（B调用）")
    print("  /api/feedback         - 埋点反馈")


if __name__ == "__main__":
    main()
