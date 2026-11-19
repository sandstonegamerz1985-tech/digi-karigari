import { useEffect, useRef, useState } from "react";
import { Link, useSearchParams } from "react-router-dom";
import { api, assetUrl } from "../api";
import { EmptyState, Loading } from "../components/States";
import { useAuth } from "../context/AuthContext";

export default function Messages() {
  const { user } = useAuth();
  const [searchParams, setSearchParams] = useSearchParams();
  const activeConvoId = searchParams.get("convo");

  const [conversations, setConversations] = useState([]);
  const [loading, setLoading] = useState(true);
  const [activeThread, setActiveThread] = useState(null);
  const [threadLoading, setThreadLoading] = useState(false);
  const [messageText, setMessageText] = useState("");
  const [sending, setSending] = useState(false);
  const [error, setError] = useState("");

  const messagesEndRef = useRef(null);

  const fetchConversations = async (keepSelection = true) => {
    try {
      const data = await api.conversations();
      setConversations(data || []);
      if (!keepSelection && data && data.length > 0 && !activeConvoId) {
        setSearchParams({ convo: data[0].id });
      }
    } catch (err) {
      setError(err.message || "Failed to load conversations.");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchConversations(false);
  }, []);

  const loadThread = async (id) => {
    setThreadLoading(true);
    try {
      const res = await api.conversationThread(id);
      setActiveThread(res);
      // Update unread count in local list
      setConversations((prev) =>
        prev.map((c) => (c.id === parseInt(id, 10) ? { ...c, unread_count: 0 } : c))
      );
    } catch (err) {
      setError(err.message || "Failed to load conversation thread.");
    } finally {
      setThreadLoading(false);
    }
  };

  useEffect(() => {
    if (activeConvoId) {
      loadThread(activeConvoId);
    } else {
      setActiveThread(null);
    }
  }, [activeConvoId]);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [activeThread]);

  const handleSendMessage = async (e) => {
    e?.preventDefault();
    if (!messageText.trim() || sending || !activeConvoId) return;

    setSending(true);
    try {
      const sentMsg = await api.sendMessage(activeConvoId, messageText.trim());
      setMessageText("");
      setActiveThread((prev) => ({
        ...prev,
        messages: [...(prev?.messages || []), sentMsg],
      }));
      // Refresh list snippet
      setConversations((prev) =>
        prev.map((c) =>
          c.id === parseInt(activeConvoId, 10)
            ? { ...c, last_message_text: sentMsg.text, last_message_at: sentMsg.created_at }
            : c
        )
      );
    } catch (err) {
      alert(err.message || "Failed to send message.");
    } finally {
      setSending(false);
    }
  };

  const handleKeyDown = (e) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSendMessage();
    }
  };

  if (loading) return <Loading text="Loading conversations..." />;

  return (
    <div className="container section">
      <div className="section-head">
        <div>
          <h2>Artisan & Buyer Messages</h2>
          <p className="muted small">Direct communication between buyers, artisans, and marketplace support.</p>
        </div>
      </div>

      {error && <div className="alert alert-error">{error}</div>}

      {conversations.length === 0 ? (
        <EmptyState
          title="Your inbox is empty"
          text="You don't have any active conversations yet. Visit product pages or order details to message an artisan directly."
        />
      ) : (
        <div className="inbox-container">
          {/* Left: Conversations list */}
          <div className="inbox-list">
            <div style={{ padding: "0.75rem 1rem", borderBottom: "1px solid var(--border)", background: "#faf8f5" }}>
              <strong style={{ fontSize: "0.88rem" }}>Conversations ({conversations.length})</strong>
            </div>
            {conversations.map((c) => {
              const isSelected = String(c.id) === String(activeConvoId);
              return (
                <div
                  key={c.id}
                  className={`inbox-item ${isSelected ? "active" : ""}`}
                  onClick={() => setSearchParams({ convo: c.id })}
                >
                  <div className="inbox-item-header">
                    <span style={{ fontWeight: c.unread_count > 0 ? 800 : 600, color: "var(--indigo)" }}>
                      {c.other_user?.name || "Marketplace User"}
                    </span>
                    <span className="small muted" style={{ fontSize: "0.72rem" }}>
                      {new Date(c.last_message_at).toLocaleDateString("en-IN", { month: "short", day: "numeric" })}
                    </span>
                  </div>

                  <div className="small muted" style={{ marginBottom: "0.2rem", fontWeight: 500 }}>
                    {c.subject}
                  </div>

                  <div className="between">
                    <span
                      className="small"
                      style={{
                        color: c.unread_count > 0 ? "var(--text)" : "var(--muted)",
                        fontWeight: c.unread_count > 0 ? 700 : 400,
                        whiteSpace: "nowrap",
                        overflow: "hidden",
                        textOverflow: "ellipsis",
                        maxWidth: "200px",
                      }}
                    >
                      {c.last_message_text || "No messages yet"}
                    </span>
                    {c.unread_count > 0 && <span className="unread-dot" title="Unread messages" />}
                  </div>
                </div>
              );
            })}
          </div>

          {/* Right: Active chat pane */}
          <div className="chat-pane">
            {!activeThread ? (
              <div style={{ display: "grid", placeItems: "center", height: "100%", padding: "2rem", color: "var(--muted)" }}>
                Select a conversation from the left to read messages.
              </div>
            ) : threadLoading ? (
              <Loading text="Loading messages..." />
            ) : (
              <>
                <div className="chat-head">
                  <div>
                    <h3 style={{ margin: 0, fontSize: "1.1rem" }}>{activeThread.conversation.other_user?.name}</h3>
                    <div className="small muted">
                      {activeThread.conversation.other_user?.craft
                        ? `Artisan: ${activeThread.conversation.other_user.craft}`
                        : `Role: ${activeThread.conversation.other_user?.role}`}
                    </div>
                  </div>

                  {activeThread.conversation.product && (
                    <Link
                      to={`/product/${activeThread.conversation.product.id}`}
                      className="row"
                      style={{
                        textDecoration: "none",
                        color: "inherit",
                        background: "#fff",
                        padding: "0.3rem 0.6rem",
                        borderRadius: "8px",
                        border: "1px solid var(--border)",
                      }}
                    >
                      {activeThread.conversation.product.image_url && (
                        <img
                          src={assetUrl(activeThread.conversation.product.image_url)}
                          alt=""
                          style={{ width: "32px", height: "32px", borderRadius: "4px", objectFit: "cover" }}
                        />
                      )}
                      <div className="small">
                        <div style={{ fontWeight: 600 }}>{activeThread.conversation.product.title.slice(0, 24)}...</div>
                        <div style={{ color: "var(--saffron-dark)" }}>
                          ₹{activeThread.conversation.product.price.toLocaleString("en-IN")}
                        </div>
                      </div>
                    </Link>
                  )}
                </div>

                <div className="chat-messages">
                  {activeThread.messages.length === 0 ? (
                    <div className="small muted" style={{ textAlign: "center", marginTop: "2rem" }}>
                      Send the first message to start this discussion.
                    </div>
                  ) : (
                    activeThread.messages.map((m) => {
                      const isMe = m.sender_id === user?.id;
                      return (
                        <div key={m.id} className={`chat-bubble ${isMe ? "chat-bubble-me" : "chat-bubble-other"}`}>
                          {!isMe && (
                            <div style={{ fontSize: "0.72rem", fontWeight: 700, marginBottom: "0.2rem", color: "var(--indigo)" }}>
                              {m.sender_name}
                            </div>
                          )}
                          <div>{m.text}</div>
                          <div className="chat-time">
                            {new Date(m.created_at).toLocaleTimeString("en-IN", { hour: "2-digit", minute: "2-digit" })}
                          </div>
                        </div>
                      );
                    })
                  )}
                  <div ref={messagesEndRef} />
                </div>

                <form className="chat-composer" onSubmit={handleSendMessage}>
                  <textarea
                    rows={1}
                    placeholder="Type your message... (Press Enter to send, Shift+Enter for new line)"
                    value={messageText}
                    onChange={(e) => setMessageText(e.target.value)}
                    onKeyDown={handleKeyDown}
                    disabled={sending}
                  />
                  <button type="submit" className="btn btn-small" disabled={sending || !messageText.trim()}>
                    {sending ? "..." : "Send"}
                  </button>
                </form>
              </>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
