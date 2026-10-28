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
    const root = document.getElementById("bots-list");
    root.textContent = "در حال دریافت ربات‌ها…";
    try {
      const bots = await api("/api/v1/tenants/" + activeTenant.id + "/bots");
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
        state.textContent = bot.status === "pending" ? "در انتظار فعال‌سازی" : bot.status === "active" ? "فعال" : "متوقف";
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
        root.append(row);
      });
    } catch(error) { root.textContent = publicError(error); }
  }
  async function openReplyEditor(bot, row, opener) {
    opener.disabled = true;
    const panel = document.createElement("section"); panel.className = "reply-editor";
    const title = document.createElement("h3"); title.textContent = "پیام‌ها و پاسخ‌های ربات";
    const status = document.createElement("p"); status.setAttribute("role", "status"); status.setAttribute("aria-live", "polite");
    const form = document.createElement("form");
    function field(parent, labelText, type = "text", value = "") {
      const label = document.createElement("label"); label.textContent = labelText;
      const input = document.createElement(type === "textarea" ? "textarea" : "input");
      if (type !== "textarea") input.type = type;
      input.value = value; input.autocomplete = "off";
      if (type === "textarea") input.rows = 3;
      label.append(input); parent.append(label); return input;
    }
    function select(parent, labelText, values, value) {
      const label = document.createElement("label"); label.textContent = labelText;
      const input = document.createElement("select");
      values.forEach(([key, text]) => { const option = document.createElement("option"); option.value = key; option.textContent = text; input.append(option); });
      input.value = value; label.append(input); parent.append(label); return input;
    }
    const greeting = field(form, "پیام شروع /start", "textarea");
    const fallback = field(form, "پاسخ به پیام‌های بدون قانون", "textarea");
    [greeting, fallback].forEach(input => { input.required = true; input.maxLength = 4096; });
    const heading = document.createElement("h4"); heading.textContent = "پاسخ‌های بیشتر";
    const hint = document.createElement("p"); hint.textContent = "برای هر موضوع یک قانون بساز؛ مثلاً «قیمت» یا «آدرس». اولین قانون فعال که با پیام تطبیق کند اجرا می‌شود. پیام /start همیشه پاسخ شروع را می‌گیرد.";
    const rulesRoot = document.createElement("div"); rulesRoot.className = "rules-list";
    const add = document.createElement("button"); add.type = "button"; add.className = "button-secondary"; add.textContent = "+ افزودن پاسخ"; add.disabled = true;
    const apiNote = document.createElement("p"); apiNote.className = "hint";
    form.append(heading, hint, rulesRoot, add, apiNote);
    const save = document.createElement("button"); save.type = "submit"; save.textContent = "ذخیره و انتشار همه پاسخ‌ها"; save.disabled = true;
    const close = document.createElement("button"); close.type = "button"; close.textContent = "بستن تنظیمات"; close.className = "button-secondary";
    close.addEventListener("click", () => { panel.remove(); opener.disabled = false; opener.focus(); });
    const buttons = document.createElement("div"); buttons.className = "editor-actions"; buttons.append(save, close); form.append(buttons);
    panel.append(title, status, form); row.append(panel);
    const base = "/api/v1/tenants/" + activeTenant.id + "/bots/" + bot.id;
    let rules = [], schemaReady = false, baseVersion = 0, draftId = null, busy = false, refreshRequired = false;
    function dirty() { draftId = null; }
    function reorder() {
      rules.forEach((rule, index) => { rule.summary.textContent = "پاسخ " + (index + 1) + (rule.keyword.value ? " — " + rule.keyword.value : ""); rulesRoot.append(rule.card); });
      add.disabled = busy || rules.length >= 100 || refreshRequired;
    }
    function addRule(value = {}) {
      if (rules.length >= 100) return;
      const card = document.createElement("details"); card.className = "rule-card"; card.open = !value.id;
      const summary = document.createElement("summary"); card.append(summary);
      const content = document.createElement("div"); content.className = "rule-fields"; card.append(content);
      const keyword = field(content, "کلمه یا عبارت محرک", "text", value.keyword || ""); keyword.required = true; keyword.maxLength = 120; keyword.placeholder = "مثلاً قیمت";
      const match = select(content, "زمان اجرای پاسخ", [["exact", "پیام دقیقاً برابر این عبارت باشد"], ["contains", "این عبارت در پیام وجود داشته باشد"]], value.match_mode || "exact");
      const action = select(content, "نوع پاسخ", [["text", "پاسخ متنی"], ["api", "دریافت پاسخ از API"]], value.action_type || "text");
      if (!schemaReady) action.options[1].disabled = true;
      const enabled = field(content, "این پاسخ فعال باشد", "checkbox"); enabled.checked = value.enabled !== false;
      const response = field(content, "متن پاسخ / پیام جایگزین در خطای API", "textarea", value.response_text || ""); response.required = true; response.maxLength = 4096;
      const apiFields = document.createElement("div"); apiFields.className = "api-fields";
      const url = field(apiFields, "نشانی HTTPS سرویس", "url", value.api?.url || ""); url.dir = "ltr"; url.placeholder = "https://api.example.com/lookup"; url.maxLength = 2048;
      const method = select(apiFields, "روش درخواست", [["GET", "GET — دریافت اطلاعات"], ["POST", "POST — ارسال JSON"]], value.api?.method || "GET");
      const path = field(apiFields, "مسیر متن در پاسخ JSON؛ مثلاً data.answer", "text", value.api?.response_path || ""); path.dir = "ltr"; path.maxLength = 200;
      const auth = select(apiFields, "احراز هویت API", [["none", "بدون کلید"], ["bearer", "Bearer Token"], ["header", "کلید در Header اختصاصی"]], value.api?.auth_mode || "none");
      const header = field(apiFields, "نام Header کلید؛ مثلاً X-API-Key", "text", value.api?.auth_header || "X-API-Key"); header.dir = "ltr";
      const credential = field(apiFields, "کلید اتصال — در پاسخ سرور نمایش داده نمی‌شود", "password"); credential.autocomplete = "new-password"; credential.maxLength = 2048;
      credential.placeholder = value.api?.credential_present ? "ذخیره شده؛ خالی بماند تا حفظ شود" : "کلید API";
      const share = field(apiFields, "متن پیام کاربر به همین API ارسال شود", "checkbox"); share.checked = value.api?.include_message === true;
      const messageField = field(apiFields, "نام فیلد متن پیام در API", "text", value.api?.message_field || "message"); messageField.dir = "ltr";
      const advanced = document.createElement("details"); const advancedTitle = document.createElement("summary"); advancedTitle.textContent = "پارامترها و بدنهٔ درخواست"; advanced.append(advancedTitle);
      const params = field(advanced, "پارامترهای Query به صورت JSON", "textarea", JSON.stringify(value.api?.params || {}, null, 2)); params.dir = "ltr"; params.maxLength = 12000;
      const body = field(advanced, "بدنهٔ JSON فقط برای POST", "textarea", JSON.stringify(value.api?.json_body || {}, null, 2)); body.dir = "ltr"; body.maxLength = 8192;
      apiFields.append(advanced);
      const privacy = document.createElement("p"); privacy.className = "hint"; privacy.textContent = "کلید را فقط در کادر کلید وارد کن. API باید HTTPS عمومی با پاسخ JSON باشد؛ نشانی بدون Query وارد می‌شود. متن کاربر فقط با انتخاب گزینهٔ بالا ارسال می‌شود. POST ممکن است در سرویس مقصد داده ایجاد کند؛ فقط API مجاز خودت را تنظیم کن.";
      apiFields.append(privacy); content.append(apiFields);
      const rule = {card, summary, keyword, match, action, enabled, response, url, method, path, auth, header, credential, share, messageField, params, body, sourceId: value.id || null};
      const actions = document.createElement("div"); actions.className = "editor-actions";
      [["بالاتر", -1], ["پایین‌تر", 1]].forEach(([text, step]) => {
        const button = document.createElement("button"); button.type = "button"; button.className = "button-secondary"; button.textContent = text;
        button.addEventListener("click", () => { const index = rules.indexOf(rule), next = index + step; if (next < 0 || next >= rules.length) return; [rules[index], rules[next]] = [rules[next], rules[index]]; dirty(); reorder(); }); actions.append(button);
      });
      const remove = document.createElement("button"); remove.type = "button"; remove.className = "button-secondary"; remove.textContent = "حذف از نسخهٔ جدید";
      remove.addEventListener("click", () => { rules = rules.filter(item => item !== rule); card.remove(); dirty(); reorder(); }); actions.append(remove); content.append(actions);
      function visibility() {
        const isApi = action.value === "api"; apiFields.hidden = !isApi;
        apiFields.querySelectorAll("input,select,textarea").forEach(input => { input.disabled = !isApi; });
        url.required = isApi; header.parentElement.hidden = auth.value !== "header";
        credential.parentElement.hidden = auth.value === "none";
        messageField.parentElement.hidden = !share.checked; body.parentElement.hidden = method.value !== "POST";
      }
      [action, auth, share, method].forEach(input => input.addEventListener("change", visibility));
      keyword.addEventListener("input", reorder); visibility(); rules.push(rule); reorder();
    }
    add.addEventListener("click", () => { addRule(); dirty(); rules[rules.length - 1]?.keyword.focus(); });
    form.addEventListener("input", dirty); form.addEventListener("change", dirty);
    async function load() {
      const current = await api(base + "/config"); schemaReady = current.api_actions_ready === true;
      baseVersion = current.published?.version || 0;
      greeting.value = current.published?.greeting || ""; fallback.value = current.published?.fallback_reply || "";
      rules = []; rulesRoot.replaceChildren(); (current.rules || []).forEach(addRule);
      apiNote.textContent = !schemaReady ? "پاسخ‌های متنی قابل تنظیم‌اند؛ بخش API هنوز روی سرویس آماده نیست." : current.external_api_enabled ? "اتصال API آماده است؛ پاسخ زنده به فعال‌بودن سرویس ارسال ربات نیز وابسته است." : "تنظیم API ذخیره می‌شود؛ اجرای واقعی API هنوز در سرویس آزمایشی روشن نشده است.";
      refreshRequired = false; save.disabled = false; reorder();
    }
    status.textContent = "در حال دریافت تنظیمات…";
    try { await load(); status.textContent = "تنظیمات فعلی بارگذاری شد؛ می‌توانی پاسخ جدید اضافه کنی."; greeting.focus(); }
    catch (error) { status.textContent = "خطای دریافت: " + publicError(error); }
    function jsonObject(input, label) {
      let value; try { value = JSON.parse(input.value || "{}"); } catch (_) { throw new Error(label + " باید JSON معتبر باشد."); }
      if (!value || typeof value !== "object" || Array.isArray(value)) throw new Error(label + " باید یک شیء JSON باشد.");
      return value;
    }
    form.addEventListener("submit", async event => {
      event.preventDefault(); if (busy || refreshRequired) return;
      let snapshot;
      try {
        if (!greeting.value.trim() || !fallback.value.trim()) throw new Error("پیام شروع و پاسخ پیش‌فرض را بنویس.");
        snapshot = {greeting: greeting.value, fallback_reply: fallback.value, base_version: baseVersion, rules: rules.map(rule => {
          if (!rule.keyword.value.trim() || !rule.response.value.trim()) throw new Error("کلمهٔ محرک و متن هر پاسخ را بنویس.");
          const item = {keyword: rule.keyword.value, match_mode: rule.match.value, response_text: rule.response.value, action_type: rule.action.value, enabled: rule.enabled.checked};
          if (rule.action.value === "api") {
            item.source_rule_id = rule.sourceId;
            item.api = {url: rule.url.value, method: rule.method.value, params: jsonObject(rule.params, "پارامترها"), json_body: rule.method.value === "POST" ? jsonObject(rule.body, "بدنه") : {},
              response_path: rule.path.value, auth_mode: rule.auth.value, auth_header: rule.header.value, include_message: rule.share.checked, message_field: rule.messageField.value,
              credential: rule.credential.value || null};
          }
          return item;
        })};
      } catch (error) { status.textContent = error.message; return; }
      busy = true; form.setAttribute("aria-busy", "true");
      const controls = Array.from(form.querySelectorAll("input,select,textarea,button")); const disabledBefore = controls.map(input => input.disabled);
      controls.forEach(input => { input.disabled = true; }); status.textContent = "در حال ذخیره و انتشار…";
      let published = false;
      try {
        if (!draftId) { const draft = await api(base + "/configs", {method: "POST", headers: {"Content-Type": "application/json"}, body: JSON.stringify(snapshot)}); draftId = draft.id; }
        await api(base + "/configs/" + draftId + "/publish?expected_version=" + baseVersion, {method: "POST"});
        published = true; draftId = null;
        status.textContent = "همهٔ پاسخ‌ها منتشر شدند. فعال‌سازی پاسخ زنده جداگانه انجام می‌شود.";
        try { await load(); }
        catch (_) { refreshRequired = true; status.textContent = "پاسخ‌ها منتشر شدند؛ برای ادامهٔ ویرایش، فرم را ببند و دوباره باز کن."; }
      } catch (error) { status.textContent = "ذخیره یا انتشار تأیید نشد: " + publicError(error); }
      finally {
        busy = false; form.removeAttribute("aria-busy");
        // Newly loaded rule controls have their own visibility/disabled state.
        controls.forEach((input, index) => { if (input.isConnected) input.disabled = disabledBefore[index]; });
        save.disabled = refreshRequired; close.disabled = false; reorder();
        if (published) rules.forEach(rule => { rule.credential.value = ""; });
      }
    });
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
    if (activeTenant) await listBots();
  });
  document.addEventListener("visibilitychange", () => {
    if (!document.hidden && activeTenant) void listBots();
  });
  initialize();
})();
