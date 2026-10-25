"use strict";
(() => {
  const app = document.getElementById("main-app");
  const notice = document.getElementById("notice");
  const telegramHelp = document.getElementById("telegram-help");
  const tenantPanel = document.getElementById("create-tenant");
  const workspace = document.getElementById("workspace");
  const botForm = document.getElementById("bot-form");
  const tenantForm = document.getElementById("tenant-form");
  const tokenField = document.getElementById("bot-token");
  const telegram = window.Telegram && window.Telegram.WebApp;
  const initData = telegram && telegram.initData ? telegram.initData : "";
  let activeTenant = null;

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
        throw new Error(detail);
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
    return map[code] || "درخواست انجام نشد. برای ادامه Mini App را دوباره باز کن.";
  }
  async function listBots() {
    const root = document.getElementById("bots-list");
    root.textContent = "در حال دریافت ربات‌ها…";
    try {
      const bots = await api("/api/v1/tenants/" + activeTenant.id + "/bots");
      root.replaceChildren();
      if (!bots.length) { root.textContent = "هنوز رباتی متصل نکرده‌ای."; root.className = "bot-empty"; return; }
      root.className = "bot-list";
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
      setNotice("حساب ساخته شد؛ اکنون رباتت را وصل کن.", "success");
      await listBots();
    } catch(error) { setNotice(publicError(error), "error"); }
    finally { button.disabled = false; }
  });
  botForm.addEventListener("submit", async (event) => {
    event.preventDefault();
    if (!activeTenant) return;
    const button = botForm.querySelector("button");
    // Clear the input before the request; never persist the bearer credential.
    const token = tokenField.value;
    tokenField.value = "";
    button.disabled = true;
    setNotice("در حال اعتبارسنجی ربات و رمزگذاری توکن…");
    try {
      const bot = await api("/api/v1/tenants/" + activeTenant.id + "/bots/connect-manual", {
        method:"POST", headers: {"Content-Type":"application/json"},
        body:JSON.stringify({bot_token:token}),
      });
      setNotice("ربات @" + bot.username + " با موفقیت به‌صورت در انتظار فعال‌سازی ثبت شد.", "success");
      await listBots();
    } catch(error) { setNotice(publicError(error), "error"); }
    finally { button.disabled = false; }
  });
  initialize();
})();
