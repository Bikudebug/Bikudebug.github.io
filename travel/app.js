/* Nagoya Journey PWA — HYD → International Residence Daiko */
"use strict";

/* ---------------- Waypoints (lng, lat) ---------------- */
const WAYPOINTS = [
  { id: "hyd",  name: "Hyderabad HYD",            lngLat: [78.4294, 17.2403],  kind: "air" },
  { id: "sin",  name: "Singapore Changi SIN",     lngLat: [103.9915, 1.3644],  kind: "air" },
  { id: "kix",  name: "Kansai Airport KIX",       lngLat: [135.2440, 34.4342], kind: "air" },
  { id: "shin", name: "Shin-Osaka Station",       lngLat: [135.5002, 34.7335], kind: "rail" },
  { id: "ngo",  name: "Nagoya Station",           lngLat: [136.8816, 35.1709], kind: "rail" },
  { id: "dyd",  name: "Nagoya Dome-mae Yada Stn", lngLat: [136.9438, 35.1852], kind: "rail" },
  { id: "dko",  name: "Int'l Residence Daiko 🏠", lngLat: [136.9351, 35.1790], kind: "home" },
];

/* Flight legs get a great-circle arc; ground legs a straight line.
   Nagoya Station → Dome-mae Yada is drawn as the real subway lines below. */
const FLIGHT_LEGS = [["hyd", "sin"], ["sin", "kix"]];
const GROUND_LEGS = [["kix", "shin"], ["shin", "ngo"], ["dyd", "dko"]];

/* Nagoya subway — both dorm routes, in the official line colours.
   Plan A: Sakura-dōri Line (red) to Hisaya-ōdōri, then Meijō Line (purple).
   Plan B: Higashiyama Line (yellow) to Sakae, then the same Meijō Line.
   The purple polyline covers both: Sakae → Hisaya-ōdōri → clockwise → Dome-mae Yada. */
const SUBWAY_LINES = [
  { id: "sakuradori", color: "#dc2626", coords: [ // Nagoya → Kokusai Center → Marunouchi → Hisaya-ōdōri
    [136.8816, 35.1709], [136.8919, 35.1731], [136.8993, 35.1747], [136.9082, 35.1734]] },
  { id: "higashiyama", color: "#eab308", coords: [ // Nagoya → Fushimi → Sakae
    [136.8816, 35.1709], [136.8983, 35.1682], [136.9077, 35.1699]] },
  { id: "meijo", color: "#9333ea", coords: [ // Sakae → Hisaya-ōdōri → Shiyakusho → Meijō Kōen → Kurokawa → Shiga-hondōri → Heian-dōri → Ōzone → Dome-mae Yada
    [136.9077, 35.1699], [136.9082, 35.1734], [136.9066, 35.1812], [136.9072, 35.1898],
    [136.9105, 35.1943], [136.9168, 35.1950], [136.9243, 35.1943], [136.9375, 35.1907],
    [136.9438, 35.1852]] },
];

/* Transfer stations get their own tap-for-info markers */
const TRANSFERS = [
  { lngLat: [136.9082, 35.1734], name: "Hisaya-ōdōri 久屋大通",
    cap: "PLAN A transfer: get off the red Sakura-dōri Line here and switch to the purple Meijō Line — clockwise / “Nagoya Dome-mae Yada” direction (~15 min)." },
  { lngLat: [136.9077, 35.1699], name: "Sakae 栄",
    cap: "PLAN B transfer: get off the yellow Higashiyama Line here and switch to the purple Meijō Line — clockwise / “Nagoya Dome-mae Yada” direction (~12 min)." },
];

/* ---------------- Timeline (times carry their own UTC offset) ---------------- */
const STEPS = [
  {
    id: "docs", when: "Before you leave", ts: "2026-09-24T18:00:00+05:30", warn: true,
    title: "Student-fare paperwork (protects your 40 kg)",
    desc: "Email passport + student visa to student.documents@makemytrip.com. Pack in hand: passport, visa, university acceptance letter, admission docs. Show them at HYD check-in or the 40 kg student baggage can be refused. Enrol in KrisFlyer for free extra benefits.",
  },
  {
    id: "hyd-imm", when: "Thu 24 Sep · ~20:30 IST", ts: "2026-09-24T20:30:00+05:30", warn: true,
    title: "🛂 INDIAN IMMIGRATION — at Hyderabad airport",
    desc: "This is the ONLY immigration on the Indian side. After check-in and security, go to the Immigration counters with your passport + Japan visa + boarding pass. Officer may ask purpose: say “PhD student at Nagoya University” and show the admission letter if asked. You get an Indian EXIT stamp. Nothing to do in Singapore.",
  },
  {
    id: "dep-hyd", when: "Thu 24 Sep · 23:15 IST", ts: "2026-09-24T23:15:00+05:30",
    title: "Depart Hyderabad — SQ 523, seat 43A",
    desc: "Rajiv Gandhi Intl. PNR E7T7RU · e-ticket 2481322049. Cabin bag max 7 kg (1 piece).",
  },
  {
    id: "arr-sin", when: "Fri 25 Sep · 06:40 SGT", ts: "2026-09-25T06:40:00+08:00",
    title: "Arrive Singapore Changi — 7h 30m layover (NO immigration here)",
    desc: "TRANSIT only — you stay airside, no Singapore immigration, no visa needed. You change planes AND terminals — departure is Terminal 2. Free rest areas + showers in transit; Jewel is landside, skip it unless you're sure.",
  },
  {
    id: "dep-sin", when: "Fri 25 Sep · 14:10 SGT", ts: "2026-09-25T14:10:00+08:00",
    title: "Depart Singapore — SQ 622, seat 45A (Terminal 2)",
    desc: "6h 25m to Osaka.",
  },
  {
    id: "arr-kix", when: "Fri 25 Sep · 21:35 JST", ts: "2026-09-25T21:35:00+09:00", warn: true,
    title: "🛂 JAPAN IMMIGRATION — at Kansai KIX, Terminal 1",
    desc: "On the plane, fill the disembarkation card + customs form they hand out. At the counter: passport + student visa. Photo + fingerprints are taken, and they PRINT YOUR RESIDENCE CARD on the spot — before walking away, check the name, date of birth and status “Student” on it. This card is your ID in Japan; you need it Monday at the ward office. Then baggage claim (both bags) → customs (hand the form).",
  },
  {
    id: "hotel", when: "Fri 25 Sep · night", ts: "2026-09-25T22:30:00+09:00",
    title: "Walk indoors to Aeroplaza → First Cabin KIX",
    desc: "Covered walkway from Terminal 1 to Aeroplaza (~5 min). Check in to the capsule hotel and sleep.",
  },
  {
    id: "jr", when: "Sat 26 Sep · 10:00 JST", ts: "2026-09-26T10:00:00+09:00", warn: true, confirm: true,
    title: "KIX JR Ticket Office — buy Haruka + Shinkansen (Niyo card)",
    desc: "ASK FOR: “Seat with an Oversized Baggage Area” for the HRX bag (164.5 cm > 160 cm limit). Without it: ¥1,000 penalty. Buy the combined Haruka + Shinkansen ticket.",
  },
  {
    id: "haruka", when: "Sat 26 Sep · morning", ts: "2026-09-26T10:45:00+09:00",
    title: "JR Haruka: KIX → Shin-Osaka (~50 min)",
    desc: "Free luggage racks on board. Get off at Shin-Osaka, NOT Osaka Station.",
  },
  {
    id: "shink", when: "Sat 26 Sep · midday", ts: "2026-09-26T12:00:00+09:00",
    title: "Tokaido Shinkansen: Shin-Osaka → Nagoya (~50 min)",
    desc: "Use your reserved oversized-baggage seat; the bag space is behind the last row of your car.",
  },
  {
    id: "last-leg", when: "Sat 26 Sep · afternoon", ts: "2026-09-26T13:15:00+09:00",
    title: "Nagoya Station → dormitory (subway 430–470 JPY, or taxi)",
    desc: "With 2 big bags a taxi is easiest (~20 min, show the Taxi Card below). Subway: PLAN A — red Sakura-dōri Line (toward Tokushige) ~5 min to Hisaya-ōdōri, change to purple Meijō Line (clockwise / “Nagoya Dome-mae Yada”) ~15 min. PLAN B — yellow Higashiyama Line ~5 min to Sakae, change to the same purple Meijō Line ~12 min. Both get off at Nagoya Dome-mae Yada → elevator to Entrance 1 → turn right at the corner → walk straight ~3 min. Full details in the 🚇 card below; tap 🚇 Metro on the map to see both routes drawn.",
  },
  {
    id: "movein", when: "Sat 26 Sep · 14:00–19:00 JST", ts: "2026-09-26T14:00:00+09:00",
    title: "Move in — International Residence Daiko 🎉 (Room 333)",
    desc: "1-1-18 Daiko-Minami, Higashi-ku. Move-in reception 14:00–19:00 only (weekends OK). Note: visitors are not allowed inside, not even family.",
  },
  {
    id: "big-monday", when: "Mon 28 Sep · from 08:45 JST", ts: "2026-09-28T08:45:00+09:00", warn: true,
    title: "THE BIG MONDAY — ward office, orientation 10:30, bank account",
    desc: "08:45 Higashi Ward Office (1-7-74 Tsutsui): register address, get it written on your residence card. 10:30 NEW-STUDENT ORIENTATION at the Graduate School of Informatics (strongly encouraged — be there). Then: collect the 'Certificate of Admission' from Student Affairs (NOT the acceptance letter), and do the Yucho bank app at the support session, International Center 2F Rm 206, 13:00–16:00. Today is the JASSO bank-application deadline. Hand over your packet originals if you carried them.",
  },
];

/* ---------------- Vault slots ---------------- */
const VAULT_SLOTS = [
  { id: "passport", name: "Passport" },
  { id: "visa", name: "Visa" },
  { id: "coe", name: "COE (Certificate of Eligibility)" },
  { id: "aadhaar", name: "Aadhaar card" },
  { id: "admission", name: "Japan Admission", special: true },
  { id: "accommodation", name: "Accommodation (dorm)" },
  { id: "residence-email", name: "Residence email PDF" },
  { id: "eticket", name: "Flight e-ticket" },
  { id: "niyo", name: "Niyo card details" },
  { id: "kix-hotel", name: "Hotel booking (KIX airport, 25 Sep)" },
  { id: "extra1", name: "Extra slot 1" },
  { id: "extra2", name: "Extra slot 2" },
];

/* ================= Password gate =================
   SHA-256 hash only — the password itself is not in this public file. */
const PW_HASH = "14a254676e12e20d3295ae0e779643dda94e989a6234328f4c062b78f6dd97cb";
async function sha256hex(s) {
  const buf = await crypto.subtle.digest("SHA-256", new TextEncoder().encode(s));
  return [...new Uint8Array(buf)].map(b => b.toString(16).padStart(2, "0")).join("");
}
(function initLock() {
  const overlay = document.getElementById("lock");
  const input = document.getElementById("lock-pw");
  const err = document.getElementById("lock-err");
  if (sessionStorage.getItem("unlocked") === "1") { overlay.hidden = true; return; }
  async function tryUnlock() {
    if ((await sha256hex(input.value)) === PW_HASH) {
      sessionStorage.setItem("unlocked", "1");
      overlay.hidden = true;
    } else {
      err.hidden = false;
      input.value = "";
    }
  }
  document.getElementById("lock-btn").addEventListener("click", tryUnlock);
  input.addEventListener("keydown", e => { if (e.key === "Enter") tryUnlock(); });
  input.focus();
})();

/* ================= Clocks & countdown ================= */
function fmtTZ(offsetMin) {
  const now = new Date(Date.now() + (offsetMin + new Date().getTimezoneOffset()) * 60000);
  return now.toTimeString().slice(0, 8);
}
function tickClocks() {
  document.getElementById("clock-ist").textContent = fmtTZ(330);
  document.getElementById("clock-jst").textContent = fmtTZ(540);
  const next = STEPS.find(s => !isDone(s.id) && new Date(s.ts) > new Date());
  const el = document.getElementById("countdown");
  if (!next) {
    const pending = STEPS.find(s => !isDone(s.id));
    el.innerHTML = pending ? `next: ${pending.title.split("—")[0]}` : "🎉 journey complete!";
    return;
  }
  let ms = new Date(next.ts) - new Date();
  const h = Math.floor(ms / 3600000); ms -= h * 3600000;
  const m = Math.floor(ms / 60000); ms -= m * 60000;
  const s = Math.floor(ms / 1000);
  const pad = n => String(n).padStart(2, "0");
  el.innerHTML = `next: ${next.when}<strong>${h}h ${pad(m)}m ${pad(s)}s</strong>`;
}
setInterval(tickClocks, 1000);

/* ================= Timeline ================= */
const doneKey = id => `done:${id}`;
const isDone = id => localStorage.getItem(doneKey(id)) === "1";

function renderTimeline() {
  const ol = document.getElementById("timeline");
  ol.innerHTML = "";
  const nextId = (STEPS.find(s => !isDone(s.id)) || {}).id;
  STEPS.forEach((s, i) => {
    const li = document.createElement("li");
    li.className = "step" + (isDone(s.id) ? " done" : "") + (s.id === nextId ? " next" : "") + (s.warn ? " warnstep" : "");
    li.innerHTML = `
      <div class="step-box">✓</div>
      <div>
        <div class="step-when"><span class="step-num">STEP ${i + 1}/${STEPS.length}</span>${s.when}</div>
        <div class="step-title">${s.title}</div>
        <div class="step-desc">${s.desc}</div>
      </div>`;
    li.addEventListener("click", () => {
      if (!isDone(s.id) && s.confirm) {
        if (!window.confirm("Did you ask for the ‘Seat with an Oversized Baggage Area’ for the 164.5 cm HRX bag?")) return;
      }
      localStorage.setItem(doneKey(s.id), isDone(s.id) ? "0" : "1");
      renderTimeline();
    });
    ol.appendChild(li);
  });
}
renderTimeline();

/* after-arrival checkboxes */
document.querySelectorAll("[data-done]").forEach(cb => {
  cb.checked = localStorage.getItem(doneKey(cb.dataset.done)) === "1";
  cb.addEventListener("change", () => localStorage.setItem(doneKey(cb.dataset.done), cb.checked ? "1" : "0"));
});

/* ================= Taxi card ================= */
document.getElementById("btn-taxi").addEventListener("click", () => {
  document.getElementById("taxi-card").hidden = false;
});
document.getElementById("btn-taxi-close").addEventListener("click", () => {
  document.getElementById("taxi-card").hidden = true;
});

/* ================= Map ================= */
const byId = id => WAYPOINTS.find(w => w.id === id);

/* Photos shown when you tap a waypoint (Wikimedia Commons, cached for offline) */
const WM = "https://upload.wikimedia.org/wikipedia/commons/thumb";
const PHOTOS = {
  hyd:  { src: `${WM}/f/f6/Hyderabad_newairport.jpg/500px-Hyderabad_newairport.jpg`, cap: "Rajiv Gandhi Intl — departure terminal" },
  sin:  { src: `${WM}/e/e9/JewelSingaporeVortex1.jpg/500px-JewelSingaporeVortex1.jpg`, cap: "Changi's Jewel waterfall (landside — skip unless sure). You transit to Terminal 2." },
  kix:  { src: `${WM}/5/56/%E9%96%A2%E8%A5%BF%E5%9B%BD%E9%9A%9B%E7%A9%BA%E6%B8%AF%E5%85%A8%E4%BD%93%E5%86%99%E7%9C%9F20220811.jpg/500px-%E9%96%A2%E8%A5%BF%E5%9B%BD%E9%9A%9B%E7%A9%BA%E6%B8%AF%E5%85%A8%E4%BD%93%E5%86%99%E7%9C%9F20220811.jpg`, cap: "Kansai Airport — an island in Osaka Bay. First Cabin is in Aeroplaza, 5 min covered walk from T1." },
  shin: { src: `${WM}/f/f1/IBA-Shinosaka-panoramic-view-2020.jpg/500px-IBA-Shinosaka-panoramic-view-2020.jpg`, cap: "Shin-Osaka Station — switch Haruka → Shinkansen here (NOT Osaka Station)" },
  ngo:  { src: `${WM}/7/7c/View_of_Nagoya_Station%2C_Tsubaki-cho_Nakamura_Ward_Nagoya_2022.jpg/500px-View_of_Nagoya_Station%2C_Tsubaki-cho_Nakamura_Ward_Nagoya_2022.jpg`, cap: "Nagoya Station — the twin towers. Taxi rank is outside; show the taxi card." },
  dyd:  { src: `${WM}/7/7a/Yutorito_Line_Nagoya_Dome-mae_Yada_station.JPG/500px-Yutorito_Line_Nagoya_Dome-mae_Yada_station.JPG`, cap: "Nagoya Dome-mae Yada — your metro stop. Elevator to Entrance 1, turn right at the corner, straight ~3 min to the dorm." },
  dko:  { src: `${WM}/f/f4/Nagoya_Dome_-_3.jpg/500px-Nagoya_Dome_-_3.jpg`, cap: "Vantelin (Nagoya) Dome — the giant landmark right next to your dorm. Room 333 awaits 🎉" },
};

function greatCircle(a, b, n = 64) {
  // simple spherical interpolation between [lng,lat] points
  const rad = d => d * Math.PI / 180, deg = r => r * 180 / Math.PI;
  const [l1, p1] = [rad(a[0]), rad(a[1])], [l2, p2] = [rad(b[0]), rad(b[1])];
  const d = 2 * Math.asin(Math.sqrt(Math.sin((p2 - p1) / 2) ** 2 + Math.cos(p1) * Math.cos(p2) * Math.sin((l2 - l1) / 2) ** 2));
  const pts = [];
  for (let i = 0; i <= n; i++) {
    const f = i / n;
    const A = Math.sin((1 - f) * d) / Math.sin(d), B = Math.sin(f * d) / Math.sin(d);
    const x = A * Math.cos(p1) * Math.cos(l1) + B * Math.cos(p2) * Math.cos(l2);
    const y = A * Math.cos(p1) * Math.sin(l1) + B * Math.cos(p2) * Math.sin(l2);
    const z = A * Math.sin(p1) + B * Math.sin(p2);
    pts.push([deg(Math.atan2(y, x)), deg(Math.atan2(z, Math.sqrt(x * x + y * y)))]);
  }
  return pts;
}

/* Normal street map (with English+Japanese labels) and a satellite view */
const STREET_STYLE = "https://tiles.openfreemap.org/styles/bright";
const SAT_STYLE = {
  version: 8,
  sources: {
    sat: {
      type: "raster",
      tiles: ["https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}"],
      tileSize: 256,
      // Esri has no photos past ~z17 in many areas and returns grey
      // "Map data not yet available" tiles — cap the source so MapLibre
      // scales up the deepest real photo instead of requesting those
      maxzoom: 17,
      attribution: "Imagery © Esri, Maxar, Earthstar Geographics",
    },
  },
  layers: [{ id: "sat", type: "raster", source: "sat" }],
};

const map = new maplibregl.Map({
  container: "map",
  style: STREET_STYLE,
  center: [110, 22],
  zoom: 2.6,
  attributionControl: { compact: true },
});

const ROUTE_BOUNDS = WAYPOINTS.reduce(
  (b, w) => b.extend(w.lngLat),
  new maplibregl.LngLatBounds(WAYPOINTS[0].lngLat, WAYPOINTS[0].lngLat)
);

/* Re-applied every time the style changes (street ⇄ satellite) */
function styleReady() {
  // Bilingual labels: English (or romaji) on top, local Japanese underneath.
  // Skip when both are identical so non-Japanese places aren't printed twice.
  const en = ["coalesce", ["get", "name:en"], ["get", "name:latin"], ["get", "name"]];
  const bilingual = [
    "case",
    ["==", en, ["get", "name"]],
    ["get", "name"],
    ["format", en, {}, "\n", {}, ["get", "name"], { "font-scale": 0.85 }],
  ];
  for (const layer of map.getStyle().layers) {
    if (layer.type !== "symbol") continue;
    const tf = map.getLayoutProperty(layer.id, "text-field");
    if (tf && JSON.stringify(tf).includes("name")) {
      map.setLayoutProperty(layer.id, "text-field", bilingual);
    }
  }

  if (!map.getSource("flight")) {
    const flight = { type: "Feature", geometry: { type: "MultiLineString", coordinates: FLIGHT_LEGS.map(([a, b]) => greatCircle(byId(a).lngLat, byId(b).lngLat)) } };
    const ground = { type: "Feature", geometry: { type: "MultiLineString", coordinates: GROUND_LEGS.map(([a, b]) => [byId(a).lngLat, byId(b).lngLat]) } };
    map.addSource("flight", { type: "geojson", data: flight });
    map.addSource("ground", { type: "geojson", data: ground });
    map.addLayer({ id: "flight-line", type: "line", source: "flight", paint: { "line-color": "#2563eb", "line-width": 2.5, "line-dasharray": [1.5, 1.5] } });
    map.addLayer({ id: "ground-line", type: "line", source: "ground", paint: { "line-color": "#d97706", "line-width": 3 } });
    for (const l of SUBWAY_LINES) {
      map.addSource(l.id, { type: "geojson", data: { type: "Feature", geometry: { type: "LineString", coordinates: l.coords } } });
      map.addLayer({
        id: `${l.id}-line`, type: "line", source: l.id,
        layout: { "line-cap": "round", "line-join": "round" },
        paint: { "line-color": l.color, "line-width": 4, "line-opacity": 0.9 },
      });
    }
  }
}
map.on("style.load", styleReady);

/* Markers with photo popups — added once; they survive style switches */
for (const w of WAYPOINTS) {
  const el = document.createElement("div");
  el.textContent = w.kind === "air" ? "✈️" : w.kind === "home" ? "🏠" : "🚉";
  el.style.fontSize = "20px";
  const p = PHOTOS[w.id];
  const html = p
    ? `<div class="poi-pop"><img src="${p.src}" alt="${w.name}" loading="lazy"><div class="poi-name">${w.name}</div><div class="poi-cap">${p.cap}</div></div>`
    : `<div class="poi-pop"><div class="poi-name">${w.name}</div></div>`;
  new maplibregl.Marker({ element: el })
    .setLngLat(w.lngLat)
    .setPopup(new maplibregl.Popup({ offset: 18, maxWidth: "280px" }).setHTML(html))
    .addTo(map);
}

/* transfer-station markers (small, tap for which line to change to) */
for (const t of TRANSFERS) {
  const el = document.createElement("div");
  el.textContent = "🔄";
  el.style.fontSize = "15px";
  new maplibregl.Marker({ element: el })
    .setLngLat(t.lngLat)
    .setPopup(new maplibregl.Popup({ offset: 14, maxWidth: "260px" })
      .setHTML(`<div class="poi-pop"><div class="poi-name">${t.name}</div><div class="poi-cap">${t.cap}</div></div>`))
    .addTo(map);
}

map.on("load", () => map.fitBounds(ROUTE_BOUNDS, { padding: 60, duration: 0 }));

/* zoom to the Nagoya Station → dorm subway section */
document.getElementById("btn-metro").addEventListener("click", () =>
  map.fitBounds([[136.874, 35.161], [136.951, 35.201]], { padding: 40 })
);

/* ================= Live journey tracker + trip animation =================
   A pulsing marker moves along the drawn track in real time, following the
   booked schedule. ▶ Play trip animates the whole route in ~25 seconds. */
const fmtDur = ms => {
  ms = Math.max(0, ms);
  let h = Math.floor(ms / 3600000);
  const m = Math.floor((ms % 3600000) / 60000);
  if (h >= 24) { const d = Math.floor(h / 24); h %= 24; return `${d}d ${h}h ${String(m).padStart(2, "0")}m`; }
  return h ? `${h}h ${String(m).padStart(2, "0")}m` : `${m}m`;
};

const FLIGHTS = [
  { no: "SQ 523", seat: "43A", from: "Hyderabad HYD", to: "Singapore SIN",
    dep: "2026-09-24T23:15:00+05:30", arr: "2026-09-25T06:40:00+08:00",
    depLocal: "24 Sep 23:15 IST", arrLocal: "06:40 SGT",
    fr24: "https://www.flightradar24.com/data/flights/sq523" },
  { no: "SQ 622", seat: "45A", from: "Singapore SIN (T2)", to: "Osaka KIX",
    dep: "2026-09-25T14:10:00+08:00", arr: "2026-09-25T21:35:00+09:00",
    depLocal: "25 Sep 14:10 SGT", arrLocal: "21:35 JST",
    fr24: "https://www.flightradar24.com/data/flights/sq622" },
];

/* the drawn subway Plan A: red line to Hisaya-ōdōri, then purple to Dome-mae Yada */
const PLAN_A_PATH = [...SUBWAY_LINES[0].coords, ...SUBWAY_LINES[2].coords.slice(2)];

/* every stage of the trip: real start/end time, the path on the map,
   marker icon, camera zoom, and how long it lasts in the ▶ Play animation */
const SEG = (t0, t1, path, icon, label, z, pv) =>
  ({ t0: +new Date(t0), t1: +new Date(t1), path, icon, label, z, pv });
const SEGMENTS = [
  SEG("2026-09-24T23:15:00+05:30", "2026-09-25T06:40:00+08:00", greatCircle(byId("hyd").lngLat, byId("sin").lngLat), "✈️", "SQ 523 — flying to Singapore", 4, 6000),
  SEG("2026-09-25T06:40:00+08:00", "2026-09-25T14:10:00+08:00", [byId("sin").lngLat, byId("sin").lngLat], "🧳", "Changi layover — go to Terminal 2, rest (no immigration)", 9, 800),
  SEG("2026-09-25T14:10:00+08:00", "2026-09-25T21:35:00+09:00", greatCircle(byId("sin").lngLat, byId("kix").lngLat), "✈️", "SQ 622 — flying to Osaka KIX", 4, 6000),
  SEG("2026-09-25T21:35:00+09:00", "2026-09-26T10:45:00+09:00", [byId("kix").lngLat, byId("kix").lngLat], "🏨", "KIX — immigration, residence card, First Cabin hotel", 10, 800),
  SEG("2026-09-26T10:45:00+09:00", "2026-09-26T11:35:00+09:00", [byId("kix").lngLat, byId("shin").lngLat], "🚄", "JR Haruka — KIX → Shin-Osaka", 9, 2500),
  SEG("2026-09-26T11:35:00+09:00", "2026-09-26T12:00:00+09:00", [byId("shin").lngLat, byId("shin").lngLat], "🚉", "Shin-Osaka — change to the Shinkansen", 12, 600),
  SEG("2026-09-26T12:00:00+09:00", "2026-09-26T12:50:00+09:00", [byId("shin").lngLat, byId("ngo").lngLat], "🚄", "Tokaido Shinkansen — Shin-Osaka → Nagoya", 8, 2500),
  SEG("2026-09-26T12:50:00+09:00", "2026-09-26T13:15:00+09:00", [byId("ngo").lngLat, byId("ngo").lngLat], "🚉", "Nagoya Station — find the subway (or taxi rank)", 13, 600),
  SEG("2026-09-26T13:15:00+09:00", "2026-09-26T13:40:00+09:00", PLAN_A_PATH, "🚇", "Subway Plan A — to Nagoya Dome-mae Yada", 12, 2500),
  SEG("2026-09-26T13:40:00+09:00", "2026-09-26T13:50:00+09:00", [byId("dyd").lngLat, byId("dko").lngLat], "🚶", "Walk — Entrance 1, turn right, ~3 min to the dorm", 14.5, 1500),
];

/* fraction 0–1 → point along a polyline, measured by real distance */
function pointAlong(seg, f) {
  const p = seg.path;
  if (p.length < 2 || f <= 0) return p[0];
  if (f >= 1) return p[p.length - 1];
  if (!seg.cum) {
    seg.cum = [0];
    for (let i = 1; i < p.length; i++) {
      const dx = (p[i][0] - p[i - 1][0]) * Math.cos(p[i][1] * Math.PI / 180);
      const dy = p[i][1] - p[i - 1][1];
      seg.cum.push(seg.cum[i - 1] + Math.hypot(dx, dy));
    }
  }
  const total = seg.cum[seg.cum.length - 1];
  if (!total) return p[0];
  const target = f * total;
  let i = 1;
  while (seg.cum[i] < target) i++;
  const g = (target - seg.cum[i - 1]) / (seg.cum[i] - seg.cum[i - 1]);
  return [p[i - 1][0] + (p[i][0] - p[i - 1][0]) * g, p[i - 1][1] + (p[i][1] - p[i - 1][1]) * g];
}

const jEl = document.createElement("div");
jEl.className = "journey-marker";
jEl.textContent = "🧳";
const journeyMarker = new maplibregl.Marker({ element: jEl })
  .setLngLat(byId("hyd").lngLat).addTo(map);

function journeyNow(now = Date.now()) {
  if (now < SEGMENTS[0].t0) return { seg: null, pos: byId("hyd").lngLat, icon: "🧳",
    text: `🧳 Journey starts 24 Sep 23:15 IST — in ${fmtDur(SEGMENTS[0].t0 - now)}` };
  for (const s of SEGMENTS) {
    if (now < s.t1) {
      const f = Math.max(0, (now - s.t0) / (s.t1 - s.t0));
      return { seg: s, f, pos: pointAlong(s, f), icon: s.icon,
        text: `${s.icon} ${s.label} · ${Math.round(f * 100)}% · ${fmtDur(s.t1 - now)} to go` };
    }
  }
  return { seg: null, pos: byId("dko").lngLat, icon: "🏠", text: "🎉 Arrived — International Residence Daiko, Room 333" };
}

let previewing = false;
function liveJourneyTick() {
  const j = journeyNow();
  if (!previewing) {
    jEl.textContent = j.icon;
    journeyMarker.setLngLat(j.pos);
  }
  document.getElementById("journey-now").innerHTML =
    `${j.text}<div class="small">tap here to see the marker on the map · it moves along the track in real time</div>`;
}
document.getElementById("journey-now").addEventListener("click", () => {
  const j = journeyNow();
  map.flyTo({ center: j.pos, zoom: j.seg ? j.seg.z : 10 });
});
setInterval(liveJourneyTick, 1000);
liveJourneyTick();

/* flight status rows — computed from the booked schedule, so they work offline */
function flightRows() {
  const box = document.getElementById("flight-list");
  box.innerHTML = "";
  const now = Date.now();
  for (const fl of FLIGHTS) {
    const dep = +new Date(fl.dep), arr = +new Date(fl.arr);
    let cls, txt;
    if (now < dep - 3600000) { cls = "st-soon"; txt = `Departs in ${fmtDur(dep - now)}`; }
    else if (now < dep) { cls = "st-board"; txt = `🔔 BOARDING SOON — ${fmtDur(dep - now)}`; }
    else if (now < arr) { cls = "st-air"; txt = `✈️ In the air ${Math.round(100 * (now - dep) / (arr - dep))}% · lands in ${fmtDur(arr - now)}`; }
    else { cls = "st-done"; txt = "Landed ✅"; }
    const row = document.createElement("div");
    row.className = "flight-row";
    row.innerHTML = `
      <div class="f-main"><div class="f-no">${fl.no} · seat ${fl.seat}</div>
        <div class="small">${fl.from} ${fl.depLocal} → ${fl.to} ${fl.arrLocal}</div></div>
      <span class="status-chip ${cls}">${txt}</span>
      <a class="f-live" href="${fl.fr24}" target="_blank" rel="noopener">📡 Live map</a>`;
    box.appendChild(row);
  }
}
flightRows();
setInterval(flightRows, 30000);

/* ▶ Play trip — fly the marker along the whole route with the camera following */
const btnPlay = document.getElementById("btn-play");
const PV_TOTAL = SEGMENTS.reduce((s, x) => s + x.pv, 0);
let animRAF = null;
function stopPreview() {
  cancelAnimationFrame(animRAF);
  animRAF = null;
  previewing = false;
  btnPlay.classList.remove("active");
  btnPlay.textContent = "▶ Play trip";
  liveJourneyTick();
  map.fitBounds(ROUTE_BOUNDS, { padding: 60 });
}
btnPlay.addEventListener("click", () => {
  if (animRAF) { stopPreview(); return; }
  previewing = true;
  btnPlay.classList.add("active");
  btnPlay.textContent = "⏹ Stop";
  const start = performance.now();
  let zoom = map.getZoom();
  const frame = t => {
    const elapsed = t - start;
    if (elapsed >= PV_TOTAL) { stopPreview(); return; }
    let acc = 0, seg = SEGMENTS[SEGMENTS.length - 1], f = 1;
    for (const s of SEGMENTS) {
      if (elapsed < acc + s.pv) { seg = s; f = (elapsed - acc) / s.pv; break; }
      acc += s.pv;
    }
    const pos = pointAlong(seg, f);
    jEl.textContent = seg.icon;
    journeyMarker.setLngLat(pos);
    zoom += (seg.z - zoom) * 0.06; // smooth zoom toward each stage's level
    map.jumpTo({ center: pos, zoom });
    animRAF = requestAnimationFrame(frame);
  };
  animRAF = requestAnimationFrame(frame);
});

/* ================= My train tickets — live status (saved on this device) ================= */
const TK_KEY = "train-tickets";
const getTickets = () => { try { return JSON.parse(localStorage.getItem(TK_KEY)) || []; } catch { return []; } };
const setTickets = t => localStorage.setItem(TK_KEY, JSON.stringify(t));

function ticketStatus(tk) {
  const dep = +new Date(`${tk.date}T${tk.dep}:00+09:00`);
  const arr = +new Date(`${tk.date}T${tk.arr}:00+09:00`);
  const now = Date.now();
  if (isNaN(dep) || isNaN(arr)) return { cls: "st-soon", txt: "check the times" };
  if (now < dep - 3600000) return { cls: "st-soon", txt: `Departs in ${fmtDur(dep - now)}` };
  if (now < dep) return { cls: "st-board", txt: `🔔 BOARD SOON — ${fmtDur(dep - now)}` };
  if (now < arr) return { cls: "st-air", txt: `🚄 En route ${Math.round(100 * (now - dep) / (arr - dep))}% · ${fmtDur(arr - now)} left` };
  return { cls: "st-done", txt: "Arrived ✅" };
}

function renderTickets() {
  const box = document.getElementById("ticket-list");
  box.innerHTML = "";
  const list = getTickets();
  if (!list.length) {
    const p = document.createElement("p");
    p.className = "small";
    p.textContent = "No tickets yet. When you buy the Haruka + Shinkansen at the KIX JR office (Sat 26 Sep), add them here — or pre-load the planned times below and edit later.";
    box.appendChild(p);
  }
  list.forEach((tk, i) => {
    const st = ticketStatus(tk);
    const div = document.createElement("div");
    div.className = "ticket";
    const main = document.createElement("div");
    main.className = "f-main";
    const t1 = document.createElement("div");
    t1.className = "f-no";
    t1.textContent = `🚄 ${tk.name}`;
    const t2 = document.createElement("div");
    t2.className = "small";
    t2.textContent = `${tk.from} ${tk.dep} → ${tk.to} ${tk.arr} JST · ${tk.date}` + (tk.seat ? ` · ${tk.seat}` : "");
    main.append(t1, t2);
    const chip = document.createElement("span");
    chip.className = `status-chip ${st.cls}`;
    chip.textContent = st.txt;
    const del = document.createElement("button");
    del.className = "tk-del";
    del.textContent = "🗑";
    del.title = "Remove this ticket";
    del.onclick = () => {
      if (!confirm(`Remove “${tk.name}”?`)) return;
      const l = getTickets(); l.splice(i, 1); setTickets(l); renderTickets();
    };
    div.append(main, chip, del);
    box.appendChild(div);
  });
}
renderTickets();
setInterval(renderTickets, 30000);

document.getElementById("btn-tk-planned").addEventListener("click", () => {
  const l = getTickets();
  l.push(
    { name: "JR Haruka (planned — edit after booking)", from: "Kansai Airport", to: "Shin-Osaka", date: "2026-09-26", dep: "10:45", arr: "11:35", seat: "" },
    { name: "Tokaido Shinkansen (planned)", from: "Shin-Osaka", to: "Nagoya", date: "2026-09-26", dep: "12:00", arr: "12:50", seat: "oversized-baggage seat" }
  );
  setTickets(l);
  renderTickets();
});

document.getElementById("tk-save").addEventListener("click", () => {
  const v = id => document.getElementById(id).value.trim();
  const tk = { name: v("tk-name"), from: v("tk-from"), to: v("tk-to"), date: v("tk-date"), dep: v("tk-dep"), arr: v("tk-arr"), seat: v("tk-seat") };
  if (!tk.name || !tk.date || !tk.dep || !tk.arr) { alert("Please fill at least: train name, date, departure time and arrival time."); return; }
  const l = getTickets();
  l.push(tk);
  setTickets(l);
  renderTickets();
  ["tk-name", "tk-from", "tk-to", "tk-dep", "tk-arr", "tk-seat"].forEach(id => document.getElementById(id).value = "");
  document.getElementById("tk-details").open = false;
});

/* pre-load the waypoint photos so they're cached for offline use */
window.addEventListener("load", () => setTimeout(() => {
  for (const p of Object.values(PHOTOS)) new Image().src = p.src;
}, 4000));

/* satellite toggle */
let satOn = false;
document.getElementById("btn-sat").addEventListener("click", e => {
  satOn = !satOn;
  e.currentTarget.classList.toggle("active", satOn);
  // diff:false forces a full style reload so "style.load" always fires and
  // styleReady() redraws the route lines on the new basemap
  map.setStyle(satOn ? SAT_STYLE : STREET_STYLE, { diff: false });
});

document.getElementById("btn-route").addEventListener("click", () =>
  map.fitBounds(ROUTE_BOUNDS, { padding: 60 })
);

/* ---------- live geolocation ---------- */
let watchId = null, meMarker = null, follow = false;
const geoStatus = document.getElementById("geo-status");
const btnLocate = document.getElementById("btn-locate");
const btnFollow = document.getElementById("btn-follow");

function setStatus(msg) {
  geoStatus.textContent = msg;
  geoStatus.classList.toggle("show", !!msg);
}

btnLocate.addEventListener("click", () => {
  if (watchId !== null) {
    navigator.geolocation.clearWatch(watchId);
    watchId = null; follow = false;
    btnLocate.classList.remove("active");
    btnFollow.classList.remove("active");
    btnFollow.disabled = true;
    if (meMarker) { meMarker.remove(); meMarker = null; }
    setStatus("");
    return;
  }
  if (!("geolocation" in navigator)) { setStatus("This browser has no geolocation."); return; }
  setStatus("Waiting for GPS…");
  btnLocate.classList.add("active");
  watchId = navigator.geolocation.watchPosition(
    pos => {
      const { longitude, latitude, accuracy, speed } = pos.coords;
      if (!meMarker) {
        const dot = document.createElement("div");
        dot.style.cssText = "width:18px;height:18px;border-radius:50%;background:#3b82f6;border:3px solid #fff;box-shadow:0 0 12px #3b82f6;";
        meMarker = new maplibregl.Marker({ element: dot }).setLngLat([longitude, latitude]).addTo(map);
        btnFollow.disabled = false;
        map.flyTo({ center: [longitude, latitude], zoom: 12 });
      } else {
        meMarker.setLngLat([longitude, latitude]);
        if (follow) map.easeTo({ center: [longitude, latitude] });
      }
      const spd = speed != null && !isNaN(speed) ? ` · ${(speed * 3.6).toFixed(0)} km/h` : "";
      setStatus(`📍 live · ±${Math.round(accuracy)} m${spd}`);
    },
    err => setStatus("GPS error: " + err.message + " (allow location for this site)"),
    { enableHighAccuracy: true, maximumAge: 5000, timeout: 20000 }
  );
});

btnFollow.addEventListener("click", () => {
  follow = !follow;
  btnFollow.classList.toggle("active", follow);
  if (follow && meMarker) map.easeTo({ center: meMarker.getLngLat() });
});

/* ---------- wake lock ---------- */
let wakeLock = null;
const btnWake = document.getElementById("btn-wake");
btnWake.addEventListener("click", async () => {
  try {
    if (wakeLock) { await wakeLock.release(); wakeLock = null; btnWake.classList.remove("active"); return; }
    wakeLock = await navigator.wakeLock.request("screen");
    btnWake.classList.add("active");
    wakeLock.addEventListener("release", () => { wakeLock = null; btnWake.classList.remove("active"); });
  } catch (e) {
    setStatus("Wake lock unavailable: " + e.message);
  }
});
document.addEventListener("visibilitychange", async () => {
  if (wakeLock === null && btnWake.classList.contains("active") && document.visibilityState === "visible") {
    try { wakeLock = await navigator.wakeLock.request("screen"); } catch {}
  }
});

/* ================= Document vault (IndexedDB, local only) ================= */
const DB_NAME = "nagoya-vault", STORE = "docs";
function openDB() {
  return new Promise((res, rej) => {
    const rq = indexedDB.open(DB_NAME, 1);
    rq.onupgradeneeded = () => rq.result.createObjectStore(STORE);
    rq.onsuccess = () => res(rq.result);
    rq.onerror = () => rej(rq.error);
  });
}
async function dbPut(key, val) {
  const db = await openDB();
  return new Promise((res, rej) => {
    const tx = db.transaction(STORE, "readwrite");
    tx.objectStore(STORE).put(val, key);
    tx.oncomplete = res; tx.onerror = () => rej(tx.error);
  });
}
async function dbGet(key) {
  const db = await openDB();
  return new Promise((res, rej) => {
    const rq = db.transaction(STORE).objectStore(STORE).get(key);
    rq.onsuccess = () => res(rq.result);
    rq.onerror = () => rej(rq.error);
  });
}
async function dbDel(key) {
  const db = await openDB();
  return new Promise((res, rej) => {
    const tx = db.transaction(STORE, "readwrite");
    tx.objectStore(STORE).delete(key);
    tx.oncomplete = res; tx.onerror = () => rej(tx.error);
  });
}

async function renderVault() {
  const grid = document.getElementById("vault-slots");
  grid.innerHTML = "";
  for (const slot of VAULT_SLOTS) {
    const rec = await dbGet(slot.id);
    const div = document.createElement("div");
    div.className = "vault-slot" + (rec ? " filled" : "") + (slot.special ? " special" : "");
    const name = document.createElement("div");
    name.className = "vault-name";
    name.textContent = (slot.special ? "⭐ " : "") + slot.name;
    div.appendChild(name);
    const meta = document.createElement("div");
    meta.className = "vault-meta";
    meta.textContent = rec ? `${rec.fileName} · ${(rec.blob.size / 1024).toFixed(0)} KB` : "empty";
    div.appendChild(meta);
    const noteKey = `note:${slot.id}`;
    const noteVal = localStorage.getItem(noteKey);
    if (noteVal) {
      const note = document.createElement("div");
      note.className = "vault-note";
      note.textContent = `📝 ${noteVal}`;
      div.appendChild(note);
    }
    const actions = document.createElement("div");
    actions.className = "vault-actions";
    const nb = document.createElement("button");
    nb.textContent = "📝";
    nb.title = "Note (e.g. file password) — saved only on this device";
    nb.onclick = ev => {
      ev.stopPropagation();
      const v = prompt(`Note shown beside “${slot.name}” (e.g. file password):`, noteVal || "");
      if (v === null) return;
      v.trim() ? localStorage.setItem(noteKey, v.trim()) : localStorage.removeItem(noteKey);
      renderVault();
    };
    actions.append(nb);
    if (rec) {
      const view = document.createElement("button");
      view.textContent = "👁 View";
      view.onclick = () => {
        const url = URL.createObjectURL(rec.blob);
        window.open(url, "_blank");
        setTimeout(() => URL.revokeObjectURL(url), 60000);
      };
      const save = document.createElement("button");
      save.textContent = "⬇ Save";
      save.title = "Download this file to this device";
      save.onclick = () => {
        const a = document.createElement("a");
        a.href = URL.createObjectURL(rec.blob);
        a.download = rec.fileName;
        a.click();
        setTimeout(() => URL.revokeObjectURL(a.href), 60000);
      };
      const del = document.createElement("button");
      del.textContent = "🗑";
      del.className = "danger";
      del.onclick = async () => { if (confirm(`Delete ${slot.name}?`)) { await dbDel(slot.id); renderVault(); } };
      actions.append(view, save, del);
    } else {
      const add = document.createElement("button");
      add.textContent = "➕ Add file";
      add.onclick = () => {
        const inp = document.createElement("input");
        inp.type = "file";
        inp.accept = "image/*,.pdf";
        inp.onchange = async () => {
          const f = inp.files[0];
          if (!f) return;
          await dbPut(slot.id, { fileName: f.name, blob: f });
          renderVault();
        };
        inp.click();
      };
      actions.append(add);
    }
    div.appendChild(actions);
    grid.appendChild(div);
  }
}
renderVault();

/* ask the browser to never auto-delete the vault to free space */
if (navigator.storage && navigator.storage.persist) navigator.storage.persist();

/* ---------- encrypted vault backup / restore (for phone ↔ laptop) ---------- */
function blobToDataURL(blob) {
  return new Promise((res, rej) => {
    const r = new FileReader();
    r.onload = () => res(r.result);
    r.onerror = () => rej(r.error);
    r.readAsDataURL(blob);
  });
}
async function deriveKey(pw, salt) {
  const base = await crypto.subtle.importKey("raw", new TextEncoder().encode(pw), "PBKDF2", false, ["deriveKey"]);
  return crypto.subtle.deriveKey(
    { name: "PBKDF2", salt, iterations: 210000, hash: "SHA-256" },
    base, { name: "AES-GCM", length: 256 }, false, ["encrypt", "decrypt"]
  );
}
/* chunked — spreading a multi-MB array into fromCharCode blows the call stack */
const b64 = u8 => {
  let s = "";
  for (let i = 0; i < u8.length; i += 0x8000) s += String.fromCharCode.apply(null, u8.subarray(i, i + 0x8000));
  return btoa(s);
};
const unb64 = s => Uint8Array.from(atob(s), c => c.charCodeAt(0));

document.getElementById("btn-vault-export").addEventListener("click", async () => {
  const pw = prompt("Password to lock the backup file (use your app password):");
  if (!pw) return;
  const docs = [];
  for (const slot of VAULT_SLOTS) {
    const rec = await dbGet(slot.id);
    if (rec) docs.push({ id: slot.id, fileName: rec.fileName, data: await blobToDataURL(rec.blob) });
  }
  const notes = {};
  for (const slot of VAULT_SLOTS) {
    const n = localStorage.getItem(`note:${slot.id}`);
    if (n) notes[slot.id] = n;
  }
  if (!docs.length && !Object.keys(notes).length) { alert("Vault is empty — nothing to back up."); return; }
  try {
    const salt = crypto.getRandomValues(new Uint8Array(16));
    const iv = crypto.getRandomValues(new Uint8Array(12));
    const key = await deriveKey(pw, salt);
    const ct = await crypto.subtle.encrypt({ name: "AES-GCM", iv }, key, new TextEncoder().encode(JSON.stringify({ docs, notes })));
    const pkg = JSON.stringify({ v: 2, stamp: new Date().toISOString(), salt: b64(salt), iv: b64(iv), ct: b64(new Uint8Array(ct)) });
    const a = document.createElement("a");
    a.href = URL.createObjectURL(new Blob([pkg], { type: "application/json" }));
    a.download = "nagoya-vault-backup.json";
    a.click();
    setTimeout(() => URL.revokeObjectURL(a.href), 60000);
    alert(`✅ Backed up ${docs.length} document(s) as an ENCRYPTED file — check your Downloads folder for nagoya-vault-backup.json.`);
  } catch (err) {
    alert("❌ Backup failed: " + (err && err.message ? err.message : err));
  }
});

document.getElementById("btn-vault-import").addEventListener("click", () => {
  const inp = document.createElement("input");
  inp.type = "file";
  inp.accept = ".json,application/json";
  inp.onchange = async () => {
    const f = inp.files[0];
    if (!f) return;
    const pw = prompt("Password of the backup file:");
    if (!pw) return;
    try {
      const pkg = JSON.parse(await f.text());
      const key = await deriveKey(pw, unb64(pkg.salt));
      const pt = await crypto.subtle.decrypt({ name: "AES-GCM", iv: unb64(pkg.iv) }, key, unb64(pkg.ct));
      const payload = JSON.parse(new TextDecoder().decode(pt));
      const docs = Array.isArray(payload) ? payload : (payload.docs || []);
      const notes = Array.isArray(payload) ? {} : (payload.notes || {});
      for (const d of docs) {
        const blob = await (await fetch(d.data)).blob();
        await dbPut(d.id, { fileName: d.fileName, blob });
      }
      for (const [k, v] of Object.entries(notes)) localStorage.setItem(`note:${k}`, v);
      renderVault();
      alert(`Restored ${docs.length} document(s) and ${Object.keys(notes).length} note(s) into this device's vault.`);
    } catch {
      alert("Could not open the backup — wrong password or damaged file.");
    }
  };
  inp.click();
});

/* ---------- cloud copy: encrypted vault bundle published on this site ----------
   The published file is AES-256 encrypted; without the password it is unreadable.
   When a new copy appears, the app offers to load it into this device's vault. */
async function checkCloudVault() {
  let pkg;
  try {
    const resp = await fetch("vaultsync/vault-cloud.json", { cache: "no-store" });
    if (!resp.ok) return;
    pkg = await resp.json();
  } catch { return; } /* offline or no cloud copy yet */
  const stamp = pkg.stamp || "";
  if (localStorage.getItem("cloud-applied") === stamp) return;
  if (!confirm("☁️ A synced copy of your documents is available. Load it into this device now?")) return;
  const pw = prompt("Password of the synced copy:");
  if (!pw) return;
  try {
    const key = await deriveKey(pw, unb64(pkg.salt));
    const pt = await crypto.subtle.decrypt({ name: "AES-GCM", iv: unb64(pkg.iv) }, key, unb64(pkg.ct));
    const payload = JSON.parse(new TextDecoder().decode(pt));
    const docs = payload.docs || [];
    for (const d of docs) {
      const blob = await (await fetch(d.data)).blob();
      await dbPut(d.id, { fileName: d.fileName, blob });
    }
    for (const [k, v] of Object.entries(payload.notes || {})) localStorage.setItem(`note:${k}`, v);
    localStorage.setItem("cloud-applied", stamp);
    renderVault();
    alert(`Loaded ${docs.length} document(s) from the synced copy. They are now saved on this device.`);
  } catch {
    alert("Wrong password — the synced copy was not loaded. It will be offered again next time.");
  }
}
checkCloudVault();

/* ---------- warn if Chrome's "Desktop site" mode is forcing a wide layout ---------- */
if (navigator.maxTouchPoints > 0 && window.innerWidth >= 980 && localStorage.getItem("dm-dismissed") !== "1") {
  const bar = document.createElement("div");
  bar.style.cssText = "position:fixed;bottom:0;left:0;right:0;z-index:250;background:#7c2d12;color:#fff;padding:12px 14px;font-size:15px;line-height:1.4;";
  bar.innerHTML = "📱 This page is being shown in <strong>desktop mode</strong>. In Chrome tap the <strong>⋮ menu</strong> and <strong>untick “Desktop site”</strong>, then reload. <button id='dm-x' style='float:right;background:#fff;color:#7c2d12;border:none;border-radius:8px;padding:6px 10px;font-weight:700'>OK</button>";
  document.body.appendChild(bar);
  document.getElementById("dm-x").onclick = () => { localStorage.setItem("dm-dismissed", "1"); bar.remove(); };
}

/* ================= Service worker ================= */
if ("serviceWorker" in navigator) {
  navigator.serviceWorker.register("sw.js");
}

/* ---------- 🔄 refresh: pull the newest app version without closing it ---------- */
const btnRefresh = document.getElementById("btn-refresh");
btnRefresh.addEventListener("click", async () => {
  btnRefresh.classList.add("spin");
  btnRefresh.disabled = true;
  try {
    const reg = "serviceWorker" in navigator && await navigator.serviceWorker.getRegistration();
    if (reg) {
      await reg.update();
      const fresh = reg.installing || reg.waiting;
      if (fresh) {
        // a newer version is downloading — reload the moment it takes over
        fresh.addEventListener("statechange", () => {
          if (fresh.state === "activated") location.reload();
        });
        setTimeout(() => location.reload(), 8000); // safety net if the event never fires
        return;
      }
    }
  } catch { /* offline — the reload below still opens fine from the cache */ }
  location.reload(); // already newest: plain reload (also re-checks the cloud vault)
});

/* ================= Emergency contact & one-tap updates =================
   Details live in localStorage only — this file is public, so no personal
   numbers or addresses are ever written into it. */
const APP_URL = "https://bikudebug.github.io/travel/";
const EC_FIELDS = ["ec-wa", "ec-mail", "my-wa", "my-mail"];
EC_FIELDS.forEach(id => {
  document.getElementById(id).value = localStorage.getItem("contact:" + id) || "";
});
document.getElementById("ec-save").addEventListener("click", () => {
  EC_FIELDS.forEach(id => localStorage.setItem("contact:" + id, document.getElementById(id).value.trim()));
  alert("✅ Saved on this phone only. The send buttons now use these details.");
});
const contactVal = id => document.getElementById(id).value.trim() || localStorage.getItem("contact:" + id) || "";

const nextStep = () => STEPS.find(s => !isDone(s.id)) || null;

function statusMessage() {
  const j = journeyNow();
  const nx = nextStep();
  let m = `LIVE UPDATE — my journey to Nagoya\n\nWhere I am now:\n${j.text}\n`;
  if (nx) m += `\nNEXT STEP (${nx.when}):\n${nx.title}\n${nx.desc}\n`;
  m += `\nFollow my live map here: ${APP_URL}\n(The page asks for a password — I'll tell you it myself.)`;
  return m;
}
/* full plan with every instruction — for email, which has room */
function planFull() {
  let m = "MY COMPLETE NAGOYA JOURNEY PLAN\n";
  STEPS.forEach((s, i) => {
    m += `\n${i + 1}) ${s.when}${isDone(s.id) ? " ✅ done" : ""}\n${s.title}\n${s.desc}\n`;
  });
  return m + `\nLive tracking map: ${APP_URL}`;
}
/* compact plan + the full next step — for WhatsApp */
function planShort() {
  let m = "MY NAGOYA JOURNEY — quick plan\n";
  STEPS.forEach((s, i) => { m += `${isDone(s.id) ? "✅" : "▫️"} ${i + 1}) ${s.when} — ${s.title}\n`; });
  const nx = nextStep();
  if (nx) m += `\nNEXT STEP in full (${nx.when}):\n${nx.title}\n${nx.desc}\n`;
  return m + `\nLive map: ${APP_URL}`;
}
function openWA(numRaw, text) {
  const num = (numRaw || "").replace(/[^0-9]/g, "");
  if (!num) { alert("First type the WhatsApp number (with country code) in the box above and tap Save."); return; }
  window.open(`https://wa.me/${num}?text=${encodeURIComponent(text)}`, "_blank");
}
function openMail(addr, subject, body) {
  if (!addr) { alert("First type the email address in the box above and tap Save."); return; }
  location.href = `mailto:${addr}?subject=${encodeURIComponent(subject)}&body=${encodeURIComponent(body)}`;
}
document.getElementById("ec-wa-status").addEventListener("click", () => openWA(contactVal("ec-wa"), statusMessage()));
document.getElementById("ec-mail-status").addEventListener("click", () => openMail(contactVal("ec-mail"), "Live update — journey to Nagoya", statusMessage()));
document.getElementById("my-wa-plan").addEventListener("click", () => openWA(contactVal("my-wa"), planShort()));
document.getElementById("my-mail-plan").addEventListener("click", () => openMail(contactVal("my-mail"), "My complete Nagoya journey plan", planFull()));

/* ---------- step reminders: real phone notifications while the app is open ---------- */
const btnRemind = document.getElementById("ec-remind");
function remindLabel() {
  const on = localStorage.getItem("remind-on") === "1";
  btnRemind.textContent = `🔔 Step reminders on this phone: ${on ? "ON" : "OFF"}`;
}
remindLabel();
btnRemind.addEventListener("click", async () => {
  if (localStorage.getItem("remind-on") === "1") { localStorage.setItem("remind-on", "0"); remindLabel(); return; }
  if (!("Notification" in window)) { alert("This browser cannot show notifications."); return; }
  const perm = await Notification.requestPermission();
  if (perm !== "granted") { alert("Notifications are blocked — allow them for this site in the browser's site settings, then try again."); return; }
  localStorage.setItem("remind-on", "1");
  remindLabel();
  try { new Notification("🔔 Reminders are ON", { body: "You'll be reminded 45 min before each step and again at step time, with the full instructions — while the app is open." }); } catch {}
});
function checkReminders() {
  if (localStorage.getItem("remind-on") !== "1") return;
  if (!("Notification" in window) || Notification.permission !== "granted") return;
  const now = Date.now();
  for (const s of STEPS) {
    if (isDone(s.id)) continue;
    const t = +new Date(s.ts);
    const fire = (tag, title) => {
      const k = `notified:${tag}:${s.id}`;
      if (localStorage.getItem(k) === "1") return;
      localStorage.setItem(k, "1");
      try { new Notification(title, { body: `${s.when}\n${s.title}\n\n${s.desc}`, tag: k, requireInteraction: true }); } catch {}
    };
    if (now >= t - 45 * 60000 && now < t) fire("pre", `⏰ In ${fmtDur(t - now)} — get ready`);
    else if (now >= t && now < t + 30 * 60000) fire("due", "🚨 It's time — next step NOW");
  }
}
setInterval(checkReminders, 30000);
checkReminders();
