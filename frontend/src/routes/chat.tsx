import { createFileRoute } from "@tanstack/react-router"
import { useEffect, useRef, useState } from "react"

import { AppShell } from "@/components/app-shell"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Skeleton } from "@/components/ui/skeleton"
import { Avatar, AvatarFallback } from "@/components/ui/avatar"
import apiFetch from "@/lib/api"
import type { Contact, Message } from "@/lib/types"

export const Route = createFileRoute("/chat")({ component: ChatPage })

function ChatPage() {
  const [contacts, setContacts] = useState<Contact[]>([])
  const [selected, setSelected] = useState<Contact | null>(null)
  const [messages, setMessages] = useState<Message[]>([])
  const [loading, setLoading] = useState(true)
  const bottomRef = useRef<HTMLDivElement>(null)

  function loadContacts() {
    setLoading(true)
    apiFetch<Contact[]>("/api/v1/contacts")
      .then((c) => {
        setContacts(c)
        if (c.length > 0) setSelected((prev) => prev || c[0])
      })
      .catch(() => {})
      .finally(() => setLoading(false))
  }

  useEffect(() => {
    loadContacts()
  }, [])

  useEffect(() => {
    if (selected) {
      apiFetch<Message[]>(`/api/v1/agent/history?contact_id=${selected.id}`)
        .then(setMessages)
        .catch(() => setMessages([]))
    }
  }, [selected])

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" })
  }, [messages])

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
            <CardTitle className="text-base">
              {selected ? selected.name || selected.phone : "Select a contact"}
            </CardTitle>
          </CardHeader>
          <CardContent className="flex flex-1 flex-col p-0">
            <div className="flex-1 space-y-3 overflow-y-auto p-4">
              {messages.length === 0 ? (
                <div className="py-16 text-center text-sm text-muted-foreground">
                  No messages yet. Start the conversation by saying "kabilai ai".
                </div>
              ) : (
                messages.map((m, i) => (
                  <div key={i} className={`flex ${m.role === "user" ? "justify-end" : "justify-start"}`}>
                    <div
                      className={`max-w-[70%] whitespace-pre-wrap rounded-lg px-3 py-2 text-sm ${
                        m.role === "user"
                          ? "bg-primary text-primary-foreground"
                          : "bg-muted"
                      }`}
                    >
                      {m.content}
                    </div>
                  </div>
                ))
              )}
              <div ref={bottomRef} />
            </div>
          </CardContent>
        </Card>
      </div>
    </AppShell>
  )
}
