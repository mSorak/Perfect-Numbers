import { siteContent } from "../content/site";

export type SiteTab = "map" | "methodology" | "about";

interface Props {
  activeTab: SiteTab;
  onTabChange: (tab: SiteTab) => void;
  showHero: boolean;
}

export function SiteHeader({ activeTab, onTabChange, showHero }: Props) {
  const { nav, hero } = siteContent;

  const tabs: Array<{ id: SiteTab; label: string }> = [
    { id: "map", label: nav.map },
    { id: "methodology", label: nav.methodology },
    { id: "about", label: nav.about },
  ];

  return (
    <header className="site-header">
      <div className="site-nav">
        <div className="site-nav-inner">
          <button
            type="button"
            className="site-brand"
            onClick={() => onTabChange("map")}
          >
            {siteContent.documentTitle}
          </button>
          <nav className="site-tabs" aria-label="Main">
            {tabs.map((tab) => (
              <button
                key={tab.id}
                type="button"
                className={`site-tab${activeTab === tab.id ? " is-active" : ""}`}
                aria-current={activeTab === tab.id ? "page" : undefined}
                onClick={() => onTabChange(tab.id)}
              >
                {tab.label}
              </button>
            ))}
          </nav>
        </div>
      </div>

      {showHero && (
        <div className="hero">
          <div className="hero-inner">
            <div className="hero-copy">
              <h1 className="hero-title">{hero.title}</h1>
              {hero.intro.map((paragraph, i) => (
                <p key={i} className="hero-intro">
                  {paragraph}
                </p>
              ))}
            </div>
            <aside className="hero-stat" aria-label="Headline statistic">
              <span className="hero-stat-label">{hero.headlineStat.label}</span>
              <span className="hero-stat-value">{hero.headlineStat.value}</span>
              {hero.headlineStat.note && (
                <span className="hero-stat-note">{hero.headlineStat.note}</span>
              )}
            </aside>
          </div>
        </div>
      )}
    </header>
  );
}
