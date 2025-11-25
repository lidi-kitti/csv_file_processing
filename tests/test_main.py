import csv
import sys
from argparse import Namespace
from pathlib import Path

import pytest

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from source.main import (  # noqa: E402
    calculate_averages,
    collect_performance,
    main,
    parse_args,
    print_table,
)


def test_parse_args_uses_defaults(monkeypatch):
    monkeypatch.setattr(
        sys,
        "argv",
        ["prog", "--files", "one.csv", "two.csv"],
    )

    args = parse_args()

    assert args.files == ["one.csv", "two.csv"]
    assert args.report == "performance"


def test_calculate_averages_keeps_best_first():
    stats = {
        "QA": [3.0, 3.0],
        "DEV": [1.0, 2.0],
    }

    result = calculate_averages(stats)

    assert result[0][0] == "QA"
    assert round(result[0][1], 2) == 3.0
    assert result[1][0] == "DEV"
    assert round(result[1][1], 2) == 1.5


def test_collect_performance_reads_csv(tmp_path):
    file_path = tmp_path / "data.csv"
    with file_path.open("w", encoding="utf-8", newline="") as csv_file:
        writer = csv.writer(csv_file)
        writer.writerow(["position", "performance"])
        writer.writerow(["QA", "3.0"])
        writer.writerow(["DEV", "1.0"])

    stats = collect_performance([str(file_path)])

    assert stats["QA"] == [3.0]
    assert stats["DEV"] == [1.0]


def test_collect_performance_missing_file():
    with pytest.raises(FileNotFoundError):
        collect_performance(["definitely_missing.csv"])


def test_collect_performance_skips_invalid_rows(tmp_path):
    file_path = tmp_path / "data.csv"
    with file_path.open("w", encoding="utf-8", newline="") as csv_file:
        writer = csv.writer(csv_file)
        writer.writerow(["position", "performance"])
        writer.writerow(["QA", "not-a-number"])
        writer.writerow(["", "2"])
        writer.writerow(["DEV", "4"])

    stats = collect_performance([str(file_path)])

    assert stats["DEV"] == [4.0]
    assert stats["QA"] == []


def test_print_table_with_rows(capsys):
    print_table([("QA", 3.14159)])

    out = capsys.readouterr().out
    assert "Позиция" in out
    assert "QA" in out
    assert "3.14" in out


def test_print_table_without_rows(capsys):
    print_table([])

    out = capsys.readouterr().out
    assert "Нет данных" in out


def test_main_success(monkeypatch, tmp_path, capsys):
    file_path = tmp_path / "data.csv"
    with file_path.open("w", encoding="utf-8", newline="") as csv_file:
        writer = csv.writer(csv_file)
        writer.writerow(["position", "performance"])
        writer.writerow(["QA", "3"])

    monkeypatch.setattr(
        "source.main.parse_args",
        lambda: Namespace(files=[str(file_path)], report="performance"),
    )

    exit_code = main()

    out = capsys.readouterr().out
    assert exit_code == 0
    assert "QA" in out


def test_main_handles_file_not_found(monkeypatch, capsys):
    monkeypatch.setattr(
        "source.main.parse_args",
        lambda: Namespace(files=["missing.csv"], report="performance"),
    )

    exit_code = main()

    out = capsys.readouterr().out
    assert exit_code == 1
    assert "Файл не найден" in out


def test_main_handles_generic_error(monkeypatch, capsys):
    monkeypatch.setattr(
        "source.main.parse_args",
        lambda: Namespace(files=["employees1.csv"], report="performance"),
    )

    def explode(_):
        raise ValueError("boom")

    monkeypatch.setattr("source.main.collect_performance", explode)

    exit_code = main()

    out = capsys.readouterr().out
    assert exit_code == 1
    assert "Ошибка при генерации отчета" in out