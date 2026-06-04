/**
 * About tab — edit freely.
 */
import type { ContentSection } from "./methodology";

export const aboutContent = {
  pageTitle: "About",
  intro:
    "This tool is a personal research project exploring the geographic distribution of motor vehicle crash costs in Maryland. It is not affiliated with any state agency or organization.",

  sections: [
    {
      heading: "How to use the map",
      paragraphs: [
        "Zoom in to move from county summaries to census places (CDPs) and, at higher zoom, census tracts and individual crash points. Use the filter bar to change the date range, crash type, pedestrian/cyclist involvement, and the metric shown on the map.",
        "Hover over a geography or crash to see a summary. Clicking a geography will eventually open a comparison dashboard (coming soon).",
      ],
    },
    {
      heading: "Data coverage",
      paragraphs: [
        "The map covers police-reported crashes in Maryland during 2024 and 2025. Place (CDP) assignments can be missing where a crash falls outside any Census place boundary.",
      ],
    },
    {
      heading: "Contact & code",
      paragraphs: [
        "Source code and analysis notebooks live in the parent crash_costs research repository. Update this section with a link or contact info when you publish.",
      ],
    },
  ] satisfies ContentSection[],
};
