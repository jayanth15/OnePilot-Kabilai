import { createFileRoute } from "@tanstack/react-router"
import { useEffect, useState } from "react"

import { AppShell } from "@/components/app-shell"
import { Button } from "@/components/ui/button"
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
} from "@/components/ui/card"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Textarea } from "@/components/ui/textarea"
import { Skeleton } from "@/components/ui/skeleton"
import { Badge } from "@/components/ui/badge"
import apiFetch from "@/lib/api"
import type { CompanyInfo } from "@/lib/types"

export const Route = createFileRoute("/settings")({ component: SettingsPage })

type AppSettings = {
  environment: string
  api_prefix: string
  agent_model: string
  messaging_channel: string
  messaging_mock: boolean
  source_number: string
  session_idle_minutes: number
  contacts: { id: number; phone: string; name: string; created_at: string }[]
}

const emptyCompany: CompanyInfo = {
  name: "",
  address: "",
  phone: "",
  whatsapp_number: "",
  intro_message: "",
  ai_enabled: true,
}

function SettingsPage() {
  const [data, setData] = useState<AppSettings | null>(null)
  const [company, setCompany] = useState<CompanyInfo>(emptyCompany)
  const [saving, setSaving] = useState(false)
  const [saveMsg, setSaveMsg] = useState<string | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  function load() {
    setLoading(true)
    setError(null)
    Promise.all([
      apiFetch<AppSettings>("/api/v1/settings"),
      apiFetch<CompanyInfo>("/api/v1/company"),
    ])
      .then(([settings, comp]) => {
        setData(settings)
        setCompany(comp)
      })
      .catch((err) => setError(err instanceof Error ? err.message : "Failed to load"))
      .finally(() => setLoading(false))
  }

  useEffect(() => {
    load()
  }, [])

  async function saveCompany(e: React.FormEvent) {
    e.preventDefault()
    setSaving(true)
    setSaveMsg(null)
    try {
      const updated = await apiFetch<CompanyInfo>("/api/v1/company", {
        method: "PATCH",
        body: JSON.stringify(company),
      })
      setCompany(updated)
      setSaveMsg("Saved. The agent will now use the updated intro message and address.")
    } catch (err) {
      setSaveMsg(err instanceof Error ? err.message : "Failed to save")
    } finally {
      setSaving(false)
    }
  }

  if (loading) {
    return (
      <AppShell>
        <Skeleton className="h-8 w-40" />
        <div className="mt-6 space-y-4">
          <Skeleton className="h-56" />
          <Skeleton className="h-40" />
          <Skeleton className="h-40" />
        </div>
      </AppShell>
    )
  }

  if (error) {
    return (
      <AppShell>
        <p className="text-destructive">{error}</p>
        <Button onClick={load} variant="outline">
          Retry
        </Button>
      </AppShell>
    )
  }

  return (
    <AppShell>
      <div className="space-y-6">
        <h1 className="text-2xl font-bold">Settings</h1>

        <Card>
          <CardHeader>
            <CardTitle className="text-sm">Company / WhatsApp Agent</CardTitle>
          </CardHeader>
          <CardContent>
            <form onSubmit={saveCompany} className="space-y-4">
              <div className="space-y-2">
                <Label htmlFor="name">Company Name</Label>
                <Input
                  id="name"
                  value={company.name}
                  onChange={(e) => setCompany({ ...company, name: e.target.value })}
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="address">Company Address</Label>
                <Textarea
                  id="address"
                  value={company.address}
                  onChange={(e) => setCompany({ ...company, address: e.target.value })}
                  placeholder="Full business address"
                />
                <p className="text-xs text-muted-foreground">
                  The agent shares this when a customer asks for the address.
                </p>
              </div>
              <div className="grid gap-4 md:grid-cols-2">
                <div className="space-y-2">
                  <Label htmlFor="phone">Phone</Label>
                  <Input
                    id="phone"
                    value={company.phone}
                    onChange={(e) => setCompany({ ...company, phone: e.target.value })}
                  />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="whatsapp_number">WhatsApp Number</Label>
                  <Input
                    id="whatsapp_number"
                    value={company.whatsapp_number}
                    onChange={(e) => setCompany({ ...company, whatsapp_number: e.target.value })}
                  />
                </div>
              </div>
              <div className="space-y-2">
                <Label htmlFor="intro_message">Introductory Message</Label>
                <Textarea
                  id="intro_message"
                  value={company.intro_message}
                  onChange={(e) => setCompany({ ...company, intro_message: e.target.value })}
                  placeholder="Sent when a customer types 'kabilai ai'"
                  rows={4}
                />
                <p className="text-xs text-muted-foreground">
                  This is the first message a customer sees when they trigger the agent with
                  "kabilai ai".
                </p>
              </div>
              {saveMsg && <p className="text-sm text-muted-foreground">{saveMsg}</p>}
              <Button type="submit" disabled={saving}>
                {saving ? "Saving..." : "Save"}
              </Button>
            </form>
          </CardContent>
        </Card>

        <div className="grid gap-4 md:grid-cols-2">
          <Card>
            <CardHeader>
              <CardTitle className="text-sm">Application</CardTitle>
            </CardHeader>
            <CardContent className="space-y-2 text-sm">
              <Row label="Environment" value={data?.environment ?? "\u2014"} />
              <Row label="API Prefix" value={data?.api_prefix ?? "\u2014"} />
              <Row label="Agent Model" value={data?.agent_model ?? "\u2014"} />
              <Row label="Session idle (min)" value={String(data?.session_idle_minutes ?? "\u2014")} />
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle className="text-sm">WhatsApp Messaging</CardTitle>
            </CardHeader>
            <CardContent className="space-y-2 text-sm">
              <Row label="Channel" value={data?.messaging_channel ?? "\u2014"} />
              <Row label="Source Number" value={data?.source_number ?? "\u2014"} />
              <div className="flex items-center justify-between py-1">
                <span className="text-muted-foreground">Mode</span>
                <Badge variant={data?.messaging_mock ? "secondary" : "default"}>
                  {data?.messaging_mock ? "Mock (test)" : "Live"}
                </Badge>
              </div>
            </CardContent>
          </Card>
        </div>

        <Card>
          <CardHeader>
            <CardTitle className="text-sm">Contacts</CardTitle>
          </CardHeader>
          <CardContent className="p-0">
            {data?.contacts.length === 0 ? (
              <div className="p-6 text-center text-sm text-muted-foreground">No contacts yet</div>
            ) : (
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b bg-muted/50 text-left">
                    <th className="px-4 py-2 font-medium">Name</th>
                    <th className="px-4 py-2 font-medium">Phone</th>
                    <th className="px-4 py-2 font-medium">Created</th>
                  </tr>
                </thead>
                <tbody>
                  {(data?.contacts ?? []).map((c) => (
                    <tr key={c.id} className="border-b">
                      <td className="px-4 py-2">{c.name || "\u2014"}</td>
                      <td className="px-4 py-2 font-mono text-xs">{c.phone}</td>
                      <td className="px-4 py-2 text-muted-foreground">
                        {new Date(c.created_at).toLocaleDateString("en-IN")}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            )}
          </CardContent>
        </Card>
      </div>
    </AppShell>
  )
}

function Row({ label, value }: { label: string; value: string }) {
  return (
    <div className="flex items-center justify-between py-1">
      <span className="text-muted-foreground">{label}</span>
      <span className="font-medium">{value}</span>
    </div>
  )
}
