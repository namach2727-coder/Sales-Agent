"use strict";
(() => {
  const app = document.getElementById("main-app");
  const notice = document.getElementById("notice");
  const telegramHelp = document.getElementById("telegram-help");
  const tenantPanel = document.getElementById("create-tenant");
  const workspace = document.getElementById("workspace");
  const tenantForm = document.getElementById("tenant-form");
  const managedForm = document.getElementById("managed-bot-form");
  const telegram = window.Telegram && window.Telegram.WebApp;
  const initData = telegram && telegram.initData ? telegram.initData : "";
  let activeTenant = null;
  const attemptedCredentialSetup = new Set();

  function setNotice(message, kind) {
    notice.textContent = message;
    notice.className = "notice" + (kind ? " " + kind : "");
  }
  function api(path, options = {}) {
    const headers = Object.assign({
      "X-Telegram-Init-Data": initData,
      "Accept": "application/json",
    }, options.headers || {});
    return fetch(path, Object.assign({}, options, {
      credentials: "omit", cache: "no-store", redirect: "error", headers,
    })).then(async response => {
      let payload = {};
      try { payload = await response.json(); } catch (_) { /* generic response */ }
      if (!response.ok) {
        const detail = payload && typeof payload.detail === "string" ? payload.detail : "request_failed";
        const error = new Error(detail);
        error.httpStatus = response.status;
        error.authShape = response.headers.get("X-TelBot-UAT-Auth-Shape") || "";
        error.ed25519 = response.headers.get("X-TelBot-UAT-Ed25519") || "";
        error.hmacDiag = response.headers.get("X-TelBot-UAT-HMAC-Diag") || "";
        throw error;
      }
      return payload;
    });
  }
  function publicError(error) {
    const code = error && error.message ? error.message : "";
    const map = {
      "Bot must be activated before reply control": "ابتدا ربات را فعال کن.",
      "Bot reply state changed; refresh before retrying": "وضعیت پاسخ‌گویی تغییر کرده؛ تنظیمات را ببند و فهرست ربات‌ها را تازه کن.",
      "Invalid bot configuration": "تنظیمات پاسخ‌ها معتبر نیست؛ کادرهای متن و API را بررسی کن.",
      "Published configuration changed; reload before saving": "نسخهٔ ربات تغییر کرده؛ فرم را ببند و دوباره باز کن.",
      "Published configuration changed; reload before publishing": "نسخهٔ تازه‌ای منتشر شده؛ قبل از انتشار دوباره تنظیمات را بارگذاری کن.",
      "API configuration unavailable": "تنظیمات امن API فعلاً قابل بازیابی نیست؛ انتشار متوقف شد.",
      "API actions schema not ready": "بخش اتصال API هنوز روی سرویس آماده نشده است.",
      "API source rule changed": "قانون API تغییر کرده؛ فرم را دوباره باز کن.",
      "api_credential_required": "برای اتصال جدید یا تغییر نشانی API، کلید را دوباره وارد کن.",
      "api_vault_unavailable": "ذخیرهٔ امن اطلاعات API فعلاً در دسترس نیست.",
      "Telegram account already has a tenant": "برای این حساب قبلاً فضای کاری ساخته شده است.",
      "Bot credential encryption unavailable": "ذخیره امن توکن فعلاً آماده نیست؛ دوباره تلاش نکن.",
      "invalid_token_format": "ساختار توکن معتبر نیست؛ توکن API را از BotFather بررسی کن.",
      "token_rejected": "توکن از طرف تلگرام تأیید نشد؛ آن را در BotFather بررسی کن.",
      "telegram_unavailable": "ارتباط با تلگرام موقتاً برقرار نشد.",
      "Bot already connected": "این ربات قبلاً به یک حساب متصل شده است.",
      "Invalid Telegram Mini App authentication": "نشست تلگرام معتبر نیست؛ Mini App را دوباره باز کن.",
      "missing_init_data": "اطلاعات ورود تلگرام ارسال نشده است. پنل را از دکمه Mini App ربات مدیریتی باز کن.",
      "malformed_init_data": "ساختار اطلاعات ورود تلگرام معتبر نیست. Mini App را ببند و دوباره باز کن.",
      "invalid_signature": "امضای نشست با ربات مدیریتی سرور مطابقت ندارد. تنظیمات ربات و دکمه Mini App باید بررسی شوند.",
      "malformed_account": "شناسه حساب تلگرام در نشست معتبر نیست. Mini App را دوباره باز کن.",
      "expired_auth_date": "اعتبار نشست تلگرام به پایان رسیده است. پنل را از داخل تلگرام دوباره باز کن.",
      "Tenant membership required": "به این حساب دسترسی نداری.",
    };
    const description = map[code] || "درخواست انجام نشد. برای ادامه Mini App را دوباره باز کن.";
    const shape = error && typeof error.authShape === "string" && /^q[01]_c[01]_s[01]_u[01]_a[01]$/.test(error.authShape) ? error.authShape : "";
    if (shape && code === "invalid_signature") {
      const check = error && ["valid", "invalid", "unavailable"].includes(error.ed25519) ? error.ed25519 : "unavailable";
      const hmac = error && ["unavailable", "token_whitespace", "signature_field_included", "key_or_payload_mismatch"].includes(error.hmacDiag) ? error.hmacDiag : "unavailable";
      return description + " (کد تشخیصی: " + shape + " | Ed25519: " + check + " | HMAC: " + hmac + ")";
    }
    if (!Object.prototype.hasOwnProperty.call(map, code)) {
      const status = error && Number.isInteger(error.httpStatus) && error.httpStatus >= 400 && error.httpStatus <= 599 ? error.httpStatus : 0;
      return description + (status ? " (HTTP " + status + ")" : " (خطای ارتباط با API)");
    }
    return description;
  }
  async function listBots() {
    // Returning to the app must not replace an editor or discard unsaved input.
    if (document.querySelector(".reply-editor")) return;
    const root = document.getElementById("bots-list");
    root.textContent = "در حال دریافت ربات‌ها…";
    try {
      const bots = await api("/api/v1/tenants/" + activeTenant.id + "/bots");
      if (document.querySelector(".reply-editor")) return;
      ["onboarding-intro", "onboarding-steps"].forEach(id => {
        const element = document.getElementById(id); if (element) element.hidden = bots.length > 0;
      });
      root.replaceChildren();
      if (!bots.length) { root.textContent = "هنوز رباتی متصل نکرده‌ای."; root.className = "bot-empty"; return; }
      root.className = "bot-list";
      // Complete managed-bot credential setup on the server, with no user token input.
      // One attempt per bot per page load; failures remain pending and retry on next opening.
      for (const bot of bots) {
        if (bot.is_managed === true && bot.credential_ready !== true &&
            bot.status === "pending" && !attemptedCredentialSetup.has(bot.id) &&
            activeTenant.role === "owner") {
          attemptedCredentialSetup.add(bot.id);
          try {
            await api("/api/v1/tenants/" + activeTenant.id +
              "/bots/" + bot.id + "/prepare-managed-credential", {method: "POST"});
            setNotice("اطلاعات امن ربات دریافت شد؛ فعال‌سازی جداگانه انجام می‌شود.", "success");
            await listBots();
            return;
          } catch (_) {
            setNotice("ربات ثبت شد، ولی تکمیل اتصال امن هنوز ممکن نیست؛ پس از مدتی پنل را دوباره باز کن.", "error");
          }
        }
      }
      bots.forEach(bot => {
        const row = document.createElement("article"); row.className = "bot-row";
        const meta = document.createElement("div");
        const name = document.createElement("strong");
        name.textContent = bot.username ? "@" + bot.username : "ربات تلگرام";
        const detail = document.createElement("small");
        detail.textContent = bot.display_name || "";
        meta.append(name, detail);
        const state = document.createElement("span"); state.className = "pending";
        state.textContent = bot.status === "pending" ? "در انتظار فعال‌سازی" : bot.status === "active" ? "فعال" : bot.status === "paused" ? "پاسخ‌گویی متوقف" : "متوقف";
        const header = document.createElement("div"); header.className = "bot-card-header";
        meta.className = "bot-identity";
        header.append(meta, state);
        const actions = document.createElement("div"); actions.className = "bot-actions";
        row.append(header, actions);
        if (bot.status === "pending" && bot.is_managed === true &&
            bot.credential_ready === true && activeTenant.role === "owner") {
          const activate = document.createElement("button");
          activate.type = "button";
          activate.textContent = "فعال‌سازی ربات";
          activate.addEventListener("click", async () => {
            activate.disabled = true;
            activate.textContent = "در حال بررسی و فعال‌سازی…";
            try {
              const result = await api("/api/v1/tenants/" + activeTenant.id +
                "/bots/" + bot.id + "/activate-managed", {method:"POST"});
              setNotice(result.status === "active" ?
                "Webhook اختصاصی ربات با موفقیت تأیید شد. وضعیت ربات فعال است." :
                "پاسخ فعال‌سازی نامشخص است.", "success");
              await listBots();
            } catch(error) {
              setNotice("خطای فعال‌سازی: " + publicError(error), "error");
              activate.textContent = "تلاش دوباره برای فعال‌سازی";
            } finally { activate.disabled = false; }
          });
          actions.append(activate);
        }
        if (activeTenant.role === "owner" || activeTenant.role === "editor") {
          const edit = document.createElement("button");
          edit.type = "button";
          edit.textContent = "تنظیم پیام‌های ربات";
          edit.addEventListener("click", () => openReplyEditor(bot, row, edit));
          actions.append(edit);
        }
        const activity = document.createElement("button"); activity.type = "button";
        activity.className = "button-secondary"; activity.textContent = "گزارش عملکرد";
        activity.addEventListener("click", () => openActivity(bot, row, activity)); actions.append(activity);
        if (["owner","editor"].includes(activeTenant.role) && ["active","paused"].includes(bot.status)) {
          const toggle = document.createElement("button"); toggle.type = "button"; toggle.className = "button-secondary reply-toggle";
          const feedback = document.createElement("p"); feedback.className = "reply-state-status hint"; feedback.setAttribute("role", "status"); feedback.setAttribute("aria-live", "polite");
          function label() { toggle.textContent = bot.status === "paused" ? "ادامهٔ پاسخ خودکار" : "توقف پاسخ خودکار"; }
          label(); feedback.textContent = "توقف برای پیام‌های بعدی است؛ پاسخِ در حال ارسال ممکن است کامل شود.";
          toggle.addEventListener("click", async () => {
            if (toggle.disabled) return;
            const paused = bot.status === "active"; toggle.disabled = true;
            feedback.textContent = paused ? "در حال توقف پاسخ خودکار…" : "در حال ادامهٔ پاسخ خودکار…";
            try {
              const result = await api("/api/v1/tenants/" + activeTenant.id + "/bots/" + bot.id + "/reply-state", {method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({paused,expected_status:bot.status})});
              if (!row.isConnected) return;
              bot.status = result.status; state.textContent = bot.status === "paused" ? "پاسخ‌گویی متوقف" : "فعال"; label();
              feedback.textContent = bot.status === "paused" ? "پاسخ خودکار متوقف شد؛ پیام‌های ورودی همچنان ثبت می‌شوند." : result.runtime_enabled ? "پاسخ خودکار برای پیام‌های جدید ادامه یافت؛ پیام‌های زمان توقف دوباره ارسال نمی‌شوند." : "ربات آماده است؛ ارسال خودکار روی سرویس هنوز فعال نشده است.";
            } catch (error) { if (row.isConnected) feedback.textContent = "تغییر وضعیت تأیید نشد: " + publicError(error); }
            finally { toggle.disabled = false; }
          }); actions.append(toggle); row.append(feedback);
        }
        root.append(row);
      });
    } catch(error) { root.textContent = publicError(error); }
  }
  async function openActivity(bot, row, opener) {
    opener.disabled = true;
    const panel = document.createElement("section"); panel.className = "activity-panel";
    const title = document.createElement("h3"); title.textContent = "عملکرد ربات در ۲۴ ساعت گذشته";
    const hint = document.createElement("p"); hint.className = "hint";
    hint.textContent = "فقط تعداد و وضعیت پیام‌ها نمایش داده می‌شود. پیام‌های قبل از فعال‌شدن پاسخ خودکار ممکن است پاسخی نداشته باشند.";
    const status = document.createElement("p"); status.className = "activity-status"; status.setAttribute("role", "status"); status.setAttribute("aria-live", "polite");
    const result = document.createElement("div"); result.className = "activity-result";
    const actions = document.createElement("div"); actions.className = "editor-actions";
    const refresh = document.createElement("button"); refresh.type = "button"; refresh.textContent = "به‌روزرسانی گزارش";
    const close = document.createElement("button"); close.type = "button"; close.className = "button-secondary"; close.textContent = "بستن گزارش";
    actions.append(refresh, close); panel.append(title, hint, status, result, actions); row.append(panel);
    close.addEventListener("click", () => { panel.remove(); opener.disabled = false; opener.focus(); });
    function time(value) {
      const date = new Date(value);
      return Number.isNaN(date.getTime()) ? "زمان نامشخص" : new Intl.DateTimeFormat("fa-IR", {hour:"2-digit",minute:"2-digit",month:"short",day:"numeric"}).format(date);
    }
    async function load() {
      if (refresh.disabled) return;
      refresh.disabled = true; status.textContent = "در حال دریافت گزارش…"; panel.setAttribute("aria-busy", "true");
      try {
        const data = await api("/api/v1/tenants/" + activeTenant.id + "/bots/" + bot.id + "/activity");
        if (!panel.isConnected) return;
        const fragment = document.createDocumentFragment(), stats = document.createElement("dl"); stats.className = "activity-stats";
        [["received","پیام دریافتی"],["sent","پاسخ ارسال‌شده"],["failed","ارسال ناموفق"],["pending","ارسال در انتظار تعیین نتیجه"]].forEach(([key,label]) => {
          const card = document.createElement("div"), name = document.createElement("dt"), value = document.createElement("dd");
          name.textContent = label; value.textContent = Number(data.summary[key]).toLocaleString("fa-IR"); card.append(name,value); stats.append(card);
        }); fragment.append(stats);
        const heading = document.createElement("h4"); heading.textContent = "آخرین پیام‌ها · حداکثر ۲۰ مورد"; fragment.append(heading);
        const list = document.createElement("ul"); list.className = "activity-events";
        data.events.forEach(event => {
          const item = document.createElement("li"), at = document.createElement("time"), state = document.createElement("span");
          at.textContent = time(event.received_at);
          state.textContent = event.delivery_status === "sent" && event.telegram_acknowledged ? "پاسخ ارسال شد" : event.delivery_status === "sent" ? "ارسال ثبت شده؛ تأیید تلگرام موجود نیست" : event.delivery_status === "failed" ? "ارسال پاسخ ناموفق بود" : event.delivery_status === "queued" ? "نتیجهٔ ارسال هنوز مشخص نیست" : "دریافت شد؛ پاسخی ثبت نشده";
          item.append(at,state); list.append(item);
        });
        if (data.events.length) fragment.append(list);
        else { const empty = document.createElement("p"); empty.textContent = "در ۲۴ ساعت گذشته پیامی دریافت نشده است."; fragment.append(empty); }
        result.replaceChildren(fragment); status.textContent = "آخرین بررسی: " + time(data.summary.checked_at);
      } catch (error) {
        if (panel.isConnected) status.textContent = "دریافت گزارش انجام نشد: " + publicError(error);
      } finally { refresh.disabled = false; panel.removeAttribute("aria-busy"); }
    }
    refresh.addEventListener("click", load); await load();
  }
  async function openReplyEditor(bot, row, opener) {
    opener.disabled = true;
    const panel = document.createElement("section"); panel.className = "reply-editor";
    const title = document.createElement("h3"); title.textContent = "پاسخ‌های ربات";
    const intro = document.createElement("p"); intro.className = "hint";
    intro.textContent = "پیام‌های رایج مشتریان را بنویس و برای هرکدام یک پاسخ تعیین کن.";
    const status = document.createElement("p"); status.className = "editor-status";
    status.setAttribute("role", "status"); status.setAttribute("aria-live", "polite");
    const form = document.createElement("form"); form.id = "reply-form-" + bot.id; form.noValidate = true;
    function field(parent, labelText, type = "text", value = "") {
      const label = document.createElement("label"), caption = document.createElement("span"); caption.textContent = labelText;
      const input = document.createElement(type === "textarea" ? "textarea" : "input");
      if (type !== "textarea") input.type = type;
      input.value = value; input.autocomplete = "off";
      if (type === "checkbox") label.className = "checkbox-label";
      if (type === "textarea") input.rows = 3;
      label.append(caption, input); parent.append(label); return input;
    }
    function select(parent, labelText, values, value) {
      const label = document.createElement("label"), caption = document.createElement("span"); caption.textContent = labelText;
      const input = document.createElement("select");
      values.forEach(([key, text]) => { const option = document.createElement("option"); option.value = key; option.textContent = text; input.append(option); });
      input.value = value; label.append(caption, input); parent.append(label); return input;
    }
    function explanation(parent, text) {
      const hint = document.createElement("p"); hint.className = "hint"; hint.textContent = text; parent.append(hint); return hint;
    }
    function disclosure(parent, text) {
      const details = document.createElement("details"), summary = document.createElement("summary");
      summary.textContent = text; details.append(summary); parent.append(details); return details;
    }
    const tabs = document.createElement("div"); tabs.className = "editor-tabs"; tabs.setAttribute("role", "tablist"); tabs.setAttribute("aria-label", "تنظیم پاسخ‌های ربات");
    const welcomePane = document.createElement("section"), rulesPane = document.createElement("section"), previewPanel = document.createElement("section");
    previewPanel.className = "response-preview";
    const views = [["welcome", "پیام شروع", welcomePane], ["rules", "پاسخ‌ها", rulesPane], ["preview", "آزمایش", previewPanel]];
    const tabButtons = [];
    function showView(key, focusTab = false) {
      views.forEach(([name, , pane], index) => {
        const selected = name === key; pane.hidden = !selected;
        tabButtons[index].setAttribute("aria-selected", String(selected)); tabButtons[index].tabIndex = selected ? 0 : -1;
        if (selected && focusTab) tabButtons[index].focus();
      });
    }
    views.forEach(([key, text, pane], index) => {
      pane.classList.add("editor-pane"); pane.id = "reply-" + bot.id + "-" + key; pane.setAttribute("role", "tabpanel");
      const tab = document.createElement("button"); tab.type = "button"; tab.className = "editor-tab"; tab.textContent = text;
      tab.id = pane.id + "-tab"; tab.setAttribute("role", "tab"); tab.setAttribute("aria-controls", pane.id); pane.setAttribute("aria-labelledby", tab.id);
      tab.addEventListener("click", () => showView(key));
      tab.addEventListener("keydown", event => {
        if (!["ArrowLeft", "ArrowRight", "Home", "End"].includes(event.key)) return;
        event.preventDefault();
        const next = event.key === "Home" ? 0 : event.key === "End" ? views.length - 1 : (index + (event.key === "ArrowLeft" ? 1 : -1) + views.length) % views.length;
        showView(views[next][0], true);
      });
      tabButtons.push(tab); tabs.append(tab);
    });
    const greeting = field(welcomePane, "پیام خوش‌آمدگویی", "textarea"); greeting.placeholder = "مثلاً سلام! به فروشگاه ما خوش آمدی.";
    explanation(welcomePane, "وقتی کاربر دکمهٔ شروع یا /start را می‌زند، این پیام را می‌بیند.");
    const heading = document.createElement("h4"); heading.textContent = "پیام‌های رایج و پاسخ‌ها";
    const count = document.createElement("span"); count.className = "rules-count"; heading.append(count);
    const rulesRoot = document.createElement("div"); rulesRoot.className = "rules-list";
    const empty = document.createElement("p"); empty.className = "rules-empty"; empty.textContent = "هنوز پاسخی نساخته‌ای. با «افزودن پاسخ» شروع کن؛ مثلاً برای قیمت یا آدرس.";
    const add = document.createElement("button"); add.type = "button"; add.className = "add-rule"; add.textContent = "+ افزودن پاسخ"; add.disabled = true;
    const undoBar = document.createElement("div"); undoBar.className = "undo-bar"; undoBar.hidden = true;
    const undoText = document.createElement("span"); undoText.textContent = "پاسخ از این فرم حذف شد.";
    const undo = document.createElement("button"); undo.type = "button"; undo.className = "button-secondary"; undo.textContent = "بازگردانی"; undoBar.append(undoText, undo);
    rulesPane.append(heading); explanation(rulesPane, "مثال: مشتری می‌نویسد «آدرس» و ربات آدرس فروشگاه را می‌فرستد. اگر چند پاسخ تطبیق داشت، پاسخ بالاتر انتخاب می‌شود.");
    rulesPane.append(empty, rulesRoot, undoBar);
    const menuPreview = document.createElement("div"); menuPreview.className = "menu-preview"; menuPreview.hidden = true;
    menuPreview.setAttribute("aria-label", "پیش‌نمایش دکمه‌های ربات"); rulesPane.append(menuPreview);
    explanation(rulesPane, "افزودن پاسخ اختیاری است. برای پاسخ بعدی دکمهٔ «افزودن پاسخ» کنار ذخیره را بزن؛ ردیف کاملاً خالی ذخیره نمی‌شود.");
    const fallbackBox = disclosure(rulesPane, "اگر پیام کاربر را نشناختیم"); fallbackBox.className = "fallback-settings";
    const fallback = field(fallbackBox, "پاسخ به پیام‌های دیگر", "textarea"); fallback.placeholder = "مثلاً برای دریافت اطلاعات، قیمت یا آدرس را بنویس.";
    explanation(fallbackBox, "اگر هیچ‌کدام از عبارت‌ها با پیام کاربر تطبیق نداشت، این پاسخ فرستاده می‌شود.");
    [greeting, fallback].forEach(input => { input.required = true; input.maxLength = 4096; input.disabled = true; });
    form.append(welcomePane, rulesPane);
    const previewHint = explanation(previewPanel, "یک پیام بنویس تا ببینی با تنظیمات همین فرم چه پاسخی انتخاب می‌شود. لازم نیست اول ذخیره کنی. این آزمایش پیامی نمی‌فرستد و به API وصل نمی‌شود.");
    previewHint.className = "hint";
    const previewText = field(previewPanel, "پیام آزمایشی", "textarea"); previewText.maxLength = 4096; previewText.placeholder = "مثلاً قیمت یا /start";
    const previewButton = document.createElement("button"); previewButton.type = "button"; previewButton.className = "button-secondary"; previewButton.textContent = "نمایش پیش‌نمایش"; previewButton.disabled = true;
    const previewOutput = document.createElement("p"); previewOutput.className = "preview-output"; previewOutput.setAttribute("role", "status"); previewOutput.setAttribute("aria-live", "polite"); previewOutput.hidden = true;
    previewPanel.append(previewButton, previewOutput);
    const save = document.createElement("button"); save.type = "button"; save.textContent = "ذخیره پاسخ‌ها"; save.disabled = true;
    const close = document.createElement("button"); close.type = "button"; close.textContent = "بستن تنظیمات"; close.className = "button-secondary";
    const buttons = document.createElement("div"); buttons.className = "editor-actions editor-footer"; buttons.append(save, add, close);
    const saveFeedback = document.createElement("p"); saveFeedback.className = "save-feedback"; saveFeedback.hidden = true;
    saveFeedback.setAttribute("role", "status"); saveFeedback.setAttribute("aria-live", "polite");
    function saveMessage(message, kind = "progress") {
      status.textContent = message; saveFeedback.hidden = false; saveFeedback.className = "save-feedback " + kind;
      if (saveFeedback.textContent !== message) saveFeedback.textContent = message;
    }
    const apiNote = document.createElement("p"); apiNote.className = "hint live-status";
    const discard = document.createElement("div"); discard.className = "discard-confirm"; discard.hidden = true;
    explanation(discard, "ذخیرهٔ این تغییرات هنوز تأیید نشده است.");
    const keepEditing = document.createElement("button"); keepEditing.type = "button"; keepEditing.textContent = "ادامهٔ ویرایش";
    const discardChanges = document.createElement("button"); discardChanges.type = "button"; discardChanges.className = "button-secondary"; discardChanges.textContent = "بستن بدون ذخیره";
    discard.append(keepEditing, discardChanges);
    panel.append(title, intro, tabs, status, form, previewPanel, buttons, saveFeedback, discard, apiNote); row.append(panel);
    const base = "/api/v1/tenants/" + activeTenant.id + "/bots/" + bot.id;
    let rules = [], schemaReady = false, baseVersion = 0, draftId = null, busy = false, refreshRequired = false, previewBusy = false, previewRevision = 0, hasChanges = false, removedRule = null;
    showView("rules");
    function closeEditor() { panel.remove(); opener.disabled = false; opener.focus(); }
    close.addEventListener("click", () => { if (hasChanges) { discard.hidden = false; keepEditing.focus(); } else closeEditor(); });
    keepEditing.addEventListener("click", () => { discard.hidden = true; close.focus(); });
    discardChanges.addEventListener("click", closeEditor);
    function invalidatePreview() { previewRevision += 1; previewOutput.hidden = true; previewOutput.textContent = ""; }
    function dirty() {
      draftId = null; hasChanges = true; discard.hidden = true; invalidatePreview();
      if (refreshRequired) return;
      const message = "تغییرات ذخیره نشده است؛ در پایان «ذخیره پاسخ‌ها» را بزن.";
      if (status.textContent !== message) status.textContent = message;
      if (!saveFeedback.hidden && saveFeedback.textContent !== message) {
        saveFeedback.className = "save-feedback"; saveFeedback.textContent = message;
      }
    }
    previewText.addEventListener("input", invalidatePreview);
    function updateRules() {
      // Typing updates captions only. Never detach/reinsert an input's ancestors.
      rules.forEach((rule, index) => {
        rule.caption.textContent = (index + 1) + ". " + (rule.keyword.value || "پاسخ جدید");
        rule.caption.title = rule.keyword.value;
        rule.badge.textContent = !rule.enabled.checked ? "غیرفعال" : rule.action.value === "api" ? "API" : "متن";
        rule.up.disabled = busy || index === 0; rule.down.disabled = busy || index === rules.length - 1;
      });
      const buttonRules = rules.filter(rule => rule.showButton.checked && rule.enabled.checked && rule.keyword.value.trim());
      menuPreview.replaceChildren(); menuPreview.hidden = buttonRules.length === 0;
      if (buttonRules.length) {
        const label = document.createElement("p"); label.className = "hint"; label.textContent = "دکمه‌های داخل چت ربات · پیش‌نمایش"; menuPreview.append(label);
        const grid = document.createElement("div"); grid.className = "menu-preview-grid";
        const seen = new Set();
        buttonRules.forEach(rule => {
          const key = rule.keyword.value.trim().toLowerCase(); if (seen.has(key)) return; seen.add(key);
          const chip = document.createElement("span"); chip.textContent = rule.keyword.value;
          if (rule.keyword.value.length > 16) chip.className = "menu-wide";
          grid.append(chip);
        }); menuPreview.append(grid);
      }
      count.textContent = rules.length ? " · " + rules.length + " پاسخ" : "";
      empty.hidden = rules.length > 0;
      add.disabled = busy || rules.length >= 100 || refreshRequired;
      undo.disabled = busy || rules.length >= 100;
    }
    function syncOrder() {
      // Only explicit add/reorder/undo actions may move cards.
      rules.forEach((rule, index) => { if (rulesRoot.children[index] !== rule.card) rulesRoot.insertBefore(rule.card, rulesRoot.children[index] || null); });
      updateRules();
    }
    function addRule(value = {}) {
      if (rules.length >= 100) return;
      const card = document.createElement("details"); card.className = "rule-card"; card.open = !value.id;
      const summary = document.createElement("summary"), caption = document.createElement("span"), badge = document.createElement("small"); badge.className = "rule-badge"; summary.append(caption, badge); card.append(summary);
      const content = document.createElement("div"); content.className = "rule-fields"; card.append(content);
      const keyword = field(content, "کاربر چه می‌نویسد؟", "text", value.keyword || ""); keyword.maxLength = 120; keyword.placeholder = "مثلاً قیمت";
      const action = select(content, "نوع پاسخ", [["text", "پاسخ متنی"], ["api", "اتصال به API"]], value.action_type || "text");
      if (!schemaReady) action.options[1].disabled = true;
      const response = field(content, "ربات چه پاسخی بدهد؟", "textarea", value.response_text || ""); response.maxLength = 4096; response.placeholder = "متن پاسخ به مشتری";
      const showButton = field(content, "نمایش این عبارت به‌صورت دکمه در ربات", "checkbox"); showButton.checked = value.show_button === true;
      explanation(content, "اختیاری · با لمس دکمه، همین عبارت ارسال می‌شود. حداکثر ۱۲ دکمه با عنوان تا ۶۴ کاراکتر.");
      const apiFields = document.createElement("div"); apiFields.className = "api-fields";
      explanation(apiFields, "این قسمت برای اتصال به سرویس خودت است. نشانی و مشخصات را از راهنمای همان سرویس بردار؛ پاسخ باید JSON باشد.");
      const url = field(apiFields, "نشانی سرویس (HTTPS)", "url", value.api?.url || ""); url.dir = "ltr"; url.placeholder = "https://api.example.com/lookup"; url.maxLength = 2048;
      const path = field(apiFields, "کدام بخش پاسخ سرویس نمایش داده شود؟", "text", value.api?.response_path || ""); path.dir = "ltr"; path.maxLength = 200; path.placeholder = "data.answer";
      explanation(apiFields, "مثلاً اگر متن جواب در data.answer است، همین مسیر را وارد کن.");
      const authBox = disclosure(apiFields, "کلید دسترسی به سرویس"); authBox.open = value.api?.auth_mode && value.api.auth_mode !== "none";
      const auth = select(authBox, "روش استفاده از کلید", [["none", "بدون کلید"], ["bearer", "Bearer Token"], ["header", "Header اختصاصی"]], value.api?.auth_mode || "none");
      const header = field(authBox, "نام Header کلید", "text", value.api?.auth_header || "X-API-Key"); header.dir = "ltr";
      const credential = field(authBox, "کلید دسترسی", "password"); credential.autocomplete = "new-password"; credential.maxLength = 2048;
      credential.placeholder = value.api?.credential_present ? "ذخیره شده؛ برای حفظ آن خالی بگذار" : "کلید را اینجا وارد کن";
      explanation(authBox, "کلید ذخیره‌شده نمایش داده نمی‌شود. کلید را فقط در همین کادر وارد کن.");
      const requestBox = disclosure(apiFields, "تنظیمات بیشتر اتصال"); requestBox.open = value.api?.method === "POST";
      const method = select(requestBox, "روش درخواست", [["GET", "GET — دریافت"], ["POST", "POST — ارسال"]], value.api?.method || "GET");
      const share = field(requestBox, "متن پیام کاربر به این سرویس فرستاده شود", "checkbox"); share.checked = value.api?.include_message === true;
      const messageField = field(requestBox, "نام فیلد پیام در سرویس", "text", value.api?.message_field || "message"); messageField.dir = "ltr";
      const params = field(requestBox, "پارامترهای Query (JSON)", "textarea", JSON.stringify(value.api?.params || {}, null, 2)); params.dir = "ltr"; params.maxLength = 12000;
      const body = field(requestBox, "بدنهٔ درخواست POST (JSON)", "textarea", JSON.stringify(value.api?.json_body || {}, null, 2)); body.dir = "ltr"; body.maxLength = 8192;
      explanation(requestBox, "نشانی را بدون Query بنویس. متن کاربر فقط با انتخاب گزینهٔ بالا ارسال می‌شود. POST ممکن است در سرویس مقصد اطلاعات ایجاد کند.");
      content.append(apiFields);
      const options = disclosure(content, "تنظیمات بیشتر این پاسخ"); options.className = "rule-options";
      const match = select(options, "چه پیام‌هایی این پاسخ را بگیرند؟", [["exact", "فقط همین عبارت"], ["contains", "شامل این عبارت"]], value.match_mode || "exact");
      const enabled = field(options, "این پاسخ فعال باشد", "checkbox"); enabled.checked = value.enabled !== false;
      const actions = document.createElement("div"); actions.className = "editor-actions";
      const up = document.createElement("button"), down = document.createElement("button");
      const rule = {card, caption, badge, showButton, keyword, match, action, enabled, response, url, method, path, auth, header, credential, share, messageField, params, body, up, down, sourceId: value.id || null};
      [[up, "بالاتر", -1], [down, "پایین‌تر", 1]].forEach(([button, text, step]) => {
        button.type = "button"; button.className = "button-secondary"; button.textContent = text;
        button.addEventListener("click", () => {
          const index = rules.indexOf(rule), next = index + step; if (next < 0 || next >= rules.length) return;
          [rules[index], rules[next]] = [rules[next], rules[index]]; dirty(); syncOrder(); button.focus();
        }); actions.append(button);
      });
      const remove = document.createElement("button"); remove.type = "button"; remove.className = "button-danger"; remove.textContent = "حذف پاسخ";
      remove.addEventListener("click", () => {
        removedRule = {rule, index: rules.indexOf(rule)}; rules = rules.filter(item => item !== rule); card.remove();
        undoBar.hidden = false; dirty(); updateRules(); undo.focus();
      }); actions.append(remove); options.append(actions);
      function visibility() {
        const isApi = action.value === "api"; apiFields.hidden = !isApi;
        apiFields.querySelectorAll("input,select,textarea").forEach(input => { input.disabled = !isApi; });
        response.parentElement.firstChild.textContent = isApi ? "اگر سرویس پاسخ نداد، چه بگوییم؟" : "ربات چه پاسخی بدهد؟";
        url.required = isApi; header.parentElement.hidden = auth.value !== "header";
        credential.parentElement.hidden = auth.value === "none";
        messageField.parentElement.hidden = !share.checked; body.parentElement.hidden = method.value !== "POST";
      }
      [action, auth, share, method].forEach(input => input.addEventListener("change", () => { visibility(); updateRules(); }));
      enabled.addEventListener("change", updateRules); showButton.addEventListener("change", updateRules); keyword.addEventListener("input", updateRules);
      visibility(); rules.push(rule); rulesRoot.append(card); updateRules();
    }
    undo.addEventListener("click", () => {
      if (!removedRule || rules.length >= 100 || busy) return;
      const {rule, index} = removedRule; rules.splice(Math.min(index, rules.length), 0, rule);
      removedRule = null; undoBar.hidden = true; dirty(); syncOrder(); rule.card.open = true; rule.keyword.focus();
    });
    function emptyNewRule(rule) {
      return !rule.sourceId && !rule.showButton.checked && rule.action.value === "text" && !rule.keyword.value.trim() && !rule.response.value.trim();
    }
    add.addEventListener("click", () => {
      if (busy || refreshRequired || add.disabled) return;
      showView("rules");
      // Reuse an untouched placeholder instead of stacking mandatory empty cards.
      const existing = rules.find(emptyNewRule);
      if (!existing) { addRule(); dirty(); }
      const rule = existing || rules[rules.length - 1];
      if (rule) { rule.card.open = true; rule.keyword.focus(); }
    });
    form.addEventListener("input", dirty); form.addEventListener("change", dirty);
    async function load(current = null) {
      if (!current) current = await api(base + "/config");
      schemaReady = current.api_actions_ready === true;
      baseVersion = current.published?.version || 0;
      greeting.value = current.published?.greeting || ""; fallback.value = current.published?.fallback_reply || "";
      greeting.disabled = busy; fallback.disabled = busy;
      rules = []; rulesRoot.replaceChildren(); (current.rules || []).forEach(addRule);
      removedRule = null; undoBar.hidden = true; hasChanges = false; discard.hidden = true;
      apiNote.textContent = !schemaReady ? "تنظیم پاسخ متنی در دسترس است؛ اتصال سرویس هنوز آماده نیست." : current.external_api_enabled ? "تنظیم اتصال سرویس در دسترس است. ارسال زندهٔ پاسخ باید جداگانه فعال باشد." : "ذخیره و آزمایش در دسترس است؛ اتصال واقعی سرویس بیرونی هنوز فعال نشده است.";
      refreshRequired = false; save.disabled = false; previewButton.disabled = busy || previewBusy; invalidatePreview(); updateRules();
      return !!current.published;
    }
    function inputError(message, input) { const error = new Error(message); error.input = input; throw error; }
    function revealError(error) {
      status.textContent = error.message;
      if (!error.input) return;
      const pane = error.input.closest(".editor-pane");
      const view = views.find(item => item[2] === pane); if (view) showView(view[0]);
      let parent = error.input.parentElement;
      while (parent && parent !== panel) { if (parent.tagName === "DETAILS") parent.open = true; parent = parent.parentElement; }
      error.input.focus();
    }
    function jsonObject(input, label) {
      let value; try { value = JSON.parse(input.value || "{}"); } catch (_) { inputError(label + " باید JSON معتبر باشد.", input); }
      if (!value || typeof value !== "object" || Array.isArray(value)) inputError(label + " باید یک شیء JSON باشد.", input);
      return value;
    }
    function readSnapshot(includeCredentials = true) {
      if (!greeting.value.trim()) inputError("متن پیام خوش‌آمدگویی را بنویس.", greeting);
      if (!fallback.value.trim()) inputError("پاسخ به پیام‌های دیگر را بنویس.", fallback);
      const selectedRules = rules.filter(rule => !emptyNewRule(rule));
      if (selectedRules.filter(rule => rule.showButton.checked).length > 12) inputError("حداکثر ۱۲ پاسخ را به‌صورت دکمه انتخاب کن.", selectedRules.find(rule => rule.showButton.checked).showButton);
      for (const rule of selectedRules) {
        if (rule.showButton.checked && rule.keyword.value.length > 64) inputError("عنوان دکمه باید حداکثر ۶۴ کاراکتر باشد؛ عبارت را کوتاه کن یا تیک دکمه را بردار.", rule.keyword);
        if (!rule.keyword.value.trim()) inputError("عبارتی را که مشتری می‌فرستد بنویس.", rule.keyword);
        if (!rule.response.value.trim()) inputError("متن پاسخ را بنویس.", rule.response);
      }
      for (const input of form.querySelectorAll("input,textarea,select")) {
        const card = input.closest(".rule-card");
        if (card && !selectedRules.some(rule => rule.card === card)) continue;
        if (!input.disabled && !input.checkValidity()) inputError("این کادر را کامل و با قالب درست وارد کن.", input);
      }
      return {greeting: greeting.value, fallback_reply: fallback.value, base_version: baseVersion, replace_reply_buttons: true, rules: selectedRules.map(rule => {
        const item = {keyword: rule.keyword.value, match_mode: rule.match.value, response_text: rule.response.value, action_type: rule.action.value, enabled: rule.enabled.checked, show_button: rule.showButton.checked};
        if (rule.action.value === "api") {
          item.source_rule_id = rule.sourceId;
          item.api = {url: rule.url.value, method: rule.method.value, params: jsonObject(rule.params, "پارامترها"), json_body: rule.method.value === "POST" ? jsonObject(rule.body, "بدنه") : {},
            response_path: rule.path.value, auth_mode: rule.auth.value, auth_header: rule.header.value, include_message: rule.share.checked, message_field: rule.messageField.value};
          if (includeCredentials) item.api.credential = rule.credential.value || null;
        }
        return item;
      })};
    }
    previewButton.addEventListener("click", async () => {
      if (busy || previewBusy || refreshRequired) return;
      previewOutput.hidden = false;
      let snapshot;
      try {
        if (!previewText.value.trim()) throw new Error("یک پیام آزمایشی بنویس.");
        snapshot = {...readSnapshot(false), text: previewText.value};
      } catch (error) { if (error.input) revealError(error); else previewOutput.textContent = error.message; return; }
      const revision = previewRevision; previewBusy = true; previewButton.disabled = true; save.disabled = true;
      previewPanel.setAttribute("aria-busy", "true"); previewOutput.textContent = "در حال انتخاب پاسخ…";
      try {
        const result = await api(base + "/preview", {method: "POST", headers: {"Content-Type": "application/json"}, body: JSON.stringify(snapshot)});
        if (!panel.isConnected) return;
        previewOutput.hidden = false;
        if (revision !== previewRevision) { previewOutput.textContent = "متن یا تنظیمات تغییر کرد؛ دوباره آزمایش کن."; return; }
        if (result.action === "api") {
          previewOutput.textContent = "پاسخ " + result.rule_index + " انتخاب شد: سرویس بیرونی. در این آزمایش API فراخوانی نشد.\nپیام جایگزین در صورت خطا:\n" + result.fallback_text;
        } else {
          const source = result.action === "greeting" ? "پیام شروع" : result.action === "text" ? "پاسخ " + result.rule_index : "پاسخ به پیام‌های دیگر";
          previewOutput.textContent = source + ":\n" + result.response_text;
        }
      } catch (error) {
        if (panel.isConnected && revision === previewRevision) { previewOutput.hidden = false; previewOutput.textContent = "آزمایش انجام نشد: " + publicError(error); }
      } finally {
        previewBusy = false; previewPanel.removeAttribute("aria-busy"); previewButton.disabled = busy || refreshRequired; save.disabled = busy || refreshRequired;
      }
    });
    function snapshotMatches(current, snapshot, published) {
      const stored = current.published;
      if (!stored || stored.id !== published.id || stored.version !== published.version ||
          stored.greeting !== snapshot.greeting || stored.fallback_reply !== snapshot.fallback_reply ||
          !Array.isArray(current.rules) || current.rules.length !== snapshot.rules.length) return false;
      const fields = ["keyword", "match_mode", "response_text", "action_type", "enabled"];
      return snapshot.rules.every((rule, index) => fields.every(key => rule[key] === current.rules[index][key]) && rule.show_button === Boolean(current.rules[index].show_button));
    }
    async function saveReplies(event) {
      event.preventDefault();
      if (busy || previewBusy) return;
      if (refreshRequired) { saveMessage("تأیید نهایی ذخیره در دسترس نیست؛ متن‌های فرم حفظ شده‌اند. برای ادامه تنظیمات را دوباره باز کن.", "error"); return; }
      saveMessage("در حال بررسی پاسخ‌ها…");
      let snapshot;
      try { snapshot = readSnapshot(); } catch (error) { revealError(error); saveMessage(error.message, "error"); return; }
      busy = true; panel.setAttribute("aria-busy", "true");
      const controls = Array.from(panel.querySelectorAll("input,select,textarea,button")), disabledBefore = controls.map(input => input.disabled);
      controls.forEach(input => { input.disabled = true; }); saveMessage("در حال ذخیرهٔ پاسخ‌ها…");
      let published = false;
      try {
        if (!draftId) { const draft = await api(base + "/configs", {method: "POST", headers: {"Content-Type": "application/json"}, body: JSON.stringify(snapshot)}); draftId = draft.id; }
        const result = await api(base + "/configs/" + draftId + "/publish?expected_version=" + baseVersion, {method: "POST"});
        published = true; draftId = null;
        saveMessage("ذخیره انجام شد؛ در حال بررسی نسخهٔ ثبت‌شده…");
        try {
          const current = await api(base + "/config");
          if (!snapshotMatches(current, snapshot, result)) throw new Error("readback_mismatch");
          await load(current); saveMessage("همهٔ پاسخ‌ها ذخیره شدند.", "success");
        } catch (_) {
          refreshRequired = true;
          saveMessage("انتشار انجام شد، اما تأیید نهایی ذخیره ممکن نشد. متن‌های این فرم حفظ شده‌اند؛ قبل از بستن آن‌ها را بررسی کن.", "error");
        }
      } catch (error) { saveMessage("ذخیره تأیید نشد: " + publicError(error), "error"); }
      finally {
        busy = false; panel.removeAttribute("aria-busy");
        controls.forEach((input, index) => { if (input.isConnected) input.disabled = disabledBefore[index]; });
        save.disabled = false; previewButton.disabled = refreshRequired; close.disabled = false; updateRules();
        if (published) rules.forEach(rule => { rule.credential.value = ""; });
      }
    }
    // Explicit clicks do not depend on native external-form submission in WebViews.
    save.addEventListener("click", saveReplies);
    form.addEventListener("submit", saveReplies);
    status.textContent = "در حال دریافت پاسخ‌های فعلی…";
    try { const published = await load(); showView(published ? "rules" : "welcome"); status.textContent = "پاسخ‌های فعلی آمادهٔ ویرایش‌اند."; }
    catch (error) { saveMessage("دریافت پاسخ‌ها انجام نشد: " + publicError(error), "error"); }
  }
  async function describeAuthFailure(error) {
    if (!error || error.message !== "Invalid Telegram Mini App authentication") {
      return publicError(error);
    }
    try {
      const response = await fetch("/api/v1/uat/manager-identity", {
        method: "GET", credentials: "omit", cache: "no-store", redirect: "error",
      });
      if (response.ok) {
        const result = await response.json();
        if (result.status === "mismatch") {
          return "تنظیم ربات مدیریتی روی سرور با @DirectPilotManagerBot یکسان نیست. این خطا باید در تنظیمات UAT اصلاح شود.";
        }
        if (result.status === "match") {
          return "ربات مدیریتی سرور درست است، اما نشست معتبر نیست. پنل را از دکمه Open TelBot داخل چت @DirectPilotManagerBot دوباره باز کن.";
        }
        if (result.status === "unavailable" || result.status === "missing") {
          return "هویت ربات مدیریتی UAT قابل تأیید نیست. تنظیم توکن سرور نیاز به بررسی دارد.";
        }
      }
    } catch (_) { /* diagnostics are optional; never expose raw transport errors */ }
    return publicError(error);
  }
  async function initialize() {
    if (!initData) {
      telegramHelp.classList.remove("hidden");
      setNotice("برای ورود، پنل را از Mini App تلگرام باز کن.", "error");
      return;
    }
    telegram.ready();
    telegram.expand();
    app.classList.remove("hidden");
    try {
      const tenants = await api("/api/v1/me/tenants");
      if (tenants.length) {
        activeTenant = tenants.find(t => t.role === "owner") || tenants[0];
        document.getElementById("tenant-display").textContent = activeTenant.display_name;
        workspace.classList.remove("hidden");
        await listBots();
      } else { tenantPanel.classList.remove("hidden"); }
      setNotice("به پنل امن تل‌بات خوش آمدی.", "success");
    } catch(error) { setNotice(await describeAuthFailure(error), "error"); }
  }
  tenantForm.addEventListener("submit", async (event) => {
    event.preventDefault();
    const button = tenantForm.querySelector("button");
    const display_name = document.getElementById("tenant-name").value.trim();
    if (!display_name) return;
    button.disabled = true;
    try {
      activeTenant = await api("/api/v1/me/tenants", {
        method:"POST", headers: {"Content-Type":"application/json"}, body:JSON.stringify({display_name}),
      });
      document.getElementById("tenant-display").textContent = activeTenant.display_name;
      tenantPanel.classList.add("hidden"); workspace.classList.remove("hidden");
      setNotice("حساب ساخته شد؛ حالا ربات اختصاصی‌ات را بساز.", "success");
      await listBots();
    } catch(error) { setNotice(publicError(error), "error"); }
    finally { button.disabled = false; }
  });
  managedForm.addEventListener("submit", async (event) => {
    event.preventDefault();
    if (!activeTenant) return;
    const button = managedForm.querySelector("button");
    const suggested_name = document.getElementById("managed-bot-name").value.trim();
    const suggested_username = document.getElementById("managed-bot-username").value.trim();
    if (!suggested_name || !/^[A-Za-z0-9_]{5,32}$/.test(suggested_username) || !/bot$/i.test(suggested_username)) {
      setNotice("نام کاربری باید ۵ تا ۳۲ کاراکتر انگلیسی/عدد/زیرخط و با پسوند bot باشد.", "error");
      return;
    }
    button.disabled = true;
    try {
      const ticket = await api("/api/v1/tenants/" + activeTenant.id + "/managed-bot-requests", {
        method: "POST", headers: {"Content-Type": "application/json"},
        body: JSON.stringify({suggested_name, suggested_username}),
      });
      const url = new URL(ticket.creation_url);
      if (url.protocol !== "https:" || url.hostname !== "t.me" ||
          !url.pathname.startsWith("/newbot/DirectPilotManagerBot/")) {
        throw new Error("invalid_creation_url");
      }
      document.getElementById("managed-bot-pending").classList.remove("hidden");
      try {
        await api("/api/v1/tenants/" + activeTenant.id +
          "/managed-bot-requests/" + ticket.request_id + "/send-keyboard",
          {method: "POST"});
        setNotice("دکمه رسمی Create Bot در چت خصوصی ربات مدیریتی ارسال شد. آن را داخل تلگرام بزن.", "success");
        if (telegram && typeof telegram.openTelegramLink === "function") {
          telegram.openTelegramLink("https://t.me/DirectPilotManagerBot");
        }
      } catch (_) {
        setNotice("ارسال دکمه تلگرام ممکن نشد؛ لینک جایگزین پایین را امتحان کن.", "error");
      }
      // The private-chat request button is preferred; deep link remains fallback.
      // The official Telegram flow requires an explicit action by the owner.
      // No BotFather API token is requested, transmitted, or stored in the browser.
      const link = document.getElementById("managed-bot-link");
      link.href = url.href;
      link.classList.remove("hidden");
      // Route Telegram deep links through the native Telegram client, not a browser preview.
      link.onclick = (event) => {
        if (telegram && typeof telegram.openTelegramLink === "function") {
          event.preventDefault();
          telegram.openTelegramLink(url.href);
        }
      };
    } catch(error) {
      if (error.message === "Pending bot request already exists") {
        setNotice("یک درخواست ساخت ربات در انتظار تأیید داری. برای درخواست جدید، پس از انقضای قبلی اقدام کن.", "error");
      } else {
        setNotice(publicError(error), "error");
      }
    } finally { button.disabled = false; }
  });
  function webhookStatus(message) {
    const target = document.getElementById("manager-webhook-status");
    if (target) target.textContent = message;
    setNotice(message, "info");
  }
  document.getElementById("check-manager-webhook").addEventListener("click", async () => {
    if (!activeTenant) { webhookStatus("خطا: حساب فعال در پنل شناسایی نشد."); return; }
    webhookStatus("در حال دریافت وضعیت اتصال مدیریتی تلگرام…");
    try {
      const w = await api("/api/v1/tenants/" + activeTenant.id + "/uat/manager-webhook");
      webhookStatus("Webhook UAT: " + (w.configured_for_uat ? "درست" : "تنظیم‌نشده یا متفاوت") +
        " | managed_bot: " + (w.allowed_managed_bot || w.allowed_updates_default ? "مجاز" : "غیرفعال") +
        " | رویداد معوق: " + w.pending_delivery_count +
        " | خطای تحویل: " + (w.delivery_error_present ? "دارد" : "ندارد"));
    } catch(error) { webhookStatus("خطای تشخیص Webhook: " + publicError(error)); }
  });
  document.getElementById("repair-manager-webhook").addEventListener("click", async () => {
    if (!activeTenant) { webhookStatus("خطا: حساب فعال در پنل شناسایی نشد."); return; }
    webhookStatus("در حال بررسی و ثبت Webhook مدیریتی UAT…");
    try {
      const w = await api("/api/v1/tenants/" + activeTenant.id + "/uat/manager-webhook/repair", {method:"POST"});
      webhookStatus(w.status === "registered_for_uat"
        ? "Webhook مدیریتی UAT ثبت شد؛ لطفاً وضعیت را مجدد بررسی کن."
        : "پاسخ ناشناخته از API ثبت Webhook");
    } catch(error) { webhookStatus("خطای اصلاح Webhook: " + publicError(error)); }
  });
  document.getElementById("refresh-bots").addEventListener("click", async () => {
    if (document.querySelector(".reply-editor")) {
      setNotice("برای تازه‌سازی فهرست، ابتدا تنظیمات باز ربات را ذخیره کن و ببند.");
      return;
    }
    if (activeTenant) await listBots();
  });
  document.addEventListener("visibilitychange", () => {
    if (!document.hidden && activeTenant) void listBots();
  });
  initialize();
})();
