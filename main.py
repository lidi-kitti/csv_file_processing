import argparse
import csv
from collections import defaultdict
from pathlib import Path
from typing import Dict, Iterable, List, Tuple


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Считает среднюю эффективность по позициям из CSV файлов."
    )
    parser.add_argument(
        "--files",
        nargs="+",
        required=True,
        help="Пути к CSV файлам с данными.",
    )
    parser.add_argument(
        "--report",
        default="performance",
        help="Название отчета (поддерживается только 'performance').",
    )
    return parser.parse_args()


def collect_performance(files: Iterable[str]) -> Dict[str, List[float]]:
    """Собирает значения performance по позициям из нескольких файлов."""
    stats: Dict[str, List[float]] = defaultdict[str, List[float]](list)
    for file_path in files:
        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(file_path)
        with path.open("r", encoding="utf-8", newline="") as source:
            reader = csv.DictReader(source)
            for row in reader:
                position = (row.get("position") or "").strip()
                performance_raw = (row.get("performance") or "").strip()
                if not position or not performance_raw:
                    continue
                try:
                    stats[position].append(float(performance_raw))
                except ValueError:
                    continue
    return stats


def calculate_averages(stats: Dict[str, List[float]]) -> List[Tuple[str, float]]:
    rows: List[Tuple[str, float]] = []
    for position, items in stats.items():
        if not items:
            continue
        rows.append((position, sum(items) / len(items)))
    rows.sort(key=lambda item: item[1], reverse=True)
    return rows


def print_table(rows: List[Tuple[str, float]]) -> None:
    if not rows:
        print("Нет данных для формирования отчета.")
        return

    headers = ("Позиция", "Средняя эффективность")
    formatted = [(pos, f"{avg:.2f}") for pos, avg in rows]

    col1_width = max(len(headers[0]), *(len(row[0]) for row in formatted))
    col2_width = max(len(headers[1]), *(len(row[1]) for row in formatted))

    def line(char: str = "-") -> str:
        return f"+{char * (col1_width + 2)}+{char * (col2_width + 2)}+"

    print(line("-"))
    print(
        f"| {headers[0].ljust(col1_width)} | "
        f"{headers[1].rjust(col2_width)} |"
    )
    print(line("="))
    for position, avg in formatted:
        print(f"| {position.ljust(col1_width)} | {avg.rjust(col2_width)} |")
    print(line("-"))


def main() -> int:
    args = parse_args()
    try:
        stats = collect_performance(args.files)
        rows = calculate_averages(stats)
        print_table(rows)
    except FileNotFoundError as err:
        print(f"Файл не найден: {err}")
        return 1
    except Exception as err:  # noqa: BLE001
        print(f"Ошибка при генерации отчета: {err}")
        return 1

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
