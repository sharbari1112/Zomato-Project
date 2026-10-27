/** Backend origin for Vercel→Render. Empty string = same-origin (local FastAPI). */
const API_BASE = String(window.__API_BASE__ || "").replace(/\/$/, "");
const API_TIMEOUT_MS = 90_000;

const state = {
  meta: null,
  lastPrefs: null,
  lastResponse: null,
};

function apiUrl(path) {
  return `${API_BASE}${path}`;
}

async function apiFetch(path, options = {}) {
  const init = { ...options };
  if (init.signal == null && typeof AbortSignal !== "undefined" && AbortSignal.timeout) {
    init.signal = AbortSignal.timeout(API_TIMEOUT_MS);
  }
  return fetch(apiUrl(path), init);
}

const views = {
  error: document.getElementById("view-error"),
  preferences: document.getElementById("view-preferences"),
  loading: document.getElementById("view-loading"),
  empty: document.getElementById("view-empty"),
  results: document.getElementById("view-results"),
};

function showView(name) {
  Object.entries(views).forEach(([key, el]) => {
    if (!el) return;
    el.classList.toggle("hidden", key !== name);
  });
}

let toastTimer;
function showToast(message, icon = "check_circle") {
  const toast = document.getElementById("micro-toast");
  const toastMsg = document.getElementById("toast-message");
  const toastIcon = document.getElementById("toast-icon");
  if (!toast || !toastMsg || !toastIcon) return;
  toastMsg.textContent = message;
  toastIcon.textContent = icon;
  toast.classList.remove("opacity-0", "translate-y-3", "pointer-events-none");
  toast.classList.add("opacity-100", "translate-y-0");
  clearTimeout(toastTimer);
  toastTimer = setTimeout(() => {
    toast.classList.remove("opacity-100", "translate-y-0");
    toast.classList.add("opacity-0", "translate-y-3", "pointer-events-none");
  }, 2800);
}

function formatCost(cost) {
  if (cost == null || Number.isNaN(Number(cost))) return "—";
  const n = Number(cost);
  return `₹${Number.isInteger(n) ? n : n.toFixed(0)} for two`;
}

function formatRating(rating) {
  if (rating == null || Number.isNaN(Number(rating))) return "—";
  return Number(rating).toFixed(1).replace(/\.0$/, "");
}

function budgetLabel(budget, cutoffs) {
  if (!cutoffs) {
    return budget.charAt(0).toUpperCase() + budget.slice(1);
  }
  if (budget === "low") return `≤ ₹${Math.round(cutoffs.low_max)} for two`;
  if (budget === "medium") return `≤ ₹${Math.round(cutoffs.medium_max)} for two`;
  return `> ₹${Math.round(cutoffs.medium_max)} for two`;
}

function matchScoreForRank(rank) {
  return Math.max(72, 100 - (rank - 1) * 4);
}

function rankBadge(rank) {
  if (rank === 1) {
    return {
      label: "#1 Top Pick",
      icon: "workspace_premium",
      classes: "bg-secondary text-on-secondary",
    };
  }
  if (rank === 2) {
    return {
      label: "#2 Recommended",
      icon: "recommend",
      classes: "bg-primary text-on-primary",
    };
  }
  return {
    label: `#${rank} Contender`,
    icon: "savings",
    classes: "bg-surface-container-highest text-on-surface",
  };
}

/** Cuisine families drive thumbnails, specialty tags, headline, and feature chips. */
const CUISINE_PROFILES = {
  italian: {
    keys: ["italian", "pizza", "pasta"],
    venueSingular: "Trattoria",
    venuePlural: "Trattorias",
    specialties: ["Wood-fired Pizza", "Artisan Pasta", "Wine & Dine"],
    features: [
      { icon: "eco", label: "Vegetarian Friendly", tone: "primary" },
      { icon: "restaurant", label: "Dine-in Only", tone: "outline" },
      { icon: "deck", label: "Outdoor Verandah", tone: "outline" },
    ],
    images: [
      "https://images.unsplash.com/photo-1517248135467-4c7edcad34c4?auto=format&fit=crop&w=900&h=700&q=80",
      "https://images.unsplash.com/photo-1555396273-367ea4eb4db5?auto=format&fit=crop&w=900&h=700&q=80",
      "https://images.unsplash.com/photo-1574071318508-1cdbab80d002?auto=format&fit=crop&w=900&h=700&q=80",
    ],
  },
  "north indian": {
    keys: ["north indian", "mughlai", "punjabi", "kebab"],
    venueSingular: "North Indian Cuisine",
    venuePlural: "North Indian Spots",
    specialties: ["Tandoor Specials", "Butter Chicken", "Dal Makhani"],
    features: [
      { icon: "local_fire_department", label: "Tandoor Fresh", tone: "secondary" },
      { icon: "restaurant", label: "Family Portions", tone: "outline" },
      { icon: "chair", label: "AC Dining", tone: "outline" },
    ],
    images: [
      "https://images.unsplash.com/photo-1585937421612-70a008356fbe?auto=format&fit=crop&w=900&h=700&q=80",
      "https://images.unsplash.com/photo-1567188040759-fb8a883dc6d8?auto=format&fit=crop&w=900&h=700&q=80",
      "https://images.unsplash.com/photo-1631452180519-c014fe946bc7?auto=format&fit=crop&w=900&h=700&q=80",
    ],
  },
  "south indian": {
    keys: ["south indian", "andhra", "kerala", "mangalorean", "chettinad"],
    venueSingular: "South Indian Kitchen",
    venuePlural: "South Indian Kitchens",
    specialties: ["Filter Coffee", "Dosa & Idli", "Meals Thali"],
    features: [
      { icon: "breakfast_dining", label: "Tiffin Friendly", tone: "primary" },
      { icon: "eco", label: "Vegetarian Staples", tone: "outline" },
      { icon: "schedule", label: "Quick Service", tone: "outline" },
    ],
    images: [
      "https://images.unsplash.com/photo-1668236543090-82eba5ee5976?auto=format&fit=crop&w=900&h=700&q=80",
      "https://images.unsplash.com/photo-1589301760014-d929f3979dbc?auto=format&fit=crop&w=900&h=700&q=80",
      "https://images.unsplash.com/photo-1606491956689-2ea866880067?auto=format&fit=crop&w=900&h=700&q=80",
    ],
  },
  biryani: {
    keys: ["biryani", "hyderabadi"],
    venueSingular: "Biryani House",
    venuePlural: "Biryani Houses",
    specialties: ["Dum Biryani", "Raita & Salan", "Family Packs"],
    features: [
      { icon: "rice_bowl", label: "Handi Fresh", tone: "secondary" },
      { icon: "groups", label: "Group Friendly", tone: "outline" },
      { icon: "takeout_dining", label: "Parcel Ready", tone: "outline" },
    ],
    images: [
      "https://images.unsplash.com/photo-1563379091339-03b21ab4a4f8?auto=format&fit=crop&w=900&h=700&q=80",
      "https://images.unsplash.com/photo-1633945274405-b6c8069047b0?auto=format&fit=crop&w=900&h=700&q=80",
      "https://images.unsplash.com/photo-1642821373181-696a54913e93?auto=format&fit=crop&w=900&h=700&q=80",
    ],
  },
  "ice cream": {
    keys: ["ice cream", "desserts", "mithai", "bakery"],
    venueSingular: "Ice Cream Parlor",
    venuePlural: "Dessert Parlors",
    specialties: ["Artisan Scoops", "Sundaes", "Seasonal Flavors"],
    features: [
      { icon: "icecream", label: "Cold Treats", tone: "primary" },
      { icon: "child_care", label: "Kid Friendly", tone: "outline" },
      { icon: "schedule", label: "Walk-in Welcome", tone: "outline" },
    ],
    images: [
      "https://images.unsplash.com/photo-1497034825429-c343d7c6a68f?auto=format&fit=crop&w=900&h=700&q=80",
      "https://images.unsplash.com/photo-1563805042-7684c019e1cb?auto=format&fit=crop&w=900&h=700&q=80",
      "https://images.unsplash.com/photo-1551024506-0bccd828d307?auto=format&fit=crop&w=900&h=700&q=80",
    ],
  },
  chinese: {
    keys: ["chinese", "asian", "momos", "thai"],
    venueSingular: "Asian Kitchen",
    venuePlural: "Asian Kitchens",
    specialties: ["Wok Tossed", "Dim Sum", "Indo-Chinese"],
    features: [
      { icon: "soup_kitchen", label: "Wok Fresh", tone: "primary" },
      { icon: "restaurant", label: "Dine-in", tone: "outline" },
      { icon: "local_dining", label: "Shareable Plates", tone: "outline" },
    ],
    images: [
      "https://images.unsplash.com/photo-1525755662778-989d0524087e?auto=format&fit=crop&w=900&h=700&q=80",
      "https://images.unsplash.com/photo-1582878826629-29b7ad1cdc43?auto=format&fit=crop&w=900&h=700&q=80",
      "https://images.unsplash.com/photo-1563245372-f21724e3856d?auto=format&fit=crop&w=900&h=700&q=80",
    ],
  },
  cafe: {
    keys: ["cafe", "coffee", "tea", "beverages", "sandwich", "salad", "healthy food"],
    venueSingular: "Cafe",
    venuePlural: "Cafes",
    specialties: ["Brew Bar", "Light Bites", "Work-friendly"],
    features: [
      { icon: "wifi", label: "Wi-Fi Friendly", tone: "primary" },
      { icon: "laptop", label: "Laptop OK", tone: "outline" },
      { icon: "deck", label: "Patio Seating", tone: "outline" },
    ],
    images: [
      "https://images.unsplash.com/photo-1554118811-1e0d58224f24?auto=format&fit=crop&w=900&h=700&q=80",
      "https://images.unsplash.com/photo-1495474472287-4d71bcdd2085?auto=format&fit=crop&w=900&h=700&q=80",
      "https://images.unsplash.com/photo-1501339847302-ac426a4a7cbb?auto=format&fit=crop&w=900&h=700&q=80",
    ],
  },
  "fast food": {
    keys: ["fast food", "burger", "rolls", "street food", "finger food", "american"],
    venueSingular: "Quick Bite Spot",
    venuePlural: "Quick Bite Spots",
    specialties: ["Loaded Burgers", "Crispy Fries", "Grab & Go"],
    features: [
      { icon: "bolt", label: "Fast Service", tone: "secondary" },
      { icon: "takeout_dining", label: "Takeaway", tone: "outline" },
      { icon: "groups", label: "Casual Seating", tone: "outline" },
    ],
    images: [
      "https://images.unsplash.com/photo-1568901346375-23c9450c58cd?auto=format&fit=crop&w=900&h=700&q=80",
      "https://images.unsplash.com/photo-1550547660-d9450f859349?auto=format&fit=crop&w=900&h=700&q=80",
      "https://images.unsplash.com/photo-1594212699903-ec8a3eca50f5?auto=format&fit=crop&w=900&h=700&q=80",
    ],
  },
  seafood: {
    keys: ["seafood", "fish", "coastal"],
    venueSingular: "Seafood Grill",
    venuePlural: "Seafood Grills",
    specialties: ["Catch of the Day", "Coastal Curry", "Grilled Platters"],
    features: [
      { icon: "set_meal", label: "Fresh Catch", tone: "primary" },
      { icon: "restaurant", label: "Dine-in", tone: "outline" },
      { icon: "liquor", label: "Pairings", tone: "outline" },
    ],
    images: [
      "https://images.unsplash.com/photo-1559339352-11d035aa65de?auto=format&fit=crop&w=900&h=700&q=80",
      "https://images.unsplash.com/photo-1615141982883-c7ad0e69fd62?auto=format&fit=crop&w=900&h=700&q=80",
      "https://images.unsplash.com/photo-1625944230946-1a0add44f997?auto=format&fit=crop&w=900&h=700&q=80",
    ],
  },
  continental: {
    keys: ["continental", "european", "mediterranean", "steak", "bbq", "mexican", "arabian"],
    venueSingular: "Continental Table",
    venuePlural: "Continental Tables",
    specialties: ["Chef Specials", "Grill Plates", "Course Dining"],
    features: [
      { icon: "event_seat", label: "Reservations Welcome", tone: "secondary" },
      { icon: "mode_fan", label: "Air Conditioned", tone: "outline" },
      { icon: "nightlife", label: "Evening Ambience", tone: "outline" },
    ],
    images: [
      "https://images.unsplash.com/photo-1414235077428-338989a2e8c0?auto=format&fit=crop&w=900&h=700&q=80",
      "https://images.unsplash.com/photo-1550966871-3ed3cdb132d8?auto=format&fit=crop&w=900&h=700&q=80",
      "https://images.unsplash.com/photo-1466978913421-dad2ebd01d17?auto=format&fit=crop&w=900&h=700&q=80",
    ],
  },
  default: {
    keys: [],
    venueSingular: "Dining Spot",
    venuePlural: "Dining Spots",
    specialties: ["House Specials", "Chef's Pick", "Local Favorite"],
    features: [
      { icon: "verified", label: "Catalog Verified", tone: "primary" },
      { icon: "restaurant", label: "Dine-in", tone: "outline" },
      { icon: "star", label: "Guest Rated", tone: "outline" },
    ],
    images: [
      "https://images.unsplash.com/photo-1517248135467-4c7edcad34c4?auto=format&fit=crop&w=900&h=700&q=80",
      "https://images.unsplash.com/photo-1559339352-11d035aa65de?auto=format&fit=crop&w=900&h=700&q=80",
      "https://images.unsplash.com/photo-1555396273-367ea4eb4db5?auto=format&fit=crop&w=900&h=700&q=80",
    ],
  },
};

function hashSeed(value) {
  const text = String(value || "");
  let hash = 0;
  for (let i = 0; i < text.length; i += 1) {
    hash = (hash * 31 + text.charCodeAt(i)) >>> 0;
  }
  return hash;
}

function normalizeCuisineToken(value) {
  return String(value || "")
    .toLowerCase()
    .replace(/[^a-z0-9\s]/g, " ")
    .replace(/\s+/g, " ")
    .trim();
}

function resolveCuisineProfile(cuisines, preferredCuisine) {
  const tokens = [
    preferredCuisine,
    ...(Array.isArray(cuisines) ? cuisines : []),
  ]
    .map(normalizeCuisineToken)
    .filter(Boolean);

  for (const [id, profile] of Object.entries(CUISINE_PROFILES)) {
    if (id === "default") continue;
    if (tokens.some((token) => profile.keys.some((key) => token.includes(key) || key.includes(token)))) {
      return { id, ...profile };
    }
  }
  return { id: "default", ...CUISINE_PROFILES.default };
}

function titleCase(value) {
  return String(value || "")
    .split(/\s+/)
    .filter(Boolean)
    .map((part) => part.charAt(0).toUpperCase() + part.slice(1).toLowerCase())
    .join(" ");
}

function specialtyTagsForItem(item, profile, preferredCuisine) {
  const fromCatalog = (item.cuisines || [])
    .map((c) => titleCase(c))
    .filter(Boolean);
  const preferred = preferredCuisine ? titleCase(preferredCuisine) : null;
  const extras = profile.specialties || [];
  const merged = [];
  const seen = new Set();

  [preferred, ...fromCatalog, ...extras].forEach((tag) => {
    if (!tag) return;
    const key = tag.toLowerCase();
    if (seen.has(key)) return;
    seen.add(key);
    merged.push(tag);
  });

  return merged.slice(0, 4);
}

function featureChipsForItem(item, profile) {
  const chips = [...(profile.features || [])];
  const rating = Number(item.rating);
  if (!Number.isNaN(rating) && rating >= 4.5) {
    chips.unshift({ icon: "workspace_premium", label: "Top Rated", tone: "secondary" });
  }
  const unique = [];
  const seen = new Set();
  chips.forEach((chip) => {
    const key = chip.label.toLowerCase();
    if (seen.has(key)) return;
    seen.add(key);
    unique.push(chip);
  });
  return unique.slice(0, 3);
}

function thumbnailForItem(item, profile) {
  const images = profile.images?.length ? profile.images : CUISINE_PROFILES.default.images;
  const index = hashSeed(item.id || item.name) % images.length;
  return images[index];
}

function resultsHeadline(prefs, recommendations) {
  const profile = resolveCuisineProfile(
    recommendations?.[0]?.cuisines || [prefs.cuisine],
    prefs.cuisine,
  );
  return `Recommended ${profile.venuePlural}`;
}

function fillSelect(select, options, preferred) {
  select.innerHTML = "";
  const values = options.length ? options : [preferred].filter(Boolean);
  values.forEach((value) => {
    const opt = document.createElement("option");
    opt.value = value;
    opt.textContent = value;
    select.appendChild(opt);
  });
  if (preferred && values.includes(preferred)) {
    select.value = preferred;
  } else if (values.length) {
    select.value = values[0];
  }
}

function setBudget(budget) {
  document.getElementById("field-budget").value = budget;
  document.querySelectorAll(".budget-pill").forEach((btn) => {
    const active = btn.dataset.budget === budget;
    btn.setAttribute("aria-pressed", active ? "true" : "false");
  });
}

function bindBudgetPills() {
  document.querySelectorAll(".budget-pill").forEach((btn) => {
    btn.addEventListener("click", () => setBudget(btn.dataset.budget));
  });
}

function updateBudgetCaption(meta) {
  const el = document.getElementById("budget-caption");
  if (!meta?.budget_cutoffs) {
    el.textContent = "Budget bands use estimated cost for two from the catalog.";
    return;
  }
  const { low_max: lowMax, medium_max: mediumMax } = meta.budget_cutoffs;
  el.textContent = `Cost for two — low ≤ ₹${Math.round(lowMax)}; medium ≤ ₹${Math.round(mediumMax)}; above that is high.`;
}

async function loadMeta() {
  const res = await apiFetch("/meta");
  if (!res.ok) {
    const detail = await res.json().catch(() => ({}));
    throw new Error(detail.detail || `Could not load catalog meta (${res.status})`);
  }
  return res.json();
}

function readPrefs() {
  const notes = document.getElementById("field-notes").value.trim();
  return {
    location: document.getElementById("field-location").value,
    budget: document.getElementById("field-budget").value,
    cuisine: document.getElementById("field-cuisine").value,
    min_rating: Number(document.getElementById("field-rating").value),
    notes: notes || null,
    top_k: Number(document.getElementById("field-top-k").value),
  };
}

function renderActiveQuery(prefs, meta) {
  const band = budgetLabel(prefs.budget, meta?.budget_cutoffs);
  document.getElementById("active-query").textContent =
    `${prefs.location} · ${prefs.budget} budget (${band}) · ${prefs.cuisine} · Rating ${prefs.min_rating}+`;
  document.getElementById("metric-budget").textContent = band;
  document.getElementById("metric-notes").textContent = prefs.notes
    ? prefs.notes.replace(/\b\w/g, (c) => c.toUpperCase())
    : "Open to vibe";
}

function featureToneClass(tone) {
  if (tone === "secondary") return "text-secondary";
  if (tone === "outline") return "text-outline";
  return "text-primary";
}

function renderCard(item, index, prefs) {
  const badge = rankBadge(item.rank);
  const score = matchScoreForRank(item.rank);
  const profile = resolveCuisineProfile(item.cuisines, prefs?.cuisine);
  const specialties = specialtyTagsForItem(item, profile, prefs?.cuisine);
  const features = featureChipsForItem(item, profile);
  const imageUrl = thumbnailForItem(item, profile);
  const stagger = Math.min(index + 3, 5);
  const locationLine = item.location.includes("Bangalore")
    ? item.location
    : `${item.location}, Bangalore`;
  const ctaLabel = item.rank === 1 ? "Reserve Table" : item.rank === 2 ? "View Menu" : "Explore Details";
  const ctaIcon = item.rank === 1 ? "arrow_forward" : item.rank === 2 ? "menu_book" : "arrow_forward";
  const ctaClasses =
    item.rank === 1
      ? "bg-primary text-on-primary hover:bg-primary-container shadow-sm"
      : "bg-surface-container hover:bg-surface-container-high text-on-surface";

  const article = document.createElement("article");
  article.className =
    "bg-surface-container-lowest rounded-2xl p-space-md md:p-space-lg shadow-sm hover:shadow-[0_12px_28px_-6px_rgba(27,27,30,0.08),0_4px_12px_-2px_rgba(27,27,30,0.04)] transition-all duration-300 ease-out hover:-translate-y-1 group flex flex-col md:flex-row gap-space-md md:gap-space-lg animate-fade-in-up relative";
  article.classList.add(`stagger-${stagger}`);

  const specialtyPills = specialties
    .map(
      (tag) =>
        `<span class="px-2.5 py-0.5 rounded-full bg-surface-container hover:bg-surface-container-high transition-colors text-on-surface-variant text-[12px] font-semibold">${escapeHtml(tag)}</span>`,
    )
    .join("");

  const featurePills = features
    .map(
      (chip) => `
        <span class="inline-flex items-center gap-1 px-2 py-0.5 rounded bg-surface-container border border-transparent hover:border-outline-variant/60 hover:-translate-y-0.5 transition-all text-on-surface-variant text-[11px] font-bold uppercase tracking-wide cursor-default">
          <span class="material-symbols-outlined text-[13px] ${featureToneClass(chip.tone)}">${chip.icon}</span>
          ${escapeHtml(chip.label)}
        </span>`,
    )
    .join("");

  article.innerHTML = `
    <div class="relative w-full md:w-5/12 h-56 md:h-auto min-h-[220px] rounded-xl overflow-hidden shrink-0 bg-surface-container card-media">
      <img
        class="card-thumb w-full h-full object-cover group-hover:scale-[1.04] transition-transform duration-500 ease-out"
        src="${escapeAttr(imageUrl)}"
        alt="${escapeAttr(`${item.name} — ${profile.venueSingular}`)}"
        loading="lazy"
        decoding="async"
        referrerpolicy="no-referrer"
      />
      <div class="absolute top-3 left-3 flex items-center gap-1.5 px-3 py-1 rounded-full ${badge.classes} shadow-sm">
        <span class="material-symbols-outlined text-[15px]">${badge.icon}</span>
        <span class="text-[11px] font-bold tracking-wide uppercase">${badge.label}</span>
      </div>
      <button type="button" class="btn-favorite absolute top-3 right-3 w-8 h-8 rounded-full bg-surface-container-lowest/85 hover:bg-surface-container-lowest text-on-surface-variant hover:text-secondary backdrop-blur-md shadow-sm flex items-center justify-center transition-all duration-200 active:scale-90" aria-label="Favorite ${escapeHtml(item.name)}">
        <span class="material-symbols-outlined text-[18px]">favorite_border</span>
      </button>
      <div class="absolute bottom-3 left-3 px-2.5 py-1 rounded-md bg-surface/90 backdrop-blur-sm shadow-sm">
        <span class="text-[11px] font-bold uppercase tracking-wide text-on-surface">${escapeHtml(profile.venueSingular)}</span>
      </div>
      <div class="absolute bottom-3 right-3 px-2.5 py-1 rounded-md bg-surface/90 backdrop-blur-sm shadow-sm flex items-center gap-1">
        <span class="text-[11px] font-bold uppercase text-on-surface-variant">Match Score:</span>
        <span class="text-[12px] font-bold text-primary match-counter" data-target="${score}">${score}%</span>
      </div>
    </div>
    <div class="flex flex-col justify-between flex-grow">
      <div>
        <div class="flex items-start justify-between gap-space-sm mb-1.5">
          <div>
            <h3 class="font-display text-[24px] font-semibold text-on-surface group-hover:text-primary transition-colors">${escapeHtml(item.name)}</h3>
            <p class="text-[13px] text-on-surface-variant flex items-center gap-1 mt-0.5">
              <span class="material-symbols-outlined text-[15px] text-outline">location_on</span>
              ${escapeHtml(locationLine)}
            </p>
          </div>
          <div class="flex items-center gap-1 px-2.5 py-1 rounded-full bg-secondary-container/20 text-on-secondary-container shrink-0 transition-transform duration-200 group-hover:scale-105">
            <span class="material-symbols-outlined text-[16px] text-secondary" style="font-variation-settings: 'FILL' 1;">star</span>
            <span class="text-[12px] font-bold">${formatRating(item.rating)}</span>
          </div>
        </div>
        <div class="flex flex-wrap items-center gap-1.5 my-space-sm">
          <span class="text-[12px] font-semibold text-primary px-2 py-0.5 rounded bg-primary-fixed/40">${formatCost(item.cost)}</span>
          ${specialties.length ? `<span class="text-outline-variant">·</span>${specialtyPills}` : ""}
        </div>
        <div class="bg-surface-container-low/90 rounded-xl p-3 my-space-sm border border-transparent hover:border-outline-variant/40 transition-colors">
          <div class="flex items-center gap-1.5 mb-1 text-primary">
            <span class="material-symbols-outlined text-[16px]">lightbulb</span>
            <span class="text-[11px] font-bold uppercase tracking-wide">Why PlateMatch Selected This</span>
          </div>
          <p class="text-[13px] text-on-surface-variant leading-relaxed">${escapeHtml(item.explanation || `Selected as a strong ${profile.venueSingular.toLowerCase()} match from the filtered catalog shortlist.`)}</p>
        </div>
      </div>
      <div class="pt-space-xs flex flex-wrap items-center justify-between gap-space-sm">
        <div class="flex flex-wrap gap-1.5">
          ${featurePills}
        </div>
        <button type="button" class="action-btn group/btn inline-flex items-center gap-1.5 px-4 py-2 rounded-xl ${ctaClasses} text-[12px] font-semibold transition-all active:scale-[0.97] ml-auto" data-action="${escapeAttr(`${ctaLabel} at ${item.name}`)}">
          <span>${ctaLabel}</span>
          <span class="material-symbols-outlined text-[16px] group-hover/btn:translate-x-1 transition-transform duration-200">${ctaIcon}</span>
        </button>
      </div>
    </div>
  `;

  const thumb = article.querySelector(".card-thumb");
  if (thumb) {
    thumb.addEventListener("error", () => {
      thumb.remove();
    });
  }

  return article;
}

function escapeHtml(value) {
  return String(value)
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;");
}

function escapeAttr(value) {
  return escapeHtml(value).replaceAll("'", "&#39;");
}

function animateMatchCounters() {
  const reduced = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
  if (reduced) return;
  document.querySelectorAll(".match-counter").forEach((counter) => {
    const target = Number(counter.getAttribute("data-target") || "90");
    let current = Math.max(0, target - 18);
    counter.textContent = `${current}%`;
    const stepTime = Math.max(16, Math.floor(800 / Math.max(1, target - current)));
    const timer = setInterval(() => {
      current += 1;
      counter.textContent = `${current}%`;
      if (current >= target) {
        clearInterval(timer);
        counter.textContent = `${target}%`;
      }
    }, stepTime);
  });
}

function bindResultInteractions(root) {
  root.querySelectorAll(".btn-favorite").forEach((btn) => {
    btn.addEventListener("click", (e) => {
      e.stopPropagation();
      const icon = btn.querySelector(".material-symbols-outlined");
      const isFav = btn.getAttribute("data-favorited") === "true";
      btn.classList.remove("heart-pop-anim");
      void btn.offsetWidth;
      btn.classList.add("heart-pop-anim");
      if (!isFav) {
        btn.setAttribute("data-favorited", "true");
        icon.textContent = "favorite";
        icon.classList.add("text-secondary");
        icon.style.fontVariationSettings = "'FILL' 1";
        showToast("Saved to your Curations", "bookmark_added");
      } else {
        btn.setAttribute("data-favorited", "false");
        icon.textContent = "favorite_border";
        icon.classList.remove("text-secondary");
        icon.style.fontVariationSettings = "'FILL' 0";
        showToast("Removed from Curations", "bookmark_remove");
      }
    });
  });

  root.querySelectorAll(".action-btn").forEach((btn) => {
    btn.addEventListener("click", () => {
      showToast(btn.getAttribute("data-action") || "Noted", "restaurant");
    });
  });
}

function renderResults(prefs, response, meta) {
  renderActiveQuery(prefs, meta);

  const fallback = document.getElementById("fallback-banner");
  const sourceChip = document.getElementById("source-chip");
  if (response.source === "fallback") {
    fallback.classList.remove("hidden");
    sourceChip.innerHTML =
      '<span class="w-2 h-2 rounded-full bg-outline shrink-0"></span> Catalog ranked';
  } else {
    fallback.classList.add("hidden");
    sourceChip.innerHTML =
      '<span class="w-2 h-2 rounded-full bg-primary pulse-indicator shrink-0"></span> AI Ranked · Realtime Match';
  }

  const summary =
    response.summary ||
    `${response.recommendations.length} ${prefs.cuisine} pick${response.recommendations.length === 1 ? "" : "s"} in ${prefs.location} for a ${prefs.budget} budget.`;
  document.getElementById("results-summary").textContent = summary;

  const sortLabel =
    response.source === "llm" ? "sorted by AI ranking" : "sorted by catalog rating";
  document.getElementById("results-count").textContent =
    `${response.recommendations.length} result${response.recommendations.length === 1 ? "" : "s"} ${sortLabel}`;

  const headline = document.getElementById("results-headline");
  if (headline) {
    headline.textContent = resultsHeadline(prefs, response.recommendations);
  }

  const list = document.getElementById("results-list");
  list.innerHTML = "";
  response.recommendations.forEach((item, index) => {
    list.appendChild(renderCard(item, index, prefs));
  });
  bindResultInteractions(list);
  animateMatchCounters();
  showView("results");
  window.scrollTo({ top: 0, behavior: "smooth" });
}

async function submitPrefs(event) {
  event.preventDefault();
  const prefs = readPrefs();
  state.lastPrefs = prefs;
  showView("loading");

  try {
    const res = await apiFetch("/recommend", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(prefs),
    });
    if (!res.ok) {
      const detail = await res.json().catch(() => ({}));
      throw new Error(
        typeof detail.detail === "string"
          ? detail.detail
          : `Recommendation failed (${res.status})`,
      );
    }
    const response = await res.json();
    state.lastResponse = response;

    if (response.status === "no_matches") {
      document.getElementById("empty-hint").textContent =
        response.hint ||
        "Try a nearby Bangalore neighborhood, a wider cuisine, or lower the minimum rating.";
      showView("empty");
      return;
    }
    renderResults(prefs, response, state.meta);
  } catch (err) {
    document.getElementById("error-detail").textContent = err.message || String(err);
    showView("error");
  }
}

function goHome() {
  showView("preferences");
  window.scrollTo({ top: 0, behavior: "smooth" });
}

async function init() {
  bindBudgetPills();
  setBudget("medium");

  document.getElementById("prefs-form").addEventListener("submit", submitPrefs);
  document.getElementById("brand-home").addEventListener("click", goHome);
  document.querySelectorAll(".btn-edit-prefs").forEach((btn) => {
    btn.addEventListener("click", () => {
      showToast("Opening taste preferences…", "tune");
      goHome();
    });
  });

  try {
    const meta = await loadMeta();
    state.meta = meta;
    updateBudgetCaption(meta);

    const locations = meta.locations || [];
    const cuisines = meta.cuisines || [];
    const preferredLocation = locations.includes("Banashankari")
      ? "Banashankari"
      : locations[0];
    const preferredCuisine = cuisines.includes("Italian") ? "Italian" : cuisines[0];

    fillSelect(document.getElementById("field-location"), locations, preferredLocation);
    fillSelect(document.getElementById("field-cuisine"), cuisines, preferredCuisine);
    showView("preferences");
  } catch (err) {
    document.getElementById("error-detail").textContent =
      err.message ||
      "Catalog not loaded. Run `python -m app.data.ingest` and restart the API.";
    showView("error");
  }
}

init();
