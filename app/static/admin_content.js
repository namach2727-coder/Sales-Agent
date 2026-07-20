"use strict";

const contentDom = {
  productSelect: document.querySelector("#content-product-select"),
  imageInput: document.querySelector("#content-image-input"),
  uploadZone: document.querySelector("#content-upload-zone"),
  assetGallery: document.querySelector("#content-asset-gallery"),
  assetsEmpty: document.querySelector("#content-assets-empty"),
  generateButton: document.querySelector("#content-generate-button"),
  publishStatus: document.querySelector("#content-publish-status"),
  draftStatus: document.querySelector("#content-draft-status"),
  previewStore: document.querySelector("#content-preview-store"),
  previewImage: document.querySelector("#content-preview-image"),
  imagePlaceholder: document.querySelector("#content-image-placeholder"),
  previewCaption: document.querySelector("#content-preview-caption"),
  editor: document.querySelector("#content-editor"),
  captionInput: document.querySelector("#content-caption-input"),
  hashtagsInput: document.querySelector("#content-hashtags-input"),
  altInput: document.querySelector("#content-alt-input"),
  salesKeywords: document.querySelector("#content-sales-keywords"),
  saveButton: document.querySelector("#content-save-button"),
  approveButton: document.querySelector("#content-approve-button"),
  publishButton: document.querySelector("#content-publish-button"),
  publishHelp: document.querySelector("#content-publish-help"),
  globalMessage: document.querySelector("#global-message"),
};

const contentState = {
  data: null,
  productId: null,
  assetId: null,
  draft: null,
  busy: false,
};

function contentClean(value) {
  return String(value ?? "").trim();
}

function contentNotify(message = "", isError = false) {
  contentDom.globalMessage.textContent = message;
  contentDom.globalMessage.hidden = !message;
  contentDom.globalMessage.classList.toggle("error", isError);
}

function contentErrorDetail(detail) {
  if (typeof detail === "string") return detail;
  if (Array.isArray(detail)) return detail.map((item) => item?.msg || "").filter(Boolean).join("، ");
  return detail?.message || detail?.msg || "";
}

async function contentRequest(url, options = {}) {
  const response = await fetch(url, {
    credentials: "same-origin",
    ...options,
    headers: {
      Accept: "application/json",
      ...(options.body ? { "Content-Type": "application/json" } : {}),
      ...(options.headers || {}),
    },
  });
  let data = null;
  try {
    data = await response.json();
  } catch (_error) {
    data = null;
  }
  if (!response.ok) {
    throw new Error(contentErrorDetail(data?.detail || data) || "انجام این کار ناموفق بود.");
  }
  return data;
}

function contentSetBusy(button, busy, label = "در حال انجام...") {
  if (!button.dataset.originalLabel) button.dataset.originalLabel = button.textContent;
  button.disabled = busy;
  button.textContent = busy ? label : button.dataset.originalLabel;
}

function currentContentProduct() {
  return (contentState.data?.products || []).find((item) => Number(item.id) === Number(contentState.productId)) || null;
}

function currentContentAsset() {
  return (currentContentProduct()?.assets || []).find((item) => item.id === contentState.assetId) || null;
}

function contentModuleEnabled(code) {
  return Boolean(contentState.data?.modules?.[code]?.enabled);
}

function renderContentModuleAccess() {
  const canCreate = contentModuleEnabled("content_strategy");
  const canReview = contentModuleEnabled("content_review");
  contentDom.imageInput.disabled = !canCreate;
  contentDom.uploadZone.classList.toggle("module-disabled", !canCreate);
  contentDom.uploadZone.setAttribute("aria-disabled", String(!canCreate));
  contentDom.captionInput.disabled = !canReview;
  contentDom.hashtagsInput.disabled = !canReview;
  contentDom.altInput.disabled = !canReview;
  if (!canCreate) {
    contentDom.publishHelp.textContent = "ماژول استراتژی و تولید محتوا برای این فروشگاه خاموش است؛ از پنجره «ماژول‌ها» آن را فعال کنید.";
  } else if (!canReview) {
    contentDom.publishHelp.textContent = "برای ویرایش و تأیید نهایی، ماژول بازبینی محتوا را فعال کنید.";
  }
}

function renderPublishingReadiness() {
  const status = contentState.data?.publishing || {};
  contentDom.publishStatus.classList.toggle("ready", Boolean(status.ready));
  contentDom.publishStatus.querySelector("strong").textContent = status.ready
    ? "انتشار مستقیم اینستاگرام آماده است"
    : "تولید محتوا فعال است؛ انتشار مستقیم هنوز غیرفعال است";
  const reason = status.reason || "پس از تأیید متن، پست مستقیماً در پیج منتشر می‌شود.";
  contentDom.publishStatus.querySelector("p").textContent = reason;
  const activeCatalog = Boolean(contentState.data?.active_catalog);
  contentDom.publishHelp.textContent = !activeCatalog
    ? "برای انتشار واقعی، ابتدا اطلاعات این محصول را در مرحله فعال‌سازی به ایجنت بدهید."
    : reason;
}

function renderContentProducts() {
  const previous = Number(contentState.productId);
  contentDom.productSelect.replaceChildren();
  for (const product of contentState.data?.products || []) {
    const option = document.createElement("option");
    option.value = String(product.id);
    option.textContent = product.name;
    contentDom.productSelect.append(option);
  }
  const products = contentState.data?.products || [];
  const selected = products.some((item) => Number(item.id) === previous) ? previous : products[0]?.id;
  contentState.productId = selected ? Number(selected) : null;
  contentDom.productSelect.value = selected ? String(selected) : "";
  contentDom.productSelect.disabled = !products.length;
}

function setPreviewAsset(asset) {
  if (!asset) {
    contentDom.previewImage.hidden = true;
    contentDom.previewImage.removeAttribute("src");
    contentDom.imagePlaceholder.hidden = false;
    return;
  }
  contentDom.previewImage.src = `${asset.preview_url}?v=${encodeURIComponent(asset.id)}`;
  contentDom.previewImage.hidden = false;
  contentDom.imagePlaceholder.hidden = true;
}

function contentStatusLabel(status) {
  const labels = {
    draft: "پیش‌نویس؛ نیازمند بررسی",
    approved: "عکس و متن تأیید شده",
    publishing: "در حال انتشار",
    published: "در اینستاگرام منتشر شد",
    failed: "انتشار ناموفق؛ پیش‌نویس محفوظ است",
    unknown: "وضعیت انتشار نامشخص؛ ابتدا پیج را بررسی کنید",
  };
  return labels[status] || "پیش‌نویس محتوا";
}

function renderSalesKeywords(values) {
  contentDom.salesKeywords.replaceChildren();
  for (const value of values || []) {
    const chip = document.createElement("span");
    chip.className = "chip";
    chip.textContent = value;
    contentDom.salesKeywords.append(chip);
  }
}

function renderContentDraft(draft) {
  contentState.draft = draft || null;
  contentDom.editor.hidden = !draft;
  if (!draft) {
    contentDom.draftStatus.textContent = "هنوز پیش‌نویسی ساخته نشده";
    contentDom.draftStatus.className = "content-status-badge";
    contentDom.previewCaption.textContent = "بعد از ساخت محتوا، متن نهایی پست را اینجا می‌بینید.";
    contentDom.publishButton.disabled = true;
    return;
  }
  contentState.productId = Number(draft.product_id);
  contentState.assetId = draft.media?.id || null;
  contentDom.captionInput.value = draft.caption || "";
  contentDom.hashtagsInput.value = (draft.hashtags || []).join(" ");
  contentDom.altInput.value = draft.alt_text || "";
  renderSalesKeywords(draft.sales_keywords || []);
  contentDom.previewCaption.textContent = [draft.caption, (draft.hashtags || []).join(" ")].filter(Boolean).join("\n\n");
  contentDom.draftStatus.textContent = contentStatusLabel(draft.status);
  contentDom.draftStatus.className = `content-status-badge ${draft.status || ""}`;
  setPreviewAsset(draft.media || currentContentAsset());
  const canReview = contentModuleEnabled("content_review");
  const ready = Boolean(
    contentState.data?.publishing?.ready
      && contentState.data?.active_catalog
      && contentModuleEnabled("instagram_publish")
  );
  contentDom.publishButton.disabled = draft.status !== "approved" || !ready;
  contentDom.approveButton.disabled = !canReview || draft.status === "published" || draft.status === "publishing";
  contentDom.saveButton.disabled = !canReview || draft.status === "published" || draft.status === "publishing";
}

function latestDraftForSelection() {
  return (contentState.data?.drafts || []).find(
    (draft) => Number(draft.product_id) === Number(contentState.productId) && draft.media?.id === contentState.assetId,
  ) || null;
}

function renderContentAssets() {
  const product = currentContentProduct();
  const assets = product?.assets || [];
  if (!assets.some((asset) => asset.id === contentState.assetId)) {
    contentState.assetId = assets[0]?.id || null;
  }
  contentDom.assetGallery.replaceChildren();
  for (const asset of assets) {
    const card = document.createElement("button");
    card.type = "button";
    card.className = `asset-card${asset.id === contentState.assetId ? " selected" : ""}`;
    card.setAttribute("aria-label", `انتخاب تصویر ${asset.filename}`);
    const image = document.createElement("img");
    image.src = asset.preview_url;
    image.alt = asset.filename;
    const remove = document.createElement("span");
    remove.className = "asset-remove";
    remove.textContent = "×";
    remove.setAttribute("role", "button");
    remove.setAttribute("aria-label", "حذف تصویر");
    remove.addEventListener("click", (event) => {
      event.preventDefault();
      event.stopPropagation();
      removeContentAsset(asset);
    });
    card.append(image, remove);
    card.addEventListener("click", () => {
      contentState.assetId = asset.id;
      renderContentAssets();
      setPreviewAsset(asset);
      renderContentDraft(latestDraftForSelection());
      updateGenerateButton();
    });
    contentDom.assetGallery.append(card);
  }
  contentDom.assetsEmpty.hidden = Boolean(assets.length);
  setPreviewAsset(currentContentAsset());
  updateGenerateButton();
}

function updateGenerateButton() {
  contentDom.generateButton.disabled = !contentModuleEnabled("content_strategy")
    || !contentState.productId
    || !contentState.assetId
    || contentState.busy;
}

function parseContentHashtags(value) {
  const seen = new Set();
  const result = [];
  for (const raw of String(value || "").split(/[\s,،]+/)) {
    const clean = raw.trim().replace(/^#+/, "");
    if (!clean) continue;
    const hashtag = `#${clean}`;
    const key = hashtag.toLocaleLowerCase("fa");
    if (seen.has(key)) continue;
    seen.add(key);
    result.push(hashtag);
    if (result.length >= 30) break;
  }
  return result;
}

async function prepareContentImage(file) {
  if (!file || !file.type.startsWith("image/")) throw new Error("یک فایل تصویری انتخاب کنید.");
  if (file.size > 15 * 1024 * 1024) throw new Error("حجم فایل اولیه باید کمتر از ۱۵ مگابایت باشد.");
  let bitmap;
  try {
    bitmap = await createImageBitmap(file);
  } catch (_error) {
    throw new Error("این فرمت تصویر قابل خواندن نیست؛ JPG، PNG یا WebP انتخاب کنید.");
  }
  const size = 1080;
  const canvas = document.createElement("canvas");
  canvas.width = size;
  canvas.height = size;
  const context = canvas.getContext("2d", { alpha: false });
  context.fillStyle = "#ffffff";
  context.fillRect(0, 0, size, size);
  const scale = Math.min(size / bitmap.width, size / bitmap.height);
  const width = Math.max(1, Math.round(bitmap.width * scale));
  const height = Math.max(1, Math.round(bitmap.height * scale));
  context.drawImage(bitmap, Math.round((size - width) / 2), Math.round((size - height) / 2), width, height);
  bitmap.close();
  const dataUrl = canvas.toDataURL("image/jpeg", 0.9);
  if (!dataUrl.startsWith("data:image/jpeg;base64,")) throw new Error("آماده‌سازی تصویر ناموفق بود.");
  const baseName = (file.name || "product").replace(/\.[^.]+$/, "").slice(0, 220);
  return { filename: `${baseName || "product"}.jpg`, data_url: dataUrl };
}

async function uploadContentImage(file) {
  if (!contentModuleEnabled("content_strategy")) {
    contentNotify("ماژول استراتژی و تولید محتوا برای این فروشگاه فعال نیست.", true);
    return;
  }
  if (!contentState.productId || contentState.busy) return;
  contentState.busy = true;
  contentNotify("تصویر در حال آماده‌سازی است...");
  try {
    const payload = await prepareContentImage(file);
    const response = await contentRequest(`/admin/api/products/${encodeURIComponent(contentState.productId)}/media`, {
      method: "POST",
      body: JSON.stringify(payload),
    });
    await loadContentStudio(response?.asset?.id);
    contentNotify("تصویر با موفقیت اضافه شد.");
  } catch (error) {
    contentNotify(error.message, true);
  } finally {
    contentState.busy = false;
    contentDom.imageInput.value = "";
    updateGenerateButton();
  }
}

async function removeContentAsset(asset) {
  if (!window.confirm("این تصویر حذف شود؟")) return;
  try {
    await contentRequest(`/admin/api/product-media/${encodeURIComponent(asset.id)}`, { method: "DELETE" });
    if (contentState.assetId === asset.id) contentState.assetId = null;
    await loadContentStudio();
    contentNotify("تصویر حذف شد.");
  } catch (error) {
    contentNotify(error.message, true);
  }
}

async function generateContentDraft() {
  if (!contentState.productId || !contentState.assetId) return;
  contentSetBusy(contentDom.generateButton, true, "در حال ساخت محتوا...");
  contentNotify();
  try {
    const response = await contentRequest("/admin/api/content-drafts/generate", {
      method: "POST",
      body: JSON.stringify({ product_id: contentState.productId, media_asset_id: contentState.assetId }),
    });
    contentState.data.drafts.unshift(response.draft);
    renderContentDraft(response.draft);
    contentNotify("متن، هشتگ و عبارت‌های فروش ساخته شد؛ لطفاً آن‌ها را بررسی کنید.");
    contentDom.editor.scrollIntoView({ behavior: "smooth", block: "start" });
  } catch (error) {
    contentNotify(error.message, true);
  } finally {
    contentSetBusy(contentDom.generateButton, false);
    updateGenerateButton();
  }
}

async function saveContentDraft() {
  const draft = contentState.draft;
  if (!draft) return null;
  contentSetBusy(contentDom.saveButton, true, "در حال ذخیره...");
  try {
    const response = await contentRequest(`/admin/api/content-drafts/${encodeURIComponent(draft.id)}`, {
      method: "PUT",
      body: JSON.stringify({
        caption: contentDom.captionInput.value,
        hashtags: parseContentHashtags(contentDom.hashtagsInput.value),
        alt_text: contentDom.altInput.value,
        expected_revision: draft.revision,
      }),
    });
    renderContentDraft(response.draft);
    contentNotify("ویرایش‌های محتوا ذخیره شد.");
    return response.draft;
  } catch (error) {
    contentNotify(error.message, true);
    return null;
  } finally {
    contentSetBusy(contentDom.saveButton, false);
    renderContentDraft(contentState.draft);
  }
}

async function approveContentDraft() {
  let draft = await saveContentDraft();
  if (!draft) return;
  contentSetBusy(contentDom.approveButton, true, "در حال تأیید...");
  try {
    const response = await contentRequest(`/admin/api/content-drafts/${encodeURIComponent(draft.id)}/approve`, {
      method: "POST",
      body: JSON.stringify({ expected_revision: draft.revision }),
    });
    renderContentDraft(response.draft);
    contentNotify("عکس و متن تأیید شد. تا زدن دکمه انتشار، چیزی در اینستاگرام ارسال نمی‌شود.");
  } catch (error) {
    contentNotify(error.message, true);
  } finally {
    contentSetBusy(contentDom.approveButton, false);
    renderContentDraft(contentState.draft);
  }
}

async function publishContentDraft() {
  const draft = contentState.draft;
  if (!draft || draft.status !== "approved") return;
  if (!window.confirm("این عکس و متن همین حالا در پیج اینستاگرام منتشر شود؟")) return;
  contentSetBusy(contentDom.publishButton, true, "در حال انتشار...");
  try {
    const response = await contentRequest(`/admin/api/content-drafts/${encodeURIComponent(draft.id)}/publish`, {
      method: "POST",
      body: JSON.stringify({ expected_revision: draft.revision, confirmation: "publish" }),
    });
    renderContentDraft(response.draft);
    const permalink = response.job?.permalink;
    contentNotify(permalink ? `پست با موفقیت منتشر شد: ${permalink}` : "پست با موفقیت در اینستاگرام منتشر شد.");
  } catch (error) {
    contentNotify(error.message, true);
    await loadContentStudio(contentState.assetId);
  } finally {
    contentSetBusy(contentDom.publishButton, false);
    renderContentDraft(contentState.draft);
  }
}

function markContentDirty() {
  if (!contentState.draft) return;
  contentDom.previewCaption.textContent = [
    contentDom.captionInput.value,
    parseContentHashtags(contentDom.hashtagsInput.value).join(" "),
  ].filter(Boolean).join("\n\n");
  if (contentState.draft.status === "approved") {
    contentDom.draftStatus.textContent = "ویرایش ذخیره‌نشده؛ نیازمند تأیید دوباره";
    contentDom.draftStatus.className = "content-status-badge";
    contentDom.publishButton.disabled = true;
  }
}

async function loadContentStudio(preferredAssetId = null) {
  try {
    const data = await contentRequest("/admin/api/content-studio");
    contentState.data = data;
    contentDom.previewStore.textContent = data.store?.name || "فروشگاه من";
    renderPublishingReadiness();
    renderContentModuleAccess();
    renderContentProducts();
    if (preferredAssetId) contentState.assetId = preferredAssetId;
    renderContentAssets();
    renderContentDraft(latestDraftForSelection());
  } catch (error) {
    contentNotify(error.message, true);
  }
}

contentDom.productSelect.addEventListener("change", () => {
  contentState.productId = Number(contentDom.productSelect.value) || null;
  contentState.assetId = null;
  renderContentAssets();
  renderContentDraft(latestDraftForSelection());
});

contentDom.imageInput.addEventListener("change", () => uploadContentImage(contentDom.imageInput.files?.[0]));
contentDom.uploadZone.addEventListener("dragover", (event) => {
  event.preventDefault();
  contentDom.uploadZone.classList.add("dragging");
});
contentDom.uploadZone.addEventListener("dragleave", () => contentDom.uploadZone.classList.remove("dragging"));
contentDom.uploadZone.addEventListener("drop", (event) => {
  event.preventDefault();
  contentDom.uploadZone.classList.remove("dragging");
  uploadContentImage(event.dataTransfer?.files?.[0]);
});
contentDom.generateButton.addEventListener("click", generateContentDraft);
contentDom.saveButton.addEventListener("click", saveContentDraft);
contentDom.approveButton.addEventListener("click", approveContentDraft);
contentDom.publishButton.addEventListener("click", publishContentDraft);
contentDom.captionInput.addEventListener("input", markContentDirty);
contentDom.hashtagsInput.addEventListener("input", markContentDirty);
contentDom.altInput.addEventListener("input", markContentDirty);

loadContentStudio();
