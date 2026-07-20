(() => {
  "use strict";

  const moduleUi = {
    trigger: document.querySelector("#module-marketplace-trigger"),
    dialog: document.querySelector("#module-marketplace-dialog"),
    dialogShell: document.querySelector(".module-dialog-shell"),
    closeButton: document.querySelector("#module-dialog-close"),
    doneButton: document.querySelector("#module-dialog-done"),
    storeSelect: document.querySelector("#module-store-select"),
    storeName: document.querySelector("#module-store-name"),
    storeDomain: document.querySelector("#module-store-domain"),
    copyDomainButton: document.querySelector("#copy-store-domain"),
    createStoreToggle: document.querySelector("#create-store-toggle"),
    createStoreForm: document.querySelector("#provider-store-form"),
    createStoreName: document.querySelector("#provider-store-name"),
    createStoreSlug: document.querySelector("#provider-store-slug"),
    createStoreSubmit: document.querySelector("#submit-store-create"),
    createStoreCancel: document.querySelector("#cancel-store-create"),
    monthlyTotal: document.querySelector("#module-monthly-total"),
    activeCount: document.querySelector("#module-active-count"),
    storeStatus: document.querySelector("#module-store-status"),
    listCount: document.querySelector("#module-list-count"),
    error: document.querySelector("#module-marketplace-error"),
    loading: document.querySelector("#module-marketplace-loading"),
    grid: document.querySelector("#module-marketplace-grid"),
    toast: document.querySelector("#toast"),
  };

  if (!moduleUi.trigger || !moduleUi.dialog) return;

  const marketplaceState = {
    stores: [],
    selectedStoreSlug: "default",
    marketplace: null,
    requestNumber: 0,
    toastTimer: null,
  };

  const statusLabels = {
    inactive: "غیرفعال",
    trial: "آزمایشی",
    active: "فعال",
    suspended: "متوقف",
  };

  const availabilityLabels = {
    ready: "آماده ارائه",
    beta: "نسخه آزمایشی",
    planned: "به‌زودی",
  };

  const categoryLabels = {
    sales: "فروش",
    content: "محتوا",
    operations: "عملیات",
    analytics: "گزارش",
  };

  const storeStatusLabels = {
    onboarding: "در حال راه‌اندازی",
    active: "فعال",
    suspended: "متوقف",
    disabled: "غیرفعال",
  };

  function createElement(tag, className = "", text = undefined) {
    const element = document.createElement(tag);
    if (className) element.className = className;
    if (text !== undefined) element.textContent = text;
    return element;
  }

  function cleanText(value) {
    return String(value ?? "").trim();
  }

  function toEnglishDigits(value) {
    return String(value ?? "")
      .replace(/[۰-۹]/g, (digit) => String("۰۱۲۳۴۵۶۷۸۹".indexOf(digit)))
      .replace(/[٠-٩]/g, (digit) => String("٠١٢٣٤٥٦٧٨٩".indexOf(digit)));
  }

  function formatNumber(value) {
    return new Intl.NumberFormat("fa-IR", { maximumFractionDigits: 0 }).format(Number(value) || 0);
  }

  function irrToToman(value) {
    const irr = Number(value);
    if (!Number.isFinite(irr)) return 0;
    return Math.round(irr / 10);
  }

  function formatTomanFromIrr(value) {
    return `${formatNumber(irrToToman(value))} تومان`;
  }

  function editableTomanFromIrr(value) {
    return formatNumber(irrToToman(value));
  }

  function parseToman(value) {
    const normalized = toEnglishDigits(value)
      .replace(/[٬،,_\s]/g, "")
      .replace(/[^0-9]/g, "");
    if (!normalized) return null;
    const number = Number(normalized);
    return Number.isSafeInteger(number) ? number : null;
  }

  function readableError(detail) {
    if (typeof detail === "string") return detail;
    if (Array.isArray(detail)) {
      return detail.map((item) => item?.msg || item?.message || "").filter(Boolean).join("، ");
    }
    if (detail && typeof detail === "object") return detail.message || detail.msg || "";
    return "";
  }

  async function moduleApi(url, options = {}) {
    const response = await fetch(url, {
      credentials: "same-origin",
      ...options,
      headers: {
        Accept: "application/json",
        ...(options.body ? { "Content-Type": "application/json" } : {}),
        ...(options.headers || {}),
      },
    }).catch(() => {
      throw new Error("ارتباط با سرور برقرار نشد. دوباره تلاش کنید.");
    });

    let data = null;
    if ((response.headers.get("content-type") || "").includes("application/json")) {
      try {
        data = await response.json();
      } catch (_error) {
        data = null;
      }
    }
    if (!response.ok) {
      throw new Error(readableError(data?.detail || data?.message || data) || "انجام این کار ممکن نشد.");
    }
    return data;
  }

  function showModuleError(message = "") {
    moduleUi.error.textContent = message;
    moduleUi.error.hidden = !message;
  }

  function showModuleToast(message, type = "success") {
    if (!moduleUi.toast) return;
    window.clearTimeout(marketplaceState.toastTimer);
    moduleUi.toast.textContent = message;
    moduleUi.toast.classList.toggle("error", type === "error");
    moduleUi.toast.hidden = false;
    marketplaceState.toastTimer = window.setTimeout(() => {
      moduleUi.toast.hidden = true;
    }, 4200);
  }

  function setButtonBusy(button, busy) {
    button.disabled = busy;
    button.classList.toggle("busy", busy);
    button.setAttribute("aria-busy", busy ? "true" : "false");
  }

  function setMarketplaceLoading(loading) {
    moduleUi.loading.hidden = !loading;
    moduleUi.grid.classList.toggle("loading", loading);
    moduleUi.storeSelect.disabled = loading;
  }

  function safeHttpUrl(value) {
    try {
      const url = new URL(String(value), window.location.origin);
      if (url.protocol === "http:" || url.protocol === "https:") return url.href;
    } catch (_error) {
      return "#";
    }
    return "#";
  }

  function openCreateStoreForm(open) {
    moduleUi.createStoreForm.hidden = !open;
    moduleUi.createStoreToggle.setAttribute("aria-expanded", open ? "true" : "false");
    if (open) window.setTimeout(() => moduleUi.createStoreName.focus(), 50);
  }

  function openMarketplaceDialog() {
    if (!moduleUi.dialog.open) {
      if (typeof moduleUi.dialog.showModal === "function") moduleUi.dialog.showModal();
      else moduleUi.dialog.setAttribute("open", "");
    }
    document.body.classList.add("module-dialog-open");
    showModuleError();
    refreshProviderStoresAndMarketplace();
  }

  function closeMarketplaceDialog() {
    if (typeof moduleUi.dialog.close === "function" && moduleUi.dialog.open) moduleUi.dialog.close();
    else moduleUi.dialog.removeAttribute("open");
    document.body.classList.remove("module-dialog-open");
    moduleUi.trigger.focus();
  }

  function renderStoreOptions(stores, preferredSlug) {
    moduleUi.storeSelect.replaceChildren();
    for (const store of stores) {
      const option = document.createElement("option");
      option.value = store.slug;
      // The dedicated field below shows the full LTR subdomain. Keeping the
      // native RTL select to the store name avoids bidi clipping in browsers.
      option.textContent = store.name;
      moduleUi.storeSelect.append(option);
    }
    const availableSlugs = new Set(stores.map((store) => store.slug));
    const selected = availableSlugs.has(preferredSlug)
      ? preferredSlug
      : availableSlugs.has("default")
        ? "default"
        : stores[0]?.slug || "default";
    marketplaceState.selectedStoreSlug = selected;
    moduleUi.storeSelect.value = selected;
    return selected;
  }

  async function loadProviderStores(preferredSlug = marketplaceState.selectedStoreSlug) {
    const data = await moduleApi("/admin/api/provider/stores");
    marketplaceState.stores = Array.isArray(data?.stores) ? data.stores : [];
    return renderStoreOptions(marketplaceState.stores, preferredSlug);
  }

  async function refreshProviderStoresAndMarketplace() {
    setMarketplaceLoading(true);
    showModuleError();
    try {
      const selected = await loadProviderStores();
      await loadMarketplace(selected, { keepLoading: true });
    } catch (error) {
      showModuleError(error.message);
      showModuleToast(error.message, "error");
    } finally {
      setMarketplaceLoading(false);
    }
  }

  async function loadMarketplace(storeSlug, options = {}) {
    const requestNumber = ++marketplaceState.requestNumber;
    marketplaceState.selectedStoreSlug = storeSlug || "default";
    if (!options.keepLoading) setMarketplaceLoading(true);
    showModuleError();
    try {
      const query = new URLSearchParams({ store_slug: marketplaceState.selectedStoreSlug });
      const data = await moduleApi(`/admin/api/module-marketplace?${query.toString()}`);
      if (requestNumber !== marketplaceState.requestNumber) return;
      renderMarketplace(data);
    } catch (error) {
      if (requestNumber !== marketplaceState.requestNumber) return;
      showModuleError(error.message);
      showModuleToast(error.message, "error");
    } finally {
      if (!options.keepLoading && requestNumber === marketplaceState.requestNumber) {
        setMarketplaceLoading(false);
      }
    }
  }

  function statusLabel(module) {
    if (module.status === "active" && !module.enabled) return "فعال‌سازی ناقص";
    return statusLabels[module.status] || module.status || "نامشخص";
  }

  function statusBadge(module) {
    const badge = createElement(
      "span",
      `module-status-badge status-${module.status || "inactive"}`,
      statusLabel(module),
    );
    return badge;
  }

  function availabilityBadge(module) {
    return createElement(
      "span",
      `module-availability-badge availability-${module.availability || "ready"}`,
      availabilityLabels[module.availability] || module.availability || "آماده",
    );
  }

  function moduleDependencyText(module, moduleNames) {
    const dependencies = Array.isArray(module.dependencies) ? module.dependencies : [];
    if (!dependencies.length) return "";
    const names = dependencies.map((code) => moduleNames.get(code) || code);
    return `نیازمند: ${names.join("، ")}`;
  }

  function makePriceInput(label, irrValue) {
    const field = createElement("label", "module-field");
    field.append(createElement("span", "", label));
    const input = document.createElement("input");
    input.type = "text";
    input.inputMode = "numeric";
    input.maxLength = 18;
    input.value = editableTomanFromIrr(irrValue);
    input.setAttribute("aria-label", label);
    field.append(input);
    return { field, input };
  }

  function makeStatusOption(value, module) {
    const option = document.createElement("option");
    option.value = value;
    option.textContent = statusLabels[value];
    if (module.availability === "planned" && (value === "active" || value === "trial")) {
      option.disabled = true;
    }
    return option;
  }

  function renderModuleCard(module, moduleNames, canManage) {
    const card = createElement("article", "marketplace-module-card");
    card.classList.toggle("enabled", Boolean(module.enabled));
    card.classList.toggle("planned", module.availability === "planned");
    card.dataset.moduleCode = module.code;

    const topLine = createElement("div", "module-card-topline");
    const badges = createElement("div", "module-card-badges");
    badges.append(
      createElement("span", "module-category-badge", categoryLabels[module.category] || module.category || "سایر"),
      statusBadge(module),
      availabilityBadge(module),
    );
    topLine.append(badges);
    card.append(topLine);

    card.append(createElement("h4", "", module.name || module.code));
    card.append(createElement("p", "module-card-description", module.description || "توضیحی ثبت نشده است."));

    const effectivePrice = createElement("div", "module-card-price-line");
    effectivePrice.append(
      createElement("span", "", "هزینه ماهانه این فروشگاه"),
      createElement("strong", "", formatTomanFromIrr(module.monthly_price_irr)),
    );
    card.append(effectivePrice);

    const dependencyCopy = moduleDependencyText(module, moduleNames);
    if (dependencyCopy) card.append(createElement("p", "module-dependencies", dependencyCopy));

    const priceEditor = createElement("div", "module-price-editor");
    const monthlyPrice = makePriceInput("قیمت نمونه ماهانه (تومان)", module.catalog_price_irr);
    const setupPrice = makePriceInput("راه‌اندازی (تومان)", module.setup_price_irr);
    const priceSave = createElement("button", "module-muted-button module-price-save", "ذخیره قیمت نمونه");
    priceSave.type = "button";
    priceSave.disabled = !canManage;
    priceSave.addEventListener("click", () => saveCatalogPrice(module, monthlyPrice.input, setupPrice.input, priceSave));
    priceEditor.append(monthlyPrice.field, setupPrice.field, priceSave);
    card.append(priceEditor);

    const statusEditor = createElement("div", "module-status-editor");
    const statusSelect = document.createElement("select");
    statusSelect.setAttribute("aria-label", `وضعیت ${module.name || module.code}`);
    for (const status of ["inactive", "trial", "active", "suspended"]) {
      statusSelect.append(makeStatusOption(status, module));
    }
    statusSelect.value = module.status || "inactive";

    const statusSave = createElement(
      "button",
      "module-primary-button",
      module.availability === "planned" ? "در برنامه توسعه" : "ذخیره وضعیت",
    );
    statusSave.type = "button";
    statusSave.disabled = !canManage || module.availability === "planned";

    const trialDaysField = createElement("label", "module-field module-trial-days");
    trialDaysField.append(createElement("span", "", "مدت آزمایش (روز)"));
    const trialDays = document.createElement("input");
    trialDays.type = "number";
    trialDays.min = "1";
    trialDays.max = "90";
    trialDays.value = "7";
    trialDaysField.append(trialDays);
    trialDaysField.hidden = statusSelect.value !== "trial";
    statusSelect.addEventListener("change", () => {
      trialDaysField.hidden = statusSelect.value !== "trial";
    });
    statusSave.addEventListener("click", () => saveModuleStatus(module, statusSelect, trialDays, statusSave));

    statusEditor.append(statusSelect, statusSave, trialDaysField);
    card.append(statusEditor);
    return card;
  }

  function renderMarketplace(data) {
    marketplaceState.marketplace = data;
    const store = data?.store || {};
    const modules = Array.isArray(data?.modules) ? data.modules : [];
    marketplaceState.selectedStoreSlug = store.slug || marketplaceState.selectedStoreSlug;
    if (Array.from(moduleUi.storeSelect.options).some((option) => option.value === marketplaceState.selectedStoreSlug)) {
      moduleUi.storeSelect.value = marketplaceState.selectedStoreSlug;
    }

    moduleUi.storeName.textContent = store.name || "فروشگاه بدون نام";
    moduleUi.storeDomain.textContent = store.subdomain || "—";
    moduleUi.storeDomain.href = safeHttpUrl(store.url);
    moduleUi.monthlyTotal.textContent = formatTomanFromIrr(data?.monthly_total_irr);
    const activeModules = modules.filter((module) => module.enabled).length;
    moduleUi.activeCount.textContent = `${formatNumber(activeModules)} از ${formatNumber(modules.length)}`;
    moduleUi.storeStatus.textContent = `وضعیت فروشگاه: ${storeStatusLabels[store.status] || store.status || "نامشخص"}`;
    moduleUi.listCount.textContent = `${formatNumber(modules.length)} ماژول`;

    const moduleNames = new Map(modules.map((module) => [module.code, module.name]));
    moduleUi.grid.replaceChildren();
    for (const module of modules) {
      moduleUi.grid.append(renderModuleCard(module, moduleNames, Boolean(data?.can_manage_modules)));
    }
    showModuleError();
  }

  async function saveCatalogPrice(module, monthlyInput, setupInput, button) {
    const monthlyToman = parseToman(monthlyInput.value);
    const setupToman = parseToman(setupInput.value);
    if (monthlyToman === null || setupToman === null) {
      showModuleError("قیمت ماهانه و راه‌اندازی را به تومان و با عدد معتبر وارد کنید.");
      return;
    }
    const monthlyIrr = monthlyToman * 10;
    const setupIrr = setupToman * 10;
    if (!Number.isSafeInteger(monthlyIrr) || !Number.isSafeInteger(setupIrr) || monthlyIrr > 10 ** 12 || setupIrr > 10 ** 12) {
      showModuleError("مبلغ واردشده از محدوده مجاز بیشتر است.");
      return;
    }

    setButtonBusy(button, true);
    showModuleError();
    try {
      await moduleApi(`/admin/api/provider/module-catalog/${encodeURIComponent(module.code)}`, {
        method: "PATCH",
        body: JSON.stringify({
          monthly_price_irr: monthlyIrr,
          setup_price_irr: setupIrr,
        }),
      });
      showModuleToast(`قیمت نمونه «${module.name}» ذخیره شد.`);
      await loadMarketplace(marketplaceState.selectedStoreSlug);
    } catch (error) {
      showModuleError(error.message);
      showModuleToast(error.message, "error");
    } finally {
      setButtonBusy(button, false);
    }
  }

  async function saveModuleStatus(module, statusSelect, trialDaysInput, button) {
    const status = statusSelect.value;
    const trialDays = status === "trial" ? Number(trialDaysInput.value) : null;
    if (status === "trial" && (!Number.isInteger(trialDays) || trialDays < 1 || trialDays > 90)) {
      showModuleError("مدت آزمایش باید بین ۱ تا ۹۰ روز باشد.");
      return;
    }

    setButtonBusy(button, true);
    showModuleError();
    try {
      const data = await moduleApi(
        `/admin/api/provider/stores/${encodeURIComponent(marketplaceState.selectedStoreSlug)}/modules/${encodeURIComponent(module.code)}`,
        {
          method: "PATCH",
          body: JSON.stringify({
            status,
            trial_days: trialDays,
            custom_monthly_price_irr: null,
          }),
        },
      );
      renderMarketplace(data);
      showModuleToast(`وضعیت «${module.name}» به‌روزرسانی شد.`);
    } catch (error) {
      showModuleError(error.message);
      showModuleToast(error.message, "error");
    } finally {
      setButtonBusy(button, false);
    }
  }

  function clearCreateStoreValidation() {
    moduleUi.createStoreForm.querySelectorAll(".module-field.invalid").forEach((field) => field.classList.remove("invalid"));
  }

  function markCreateStoreInvalid(input) {
    input.closest(".module-field")?.classList.add("invalid");
  }

  async function createProviderStore(event) {
    event.preventDefault();
    clearCreateStoreValidation();
    const name = cleanText(moduleUi.createStoreName.value);
    const slug = cleanText(moduleUi.createStoreSlug.value).toLowerCase();
    let firstInvalid = null;
    if (name.length < 2) {
      markCreateStoreInvalid(moduleUi.createStoreName);
      firstInvalid = moduleUi.createStoreName;
    }
    if (!/^[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?$/.test(slug)) {
      markCreateStoreInvalid(moduleUi.createStoreSlug);
      firstInvalid ||= moduleUi.createStoreSlug;
    }
    if (firstInvalid) {
      showModuleError("نام فروشگاه و ساب‌دامین انگلیسی معتبر را کامل کنید.");
      firstInvalid.focus();
      return;
    }

    setButtonBusy(moduleUi.createStoreSubmit, true);
    showModuleError();
    try {
      const marketplace = await moduleApi("/admin/api/provider/stores", {
        method: "POST",
        body: JSON.stringify({ name, slug }),
      });
      await loadProviderStores(marketplace?.store?.slug || slug);
      renderMarketplace(marketplace);
      moduleUi.createStoreName.value = "";
      moduleUi.createStoreSlug.value = "";
      openCreateStoreForm(false);
      showModuleToast(`فروشگاه «${name}» ساخته شد.`);
    } catch (error) {
      showModuleError(error.message);
      showModuleToast(error.message, "error");
    } finally {
      setButtonBusy(moduleUi.createStoreSubmit, false);
    }
  }

  async function copyStoreDomain() {
    const domain = cleanText(moduleUi.storeDomain.textContent);
    if (!domain || domain === "—") return;
    try {
      if (!window.navigator.clipboard?.writeText) throw new Error("clipboard-unavailable");
      await window.navigator.clipboard.writeText(domain);
      showModuleToast("ساب‌دامین کپی شد.");
    } catch (_error) {
      showModuleError("کپی خودکار در دسترس نیست؛ ساب‌دامین را به‌صورت دستی کپی کنید.");
    }
  }

  moduleUi.trigger.addEventListener("click", openMarketplaceDialog);
  moduleUi.closeButton.addEventListener("click", closeMarketplaceDialog);
  moduleUi.doneButton.addEventListener("click", closeMarketplaceDialog);
  moduleUi.dialog.addEventListener("close", () => document.body.classList.remove("module-dialog-open"));
  moduleUi.dialog.addEventListener("click", (event) => {
    if (event.target !== moduleUi.dialog) return;
    const bounds = moduleUi.dialogShell.getBoundingClientRect();
    const outside = event.clientX < bounds.left
      || event.clientX > bounds.right
      || event.clientY < bounds.top
      || event.clientY > bounds.bottom;
    if (outside) closeMarketplaceDialog();
  });

  moduleUi.storeSelect.addEventListener("change", () => loadMarketplace(moduleUi.storeSelect.value));
  moduleUi.createStoreToggle.addEventListener("click", () => openCreateStoreForm(moduleUi.createStoreForm.hidden));
  moduleUi.createStoreCancel.addEventListener("click", () => openCreateStoreForm(false));
  moduleUi.createStoreForm.addEventListener("submit", createProviderStore);
  moduleUi.createStoreSlug.addEventListener("input", () => {
    moduleUi.createStoreSlug.value = toEnglishDigits(moduleUi.createStoreSlug.value)
      .toLowerCase()
      .replace(/\s+/g, "-")
      .replace(/[^a-z0-9-]/g, "");
  });
  moduleUi.copyDomainButton.addEventListener("click", copyStoreDomain);
})();
