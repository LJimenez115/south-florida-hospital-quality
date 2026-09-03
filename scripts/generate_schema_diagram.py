"""Render a PNG describing the Project 2 hospital-quality database schema."""

from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch


# Why: The schema image is delivered beside the database so a reviewer can see the
# relationships without opening SQL or needing to infer the model from field names.
PROJECT_ROOT = Path(__file__).resolve().parents[1]
OUTPUT_FILE = PROJECT_ROOT / "database" / "south_florida_hospital_quality_schema.png"

# Why: The diagram shows the fields needed to understand relationships and grain;
# the full SQL file remains the authoritative definition of every stored column.
TABLES = {
    "dim_hospital": (0.35, 3.35, 3.55, 2.4, ["PK  hospital_key", "facility_id", "name • county • city", "type • ownership • emergency", "benchmark_group"]),
    "dim_hcahps_measure": (0.35, 6.65, 3.55, 1.65, ["PK  hcahps_measure_key", "measure_id", "HCAHPS question"]),
    "dim_survey_period": (0.35, 1.05, 3.55, 1.45, ["PK  survey_period_key", "survey start • end"]),
    "fact_hospital_quality": (5.0, 5.65, 4.3, 2.45, ["PK  hospital_quality_key", "FK  hospital_key", "overall rating", "mortality • safety", "readmission • experience"]),
    "fact_hcahps_rating": (5.0, 1.85, 4.3, 2.85, ["PK  hcahps_rating_key", "FK  hospital_key", "FK  measure_key • period_key", "patient survey star rating", "survey count • response rate"]),
}


def draw_table(axis, name, x, y, width, height, fields) -> None:
    """Draw one database table with a consistent title band and key field list."""
    # Why: The fact tables use a stronger fill color so the reader can immediately
    # distinguish their stored observations from reusable lookup dimensions.
    is_fact = name.startswith("fact_")
    fill = "#D8EAF8" if is_fact else "#F7FAFC"
    title_fill = "#1F4E79" if is_fact else "#4E7B9A"
    axis.add_patch(FancyBboxPatch((x, y), width, height, boxstyle="round,pad=0.04", facecolor=fill,
                                  edgecolor="#315A73", linewidth=1.2, zorder=3))
    axis.add_patch(FancyBboxPatch((x, y + height - 0.43), width, 0.43, boxstyle="round,pad=0.04",
                                  facecolor=title_fill, edgecolor=title_fill, zorder=4))
    axis.text(x + width / 2, y + height - 0.215, name, ha="center", va="center", color="white",
              fontsize=10, fontweight="bold", zorder=5)
    for index, field in enumerate(fields):
        axis.text(x + 0.18, y + height - 0.72 - index * 0.33, field, ha="left", va="center",
                  fontsize=8.5, color="#17324D", zorder=5)


def connect(axis, start, end) -> None:
    """Draw a dimension-to-fact foreign-key relationship behind the boxes."""
    # Why: Arrowheads point toward the fact table to show that dimension members
    # are referenced by many observations rather than the other way around.
    axis.annotate("", xy=end, xytext=start, arrowprops={"arrowstyle": "->", "color": "#7895A9", "lw": 1.6}, zorder=1)


def main() -> None:
    """Create the hospital-quality schema image."""
    # Why: A fixed high-resolution figure produces a readable portfolio asset for
    # GitHub, a case study, or reference while configuring Power BI relationships.
    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    figure, axis = plt.subplots(figsize=(13, 8.5))
    axis.set(xlim=(0, 13.4), ylim=(0.5, 9.35))
    axis.axis("off")
    figure.suptitle("South Florida Hospital Quality — Power BI Data Model", fontsize=16, fontweight="bold", color="#17324D")
    connect(axis, (3.9, 5.1), (5.0, 6.85))
    connect(axis, (3.9, 4.4), (5.0, 3.55))
    connect(axis, (3.9, 7.45), (5.0, 4.0))
    connect(axis, (3.9, 1.8), (5.0, 2.55))
    for name, values in TABLES.items():
        draw_table(axis, name, *values)
    figure.text(0.5, 0.04, "Arrow direction: dimension table → fact-table foreign key", ha="center", fontsize=9, color="#4C6274")
    figure.tight_layout(rect=(0, 0.06, 1, 0.94))
    figure.savefig(OUTPUT_FILE, dpi=200, bbox_inches="tight")
    plt.close(figure)
    print(f"Created schema image: {OUTPUT_FILE}")


if __name__ == "__main__":
    # Why: The guard allows future reuse of the table layout without automatically
    # overwriting the schema image whenever the module is imported.
    main()
