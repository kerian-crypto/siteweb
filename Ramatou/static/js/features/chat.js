import { api } from "../core/api.js";

function renderAttachment(message) {
  if (!message.attachment_url) return "";
  if (message.attachment_kind === "image") {
    return `<p><img src="${message.attachment_url}" alt="${message.attachment_name || "image"}" class="chat-media-image"></p>`;
  }
  if (message.attachment_kind === "video") {
    return `<p><video controls class="chat-media-video" src="${message.attachment_url}"></video></p>`;
  }
  return `<p><a href="${message.attachment_url}" target="_blank" rel="noopener">${message.attachment_name || "Document"}</a></p>`;
}

function renderChat(chatBoxEl, messages) {
  chatBoxEl.innerHTML = messages
    .map(
      (m) => `
      <div class="msg ${m.sender_role === "user" ? "client" : "admin"}">
        <strong>${m.author}</strong><br>
        ${m.message ? `<span>${m.message}</span>` : ""}
        ${renderAttachment(m)}
      </div>
      `
    )
    .join("");
  chatBoxEl.scrollTop = chatBoxEl.scrollHeight;
}

export function bindChat({ chatBoxEl, chatFormEl }) {
  if (!chatBoxEl || !chatFormEl) return;

  async function loadChat() {
    const payload = await api("/api/chat/thread");
    renderChat(chatBoxEl, payload.messages || []);
  }

  chatFormEl.addEventListener("submit", async (event) => {
    event.preventDefault();
    const data = new FormData(chatFormEl);
    const text = String(data.get("message") || "").trim();
    const attachment = data.get("attachment");
    if (!text && !(attachment && attachment.name)) return;

    try {
      await api("/api/chat/messages", {
        method: "POST",
        body: data,
      });
      chatFormEl.reset();
      await loadChat();
    } catch (error) {
      alert(error.message);
    }
  });

  loadChat();
  setInterval(loadChat, 4000);
}
