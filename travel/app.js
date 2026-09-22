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

/* Flight legs get a great-circle arc; ground legs a straight line */
const FLIGHT_LEGS = [["hyd", "sin"], ["sin", "kix"]];
const GROUND_LEGS = [["kix", "shin"], ["shin", "ngo"], ["ngo", "dyd"], ["dyd", "dko"]];

/* ---------------- Timeline (times carry their own UTC offset) ---------------- */
const STEPS = [
  {
    id: "docs", when: "Before you leave", ts: "2026-09-24T18:00:00+05:30", warn: true,
    title: "Student-fare paperwork (protects your 40 kg)",
    desc: "Email passport + student visa to student.documents@makemytrip.com. Pack in hand: passport, visa, university acceptance letter, admission docs. Show them at HYD check-in or the 40 kg student baggage can be refused. Enrol in KrisFlyer for free extra benefits.",
  },
  {
    id: "dorm-reply", when: "Wed 23 Sep — do TODAY", ts: "2026-09-23T20:00:00+05:30", warn: true,
    title: "Reply to the dorm email + book First Cabin + get cash",
    desc: "1) REPLY to ITO Kanako's email (ito.kanako.d8@mail.f.thers.ac.jp): move-in 26 Sep, arrival ~14:00, bedding rental yes/no (¥1,650/mo — the room has NO pillow/comforter/sheets). The dorm REQUIRES advance contact. 2) BOOK First Cabin KIX for the night of 25 Sep. 3) Carry ¥60,000–100,000 cash (first dorm bill: Sep rent ¥25,000 unprorated + ¥15,000 restoration + Wi-Fi + utilities; Yucho card takes ~1 week). 4) Consider a Japan eSIM bought in India. 5) Search your inbox for ITO-san's follow-up emails (dorm password; orientation details).",
  },
  {
    id: "dep-hyd", when: "Thu 24 Sep · 23:15 IST", ts: "2026-09-24T23:15:00+05:30",
    title: "Depart Hyderabad — SQ 523, seat 43A",
    desc: "Rajiv Gandhi Intl. PNR E7T7RU · e-ticket 2481322049. Cabin bag max 7 kg (1 piece).",
  },
  {
    id: "arr-sin", when: "Fri 25 Sep · 06:40 SGT", ts: "2026-09-25T06:40:00+08:00",
    title: "Arrive Singapore Changi — 7h 30m layover",
    desc: "TRANSIT only (no Singapore immigration). You change planes AND terminals — departure is Terminal 2. Free rest areas + showers in transit; Jewel is landside, skip it unless you're sure.",
  },
  {
    id: "dep-sin", when: "Fri 25 Sep · 14:10 SGT", ts: "2026-09-25T14:10:00+08:00",
    title: "Depart Singapore — SQ 622, seat 45A (Terminal 2)",
    desc: "6h 25m to Osaka.",
  },
  {
    id: "arr-kix", when: "Fri 25 Sep · 21:35 JST", ts: "2026-09-25T21:35:00+09:00",
    title: "Arrive Kansai KIX, Terminal 1 — immigration",
    desc: "Show passport + visa (COE-based). Residence card is issued at KIX — check the details on it before leaving the counter. Collect both bags.",
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
    title: "Nagoya Station → dormitory",
    desc: "EASIEST with 2 big bags: taxi (~20 min, show the Taxi Card below). Cheap option: Higashiyama line to Sakae → Meijo line to Nagoya Dome-mae Yada, then ~8 min walk.",
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
  { id: "niyo", name: "Niyo card details" },
  { id: "eticket", name: "Flight e-ticket" },
  { id: "admission", name: "Japan Admission", special: true },
  { id: "extra1", name: "Extra slot 1" },
  { id: "extra2", name: "Extra slot 2" },
];

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
  for (const s of STEPS) {
    const li = document.createElement("li");
    li.className = "step" + (isDone(s.id) ? " done" : "") + (s.id === nextId ? " next" : "") + (s.warn ? " warnstep" : "");
    li.innerHTML = `
      <div class="step-box">✓</div>
      <div>
        <div class="step-when">${s.when}</div>
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
  }
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
  dyd:  { src: `${WM}/7/7a/Yutorito_Line_Nagoya_Dome-mae_Yada_station.JPG/500px-Yutorito_Line_Nagoya_Dome-mae_Yada_station.JPG`, cap: "Nagoya Dome-mae Yada — your metro stop, ~8 min walk to the dorm" },
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

map.on("load", () => map.fitBounds(ROUTE_BOUNDS, { padding: 60, duration: 0 }));

/* pre-load the waypoint photos so they're cached for offline use */
window.addEventListener("load", () => setTimeout(() => {
  for (const p of Object.values(PHOTOS)) new Image().src = p.src;
}, 4000));

/* satellite toggle */
let satOn = false;
document.getElementById("btn-sat").addEventListener("click", e => {
  satOn = !satOn;
  e.currentTarget.classList.toggle("active", satOn);
  map.setStyle(satOn ? SAT_STYLE : STREET_STYLE);
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
    const actions = document.createElement("div");
    actions.className = "vault-actions";
    if (rec) {
      const view = document.createElement("button");
      view.textContent = "👁 View";
      view.onclick = () => {
        const url = URL.createObjectURL(rec.blob);
        window.open(url, "_blank");
        setTimeout(() => URL.revokeObjectURL(url), 60000);
      };
      const del = document.createElement("button");
      del.textContent = "🗑";
      del.className = "danger";
      del.onclick = async () => { if (confirm(`Delete ${slot.name}?`)) { await dbDel(slot.id); renderVault(); } };
      actions.append(view, del);
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

/* ================= Service worker ================= */
if ("serviceWorker" in navigator) {
  navigator.serviceWorker.register("sw.js");
}
