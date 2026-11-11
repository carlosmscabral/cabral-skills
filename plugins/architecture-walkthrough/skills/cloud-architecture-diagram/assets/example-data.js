/*
 * The data shape, as a working example: a photo-upload API on Cloud Run that
 * calls a model, stores the result, and reports what it did.
 *
 * Every coordinate is in the SVG's own units and is placed by hand. Read
 * references/layout-rules.md before you move any of them: the corridor
 * between the middle and right columns holds six vertical lanes, and two
 * connectors may share a lane only when their vertical spans do not overlap.
 *
 * Icons come from scripts/fetch-gcp-icons.sh and are referenced by name.
 */

const DIAGRAM = {
  title: "Photo API · reference architecture",
  theme: "light",
  notice: "Illustrative architecture — configuration values are examples, not production measurements.",
  legend: ["Solid: main request", "Dashed: secondary operations", "Tinted groups: functional concerns"],
  viewBox: [1025, 640],
  outsideLabel: "OUTSIDE",
  cloud: { x: 312, y: 24, w: 690, h: 596, icon: "google-cloud", label: "Google Cloud · us-central1" }
};

/* Actors. Outside the cloud boundary, line-art glyph, never a product icon. */
const OUTSIDE = [
  {
    id: "user", x: 16, y: 60, w: 210, h: 84, glyph: "person",
    title: "Person", sub: "on the web",
    what: "Uploads one photograph and waits for the result. No account, no sign-in."
  },
  {
    id: "browser", x: 16, y: 180, w: 210, h: 150, glyph: "browser",
    title: "Browser", sub: "single page app",
    rows: ["Crops before upload", "Shows the result inline"],
    what: "Crops the photograph in the page before sending it, so the request that leaves the device is already small."
  },
  {
    id: "operator", x: 16, y: 430, w: 210, h: 84, glyph: "person",
    title: "Operator", sub: "authorised account",
    what: "Reads the logs and clears a stuck job. Reaches the service through the identity proxy, never anonymously."
  }
];

/* One group per environment or concern. `dash` means it is not part of the
 * running system: build pipelines, registries, CI. */
const GROUPS = [
  { id: "g-api", x: 332, y: 60, w: 250, h: 250, title: "Public API", tone: "blue" },
  { id: "g-ops", x: 332, y: 400, w: 250, h: 160, title: "Operations", tone: "red" },
  { id: "g-model", x: 650, y: 60, w: 326, h: 130, title: "Vertex AI", tone: "yellow" },
  { id: "g-data", x: 650, y: 230, w: 326, h: 200, title: "Data", tone: "green" },
  { id: "g-obs", x: 650, y: 470, w: 326, h: 90, title: "Observability", tone: "grey" }
];

/* Product cards. `sub` is one line of real configuration, in monospace. */
const CARDS = [
  {
    id: "gate", group: "g-api", x: 346, y: 100, w: 222, h: 44, icon: null,
    title: "Admission control", sub: "2 in flight, then 503",
    what: "A counter on the route that calls the model. Past two concurrent jobs it answers 503 with Retry-After."
  },
  {
    id: "api", group: "g-api", x: 346, y: 166, w: 222, h: 52, icon: "cloud-run",
    title: "photo-api", sub: "Cloud Run · public",
    what: "Serves the page, calls the model, writes to the bucket, and returns the result as base64."
  },
  {
    id: "media", group: "g-api", x: 346, y: 246, w: 222, h: 44, icon: null,
    title: "Media proxy", sub: "GET /media",
    what: "The only door into the bucket. Serves one prefix, always as PNG, and never the uploads."
  },
  {
    id: "iap", group: "g-ops", x: 346, y: 440, w: 222, h: 40, icon: "identity-aware-proxy",
    title: "Identity-Aware Proxy", sub: "no anonymous access",
    what: "Authenticates whoever reaches the operator surface and writes the identity header the server trusts."
  },
  {
    id: "admin", group: "g-ops", x: 346, y: 496, w: 222, h: 52, icon: "cloud-run",
    title: "photo-admin", sub: "Cloud Run · behind IAP",
    what: "The same image with one environment variable flipped. The public service answers 404 on every route this one serves."
  },
  {
    id: "model", group: "g-model", x: 664, y: 98, w: 298, h: 52, icon: "vertexai",
    title: "Image model", sub: "1 call per upload",
    what: "One call per photograph, with a 60 second timeout and a fallback model behind it."
  },
  {
    id: "bucket", group: "g-data", x: 664, y: 268, w: 298, h: 52, icon: "cloud-storage",
    title: "Cloud Storage", sub: "private · 30 day lifecycle",
    what: "Holds the upload and the result under separate prefixes. Public access is prevented at the bucket."
  },
  {
    id: "db", group: "g-data", x: 664, y: 340, w: 298, h: 52, icon: "firestore",
    title: "Firestore", sub: "2 collections",
    what: "One document per job, and one per published result. Nothing in here is served to the internet directly."
  },
  {
    id: "logs", group: "g-obs", x: 664, y: 500, w: 298, h: 44, icon: "cloud-logging",
    title: "Cloud Logging", sub: "one report per job",
    what: "Each job writes the time of every stage, so a slow request names the stage that was slow."
  }
];

/*
 * Connectors. `n` numbers the request path; an edge without `n` is a side
 * path and is drawn dashed. `pts` are absolute and the arrow lands on the
 * last one. `disc` and the label position are explicit, because every
 * automatic placement collided with a lane in this corridor.
 */
const EDGES = [
  { id: "e1", n: "1", from: "user", to: "browser",
    pts: [[121, 144], [121, 180]], disc: [121, 162],
    label: "uploads", lx: 133, ly: 166, anchor: "start" },

  { id: "e2", n: "2", from: "browser", to: "gate",
    pts: [[226, 202], [244, 202], [244, 122], [346, 122]], disc: [244, 150],
    label: "POST /photo", lx: 304, ly: 115, anchor: "middle" },

  { id: "e3", n: "3", from: "gate", to: "api",
    pts: [[457, 144], [457, 166]], disc: [457, 155] },

  { id: "e4", n: "4", from: "api", to: "model",
    pts: [[568, 178], [630, 178], [630, 124], [664, 124]], disc: [630, 151] },

  /* No label: the corridor is 96 px and the disc takes 18 of them, so
   * "upload + result" would have run under the Cloud Storage card. The
   * slide's own line says it instead. */
  { id: "e5", n: "5", from: "api", to: "bucket",
    pts: [[568, 194], [606, 194], [606, 284], [664, 284]], disc: [606, 239] },

  { id: "e6", n: "6", from: "api", to: "db",
    pts: [[568, 206], [594, 206], [594, 366], [664, 366]], disc: [594, 286] },

  { id: "e7", n: "7", from: "api", to: "logs",
    pts: [[568, 214], [582, 214], [582, 522], [664, 522]], disc: [582, 368] },

  { id: "e8", n: "8", from: "api", to: "browser",
    pts: [[346, 198], [302, 198], [302, 280], [226, 280]], disc: [302, 240],
    label: "result", lx: 262, ly: 271, anchor: "middle" },

  { id: "s1", from: "media", to: "bucket", dash: true,
    pts: [[568, 268], [618, 268], [618, 306], [664, 306]] },

  { id: "s2", from: "operator", to: "iap", dash: true,
    pts: [[226, 472], [286, 472], [286, 460], [346, 460]],
    label: "console", lx: 232, ly: 465, anchor: "start" },

  { id: "s3", from: "iap", to: "admin", dash: true,
    pts: [[457, 480], [457, 496]] },

  { id: "s4", from: "admin", to: "logs", dash: true,
    pts: [[568, 522], [664, 522]] }
];

/*
 * The slideshow. A slide is a number, a title and one line of about 25 words.
 * It names what it lights; the zoom is computed from that list, so adding a
 * step costs one entry and no coordinates. A slide that lights nothing shows
 * the whole drawing undimmed.
 */
const SLIDES = [
  {
    title: "One photograph in, one picture out",
    notes: "Illustrative reference only. Verify authentication, deployment locations, model configuration and retention against the target application's sources before adapting this drawing.",
    line: "Eight steps, from the upload leaving the browser to the result coming back.",
    edges: [], units: []
  },
  {
    n: "1", tone: "blue", title: "Someone uploads",
    line: "The browser crops the photograph before sending, so the request that leaves the device is already small.",
    facts: [["Sign-in", "none"], ["Cropped", "in the page"]],
    edges: ["e1"], units: ["user", "browser"]
  },
  {
    n: "2", tone: "blue", title: "The request arrives",
    line: "One POST carries the cropped photograph to the public service.",
    facts: [["Route", "POST /photo"], ["Body cap", "8 MB"]],
    edges: ["e2"], units: ["browser", "gate"]
  },
  {
    n: "3", tone: "red", title: "The queue guard",
    line: "Two jobs in flight per instance. Past that it is 503 with Retry-After.",
    facts: [["Limit", "2 per instance"], ["Answer", "503 + Retry-After"]],
    edges: ["e3"], units: ["gate", "api"]
  },
  {
    n: "4", tone: "yellow", title: "The model runs",
    line: "One call per photograph, with a sixty second timeout and a fallback behind it.",
    facts: [["Calls", "1"], ["Timeout", "60 s"]],
    edges: ["e4"], units: ["api", "model"]
  },
  {
    n: "5", tone: "green", title: "The files land",
    line: "The upload and the result go to separate prefixes in a private bucket.",
    facts: [["Public access", "prevented"], ["Lifecycle", "30 days"]],
    edges: ["e5"], units: ["api", "bucket"]
  },
  {
    n: "6", tone: "green", title: "The job is recorded",
    line: "One document per job, which is what ties the result to the person who asked for it.",
    facts: [["Collections", "2"]],
    edges: ["e6"], units: ["api", "db"]
  },
  {
    n: "7", tone: "grey", title: "It says what it did",
    line: "Each job writes the time of every stage, so a slow request names the stage that was slow.",
    facts: [["Per job", "1 report"], ["Stages", "4"]],
    edges: ["e7"], units: ["api", "logs"]
  },
  {
    n: "8", tone: "blue", title: "The result comes back",
    line: "The picture returns inline and the browser shows it without a second round trip.",
    facts: [["Round trips", "1"]],
    edges: ["e8"], units: ["api", "browser"]
  },
  {
    n: "·", tone: "grey", title: "Off the request path",
    line: "The media proxy reads the bucket, and the operator reaches the admin surface through the identity proxy.",
    facts: [["Anonymous admin", "no"], ["Bucket doors", "1"]],
    edges: ["s1", "s2", "s3", "s4"], units: ["media", "bucket", "operator", "iap", "admin", "logs"]
  },
  /* Lights nothing, so the whole drawing comes back undimmed. The closing
   * slide shows the same picture the opening one did, now that the reader
   * knows what is in it, and carries the numbers worth leaving them with. */
  {
    title: "The whole application",
    line: "One public request path, private data, and a separate operator surface. Validate the example configuration before using it.",
    notes: "No production cost or latency measurements are supplied. Replace illustrative configuration with sourced evidence for your application.",
    edges: [], units: []
  }
];
