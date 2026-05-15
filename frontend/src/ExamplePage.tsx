type ResultCardVariant = {
  id: string;
  name: string;
  tone: string;
  summary: string;
  shellClassName: string;
  metaClassName: string;
  actionsClassName: string;
  previewClassName: string;
  disclosureBodyClassName: string;
};

const SAMPLE_PASSAGE = {
  title: "Adaptive Sensor Processing System",
  section: "SPECIFICATION",
  sectionTitle: "DETAILED DESCRIPTION",
  passage: "In one embodiment, the signal processing module receives raw measurements from multiple channels.",
  before: "(none)",
  after: "A calibration submodule computes adjustment factors for each channel before output.",
  reasons: "Matched section:SPECIFICATION; Matched contains:\"signal processing\"",
};

const RESULT_CARD_VARIANTS: ResultCardVariant[] = [
  {
    id: "compact-neutral",
    name: "Compact Ops / Neutral",
    tone: "Tight, quiet, and closest to a productivity tool.",
    summary: "Keeps the compact layout, shrinks the expanded text, and avoids extra color so the card stays understated.",
    shellClassName: "exampleResultShellCompactOps",
    metaClassName: "exampleResultMetaCompactOps",
    actionsClassName: "exampleResultActionsCompactOps",
    previewClassName: "examplePassagePreviewCompactOps",
    disclosureBodyClassName: "exampleDisclosureBodyUtilityCompact",
  },
  {
    id: "compact-accent-actions",
    name: "Compact Ops / Accent Actions",
    tone: "Adds just enough product color to improve scanability.",
    summary: "Same compact hierarchy, but with one emphasized action and slightly more colored metadata to test whether subtle accents help.",
    shellClassName: "exampleResultShellCompactOps",
    metaClassName: "exampleResultMetaCompactOpsAccent",
    actionsClassName: "exampleResultActionsCompactOpsAccent",
    previewClassName: "examplePassagePreviewCompactOps",
    disclosureBodyClassName: "exampleDisclosureBodyUtilityCompactAccent",
  },
  {
    id: "compact-accent-copy",
    name: "Compact Ops / Accent Copy",
    tone: "Tests whether small color cues inside the expanded content help without feeling decorative.",
    summary: "Keeps the card dense, but gives the expanded labels and context panel a little more visual structure.",
    shellClassName: "exampleResultShellCompactOps",
    metaClassName: "exampleResultMetaCompactOps",
    actionsClassName: "exampleResultActionsCompactOps",
    previewClassName: "examplePassagePreviewCompactOps",
    disclosureBodyClassName: "exampleDisclosureBodyUtilityCompactLabels",
  },
];

export default function ExamplePage() {
  return (
    <main className="examplePage">
      <section className="exampleHero">
        <div>
          <p className="exampleEyebrow">Result refinement</p>
          <h1>Compact ops refinements</h1>
          <p className="exampleIntro">
            This page now keeps only the current active direction. The utility disclosure stays fixed, and these options only test two things: smaller expanded copy and whether subtle color on text or buttons helps.
          </p>
        </div>
        <div className="exampleHeroActions">
          <a href="/demo">Back to /demo</a>
          <a href="/">Current UI</a>
        </div>
      </section>

      <section className="exampleGrid">
        {RESULT_CARD_VARIANTS.map((variant) => (
          <article key={variant.id} className="exampleCard">
            <div className="exampleCardHeader">
              <div>
                <p className="exampleVariantLabel">Option</p>
                <h2>{variant.name}</h2>
                <p className="exampleVariantTone">{variant.tone}</p>
              </div>
              <p className="exampleVariantSummary">{variant.summary}</p>
            </div>

            <div className={`exampleResultShell ${variant.shellClassName}`}>
              <div className={`exampleResultMeta ${variant.metaClassName}`}>
                <strong>{SAMPLE_PASSAGE.title}</strong>
                <span>{SAMPLE_PASSAGE.section}</span>
                <span>{SAMPLE_PASSAGE.sectionTitle}</span>
                <span>Passage 0</span>
              </div>

              <div className={`exampleResultActions ${variant.actionsClassName}`}>
                <button type="button">Copy citation</button>
                <button type="button">Add to chart</button>
                <button type="button">View chart</button>
              </div>

              <p className={`examplePassagePreview ${variant.previewClassName}`}>{SAMPLE_PASSAGE.passage}</p>

              <details className="exampleDisclosure exampleDisclosureutility-drawer" open>
                <summary className="exampleDisclosureSummary">
                  <span className="exampleDisclosureSummaryText">Full passage + context</span>
                  <span className="exampleDisclosureMeta">Tap to expand</span>
                </summary>
                <div className={`exampleDisclosureBody exampleDisclosureBodyUtility ${variant.disclosureBodyClassName}`}>
                  <p>
                    <b>Matched passage:</b> {SAMPLE_PASSAGE.passage}
                  </p>
                  <p>
                    <b>Before:</b> {SAMPLE_PASSAGE.before}
                  </p>
                  <p>
                    <b>After:</b> {SAMPLE_PASSAGE.after}
                  </p>
                  <p>
                    <b>Why it matched:</b> {SAMPLE_PASSAGE.reasons}
                  </p>
                </div>
              </details>
            </div>
          </article>
        ))}
      </section>
    </main>
  );
}