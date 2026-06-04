import type { ContentSection } from "../content/methodology";

interface Props {
  title: string;
  intro: string;
  sections: ContentSection[];
}

export function ProsePage({ title, intro, sections }: Props) {
  return (
    <article className="prose-page">
      <h1>{title}</h1>
      <p className="prose-lead">{intro}</p>
      {sections.map((section, i) => (
        <section key={i} className="prose-section">
          {section.heading && <h2>{section.heading}</h2>}
          {section.paragraphs.map((p, j) => (
            <p key={j}>{p}</p>
          ))}
          {section.bullets && section.bullets.length > 0 && (
            <ul>
              {section.bullets.map((b, k) => (
                <li key={k}>{b}</li>
              ))}
            </ul>
          )}
        </section>
      ))}
    </article>
  );
}
