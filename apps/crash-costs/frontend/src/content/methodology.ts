/**
 * Methodology & Sources tab — edit freely.
 */
export interface ContentSection {
  heading?: string;
  paragraphs: string[];
  bullets?: string[];
}

export const methodologyContent = {
  pageTitle: "Methodology & Sources",
  intro:
    "Crash costs on this map are estimated from Maryland CRASH/LOD police reports and unit-cost tables from NHTSA's The Economic and Societal Impact of Motor Vehicle Crashes, 2019 (Revised). Dollar figures are adjusted to June 2025 using a 1.26 cumulative inflation factor (BLS, June 2019 → June 2025).",

  sections: [
    {
      heading: "Maryland crash data",
      paragraphs: [
        "Half-year CSV extracts from the Maryland crash reporting system cover 2024 and 2025. Reports, vehicles, occupants, and non-motorists are merged into a single crash-level table keyed by report number.",
      ],
      bullets: [
        "Reports — one row per crash (severity, date, coordinates, county, etc.)",
        "Vehicles, occupants, and non-motorists — linked by report number; injury status codes drive person-level cost assignment",
      ],
    },
    {
      heading: "Unit costs and injury mapping",
      paragraphs: [
        "Unit costs come from NHTSA Table 1-10 (comprehensive police-reported crash costs). Maryland police injury status codes are mapped to MAIS-based cost columns (Fatal, MAIS0–MAIS4). Property-damage-only crashes (severity code 3) use per-vehicle costs only; injury crashes use person-based columns.",
        "Comprehensive cost includes QALY-valued losses as defined in the NHTSA report — not purely out-of-pocket economic costs.",
      ],
    },
    {
      heading: "Geography",
      paragraphs: [
        "Each crash point is spatially joined to 2024 TIGER/Line boundaries for Maryland counties, census tracts, and places (CDPs and incorporated places). Population and vehicle-ownership context come from NHGIS / ACS summaries merged at prepare time.",
      ],
    },
    {
      heading: "Sources",
      paragraphs: [],
      bullets: [
        "Maryland CRASH/LOD exports (2024–2025)",
        "NHTSA — The Economic and Societal Impact of Motor Vehicle Crashes, 2019 (Revised)",
        "U.S. Census Bureau — TIGER/Line shapefiles; ACS via NHGIS",
        "Bureau of Labor Statistics — CPI inflation adjustment (June 2019 → June 2025)",
      ],
    },
  ] satisfies ContentSection[],
};
