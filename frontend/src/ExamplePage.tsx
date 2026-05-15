type VisualThemeVariant = {
  id: string;
  name: string;
  tone: string;
  summary: string;
  shellClassName: string;
};

const ACTIVE_FILTERS = ["15 selected patents", "1 metadata filter"];
const SAMPLE_QUERY = 'section:SPECIFICATION AND contains:"virtual network"';
const RESULT_TAGS = ["Description", "Brief description of the drawings", "Passage 8", "¶ [9]"];

const VISUAL_THEME_VARIANTS: VisualThemeVariant[] = [
  {
    id: "cool-editorial",
    name: "Cool Editorial",
    tone: "Closest to the current direction, but sharper and more composed.",
    summary: "Blue-gray panels, crisp sans-serif UI, and a restrained editorial headline treatment.",
    shellClassName: "exampleThemeShell exampleThemeShellEditorial",
  },
  {
    id: "soft-product",
    name: "Soft Product",
    tone: "Warmer and calmer, with slightly softer contrast.",
    summary: "Cream-tinted surfaces, rounder components, and a gentler product feel without going decorative.",
    shellClassName: "exampleThemeShell exampleThemeShellSoft",
  },
  {
    id: "technical-ops",
    name: "Technical Ops",
    tone: "Most utilitarian and tool-like, with stronger structure.",
    summary: "Cool steel surfaces, tighter type, and a more explicitly operational interface language.",
    shellClassName: "exampleThemeShell exampleThemeShellOps",
  },
];

export default function ExamplePage() {
  return (
    <main className="examplePage">
      <section className="exampleHero">
        <div>
          <p className="exampleEyebrow">Palette and type</p>
          <h1>Which visual language fits the workspace?</h1>
          <p className="exampleIntro">
            This page keeps the same layout and interaction model. The only thing changing is the visual system: palette, typography, and the tone of the surfaces.
          </p>
        </div>
        <div className="exampleHeroActions">
          <a href="/demo">Back to /demo</a>
          <a href="/">Current UI</a>
        </div>
      </section>

      <section className="exampleGrid">
        {VISUAL_THEME_VARIANTS.map((variant) => (
          <article key={variant.id} className="exampleCard">
            <div className="exampleCardHeader">
              <div>
                <p className="exampleVariantLabel">Option</p>
                <h2>{variant.name}</h2>
                <p className="exampleVariantTone">{variant.tone}</p>
              </div>
              <p className="exampleVariantSummary">{variant.summary}</p>
            </div>

            <div className={variant.shellClassName}>
              <div className="exampleThemeTopbar">
                <span className="exampleThemeTopbarLabel">Search workspace</span>
                <div className="exampleThemeTopbarMeta">
                  <span>15 docs</span>
                  <span>15 selected</span>
                </div>
              </div>

              <div className="exampleThemePanel exampleThemeRail">
                <div className="exampleThemeSectionHeader">
                  <strong>Selected patents</strong>
                  <span>15 chosen</span>
                </div>
                <div className="exampleThemeActionRow">
                  <button type="button" className="exampleThemeAction exampleThemeActionSecondary">
                    Select filtered
                  </button>
                  <button type="button" className="exampleThemeAction exampleThemeActionSecondary">
                    Clear
                  </button>
                </div>
                <div className="exampleThemeSelectedList">
                  <label className="exampleThemeSelectedItem">
                    <input type="checkbox" checked readOnly />
                    <span>
                      <strong>Adaptive Sensor Processing System</strong>
                      <small>sample-patent-1</small>
                    </span>
                  </label>
                  <label className="exampleThemeSelectedItem">
                    <input type="checkbox" checked readOnly />
                    <span>
                      <strong>Virtual Network For Virtual Machine Communication And Migration</strong>
                      <small>us-10228959-b1-i</small>
                    </span>
                  </label>
                </div>
              </div>

              <div className="exampleThemePanel exampleThemeComposer">
                <div className="exampleThemeSectionHeader">
                  <div>
                    <strong>Query DSL</strong>
                    <p>Searching passages inside the current filtered corpus.</p>
                  </div>
                  <span className="exampleThemeBadge">36 matches last run</span>
                </div>

                <div className="exampleThemePills">
                  {ACTIVE_FILTERS.map((item) => (
                    <span key={item} className="exampleThemePill">
                        {item}
                    </span>
                  ))}
                </div>

                <label className="exampleThemeField">
                  <span className="exampleThemeFieldLabel">Draft query</span>
                  <textarea rows={3} readOnly value={SAMPLE_QUERY} />
                </label>

                <div className="exampleThemeFooter">
                  <p className="exampleThemeHint">Start with section and phrase matching, then narrow only if needed.</p>
                  <button type="button" className="exampleThemeAction exampleThemeActionPrimary">
                    Search passages
                  </button>
                </div>
              </div>

              <div className="exampleThemePanel exampleThemeResultCard">
                <div className="exampleThemeResultHeader">
                  <div>
                    <strong>Virtual Network For Virtual Machine Communication And Migration</strong>
                    <small>us-10228959-b1-i</small>
                  </div>
                  <div className="exampleThemeResultActions">
                    <button type="button" className="exampleThemeAction exampleThemeActionGhost">
                      Copy citation
                    </button>
                    <button type="button" className="exampleThemeAction exampleThemeActionGhost">
                      Add to chart
                    </button>
                  </div>
                </div>

                <div className="exampleThemeTags">
                  {RESULT_TAGS.map((tag) => (
                    <span key={tag} className="exampleThemeTag">
                      {tag}
                    </span>
                  ))}
                </div>

                <p className="exampleThemePassage">
                  FIG. 7B shows an after-migration snapshot of a <mark>virtual network</mark> routing table.
                </p>

                <div className="exampleThemeDisclosure">
                  <span>Full passage + context</span>
                  <span>View</span>
                </div>
              </div>
            </div>
          </article>
        ))}
      </section>
    </main>
  );
}