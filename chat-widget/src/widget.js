const AGENT_URL = import.meta.env.VITE_AGENT_URL || "http://localhost:8000";

function mount(root) {
  root.innerHTML = `
    <div class="ai-widget">
      <strong>AI Chat Widget</strong>
      <p>Phase 1 stub. Agent: <code>${AGENT_URL}/health</code></p>
    </div>
  `;
}

const root = document.getElementById("ai-chat-widget-root");
if (root) {
  mount(root);
}

export function createChatWidget(target) {
  const el = typeof target === "string" ? document.querySelector(target) : target;
  if (!el) {
    throw new Error("chat widget mount target not found");
  }
  mount(el);
}

export default { createChatWidget };
