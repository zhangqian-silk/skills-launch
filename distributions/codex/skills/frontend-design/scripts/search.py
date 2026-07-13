#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Frontend Design Search - BM25 search engine for UI/UX style guides
Usage: python search.py "<query>" [--domain <domain>] [--stack <stack>] [--max-results 3]
       python search.py "<query>" --design-system [-p "Project Name"]
       python search.py "<query>" --design-system --persist [-p "Project Name"] [--page "dashboard"]
       python search.py "<query>" --design-system --variance 8 --motion 9 --density 7

Domains are discovered from the packaged search configuration.
Stacks: discovered from the packaged data/stacks directory

Design dials (1-10, only with --design-system):
  --variance   DESIGN_VARIANCE: 1=centered/minimal, 10=bold/asymmetric
  --motion     MOTION_INTENSITY: 1=subtle, 10=complex; attaches a GSAP snippet from motion.csv
  --density    VISUAL_DENSITY: 1=spacious, 10=dense/dashboard; overrides the spacing scale

Persistence (Master + Overrides pattern):
  --persist    Save the design system under design-system/<project>/MASTER.md
  --page       Also create an override under design-system/<project>/pages/
"""

import argparse
import sys
import io

# Treat the installed skill as read-only runtime data.
sys.dont_write_bytecode = True

from core import CSV_CONFIG, AVAILABLE_STACKS, MAX_RESULTS, search, search_stack
from design_system import generate_design_system, safe_path_segment

# Force UTF-8 for stdout/stderr to handle emojis on Windows (cp1252 default)
if sys.stdout.encoding and sys.stdout.encoding.lower() != 'utf-8':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
if sys.stderr.encoding and sys.stderr.encoding.lower() != 'utf-8':
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')


def format_output(result):
    """Format compact search results."""
    if "error" in result:
        return f"Error: {result['error']}"

    output = []
    if result.get("stack"):
        output.append("## Stack Guidelines")
        output.append(f"**Stack:** {result['stack']} | **Query:** {result['query']}")
    else:
        output.append("## Design Search Results")
        output.append(f"**Domain:** {result['domain']} | **Query:** {result['query']}")
    output.append(f"**Source:** {result['file']} | **Found:** {result['count']} results\n")

    for i, row in enumerate(result['results'], 1):
        output.append(f"### Result {i}")
        for key, value in row.items():
            value_str = str(value)
            if len(value_str) > 300:
                value_str = value_str[:300] + "..."
            output.append(f"- **{key}:** {value_str}")
        output.append("")

    return "\n".join(output)


def exit_on_search_error(result):
    """Print a search error to stderr and terminate unsuccessfully."""
    if "error" in result:
        print(f"Error: {result['error']}", file=sys.stderr)
        raise SystemExit(1)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Frontend design search",
        epilog=f"Domains: {', '.join(CSV_CONFIG)}",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("query", help="Search query")
    parser.add_argument("--domain", "-d", choices=list(CSV_CONFIG.keys()), help="Search domain")
    parser.add_argument("--stack", "-s", choices=AVAILABLE_STACKS, help=f"Stack-specific search. Available: {', '.join(AVAILABLE_STACKS)}")
    parser.add_argument("--max-results", "-n", type=int, default=MAX_RESULTS, help="Max results (default: 3)")
    parser.add_argument("--json", action="store_true", help="Output as JSON")
    # Design system generation
    parser.add_argument("--design-system", "-ds", action="store_true", help="Generate complete design system recommendation")
    parser.add_argument("--project-name", "-p", type=str, default=None, help="Project name for design system output")
    parser.add_argument("--format", "-f", choices=["ascii", "markdown"], default="ascii", help="Output format for design system")
    # Persistence (Master + Overrides pattern)
    parser.add_argument("--persist", action="store_true", help="Save under design-system/<project>/MASTER.md")
    parser.add_argument("--page", type=str, default=None, help="Create an override under design-system/<project>/pages/")
    parser.add_argument("--output-dir", "-o", type=str, default=None, help="Output directory for persisted files (default: current directory)")
    # Design dials (1-10), only applied with --design-system
    parser.add_argument("--variance", type=int, choices=range(1, 11), metavar="1-10", help="DESIGN_VARIANCE dial: 1=centered/minimal, 10=bold/asymmetric (only with --design-system)")
    parser.add_argument("--motion", type=int, choices=range(1, 11), metavar="1-10", help="MOTION_INTENSITY dial: 1=subtle, 10=complex; pulls a matching GSAP snippet from motion.csv (only with --design-system)")
    parser.add_argument("--density", type=int, choices=range(1, 11), metavar="1-10", help="VISUAL_DENSITY dial: 1=spacious, 10=dense/dashboard; overrides the spacing scale (only with --design-system)")

    args = parser.parse_args()

    # Design system takes priority
    if args.design_system:
        result = generate_design_system(
            args.query,
            args.project_name,
            args.format,
            persist=args.persist,
            page=args.page,
            output_dir=args.output_dir,
            variance=args.variance,
            motion=args.motion,
            density=args.density
        )
        print(result)

        # Print persistence confirmation
        if args.persist:
            project_slug = safe_path_segment(args.project_name or args.query, "default")
            print("\n" + "=" * 60)
            print(f"✅ Design system persisted to design-system/{project_slug}/")
            print(f"   📄 design-system/{project_slug}/MASTER.md (Global Source of Truth)")
            if args.page:
                page_filename = safe_path_segment(args.page, "page")
                print(f"   📄 design-system/{project_slug}/pages/{page_filename}.md (Page Overrides)")
            print("")
            print(f"📖 Usage: When building a page, check design-system/{project_slug}/pages/[page].md first.")
            print(f"   If exists, its rules override MASTER.md. Otherwise, use MASTER.md.")
            print("=" * 60)
    # Stack search
    elif args.stack:
        result = search_stack(args.query, args.stack, args.max_results)
        exit_on_search_error(result)
        if args.json:
            import json
            print(json.dumps(result, indent=2, ensure_ascii=False))
        else:
            print(format_output(result))
    # Domain search
    else:
        result = search(args.query, args.domain, args.max_results)
        exit_on_search_error(result)
        if args.json:
            import json
            print(json.dumps(result, indent=2, ensure_ascii=False))
        else:
            print(format_output(result))
