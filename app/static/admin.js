"use strict";

const dom = {
  statusDot: document.querySelector("#status-dot"),
  activeVersionLabel: document.querySelector("#active-version-label"),
  sidebarStoreName: document.querySelector("#sidebar-store-name"),
  storeName: document.querySelector("#store-name"),
  draftBadge: document.querySelector("#draft-badge"),
  globalMessage: document.querySelector("#global-message"),
  toast: document.querySelector("#toast"),
  stepButtons: Array.from(document.querySelectorAll("[data-step]")),
  stepPanels: Array.from(document.querySelectorAll("[data-step-panel]")),
  productEntryList: document.querySelector("#product-entry-list"),
  knowledgeEntryList: document.querySelector("#knowledge-entry-list"),
  knowledgeEmpty: document.querySelector("#knowledge-empty"),
  addProductButton: document.querySelector("#add-product-button"),
  addKnowledgeButton: document.querySelector("#add-knowledge-button"),
  analyzeButton: document.querySelector("#analyze-button"),
  productEntryTemplate: document.querySelector("#product-entry-template"),
  knowledgeEntryTemplate: document.querySelector("#knowledge-entry-template"),
  productPreviewTemplate: document.querySelector("#product-preview-template"),
  knowledgePreviewTemplate: document.querySelector("#knowledge-preview-template"),
  productPreviewList: document.querySelector("#product-preview-list"),
  knowledgePreviewList: document.querySelector("#knowledge-preview-list"),
  knowledgePreviewSection: document.querySelector("#knowledge-preview-section"),
  warningPanel: document.querySelector("#warning-panel"),
  warningList: document.querySelector("#warning-list"),
  resultCount: document.querySelector("#result-count"),
  reviewCompleteButton: document.querySelector("#review-complete-button"),
  publishStoreName: document.querySelector("#publish-store-name"),
  publishProductCount: document.querySelector("#publish-product-count"),
  publishAliasCount: document.querySelector("#publish-alias-count"),
  publishKnowledgeCount: document.querySelector("#publish-knowledge-count"),
  publishConfirmation: document.querySelector("#publish-confirmation"),
  publishButton: document.querySelector("#publish-button"),
  publishedVersionCopy: document.querySelector("#published-version-copy"),
  testForm: document.querySelector("#test-form"),
  testInput: document.querySelector("#test-message-input"),
  testSendButton: document.querySelector("#test-send-button"),
  testMessages: document.querySelector("#test-messages"),
  testSuggestions: document.querySelector("#test-suggestions"),
};

const appState = {
  serverState: null,
  draft: null,
  warnings: [],
  currentStep: 1,
  enabledSteps: new Set([1]),
  toastTimer: null,
};

const kindLabels = {
  faq: "سؤال پرتکرار",
  rule: "قانون فروشگاه",
  shipping: "ارسال",
  payment: "پرداخت",
  returns: "مرجوعی",
  warranty: "ضمانت",
  policy: "قانون فروشگاه",
  general: "اطلاعات عمومی",
};

function makeClientId(prefix) {
  if (window.crypto && typeof window.crypto.randomUUID === "function") {
    return `${prefix}-${window.crypto.randomUUID()}`;
  }
  return `${prefix}-${Date.now()}-${Math.random().toString(16).slice(2)}`;
}

function toEnglishDigits(value) {
  return String(value ?? "")
    .replace(/[۰-۹]/g, (digit) => String("۰۱۲۳۴۵۶۷۸۹".indexOf(digit)))
    .replace(/[٠-٩]/g, (digit) => String("٠١٢٣٤٥٦٧٨٩".indexOf(digit)));
}

function toPersianNumber(value) {
  return new Intl.NumberFormat("fa-IR", { maximumFractionDigits: 0 }).format(Number(value) || 0);
}

function formatPrice(value) {
  const number = Number(value);
  if (!Number.isFinite(number)) return "";
  return `${toPersianNumber(number)} تومان`;
}

function parsePrice(value) {
  const clean = toEnglishDigits(value)
    .replace(/[٬،,_\s]/g, "")
    .replace(/[^0-9.]/g, "");
  if (!clean) return null;
  const number = Number(clean);
  return Number.isFinite(number) ? number : null;
}

function cleanText(value) {
  return String(value ?? "").trim();
}

function uniqueStrings(values) {
  const result = [];
  const seen = new Set();
  for (const raw of values || []) {
    const value = cleanText(typeof raw === "string" ? raw : raw?.value ?? raw?.alias ?? raw?.text);
    const key = value.toLocaleLowerCase("fa");
    if (!value || seen.has(key)) continue;
    seen.add(key);
    result.push(value);
  }
  return result;
}

function cloneValue(value) {
  if (value === undefined) return undefined;
  try {
    return JSON.parse(JSON.stringify(value));
  } catch (_error) {
    return value;
  }
}

function setGlobalMessage(message = "") {
  dom.globalMessage.textContent = message;
  dom.globalMessage.hidden = !message;
}

function showToast(message, type = "success") {
  window.clearTimeout(appState.toastTimer);
  dom.toast.textContent = message;
  dom.toast.classList.toggle("error", type === "error");
  dom.toast.hidden = false;
  appState.toastTimer = window.setTimeout(() => {
    dom.toast.hidden = true;
  }, 4500);
}

function setConnectionState(status, label) {
  dom.statusDot.classList.toggle("ready", status === "ready");
  dom.statusDot.classList.toggle("error", status === "error");
  dom.activeVersionLabel.textContent = label;
}

function readableErrorDetail(detail) {
  if (typeof detail === "string") return detail;
  if (Array.isArray(detail)) {
    const messages = detail.map((item) => item?.msg || item?.message || "").filter(Boolean);
    return messages.join("، ");
  }
  if (detail && typeof detail === "object") return detail.message || detail.msg || "";
  return "";
}

async function apiRequest(url, options = {}) {
  const request = {
    credentials: "same-origin",
    ...options,
    headers: {
      Accept: "application/json",
      ...(options.body ? { "Content-Type": "application/json" } : {}),
      ...(options.headers || {}),
    },
  };
  let response;
  try {
    response = await fetch(url, request);
  } catch (_error) {
    throw new Error("ارتباط با سرور برقرار نشد. چند لحظه دیگر دوباره تلاش کنید.");
  }

  let data = null;
  const contentType = response.headers.get("content-type") || "";
  if (contentType.includes("application/json")) {
    try {
      data = await response.json();
    } catch (_error) {
      data = null;
    }
  }

  if (!response.ok) {
    const detail = readableErrorDetail(data?.detail || data?.message || data);
    const error = new Error(detail || "در انجام این کار مشکلی پیش آمد.");
    error.status = response.status;
    error.data = data;
    throw error;
  }
  return data;
}

function enableStep(step) {
  appState.enabledSteps.add(step);
  const button = dom.stepButtons.find((item) => Number(item.dataset.step) === step);
  if (button) button.disabled = false;
}

function showStep(step) {
  if (!appState.enabledSteps.has(step)) return;
  appState.currentStep = step;
  dom.stepPanels.forEach((panel) => {
    const isActive = Number(panel.dataset.stepPanel) === step;
    panel.hidden = !isActive;
    panel.classList.toggle("active", isActive);
  });
  dom.stepButtons.forEach((button) => {
    const buttonStep = Number(button.dataset.step);
    const isActive = buttonStep === step;
    button.classList.toggle("active", isActive);
    button.classList.toggle("completed", buttonStep < step && appState.enabledSteps.has(buttonStep + 1));
    if (isActive) button.setAttribute("aria-current", "step");
    else button.removeAttribute("aria-current");
  });
  setGlobalMessage();
  window.scrollTo({ top: 0, behavior: "smooth" });
  if (step === 4) window.setTimeout(() => dom.testInput.focus(), 120);
}

function makeChip(value, list, records = null, record = null) {
  const chip = document.createElement("span");
  chip.className = "chip";
  const copy = document.createElement("span");
  copy.textContent = value;
  if (cleanText(record?.kind).toLowerCase() === "canonical") {
    chip.classList.add("locked");
    chip.title = "نام اصلی محصول همیشه حفظ می‌شود";
    chip.append(copy);
    list.append(chip);
    return;
  }
  const remove = document.createElement("button");
  remove.type = "button";
  remove.setAttribute("aria-label", `حذف ${value}`);
  remove.textContent = "×";
  remove.addEventListener("click", () => {
    if (records && record) {
      record.approved = false;
    }
    chip.remove();
  });
  chip.append(copy, remove);
  list.append(chip);
}

function renderSimpleChips(list, values) {
  list.replaceChildren();
  for (const value of uniqueStrings(values)) makeChip(value, list);
}

function chipValues(list) {
  return Array.from(list.querySelectorAll(".chip > span"), (chip) => cleanText(chip.textContent)).filter(Boolean);
}

function addSimpleChip(input, list) {
  const rawValues = cleanText(input.value).split(/[،,]/);
  const values = uniqueStrings([...chipValues(list), ...rawValues]);
  renderSimpleChips(list, values);
  input.value = "";
  input.focus();
}

function bindSimpleChipEditor(container, inputSelector, listSelector) {
  const input = container.querySelector(inputSelector);
  const list = container.querySelector(listSelector);
  const button = input.closest(".chip-input-row").querySelector(".add-chip-button");
  button.addEventListener("click", () => addSimpleChip(input, list));
  input.addEventListener("keydown", (event) => {
    if (event.key === "Enter" || event.key === "," || event.key === "،") {
      event.preventDefault();
      addSimpleChip(input, list);
    }
  });
}

function updateEntryIndexes(list, label) {
  Array.from(list.children).forEach((entry, index) => {
    const number = entry.querySelector(".entry-index");
    const title = entry.querySelector(".entry-card-header strong");
    if (number) number.textContent = toPersianNumber(index + 1);
    if (title) title.textContent = `${label} ${toPersianNumber(index + 1)}`;
  });
}

function normalizeKeywordValues(item) {
  const provided = item?.keywords ?? item?.provided_keywords ?? item?.providedKeywords ?? [];
  return uniqueStrings(provided);
}

function addProductEntry(product = {}) {
  const entry = dom.productEntryTemplate.content.firstElementChild.cloneNode(true);
  entry.dataset.clientId = cleanText(product.client_id || product.clientId) || makeClientId("product");
  if (product.product_id !== undefined && product.product_id !== null) {
    entry.dataset.productId = String(product.product_id);
  } else if (product.id !== undefined && product.id !== null) {
    entry.dataset.productId = String(product.id);
  }

  entry.querySelector(".product-name").value = product.name || "";
  entry.querySelector(".product-description").value = product.description || "";
  entry.querySelector(".product-price").value = product.price ?? "";
  const available = product.is_available ?? product.available ?? true;
  entry.querySelector(".product-available").checked = Boolean(available);
  renderSimpleChips(entry.querySelector(".keyword-list"), normalizeKeywordValues(product));
  bindSimpleChipEditor(entry, ".keyword-input", ".keyword-list");

  const priceInput = entry.querySelector(".product-price");
  const pricePreview = entry.querySelector(".price-preview");
  const updatePrice = () => {
    const parsed = parsePrice(priceInput.value);
    pricePreview.textContent = parsed === null ? "" : formatPrice(parsed);
  };
  priceInput.addEventListener("input", updatePrice);
  updatePrice();

  const availableInput = entry.querySelector(".product-available");
  const availableCopy = entry.querySelector(".availability-copy");
  const updateAvailability = () => {
    availableCopy.textContent = availableInput.checked ? "موجود است" : "فعلاً ناموجود";
  };
  availableInput.addEventListener("change", updateAvailability);
  updateAvailability();

  entry.querySelector(".remove-entry").addEventListener("click", () => {
    if (dom.productEntryList.children.length <= 1) {
      showToast("حداقل یک محصول باید باقی بماند.", "error");
      return;
    }
    entry.remove();
    updateEntryIndexes(dom.productEntryList, "محصول");
  });
  dom.productEntryList.append(entry);
  updateEntryIndexes(dom.productEntryList, "محصول");
  return entry;
}

function addKnowledgeEntry(item = {}) {
  const entry = dom.knowledgeEntryTemplate.content.firstElementChild.cloneNode(true);
  entry.dataset.clientId = cleanText(item.client_id || item.clientId) || makeClientId("knowledge");
  if (item.id !== undefined && item.id !== null) entry.dataset.knowledgeId = String(item.id);
  const kind = item.kind || "faq";
  const select = entry.querySelector(".knowledge-kind");
  if (Array.from(select.options).some((option) => option.value === kind)) select.value = kind;
  entry.querySelector(".knowledge-title").value = item.title || item.question || "";
  entry.querySelector(".knowledge-answer").value = item.answer || "";
  renderSimpleChips(entry.querySelector(".keyword-list"), normalizeKeywordValues(item));
  bindSimpleChipEditor(entry, ".keyword-input", ".keyword-list");
  entry.querySelector(".remove-entry").addEventListener("click", () => {
    entry.remove();
    updateEntryIndexes(dom.knowledgeEntryList, "پاسخ");
    updateKnowledgeEmptyState();
  });
  dom.knowledgeEntryList.append(entry);
  updateEntryIndexes(dom.knowledgeEntryList, "پاسخ");
  updateKnowledgeEmptyState();
  return entry;
}

function updateKnowledgeEmptyState() {
  dom.knowledgeEmpty.hidden = dom.knowledgeEntryList.children.length > 0;
}

function clearValidation() {
  document.querySelectorAll(".field.invalid").forEach((field) => field.classList.remove("invalid"));
}

function markInvalid(input) {
  input.closest(".field")?.classList.add("invalid");
}

function collectEntryPayload() {
  clearValidation();
  const storeName = cleanText(dom.storeName.value);
  let firstInvalid = null;
  if (!storeName) {
    markInvalid(dom.storeName);
    firstInvalid = dom.storeName;
  }

  const products = Array.from(dom.productEntryList.children).map((entry) => {
    const nameInput = entry.querySelector(".product-name");
    const priceInput = entry.querySelector(".product-price");
    const name = cleanText(nameInput.value);
    const price = parsePrice(priceInput.value);
    if (!name) {
      markInvalid(nameInput);
      firstInvalid ||= nameInput;
    }
    if (price === null || price < 0) {
      markInvalid(priceInput);
      firstInvalid ||= priceInput;
    }
    const product = {
      client_id: entry.dataset.clientId,
      name,
      description: cleanText(entry.querySelector(".product-description").value) || null,
      price: price ?? 0,
      is_available: entry.querySelector(".product-available").checked,
      keywords: chipValues(entry.querySelector(".keyword-list")),
    };
    if (entry.dataset.productId) {
      const productId = Number(entry.dataset.productId);
      product.product_id = Number.isFinite(productId) ? productId : entry.dataset.productId;
    }
    return product;
  });

  const knowledgeItems = Array.from(dom.knowledgeEntryList.children).map((entry) => {
    const titleInput = entry.querySelector(".knowledge-title");
    const answerInput = entry.querySelector(".knowledge-answer");
    const title = cleanText(titleInput.value);
    const answer = cleanText(answerInput.value);
    if (!title) {
      markInvalid(titleInput);
      firstInvalid ||= titleInput;
    }
    if (!answer) {
      markInvalid(answerInput);
      firstInvalid ||= answerInput;
    }
    const item = {
      client_id: entry.dataset.clientId,
      kind: entry.querySelector(".knowledge-kind").value,
      title,
      answer,
      keywords: chipValues(entry.querySelector(".keyword-list")),
    };
    return item;
  });

  if (!products.length) {
    setGlobalMessage("حداقل یک محصول اضافه کنید.");
    return null;
  }
  if (firstInvalid) {
    setGlobalMessage("لطفاً خانه‌های ضروری را کامل کنید.");
    firstInvalid.focus();
    firstInvalid.scrollIntoView({ behavior: "smooth", block: "center" });
    return null;
  }
  return { store_name: storeName, products, knowledge_items: knowledgeItems };
}

function parsePossibleJson(value) {
  if (typeof value !== "string") return value;
  try {
    return JSON.parse(value);
  } catch (_error) {
    return null;
  }
}

function draftPayload(draft) {
  if (!draft) return null;
  const candidates = [
    draft.payload,
    draft.draft_payload,
    draft.payload_json,
    draft.analyzed_payload,
    draft.data,
    draft.content,
    draft,
  ];
  for (const candidate of candidates) {
    const parsed = parsePossibleJson(candidate);
    if (parsed && typeof parsed === "object" && Array.isArray(parsed.products)) return parsed;
  }
  return null;
}

function draftId(draft) {
  return draft?.id ?? draft?.draft_id ?? draft?.draftId ?? null;
}

function warningMessage(warning) {
  if (typeof warning === "string") return warning;
  return cleanText(warning?.message || warning?.detail || warning?.text || warning?.title) || "یک مورد نیازمند بررسی است.";
}

function normalizeWarnings(warnings) {
  if (!warnings) return [];
  const list = Array.isArray(warnings) ? warnings : [warnings];
  return list.map((warning) => {
    if (typeof warning === "string") return { message: warning, blocking: false };
    const severity = cleanText(warning?.severity || warning?.level || warning?.kind).toLowerCase();
    return {
      ...warning,
      message: warningMessage(warning),
      blocking: Boolean(warning?.blocking || warning?.is_blocking || severity === "error" || severity === "blocking"),
    };
  });
}

function responseWarnings(response, draft = null) {
  const payload = draftPayload(draft);
  return normalizeWarnings(response?.warnings ?? draft?.warnings ?? payload?.warnings ?? []);
}

function aliasRecord(raw, fallbackSource = "generated") {
  if (typeof raw === "string") return { value: cleanText(raw), source: fallbackSource };
  return {
    ...(raw || {}),
    value: cleanText(raw?.value ?? raw?.alias ?? raw?.text),
    source: cleanText(raw?.source ?? raw?.kind) || fallbackSource,
  };
}

function productAliasRecords(product) {
  const records = [];
  const seen = new Set();
  const add = (raw, source) => {
    const record = aliasRecord(raw, source);
    const key = record.value.toLocaleLowerCase("fa");
    if (!record.value || seen.has(key)) return;
    seen.add(key);
    records.push(record);
  };
  const aliases = product?.aliases ?? product?.alias_suggestions ?? product?.generated_aliases ?? [];
  for (const alias of aliases || []) add(alias, "generated");
  for (const keyword of normalizeKeywordValues(product)) add(keyword, "keyword");
  return records;
}

function categoryValue(product) {
  const category = product?.category ?? product?.category_suggestion ?? product?.suggested_category ?? "";
  if (typeof category === "string") return category;
  return cleanText(category?.name ?? category?.label ?? category?.path ?? category?.value);
}

function renderAliasRecords(card, list, records) {
  list.replaceChildren();
  for (const record of records) {
    if (record.approved !== false) makeChip(record.value, list, records, record);
  }
  card._aliasRecords = records;
}

function addAliasRecord(card, input, list, source = "manager") {
  const values = uniqueStrings(cleanText(input.value).split(/[،,]/));
  const records = card._aliasRecords || [];
  for (const value of values) {
    const key = value.toLocaleLowerCase("fa");
    const existing = records.find((record) => record.value.toLocaleLowerCase("fa") === key);
    if (existing) {
      existing.approved = true;
      existing.source = source;
      existing.kind = existing.kind || source;
    } else {
      records.push({ value, source });
    }
  }
  renderAliasRecords(card, list, records);
  input.value = "";
  input.focus();
}

function bindAliasEditor(card, inputSelector, listSelector, source) {
  const input = card.querySelector(inputSelector);
  const list = card.querySelector(listSelector);
  const button = input.closest(".chip-input-row").querySelector(".add-chip-button");
  button.addEventListener("click", () => addAliasRecord(card, input, list, source));
  input.addEventListener("keydown", (event) => {
    if (event.key === "Enter" || event.key === "," || event.key === "،") {
      event.preventDefault();
      addAliasRecord(card, input, list, source);
    }
  });
}

function productWarnings(product) {
  return normalizeWarnings(product?.warnings ?? product?.issues ?? []);
}

function renderProductPreview(product, index) {
  const card = dom.productPreviewTemplate.content.firstElementChild.cloneNode(true);
  card._sourceProduct = cloneValue(product) || {};
  card._aliasKey = Object.prototype.hasOwnProperty.call(product, "aliases")
    ? "aliases"
    : Object.prototype.hasOwnProperty.call(product, "alias_suggestions")
      ? "alias_suggestions"
      : Object.prototype.hasOwnProperty.call(product, "generated_aliases")
        ? "generated_aliases"
        : "aliases";
  const originalAliases = product[card._aliasKey];
  card._aliasesWereObjects = Array.isArray(originalAliases)
    && originalAliases.some((alias) => alias && typeof alias === "object");
  card.querySelector(".preview-number").textContent = toPersianNumber(index + 1);
  card.querySelector(".preview-product-name").textContent = product.name || "محصول بدون نام";
  const availability = (product.is_available ?? true) ? "موجود" : "ناموجود";
  card.querySelector(".preview-product-facts").textContent = `${formatPrice(product.price)} · ${availability}`;
  card.querySelector(".preview-category").value = categoryValue(product);
  const records = productAliasRecords(product);
  renderAliasRecords(card, card.querySelector(".alias-list"), records);
  bindAliasEditor(card, ".alias-input", ".alias-list", "manager");

  const warnings = productWarnings(product);
  const warningBox = card.querySelector(".card-warning");
  if (warnings.length) {
    warningBox.textContent = warnings.map((warning) => warning.message).join(" — ");
    warningBox.hidden = false;
  }
  dom.productPreviewList.append(card);
}

function knowledgeIsApproved(item) {
  const state = cleanText(item?.review_state || item?.status).toLowerCase();
  if (state === "rejected" || state === "disabled") return false;
  if (typeof item?.approved === "boolean") return item.approved;
  if (typeof item?.is_approved === "boolean") return item.is_approved;
  return true;
}

function renderKnowledgePreview(item) {
  const card = dom.knowledgePreviewTemplate.content.firstElementChild.cloneNode(true);
  card._sourceKnowledge = cloneValue(item) || {};
  card.querySelector(".knowledge-kind-badge").textContent = kindLabels[item.kind] || item.kind || "پاسخ";
  card.querySelector(".preview-knowledge-title").textContent = item.title || item.question || "بدون عنوان";
  card.querySelector(".preview-knowledge-answer").value = item.answer || "";
  const approved = knowledgeIsApproved(item);
  const approvedInput = card.querySelector(".knowledge-approved");
  approvedInput.checked = approved;
  card.classList.toggle("rejected", !approved);
  approvedInput.addEventListener("change", () => card.classList.toggle("rejected", !approvedInput.checked));

  const records = normalizeKeywordValues(item).map((value) => ({ value, source: "keyword" }));
  renderAliasRecords(card, card.querySelector(".knowledge-keyword-list"), records);
  bindAliasEditor(card, ".knowledge-keyword-input", ".knowledge-keyword-list", "manager");
  dom.knowledgePreviewList.append(card);
}

function renderWarnings(warnings) {
  appState.warnings = normalizeWarnings(warnings);
  dom.warningList.replaceChildren();
  for (const warning of appState.warnings) {
    const item = document.createElement("li");
    item.textContent = warning.message;
    dom.warningList.append(item);
  }
  dom.warningPanel.hidden = appState.warnings.length === 0;
}

function renderDraft(draft, warnings = []) {
  const payload = draftPayload(draft);
  if (!payload) throw new Error("پاسخ مرتب‌سازی قابل نمایش نیست.");
  appState.draft = draft;
  dom.productPreviewList.replaceChildren();
  dom.knowledgePreviewList.replaceChildren();
  const products = payload.products || [];
  const knowledgeItems = payload.knowledge_items || payload.knowledgeItems || [];
  products.forEach(renderProductPreview);
  knowledgeItems.forEach(renderKnowledgePreview);
  dom.knowledgePreviewSection.hidden = knowledgeItems.length === 0;
  dom.resultCount.textContent = `${toPersianNumber(products.length)} محصول`;
  renderWarnings(warnings.length ? warnings : payload.warnings || draft?.warnings || []);
  dom.draftBadge.hidden = false;
  enableStep(2);
}

function updateCategoryShape(source, value) {
  const categoryKey = Object.prototype.hasOwnProperty.call(source, "category_suggestion")
    ? "category_suggestion"
    : Object.prototype.hasOwnProperty.call(source, "suggested_category")
      ? "suggested_category"
      : "category";
  const original = source[categoryKey];
  if (original && typeof original === "object") {
    const next = { ...original };
    if (Object.prototype.hasOwnProperty.call(next, "label")) next.label = value;
    else if (Object.prototype.hasOwnProperty.call(next, "path")) next.path = value;
    else if (Object.prototype.hasOwnProperty.call(next, "value")) next.value = value;
    else next.name = value;
    source[categoryKey] = next;
  } else {
    source[categoryKey] = value;
  }
}

function collectPreviewProduct(card) {
  const product = cloneValue(card._sourceProduct) || {};
  updateCategoryShape(product, cleanText(card.querySelector(".preview-category").value));
  const records = (card._aliasRecords || []).filter((record) => cleanText(record.value));
  const keywordRecords = records.filter((record) => {
    const source = cleanText(record.kind || record.source).toLowerCase();
    return record.approved !== false
      && (source === "keyword" || source === "provided" || source === "provided_keyword");
  });
  const aliasRecords = records.filter((record) => !keywordRecords.includes(record));
  product.keywords = uniqueStrings(keywordRecords.map((record) => record.value));
  if (Object.prototype.hasOwnProperty.call(product, "provided_keywords")) {
    product.provided_keywords = [...product.keywords];
  }
  product[card._aliasKey] = aliasRecords.map((record) => ({
    ...record,
    value: cleanText(record.value),
    kind: cleanText(record.kind || record.source) || "generated",
    source: cleanText(record.source || record.kind) || "manager",
  }));
  return product;
}

function collectPreviewKnowledge(card) {
  const item = cloneValue(card._sourceKnowledge) || {};
  item.answer = cleanText(card.querySelector(".preview-knowledge-answer").value);
  item.keywords = uniqueStrings(
    (card._aliasRecords || [])
      .filter((record) => record.approved !== false)
      .map((record) => record.value),
  );
  if (Object.prototype.hasOwnProperty.call(item, "provided_keywords")) {
    item.provided_keywords = [...item.keywords];
  }
  const approved = card.querySelector(".knowledge-approved").checked;
  item.review_state = approved ? "approved" : "rejected";
  if (Object.prototype.hasOwnProperty.call(item, "approved")) item.approved = approved;
  if (Object.prototype.hasOwnProperty.call(item, "is_approved")) item.is_approved = approved;
  return item;
}

function collectPreviewPayload() {
  const currentPayload = draftPayload(appState.draft) || {};
  return {
    ...cloneValue(currentPayload),
    store_name: cleanText(dom.storeName.value) || currentPayload.store_name || "فروشگاه من",
    products: Array.from(dom.productPreviewList.children).map(collectPreviewProduct),
    knowledge_items: Array.from(dom.knowledgePreviewList.children)
      .map(collectPreviewKnowledge)
      .filter((item) => item.review_state === "approved"),
  };
}

function hasBlockingWarnings() {
  return appState.warnings.some((warning) => warning.blocking);
}

function populatePublishSummary() {
  const payload = collectPreviewPayload();
  const aliases = payload.products.reduce((count, product) => {
    const productAliases = product.aliases ?? product.alias_suggestions ?? product.generated_aliases ?? [];
    const aliasCount = Array.isArray(productAliases)
      ? productAliases.filter((alias) => typeof alias === "string" || alias?.approved !== false).length
      : 0;
    return count + aliasCount + normalizeKeywordValues(product).length;
  }, 0);
  const approvedKnowledge = payload.knowledge_items.filter((item) => item.review_state === "approved").length;
  dom.publishStoreName.textContent = payload.store_name;
  dom.publishProductCount.textContent = toPersianNumber(payload.products.length);
  dom.publishAliasCount.textContent = toPersianNumber(aliases);
  dom.publishKnowledgeCount.textContent = toPersianNumber(approvedKnowledge);
  dom.publishConfirmation.checked = false;
  dom.publishButton.disabled = true;
}

function setButtonBusy(button, busy) {
  button.disabled = busy;
  button.classList.toggle("busy", busy);
  button.setAttribute("aria-busy", busy ? "true" : "false");
}

async function analyzeCatalog() {
  const payload = collectEntryPayload();
  if (!payload) return;
  setGlobalMessage();
  setButtonBusy(dom.analyzeButton, true);
  try {
    const response = await apiRequest("/admin/api/drafts/analyze", {
      method: "POST",
      body: JSON.stringify(payload),
    });
    if (!response?.draft) throw new Error("پیش‌نویس از سرور دریافت نشد.");
    renderDraft(response.draft, responseWarnings(response, response.draft));
    showStep(2);
    showToast("محصولات مرتب شدند؛ پیشنهادها را بررسی کنید.");
  } catch (error) {
    setGlobalMessage(error.message);
    showToast(error.message, "error");
  } finally {
    setButtonBusy(dom.analyzeButton, false);
  }
}

async function saveDraft() {
  const id = draftId(appState.draft);
  if (id === null) throw new Error("شناسه پیش‌نویس پیدا نشد؛ دوباره مرتب‌سازی را انجام دهید.");
  const payload = collectPreviewPayload();
  const response = await apiRequest(`/admin/api/drafts/${encodeURIComponent(id)}`, {
    method: "PUT",
    body: JSON.stringify(payload),
  });
  const nextDraft = response?.draft || response || appState.draft;
  appState.draft = nextDraft;
  renderWarnings(responseWarnings(response, nextDraft));
  return response;
}

async function completeReview() {
  setButtonBusy(dom.reviewCompleteButton, true);
  setGlobalMessage();
  try {
    await saveDraft();
    if (hasBlockingWarnings()) {
      setGlobalMessage("یک تداخل مهم باقی مانده است. عبارت‌های مشابه را اصلاح و دوباره ادامه دهید.");
      return;
    }
    populatePublishSummary();
    enableStep(3);
    showStep(3);
    showToast("تغییرات بررسی و ذخیره شد.");
  } catch (error) {
    setGlobalMessage(error.message);
    showToast(error.message, "error");
  } finally {
    setButtonBusy(dom.reviewCompleteButton, false);
  }
}

function activeVersionLabel(version) {
  if (!version) return "";
  return cleanText(version.label || version.name || version.version || version.version_number || version.id);
}

function applyServerState(serverState) {
  appState.serverState = serverState;
  const store = serverState?.store || {};
  const storeName = cleanText(store.name || serverState?.store_name) || cleanText(dom.storeName.value) || "فروشگاه من";
  dom.storeName.value = storeName;
  dom.sidebarStoreName.textContent = storeName;
  const version = serverState?.active_version;
  const versionLabel = activeVersionLabel(version);
  if (version) {
    setConnectionState("ready", versionLabel ? `نسخه فعال ${versionLabel}` : "دستیار فعال است");
    dom.publishedVersionCopy.textContent = versionLabel
      ? `نسخه ${versionLabel} با موفقیت فعال است.`
      : "نسخه جدید با موفقیت فعال است.";
    enableStep(4);
  } else {
    setConnectionState("ready", "هنوز نسخه‌ای فعال نشده است");
  }
}

async function publishDraft() {
  if (!dom.publishConfirmation.checked) return;
  setButtonBusy(dom.publishButton, true);
  setGlobalMessage();
  try {
    await saveDraft();
    if (hasBlockingWarnings()) {
      showStep(2);
      setGlobalMessage("به‌دلیل تداخل عبارت‌های مشابه، نسخه فعال نشد.");
      return;
    }
    const id = draftId(appState.draft);
    const serverState = await apiRequest(`/admin/api/drafts/${encodeURIComponent(id)}/publish`, {
      method: "POST",
      body: JSON.stringify({}),
    });
    applyServerState(serverState || {});
    enableStep(4);
    showStep(4);
    dom.draftBadge.hidden = true;
    showToast("نسخه جدید دستیار با موفقیت فعال شد.");
  } catch (error) {
    setGlobalMessage(error.message);
    showToast(error.message, "error");
  } finally {
    setButtonBusy(dom.publishButton, false);
    dom.publishButton.disabled = !dom.publishConfirmation.checked;
  }
}

function clearEntries() {
  dom.productEntryList.replaceChildren();
  dom.knowledgeEntryList.replaceChildren();
}

function populateEntryForms(payload) {
  clearEntries();
  const products = payload?.products || [];
  const knowledgeItems = payload?.knowledge_items || payload?.knowledgeItems || [];
  products.forEach(addProductEntry);
  knowledgeItems.forEach(addKnowledgeEntry);
  if (!products.length) addProductEntry();
  updateKnowledgeEmptyState();
}

async function loadState() {
  setConnectionState("loading", "در حال دریافت وضعیت...");
  try {
    const serverState = await apiRequest("/admin/api/state");
    applyServerState(serverState || {});
    const latestDraft = serverState?.latest_draft;
    const latestPayload = draftPayload(latestDraft);
    const activePayload = {
      store_name: serverState?.store?.name || serverState?.store_name || "فروشگاه من",
      products: serverState?.products || [],
      knowledge_items: serverState?.knowledge_items || [],
    };
    dom.storeName.value = latestPayload?.store_name || activePayload.store_name;
    dom.sidebarStoreName.textContent = dom.storeName.value;
    populateEntryForms(latestPayload || activePayload);
    enableStep(5);

    const status = cleanText(latestDraft?.status).toLowerCase();
    if (latestDraft && latestPayload && status !== "published" && status !== "superseded") {
      appState.draft = latestDraft;
      renderDraft(latestDraft, responseWarnings(serverState, latestDraft));
      dom.draftBadge.hidden = false;
    }
  } catch (error) {
    setConnectionState("error", "دریافت وضعیت ناموفق بود");
    setGlobalMessage(error.message);
    populateEntryForms({ products: [], knowledge_items: [] });
    enableStep(5);
  }
}

function appendTestMessage(role, text, product = null) {
  const row = document.createElement("div");
  row.className = `chat-row ${role === "user" ? "user-row" : "assistant-row"}`;
  const bubble = document.createElement("div");
  bubble.className = "chat-bubble";
  const copy = document.createElement("div");
  copy.textContent = text;
  bubble.append(copy);
  if (product) {
    const productCopy = document.createElement("div");
    productCopy.className = "chat-product";
    const price = product.price === undefined || product.price === null ? "" : ` · ${formatPrice(product.price)}`;
    productCopy.textContent = `${product.name || "محصول"}${price}`;
    bubble.append(productCopy);
  }
  row.append(bubble);
  dom.testMessages.append(row);
  dom.testMessages.scrollTop = dom.testMessages.scrollHeight;
  return row;
}

function showTyping() {
  const row = document.createElement("div");
  row.className = "chat-row assistant-row";
  row.id = "test-typing";
  const bubble = document.createElement("div");
  bubble.className = "chat-bubble typing-bubble";
  bubble.setAttribute("aria-label", "دستیار در حال پاسخ‌دادن است");
  bubble.append(document.createElement("i"), document.createElement("i"), document.createElement("i"));
  row.append(bubble);
  dom.testMessages.append(row);
  dom.testMessages.scrollTop = dom.testMessages.scrollHeight;
}

function hideTyping() {
  document.querySelector("#test-typing")?.remove();
}

async function testMessage(message) {
  const cleanMessage = cleanText(message);
  if (!cleanMessage || dom.testSendButton.disabled) return;
  appendTestMessage("user", cleanMessage);
  dom.testInput.value = "";
  dom.testSendButton.disabled = true;
  showTyping();
  try {
    const response = await apiRequest("/admin/api/test", {
      method: "POST",
      body: JSON.stringify({ message: cleanMessage }),
    });
    hideTyping();
    appendTestMessage("assistant", response?.reply || "پاسخی دریافت نشد.", response?.product || null);
  } catch (error) {
    hideTyping();
    appendTestMessage("assistant", `آزمایش انجام نشد: ${error.message}`);
  } finally {
    dom.testSendButton.disabled = false;
    dom.testInput.focus();
  }
}

dom.addProductButton.addEventListener("click", () => {
  const entry = addProductEntry();
  entry.querySelector(".product-name").focus();
});

dom.addKnowledgeButton.addEventListener("click", () => {
  const entry = addKnowledgeEntry();
  entry.querySelector(".knowledge-title").focus();
});

dom.analyzeButton.addEventListener("click", analyzeCatalog);
dom.reviewCompleteButton.addEventListener("click", completeReview);
dom.publishConfirmation.addEventListener("change", () => {
  dom.publishButton.disabled = !dom.publishConfirmation.checked;
});
dom.publishButton.addEventListener("click", publishDraft);

dom.storeName.addEventListener("input", () => {
  const name = cleanText(dom.storeName.value) || "فروشگاه من";
  dom.sidebarStoreName.textContent = name;
});

dom.stepButtons.forEach((button) => {
  button.addEventListener("click", () => {
    const step = Number(button.dataset.step);
    if (step === 3) populatePublishSummary();
    showStep(step);
  });
});

document.querySelectorAll("[data-go-step]").forEach((button) => {
  button.addEventListener("click", () => showStep(Number(button.dataset.goStep)));
});

dom.testForm.addEventListener("submit", (event) => {
  event.preventDefault();
  testMessage(dom.testInput.value);
});

dom.testSuggestions.addEventListener("click", (event) => {
  const button = event.target.closest("[data-test-message]");
  if (button) testMessage(button.dataset.testMessage || "");
});

loadState();
