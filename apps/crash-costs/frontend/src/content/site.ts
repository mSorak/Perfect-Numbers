/**
 * Main site copy — edit freely. Used for the hero, navigation labels, and
 * document title.
 */
export const siteContent = {
  documentTitle: "Maryland Crash Costs",

  nav: {
    map: "Map",
    methodology: "Methodology & Sources",
    about: "About",
  },

  hero: {
    title: "What do Maryland's crashes cost?",
    intro: [
      "Police-reported motor vehicle crashes carry enormous economic and societal costs — medical care, emergency response, congestion, property damage, and the value of life years lost.",
      "This map estimates comprehensive crash costs across Maryland for 2024–2025, letting you explore how those costs vary by county, community, and neighborhood.",
    ],
    headlineStat: {
      label: "Comprehensive crash costs (2024–2025)",
      /** Replace with a dollar total from your analysis when ready. */
      value: "—",
      note: "Update this value in frontend/src/content/site.ts",
    },
  },
};
