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
        const row = document.createElement("div"); row.className = "bot-row";
        const meta = document.createElement("div");
        const name = document.createElement("strong");
        name.textContent = bot.username ? "@" + bot.username : "ربات تلگرام";
        const detail = document.createElement("small");
        detail.textContent = bot.display_name || "";
        meta.append(name, detail);
        const state = document.createElement("span"); state.className = "pending";
        state.textContent = bot.status === "pending" ? "در انتظار فعال‌سازی" : bot.status === "active" ? "فعال" : "متوقف";
        row.append(meta, state); root.append(row);
      });
    } catch(error) { root.textContent = publicError(error); }
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
  document.getElementById("check-manager-webhook").addEventListener("click", async () => {
    if (!activeTenant) return;
    try {
      const w = await api("/api/v1/tenants/" + activeTenant.id + "/uat/manager-webhook");
      setNotice("Webhook UAT: " + (w.configured_for_uat ? "درست" : "ثبت‌نشده یا متفاوت") +
        " | managed_bot: " + (w.allowed_managed_bot || w.allowed_updates_default ? "مجاز" : "غیرفعال") +
        " | رویدادهای معوق: " + w.pending_delivery_count +
        " | سابقه خطای ارسال: " + (w.delivery_error_present ? "دارد" : "ندارد"), "info");
    } catch(error) { setNotice(publicError(error), "error"); }
  });
  document.getElementById("repair-manager-webhook").addEventListener("click", async () => {
    if (!activeTenant) return;
    try {
      const w = await api("/api/v1/tenants/" + activeTenant.id + "/uat/manager-webhook/repair", {method:"POST"});
      setNotice(w.status === "registered_for_uat"
        ? "Webhook مدیریتی UAT ثبت شد؛ رویدادهای قبلیِ منقضی‌شده الزاماً بازیابی نمی‌شوند."
        : "وضعیت نامشخص", "success");
    } catch(error) { setNotice(publicError(error), "error"); }
  });
  document.getElementById("refresh-bots").addEventListener("click", async () => {
    if (activeTenant) await listBots();
  });
  document.addEventListener("visibilitychange", () => {
    if (!document.hidden && activeTenant) void listBots();
  });
  initialize();
})();
