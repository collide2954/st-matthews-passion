"""Command line interface of the style study."""

from __future__ import annotations

import argparse

from . import corpus


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="stmatthew-study",
        description="Build the style study: download open data, measure it, write the report.",
    )
    commands = parser.add_subparsers(dest="command", required=True)
    fetch = commands.add_parser("fetch", help="download the open data files into the cache")
    fetch.add_argument("--force", action="store_true", help="download again")
    commands.add_parser("measure", help="measure the data and write research/measured/*.csv")
    commands.add_parser("report", help="write docs/style-study.md from the tables")
    commands.add_parser("check", help="check the tables for errors")
    commands.add_parser("all", help="do fetch, measure, check, and report")
    args = parser.parse_args(argv)

    if args.command in ("fetch", "all"):
        for path in corpus.fetch_all(force=getattr(args, "force", False)):
            print(f"ready: {path}")
    if args.command in ("measure", "all"):
        from . import measure

        measure.measure_all()
        print(f"measured tables: {measure.OUTPUT_DIR}")
    if args.command in ("check", "all"):
        from . import report

        problems = report.check()
        for problem in problems:
            print(f"problem: {problem}")
        if problems:
            return 1
        print("tables: no problems")
    if args.command in ("report", "all"):
        from . import report

        print(f"report: {report.write()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
