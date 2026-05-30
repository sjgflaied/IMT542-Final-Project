<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Improving the SAMHSA Mental Health Data Structure</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Fraunces:opsz,wght@9..144,400;9..144,500;9..144,700;9..144,900&family=JetBrains+Mono:wght@400;500&family=Inter+Tight:wght@400;500;600&display=swap" rel="stylesheet">
<style>
  :root {
    --ink: #14181f;
    --paper: #f6f2ea;
    --paper-2: #ede7da;
    --rule: #1a1f28;
    --accent: #b03a2e;
    --accent-soft: #d97757;
    --muted: #5a6473;
    --good: #2f6b4f;
  }
  * { box-sizing: border-box; }
  html, body { margin: 0; padding: 0; }
  body {
    font-family: 'Inter Tight', system-ui, sans-serif;
    background: var(--paper);
    color: var(--ink);
    font-size: 16.5px;
    line-height: 1.55;
    -webkit-font-smoothing: antialiased;
  }

  /* Masthead */
  .masthead {
    border-bottom: 3px double var(--rule);
    padding: 28px 48px 16px;
    background: var(--paper);
  }
  .masthead-top {
    display: flex;
    justify-content: space-between;
    align-items: baseline;
    font-family: 'JetBrains Mono', monospace;
    font-size: 11px;
    letter-spacing: 0.14em;
    text-transform: uppercase;
    color: var(--muted);
  }
  .masthead-top .dot {
    display: inline-block;
    width: 7px; height: 7px;
    background: var(--accent);
    border-radius: 50%;
    margin-right: 6px;
    vertical-align: middle;
  }
  h1.title {
    font-family: 'Fraunces', serif;
    font-weight: 900;
    font-size: clamp(38px, 5.2vw, 64px);
    line-height: 0.95;
    letter-spacing: -0.02em;
    margin: 14px 0 8px;
    font-variation-settings: "opsz" 144;
  }
  h1.title em {
    font-style: italic;
    font-weight: 400;
    color: var(--accent);
  }
  .subtitle {
    font-family: 'Fraunces', serif;
    font-weight: 400;
    font-style: italic;
    font-size: 19px;
    color: var(--muted);
    margin: 0 0 6px;
    max-width: 760px;
  }

  /* Layout */
  .wrap {
    max-width: 1180px;
    margin: 0 auto;
    padding: 40px 48px 80px;
  }

  /* Project block */
  .project {
    display: grid;
    grid-template-columns: 220px 1fr;
    gap: 36px;
    padding: 22px 0 32px;
    border-bottom: 1px solid var(--rule);
  }
  .project .label {
    font-family: 'JetBrains Mono', monospace;
    font-size: 11px;
    letter-spacing: 0.16em;
    text-transform: uppercase;
    color: var(--muted);
    padding-top: 5px;
  }
  .project p { margin: 0 0 12px; }
  .stages {
    margin: 14px 0 0;
    padding: 0;
    list-style: none;
    counter-reset: stage;
  }
  .stages li {
    counter-increment: stage;
    position: relative;
    padding: 10px 0 10px 46px;
    border-top: 1px solid var(--paper-2);
  }
  .stages li:first-child { border-top: 0; }
  .stages li::before {
    content: counter(stage, decimal-leading-zero);
    position: absolute;
    left: 0; top: 11px;
    font-family: 'Fraunces', serif;
    font-weight: 900;
    font-size: 22px;
    color: var(--accent);
    letter-spacing: -0.02em;
  }

  /* Section headers */
  .section {
    margin-top: 56px;
  }
  .section-tag {
    display: inline-block;
    font-family: 'JetBrains Mono', monospace;
    font-size: 10.5px;
    letter-spacing: 0.18em;
    text-transform: uppercase;
    color: var(--paper);
    background: var(--ink);
    padding: 4px 9px;
    margin-bottom: 14px;
  }
  h2 {
    font-family: 'Fraunces', serif;
    font-weight: 700;
    font-size: clamp(28px, 3.4vw, 40px);
    line-height: 1.05;
    letter-spacing: -0.015em;
    margin: 0 0 8px;
    max-width: 880px;
  }
  h2 .num {
    font-style: italic;
    font-weight: 400;
    color: var(--accent);
    margin-right: 10px;
  }
  .deck {
    font-family: 'Fraunces', serif;
    font-style: italic;
    color: var(--muted);
    max-width: 760px;
    margin: 0 0 28px;
    font-size: 17.5px;
  }

  /* Comparison cards */
  .compare {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 22px;
    margin-top: 18px;
  }
  .card {
    border: 1px solid var(--rule);
    padding: 22px 24px 24px;
    background: var(--paper);
    position: relative;
  }
  .card.new { background: var(--paper-2); }
  .card-hdr {
    display: flex;
    align-items: center;
    gap: 10px;
    font-family: 'JetBrains Mono', monospace;
    font-size: 10.5px;
    letter-spacing: 0.16em;
    text-transform: uppercase;
    color: var(--muted);
    margin-bottom: 8px;
  }
  .card-hdr .pill {
    background: var(--ink);
    color: var(--paper);
    padding: 2px 7px;
    letter-spacing: 0.14em;
  }
  .card.new .card-hdr .pill {
    background: var(--accent);
  }
  .card h3 {
    font-family: 'Fraunces', serif;
    font-weight: 700;
    font-size: 22px;
    margin: 0 0 14px;
    line-height: 1.15;
  }
  .card ul {
    margin: 10px 0 0;
    padding: 0;
    list-style: none;
  }
  .card li {
    padding: 9px 0 9px 22px;
    border-top: 1px dashed rgba(20,24,31,0.18);
    position: relative;
    font-size: 15px;
  }
  .card li:first-child { border-top: 0; padding-top: 4px; }
  .card.old li::before {
    content: "✕";
    position: absolute; left: 0; top: 9px;
    color: var(--accent);
    font-size: 13px;
  }
  .card.new li::before {
    content: "→";
    position: absolute; left: 0; top: 8px;
    color: var(--good);
    font-weight: 600;
  }
  .card.old li:first-child::before { top: 4px; }
  .card.new li:first-child::before { top: 3px; }
  code, .mono {
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.86em;
    background: rgba(20,24,31,0.06);
    padding: 1px 5px;
    border-radius: 2px;
  }
  .card.new code { background: rgba(20,24,31,0.08); }

  /* Footer */
  footer {
    margin-top: 72px;
    padding-top: 18px;
    border-top: 3px double var(--rule);
    font-family: 'JetBrains Mono', monospace;
    font-size: 11px;
    letter-spacing: 0.14em;
    text-transform: uppercase;
    color: var(--muted);
    display: flex;
    justify-content: space-between;
  }

  @media (max-width: 820px) {
    .masthead { padding: 22px 22px 14px; }
    .wrap { padding: 28px 22px 60px; }
    .project { grid-template-columns: 1fr; gap: 8px; }
    .compare { grid-template-columns: 1fr; }
  }
</style>
</head>
<body>

<header class="masthead">
  <div class="masthead-top">
    <div><span class="dot"></span>Group Project · Information Structure Redesign</div>
    <div>INFO 200 / SP 26 · Submission Draft</div>
  </div>
  <h1 class="title">From an annual file<br>to a <em>living</em> risk record.</h1>
  <p class="subtitle">Replacing SAMHSA's MH-CLD flat CSV with a typed, provenance-bearing, tiered-access structure for community mental health risk.</p>
</header>

<main class="wrap">

  <!-- Project overview -->
  <section class="project">
    <div class="label">Project<br>Overview</div>
    <div>
      <p>This project rebuilds how SAMHSA-derived mental health data is delivered to local public-health responders. The existing platform — the Mental Health Client-Level Data (MH-CLD) release — ships once a year as a single flat CSV in which every field is a numeric code that has to be decoded against a separate PDF. Our redesign turns this into a continuously updated stream of typed, validated risk records keyed by ZIP code and ISO week.</p>
      <p><strong>The system works in three stages:</strong></p>
      <ol class="stages">
        <li>Ingests SAMHSA MH-CLD releases, CDC PLACES, and ACS demographic data through validated source adapters.</li>
        <li>Computes a weekly per-ZIP risk score through a versioned model, attaching provenance and quality flags to every record.</li>
        <li>Serves results through a two-tier API — open public risk scores and authenticated dispatch-log access for credentialed responders.</li>
      </ol>
    </div>
  </section>

  <!-- Section 1: Data Quality -->
  <section class="section">
    <span class="section-tag">Part One · Data Quality</span>
    <h2><span class="num">01.</span>How our structure makes maintaining and measuring quality easier</h2>
    <p class="deck">Bad data should be caught at the boundary, not discovered months later. Our schema enforces three checks the existing MH-CLD format cannot.</p>

    <div class="compare">
      <div class="card old">
        <div class="card-hdr"><span class="pill">Existing</span> MH-CLD CSV</div>
        <h3>Codes in, no validation, ambiguous gaps</h3>
        <ul>
          <li>Every field is an opaque integer (<code>MH1=6</code>, <code>RACE=5</code>) requiring an external codebook to interpret — drift between code and PDF goes undetected.</li>
          <li>Missing values, refusals, and "not applicable" all collapse to the same sentinel (<code>-9</code>), so completeness cannot be measured by reason.</li>
          <li>No primary key beyond <code>CASEID</code> and no expected record count — there is no way to verify the file is whole.</li>
          <li>Released annually with a ~2-year lag, so quality issues surface long after the source data was generated.</li>
        </ul>
      </div>

      <div class="card new">
        <div class="card-hdr"><span class="pill">New</span> ZIP-Week Risk Record</div>
        <h3>Typed fields, known cardinality, per-record provenance</h3>
        <ul>
          <li>Every field is typed and bounded: <code>riskScore</code> must fall within <code>[0.0, 1.0]</code> and <code>riskTier</code> must be one of four enum values — invalid records are rejected at ingestion.</li>
          <li>Composite key <code>zipCode + isoWeek</code> defines an expected record count (≈42,000 ZIPs × 52 weeks). Missing rows are detectable; nothing hides in the gaps.</li>
          <li>Each record carries <code>metadata.modelVersion</code>, <code>sourceProvenance</code>, and a <code>qualityFlags</code> block (<code>completenessCheck</code>, <code>rangeCheck</code>, <code>schemaValidation</code>) — so a bad value can be traced to the model run and source fetch that produced it.</li>
          <li>Weekly cadence means quality regressions show up within seven days, not two years.</li>
        </ul>
      </div>
    </div>
  </section>

  <!-- Section 2: Information Security -->
  <section class="section">
    <span class="section-tag">Part Two · Information Security</span>
    <h2><span class="num">02.</span>How our structure surfaces and manages security issues over time</h2>
    <p class="deck">The existing release protects privacy by destroying local detail. Our schema protects privacy by classifying every field and gating access at the record level.</p>

    <div class="compare">
      <div class="card old">
        <div class="card-hdr"><span class="pill">Existing</span> MH-CLD CSV</div>
        <h3>One file, one access level, geography sacrificed</h3>
        <ul>
          <li>Single public download with no authentication tier — you either get the whole file or nothing, so sensitivity must be handled by stripping data before release.</li>
          <li>To protect re-identification, <code>STATEFIP</code> is the finest geography retained; ZIP, county, and tract are removed entirely, making the file unusable for local intervention.</li>
          <li>No field-level classification — there is no way to mark which variables are sensitive, so risk is managed only by exclusion.</li>
          <li>No access logging at the record level; if a re-identification incident occurred, there is no way to scope which downloads were affected.</li>
        </ul>
      </div>

      <div class="card new">
        <div class="card-hdr"><span class="pill">New</span> Tiered Access Schema</div>
        <h3>Field-level classification, gated access, audit by design</h3>
        <ul>
          <li><code>metadata.dataClassification</code> labels every record as <code>public</code> or <code>restricted</code>, making sensitivity an enforceable schema property rather than an editorial decision.</li>
          <li>Aggregated <code>riskAssessment</code> and <code>publicIndicators</code> are open at ZIP-week granularity; raw dispatch logs live under <code>sensitiveDataReference</code> behind <code>accessControl.authRequired = true</code> with role-based claims (<code>clinician</code>, <code>public_health_analyst</code>, <code>auditor</code>).</li>
          <li>Because access is mediated by an authenticated API rather than a bulk download, <code>accessControl.auditLogged = true</code> guarantees every fetch is attributable — incident scoping becomes a query, not an investigation.</li>
          <li>Local geographic resolution is preserved (ZIP code) without exposing individuals, so public-health responders can act on neighborhood-level signals that MH-CLD's state aggregates cannot support.</li>
        </ul>
      </div>
    </div>
  </section>

  <footer>
    <div>SAMHSA · MH-CLD Redesign</div>
    <div>v1.0 · Draft for class feedback</div>
  </footer>

</main>
</body>
</html>
