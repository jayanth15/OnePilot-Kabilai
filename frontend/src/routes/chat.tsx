import { createFileRoute } from "@tanstack/react-router"
import { useEffect, useRef, useState } from "react"

import { AppShell } from "@/components/app-shell"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Input } from "@/components/ui/input"
import { Skeleton } from "@/components/ui/skeleton"
import { Avatar, AvatarFallback } from "@/components/ui/avatar"
import { Badge } from "@/components/ui/badge"
import apiFetch from "@/lib/api"
import type { Contact, Message } from "@/lib/types"
import { formatTimeIST } from "@/lib/datetime"

export const Route = createFileRoute("/chat")({
  component: ChatPage,
  validateSearch: (search: Record<string, unknown>) => ({
    contact_id: typeof search.contact_id === "number" ? search.contact_id : undefined,
  }),
})

function ChatPage() {
  const [contacts, setContacts] = useState<Contact[]>([])
  const [selected, setSelected] = useState<Contact | null>(null)
  const [messages, setMessages] = useState<Message[]>([])
  const [input, setInput] = useState("")
  const [sending, setSending] = useState(false)
  const [flagging, setFlagging] = useState(false)
  const [loading, setLoading] = useState(true)
  const bottomRef = useRef<HTMLDivElement>(null)
  const sendingRef = useRef(false)
  const lastCountRef = useRef(0)

  function loadContacts(initial = false) {
    if (initial) setLoading(true)
    apiFetch<Contact[]>("/api/v1/contacts")
      .then((c) => {
        setContacts(c)
        if (c.length === 0) return
        const params = new URLSearchParams(window.location.search)
        const wanted = Number(params.get("contact_id"))
        if (Number.isFinite(wanted) && wanted > 0) {
          const match = c.find((item) => item.id === wanted)
          if (match) {
            setSelected(match)
            return
          }
        }
        setSelected((prev) => prev || c[0])
      })
      .catch(() => {})
      .finally(() => {
        if (initial) setLoading(false)
      })
  }

  useEffect(() => {
    loadContacts(true)
    // Background poll: keep the contact list and last-message previews fresh
    // (selection is preserved by `setSelected((prev) => prev || c[0])`).
    const t = setInterval(() => loadContacts(), 15000)
    return () => clearInterval(t)
  }, [])

  useEffect(() => {
    if (!selected) {
      setMessages([])
      return
    }
    let cancelled = false
    const fetchHistory = () => {
      apiFetch<Message[]>(`/api/v1/agent/history?contact_id=${selected.id}`)
        .then((msgs) => {
          // Don't clobber the optimistic message while a staff send is in flight
          if (!cancelled && !sendingRef.current) setMessages(msgs)
        })
        .catch(() => {})
    }
    fetchHistory()
    // Poll every 5s so inbound WhatsApp / AI replies sync while the chat is open
    const t = setInterval(fetchHistory, 5000)
    return () => {
      cancelled = true
      clearInterval(t)
    }
  }, [selected])

  useEffect(() => {
    // Only auto-scroll when messages were actually added, not on every poll refresh
    if (messages.length !== lastCountRef.current) {
      lastCountRef.current = messages.length
      bottomRef.current?.scrollIntoView({ behavior: "smooth" })
    }
  }, [messages])

  async function sendMessage(e: React.FormEvent) {
    e.preventDefault()
    if (!input.trim() || !selected || sending) return
    const text = input.trim()
    setInput("")
    setSending(true)
    sendingRef.current = true
    try {
      await apiFetch("/api/v1/agent/send", {
        method: "POST",
        body: JSON.stringify({ contact_id: selected.id, message: text }),
      })
      setMessages((m) => [
        ...m,
        { role: "assistant", content: text, direction: "outbound", created_at: new Date().toISOString() },
      ])
    } catch {
      alert("Failed to send message")
    } finally {
      sendingRef.current = false
      setSending(false)
      // Re-sync right away: the backend stores the message before replying,
      // so this picks it up (plus anything that arrived meanwhile).
      apiFetch<Message[]>(`/api/v1/agent/history?contact_id=${selected.id}`)
        .then(setMessages)
        .catch(() => {})
    }
  }

  async function flag(kind: "complaint" | "enquiry") {
    if (!selected || flagging) return
    setFlagging(true)
    try {
      const res = await apiFetch<{ kind: string; reference: string }>(`/api/v1/agent/${selected.id}/flag`, {
        method: "POST",
        body: JSON.stringify({ kind }),
      })
      alert(`Marked as ${res.kind}: ${res.reference}`)
    } catch {
      alert("Failed to flag as " + kind)
    } finally {
      setFlagging(false)
    }
  }

  return (
    <AppShell>
      <div className="flex h-[calc(100vh-7rem)] gap-4">
        <Card className="w-64 shrink-0">
          <CardHeader>
            <CardTitle className="text-sm">Contacts</CardTitle>
          </CardHeader>
          <CardContent className="p-0">
            {loading ? (
              <div className="space-y-2 p-3">
                <Skeleton className="h-10" />
                <Skeleton className="h-10" />
                <Skeleton className="h-10" />
              </div>
            ) : contacts.length === 0 ? (
              <div className="p-4 text-center text-sm text-muted-foreground">
                No contacts yet. Message the WhatsApp bot.
              </div>
            ) : (
              <div className="max-h-[calc(100vh-14rem)] overflow-y-auto">
                {contacts.map((c) => (
                  <button
                    key={c.id}
                    className={`flex w-full items-center gap-3 px-3 py-2 text-left hover:bg-accent ${
                      selected?.id === c.id ? "bg-accent" : ""
                    }`}
                    onClick={() => setSelected(c)}
                  >
                    <Avatar className="size-8">
                      <AvatarFallback className="text-xs">
                        {(c.name || "?").slice(0, 2).toUpperCase()}
                      </AvatarFallback>
                    </Avatar>
                    <div className="min-w-0 flex-1">
                      <div className="text-sm font-medium">{c.name || c.phone}</div>
                      {c.last_message && (
                        <div className="truncate text-xs text-muted-foreground">{c.last_message}</div>
                      )}
                    </div>
                  </button>
                ))}
              </div>
            )}
          </CardContent>
        </Card>

        <Card className="flex flex-1 flex-col">
          <CardHeader className="border-b">
            <div className="flex items-center justify-between">
              <CardTitle className="text-base">
                {selected ? selected.name || selected.phone : "Select a contact"}
              </CardTitle>
              {selected && (
                <div className="flex items-center gap-1">
                  <Badge variant="secondary" className="mr-1 text-xs">
                    Flag as
                  </Badge>
                  <Button size="xs" variant="outline" disabled={flagging} onClick={() => flag("complaint")}>
                    Complaint
                  </Button>
                  <Button size="xs" variant="outline" disabled={flagging} onClick={() => flag("enquiry")}>
                    Enquiry
                  </Button>
                </div>
              )}
            </div>
          </CardHeader>
          <CardContent className="flex flex-1 flex-col p-0">
            <div className="flex-1 space-y-3 overflow-y-auto p-4">
              {messages.length === 0 ? (
                <div className="py-16 text-center text-sm text-muted-foreground">
                  No messages yet for this contact.
                </div>
              ) : (
                messages.map((m, i) => {
                  const isOutbound = m.direction === "outbound" || m.role === "assistant"
                  const ts = m.created_at ? formatTimeIST(m.created_at) : ""
                  return (
                    <div key={i} className={`flex ${isOutbound ? "justify-end" : "justify-start"}`}>
                      <div className="flex max-w-[70%] flex-col">
                        <div
                          className={`whitespace-pre-wrap rounded-lg px-3 py-2 text-sm ${
                            isOutbound ? "bg-primary text-primary-foreground" : "bg-muted"
                          }`}
                        >
                          {m.content}
                        </div>
                        {ts && <div className="mt-0.5 text-right text-xs text-muted-foreground">{ts}</div>}
                      </div>
                    </div>
                  )
                })
              )}
              <div ref={bottomRef} />
            </div>
            <form onSubmit={sendMessage} className="flex gap-2 border-t p-3">
              <Input
                value={input}
                onChange={(e) => setInput(e.target.value)}
                placeholder="Type a message to send to the customer..."
                disabled={!selected}
              />
              <Button type="submit" disabled={!selected || !input.trim() || sending}>
                {sending ? "Sending..." : "Send"}
              </Button>
            </form>
          </CardContent>
        </Card>
      </div>
    </AppShell>
  )
}
