# ruff: noqa
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))


def count_lines_in_dir(path: str) -> tuple[int, int]:
    """Возвращает (строк_кода, строк_тестов) для указанной папки."""
    code_lines = 0
    test_lines = 0
    for root, _, files in os.walk(path):
        # пропускаем миграции
        if "migrations" in root:
            continue
        for file in files:
            if not file.endswith(".py"):
                continue
            full_path = os.path.join(root, file)
            with open(full_path, encoding="utf-8", errors="ignore") as f:
                lines = sum(1 for _ in f)
            if "test" in file.lower() or "tests" in root.lower():
                test_lines += lines
            else:
                code_lines += lines
    return code_lines, test_lines


def main() -> None:
    total_code, total_tests = 0, 0
    for name in os.listdir(BASE_DIR):
        path = os.path.join(BASE_DIR, name)
        if not os.path.isdir(path) or name.startswith((".", "__")):
            continue
        # считаем только папки, содержащие Python-код
        if not any(fn.endswith(".py") for fn in os.listdir(path) if os.path.isfile(os.path.join(path, fn))):
            continue

        code, tests = count_lines_in_dir(path)
        if code or tests:
            print(f"{name}: code={code}, tests={tests}")
            total_code += code
            total_tests += tests

    print("-" * 40)
    print(f"TOTAL: code={total_code}, tests={total_tests}, all={total_code + total_tests}")


if __name__ == "__main__":
    main()
