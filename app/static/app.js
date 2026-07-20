const messages = document.querySelector("#messages");
const form = document.querySelector("#chat-form");
const input = document.querySelector("#message-input");
const sendButton = document.querySelector("#send-button");
const productList = document.querySelector("#product-list");
const productCount = document.querySelector("#product-count");
const leadList = document.querySelector("#lead-list");
const leadCount = document.querySelector("#lead-count");
const orderList = document.querySelector("#order-list");
const orderCount = document.querySelector("#order-count");
const refreshLeadsButton = document.querySelector("#refresh-leads");
const operatorButton = document.querySelector("#operator-button");
const connectionPill = document.querySelector("#connection-pill");
const connectionText = document.querySelector("#connection-text");

const customerId = getCustomerId();

function getCustomerId() {
  const storageKey = "sales-assistant-demo-user";
  const existing = window.localStorage.getItem(storageKey);
  if (existing) return existing;

  const generated = `web-demo-${Date.now()}-${Math.random().toString(16).slice(2)}`;
  window.localStorage.setItem(storageKey, generated);
  return generated;
}

function toPersianDigits(value) {
  return String(value).replace(/\d/g, (digit) => "۰۱۲۳۴۵۶۷۸۹"[Number(digit)]);
}

function formatPrice(price) {
  return `${toPersianDigits(new Intl.NumberFormat("en-US", { maximumFractionDigits: 0 }).format(price))} تومان`;
}

function currentTime() {
  return new Intl.DateTimeFormat("fa-IR", { hour: "2-digit", minute: "2-digit" }).format(new Date());
}

function makeElement(tag, className, text) {
  const element = document.createElement(tag);
  if (className) element.className = className;
  if (text !== undefined) element.textContent = text;
  return element;
}

function setConnection(isOnline) {
  connectionPill.classList.toggle("offline", !isOnline);
  connectionText.textContent = isOnline ? "سیستم آماده است" : "اتصال قطع است";
}

function appendMessage(role, text, product = null, order = null) {
  const row = makeElement("div", `message-row ${role === "user" ? "user-row" : "assistant-row"}`);

  if (role !== "user") {
    row.append(makeElement("div", "mini-avatar", "ف"));
  }

  const bubble = makeElement("div", `message ${role === "user" ? "user-message" : "assistant-message"}`);
  bubble.append(makeElement("p", "", text));

  if (product) {
    bubble.append(makeElement("div", "message-product", `${product.name} · ${formatPrice(product.price)}`));
  }

  if (order) {
    bubble.append(makeElement("div", "message-order", `سفارش #${toPersianDigits(order.id)} · در انتظار پیگیری`));
  }

  bubble.append(makeElement("time", "", currentTime()));
  row.append(bubble);
  messages.append(row);
  messages.scrollTop = messages.scrollHeight;
}

function showTyping() {
  const row = makeElement("div", "message-row assistant-row");
  row.id = "typing-row";
  row.append(makeElement("div", "mini-avatar", "ف"));
  const bubble = makeElement("div", "message assistant-message typing");
  bubble.setAttribute("aria-label", "دستیار در حال نوشتن است");
  bubble.append(makeElement("span"), makeElement("span"), makeElement("span"));
  row.append(bubble);
  messages.append(row);
  messages.scrollTop = messages.scrollHeight;
}

function hideTyping() {
  document.querySelector("#typing-row")?.remove();
}

async function sendMessage(message) {
  const cleanMessage = message.trim();
  if (!cleanMessage || sendButton.disabled) return;

  appendMessage("user", cleanMessage);
  input.value = "";
  input.focus();
  sendButton.disabled = true;
  showTyping();

  try {
    const response = await fetch("/chat", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        instagram_user_id: customerId,
        customer_name: "بازدیدکننده دمو",
        message: cleanMessage,
      }),
    });

    if (!response.ok) throw new Error("Chat request failed");
    const result = await response.json();
    hideTyping();
    appendMessage("assistant", result.reply, result.product, result.order);
    setConnection(true);

    if (result.phone_saved || result.needs_human) {
      await loadLeads();
    }
    if (result.order) {
      await loadOrders();
      switchSalesTab("orders");
    }
  } catch (error) {
    hideTyping();
    appendMessage("assistant", "در ارتباط با سرور مشکلی پیش آمد. لطفاً چند لحظه دیگر دوباره تلاش کن.");
    setConnection(false);
  } finally {
    sendButton.disabled = false;
  }
}

function renderProducts(products) {
  productList.replaceChildren();
  productCount.textContent = toPersianDigits(products.length);

  products.forEach((product, index) => {
    const card = makeElement("article", "product-card");
    const meta = makeElement("div", "product-meta");
    meta.append(makeElement("div", "product-number", toPersianDigits(index + 1)));

    const details = makeElement("div");
    details.append(makeElement("h3", "", product.name));
    details.append(makeElement("p", "availability", product.is_available ? "موجود" : "ناموجود"));
    meta.append(details);
    card.append(meta);

    const price = makeElement("p", "price");
    price.append(document.createTextNode(formatPrice(product.price) + " "));
    price.append(makeElement("small", "", "قیمت فرضی"));
    card.append(price);

    const actions = makeElement("div", "product-actions");
    const askButton = makeElement("button", "ask-product", "درباره محصول");
    askButton.type = "button";
    askButton.addEventListener("click", () => sendMessage(`قیمت ${product.name} چنده؟`));
    const orderButton = makeElement("button", "order-product", "ثبت سفارش");
    orderButton.type = "button";
    orderButton.addEventListener("click", () => sendMessage(`سفارش ${product.name} را ثبت کن`));
    actions.append(askButton, orderButton);
    card.append(actions);
    productList.append(card);
  });
}

async function loadProducts() {
  try {
    const response = await fetch("/products");
    if (!response.ok) throw new Error("Products request failed");
    renderProducts(await response.json());
    setConnection(true);
  } catch (error) {
    productList.replaceChildren(makeElement("p", "loading-copy", "محصولات دریافت نشدند."));
    setConnection(false);
  }
}

function formatLeadDate(value) {
  try {
    return new Intl.DateTimeFormat("fa-IR", { dateStyle: "short", timeStyle: "short" }).format(new Date(value));
  } catch (error) {
    return "همین حالا";
  }
}

function renderLeads(leads) {
  leadList.replaceChildren();
  leadCount.textContent = toPersianDigits(leads.length);

  if (!leads.length) {
    const empty = makeElement("div", "empty-state");
    empty.append(makeElement("div", "empty-icon", "＋"));
    empty.append(makeElement("p", "", "هنوز شماره‌ای ثبت نشده"));
    empty.append(makeElement("span", "", "در چت یک شماره موبایل بفرست تا اینجا نمایش داده شود."));
    leadList.append(empty);
    return;
  }

  leads.forEach((lead) => {
    const card = makeElement("article", "lead-card");
    card.append(makeElement("h3", "", lead.name || "مشتری جدید"));
    const phone = makeElement("a", "", toPersianDigits(lead.phone));
    phone.href = `tel:${lead.phone}`;
    phone.setAttribute("aria-label", `تماس با ${lead.phone}`);
    card.append(phone);
    card.append(makeElement("p", "", `ثبت‌شده در ${formatLeadDate(lead.created_at)}`));
    leadList.append(card);
  });
}

async function loadLeads() {
  refreshLeadsButton.disabled = true;
  try {
    const response = await fetch("/leads");
    if (!response.ok) throw new Error("Leads request failed");
    renderLeads(await response.json());
  } catch (error) {
    leadList.replaceChildren(makeElement("p", "loading-copy", "سرنخ‌ها دریافت نشدند."));
  } finally {
    refreshLeadsButton.disabled = false;
  }
}

function renderOrders(orders) {
  orderList.replaceChildren();
  orderCount.textContent = toPersianDigits(orders.length);

  if (!orders.length) {
    const empty = makeElement("div", "empty-state");
    empty.append(makeElement("div", "empty-icon", "✓"));
    empty.append(makeElement("p", "", "هنوز سفارشی ثبت نشده"));
    empty.append(makeElement("span", "", "یک محصول انتخاب کن و بنویس «سفارشم را ثبت کن»."));
    orderList.append(empty);
    return;
  }

  orders.forEach((order) => {
    const card = makeElement("article", "lead-card order-card");
    const header = makeElement("div", "order-card-header");
    header.append(makeElement("h3", "", order.product_name));
    header.append(makeElement("span", "order-status", order.status === "pending" ? "در انتظار پیگیری" : order.status));
    card.append(header);
    card.append(makeElement("p", "order-price", formatPrice(order.total_price)));
    card.append(makeElement("span", "order-number", `ORDER #${order.id}`));
    card.append(makeElement("p", "", `${order.customer_name || "مشتری جدید"} · ${formatLeadDate(order.created_at)}`));
    orderList.append(card);
  });
}

async function loadOrders() {
  try {
    const response = await fetch("/orders");
    if (!response.ok) throw new Error("Orders request failed");
    renderOrders(await response.json());
  } catch (error) {
    orderList.replaceChildren(makeElement("p", "loading-copy", "سفارش‌ها دریافت نشدند."));
  }
}

function switchSalesTab(target) {
  document.querySelectorAll("[data-sales-tab]").forEach((button) => {
    const isActive = button.dataset.salesTab === target;
    button.classList.toggle("active", isActive);
    button.setAttribute("aria-selected", String(isActive));
  });
  document.querySelector("#leads-view").hidden = target !== "leads";
  document.querySelector("#orders-view").hidden = target !== "orders";
}

form.addEventListener("submit", (event) => {
  event.preventDefault();
  sendMessage(input.value);
});

document.querySelectorAll(".suggestion-chip").forEach((button) => {
  button.addEventListener("click", () => sendMessage(button.dataset.message || ""));
});

refreshLeadsButton.addEventListener("click", () => Promise.all([loadLeads(), loadOrders()]));
operatorButton.addEventListener("click", () => sendMessage("می‌خواهم با اپراتور صحبت کنم"));

document.querySelectorAll("[data-sales-tab]").forEach((button) => {
  button.addEventListener("click", () => switchSalesTab(button.dataset.salesTab));
});

Promise.all([loadProducts(), loadLeads(), loadOrders()]);
