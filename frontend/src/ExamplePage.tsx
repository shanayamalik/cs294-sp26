type QueryComposerVariant = {
  id: string;
  name: string;
  tone: string;
  summary: string;
  composerClassName: string;
  actionLabel: string;
};

const ACTIVE_FILTERS = ["4 selected patents", "Assignee: Google LLC", "Section: specification"];
const QUERY_TOKENS = ["section:SPECIFICATION", 'contains:"signal processing"', "assignee:Google"];
const SAMPLE_QUERY = 'section:SPECIFICATION AND contains:"signal processing"';

const QUERY_COMPOSER_VARIANTS: QueryComposerVariant[] = [
  {
    id: "compact-stack",
    name: "Compact Stack",
    tone: "Most restrained and closest to a production search tool.",
    summary: "Keeps label, query field, helper context, and run action in one tight vertical block with minimal chrome.",
    composerClassName: "exampleComposer exampleComposerCompact",
    actionLabel: "Run query",
  },
  {
    id: "toolbar-shell",
    name: "Toolbar Shell",
    tone: "More operational and explicit about scope before writing.",
    summary: "Uses a small composer header with scope and helper tokens, then puts the textarea and action below like a compact workbench.",
    composerClassName: "exampleComposer exampleComposerToolbar",
    actionLabel: "Search passages",
  },
  {
    id: "inline-command",
    name: "Inline Command",
    tone: "Most stylized, but still compact enough to test seriously.",
    summary: "Treats the composer a bit more like a command surface, with DSL context and the primary action sharing the same visual band.",
    composerClassName: "exampleComposer exampleComposerInline",
    actionLabel: "Run DSL",
  },
];

export default function ExamplePage() {
  return (
    <main className="examplePage">
      <section className="exampleHero">
        <div>
          <p className="exampleEyebrow">Query composer layout</p>
          <h1>How should the query composer feel?</h1>
          <p className="exampleIntro">
            This page keeps the same DSL text, helper content, and scope context. The only thing changing is layout: where the context sits, how much framing the textarea gets, and where the primary action belongs.
          </p>
        </div>
        <div className="exampleHeroActions">
          <a href="/demo">Back to /demo</a>
          <a href="/">Current UI</a>
        </div>
      </section>

      <section className="exampleGrid">
        {QUERY_COMPOSER_VARIANTS.map((variant) => (
          <article key={variant.id} className="exampleCard">
            <div className="exampleCardHeader">
              <div>
                <p className="exampleVariantLabel">Option</p>
                <h2>{variant.name}</h2>
                <p className="exampleVariantTone">{variant.tone}</p>
              </div>
              <p className="exampleVariantSummary">{variant.summary}</p>
            </div>

            <div className={variant.composerClassName}>
              <div className="exampleComposerMeta">
                <div>
                  <strong>Query DSL</strong>
                  <p>Searching passages inside the current filtered corpus.</p>
                </div>
                <span className="exampleComposerCount">27 matches last run</span>
              </div>

              {variant.id === "toolbar-shell" ? (
                <div className="exampleComposerToolbar">
                  <div className="exampleComposerPills">
                    {ACTIVE_FILTERS.map((item) => (
                      <span key={item} className="exampleComposerPill">
                        {item}
                      </span>
                    ))}
                  </div>
                  <button type="button" className="exampleComposerUtility">
                    Edit scope
                  </button>
                </div>
              ) : null}

              <label className="exampleComposerField">
                <span className="exampleComposerFieldLabel">Draft query</span>
                <textarea rows={variant.id === "inline-command" ? 3 : 4} readOnly value={SAMPLE_QUERY} />
              </label>

              <div className="exampleComposerFooter">
                <div className="exampleComposerHints">
                  {variant.id === "compact-stack" ? <p className="exampleComposerHelper">Start with section and phrase matching, then narrow only if needed.</p> : null}

                  {variant.id === "inline-command" ? (
                    <div className="exampleComposerCommandRow">
                      <span className="exampleComposerPrompt">DSL</span>
                      <div className="exampleComposerTokens">
                        {QUERY_TOKENS.map((token) => (
                          <span key={token} className="exampleComposerToken">
                            {token}
                          </span>
                        ))}
                      </div>
                    </div>
                  ) : (
                    <div className="exampleComposerTokens">
                      {QUERY_TOKENS.map((token) => (
                        <span key={token} className="exampleComposerToken">
                          {token}
                        </span>
                      ))}
                    </div>
                  )}

                  {variant.id !== "compact-stack" ? (
                    <p className="exampleComposerHelper">The scope stays visible, but secondary to the query itself.</p>
                  ) : null}
                </div>

                <div className="exampleComposerActions">
                  {variant.id === "compact-stack" ? <span className="exampleComposerSubtle">Live query on edit</span> : null}
                  {variant.id === "toolbar-shell" ? <span className="exampleComposerSubtle">4 patents selected</span> : null}
                  <button type="button" className="exampleComposerPrimary">
                    {variant.actionLabel}
                  </button>
                </div>
              </div>
            </div>
          </article>
        ))}
      </section>
    </main>
  );
}