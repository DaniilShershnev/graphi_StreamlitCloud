#!/usr/bin/env python3
"""
Convert SVG files to PDF for LaTeX inclusion
"""
import os
import glob
from pathlib import Path

try:
    from svglib.svglib import svg2rlg
    from reportlab.graphics import renderPDF
    print("Using svglib + reportlab for conversion")
    converter_available = True
except ImportError:
    print("svglib not available")
    converter_available = False

def convert_svg_to_pdf(svg_path, pdf_path):
    """Convert SVG to PDF"""
    if not converter_available:
        return False

    try:
        drawing = svg2rlg(svg_path)
        if drawing is None:
            print(f"Failed to parse SVG: {svg_path}")
            return False
        renderPDF.drawToFile(drawing, pdf_path)
        return True
    except Exception as e:
        print(f"Error: {e}")
        return False

def main():
    output_dir = Path("D:/graphic/output")

    # Find all SVG files related to our work
    svg_files = [
        "phase_portrait_general.svg",
        "phase_portrait_frenkel_A02.svg",
        "phase_portrait_frenkel_A05.svg",
        "phase_portrait_frenkel_A08.svg",
        "timeseries_ic1.svg",
        "timeseries_ic2.svg",
        "timeseries_frenkel_A05.svg",
    ]

    converted = 0
    failed = 0

    for svg_file in svg_files:
        svg_path = output_dir / svg_file
        if not svg_path.exists():
            print(f"⚠ File not found: {svg_file}")
            continue

        pdf_file = svg_file.replace('.svg', '.pdf')
        pdf_path = output_dir / pdf_file

        print(f"Converting {svg_file} -> {pdf_file}...", end=' ')

        if convert_svg_to_pdf(str(svg_path), str(pdf_path)):
            print("[OK]")
            converted += 1
        else:
            print("[FAIL]")
            failed += 1

    print(f"\nSummary: {converted} converted, {failed} failed")

    if converted > 0:
        print(f"\n[SUCCESS] PDF files are ready in {output_dir}")
        return 0
    else:
        print("\n[ERROR] No files were converted")
        return 1

if __name__ == "__main__":
    exit(main())
