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
import { Skeleton } from "@/components/ui/skeleton"
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table"
import { Badge } from "@/components/ui/badge"
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogFooter,
  DialogDescription,
} from "@/components/ui/dialog"
import apiFetch from "@/lib/api"
import type { Enquiry, EnquiryHistoryPage } from "@/lib/types"
import { isAdmin, resolveUser } from "@/lib/auth"
import { cn } from "@/lib/utils"

export const Route = createFileRoute("/enquiries")({ component: EnquiriesPage })

const emptyForm = {
  customer_name: "",
  phone: "",
  message: "",
  product_interest: "",
  delivery_area: "",
  source: "staff",
}

const STATUSES = ["new", "contacted", "converted", "closed"]

const statusStyles: Record<string, string> = {
  new: "border-blue-500/40 bg-blue-50 text-blue-700 dark:bg-blue-500/10 dark:text-blue-400",
  contacted: "border-amber-500/40 bg-amber-50 text-amber-700 dark:bg-amber-500/10 dark:text-amber-400",
  converted: "border-green-600/40 bg-green-50 text-green-700 dark:bg-green-500/10 dark:text-green-400",
  closed: "border-gray-300 bg-gray-100 text-gray-600 dark:border-gray-700 dark:bg-gray-800 dark:text-gray-400",
}

function EnquiryStatusBadge({ status }: { status: string }) {
  return (
    <Badge
      variant="outline"
      className={cn(
        "inline-flex items-center rounded-full border px-2.5 py-0.5 text-xs font-medium normal-case tracking-normal",
        statusStyles[status] ||
          "border-gray-300 bg-gray-100 text-gray-600 dark:border-gray-700 dark:bg-gray-800 dark:text-gray-400"
      )}
    >
      {status}
    </Badge>
  )
}

function EnquiriesPage() {
  const [admin, setAdmin] = useState(isAdmin())
  const [enquiries, setEnquiries] = useState<Enquiry[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [statusFilter, setStatusFilter] = useState("")
  const [showModal, setShowModal] = useState(false)
  const [form, setForm] = useState(emptyForm)
  const [saving, setSaving] = useState(false)
  const [historyFor, setHistoryFor] = useState<number | null>(null)
  const [historyData, setHistoryData] = useState<EnquiryHistoryPage | null>(null)
  const [historyLoading, setHistoryLoading] = useState(false)
  const [historyPage, setHistoryPage] = useState(0)
  const PAGE_SIZE = 10

  useEffect(() => {
    resolveUser().then((u) => setAdmin(u.role === "admin"))
  }, [])

  async function loadHistory(enquiryId: number, page = 0) {
    setHistoryFor(enquiryId)
    setHistoryPage(page)
    setHistoryLoading(true)
    try {
      const data = await apiFetch<EnquiryHistoryPage>(
        `/api/v1/enquiries/${enquiryId}/history?limit=${PAGE_SIZE}&offset=${page * PAGE_SIZE}`
      )
      setHistoryData(data)
    } catch {
      setHistoryData(null)
    } finally {
      setHistoryLoading(false)
    }
  }

  function closeHistory() {
    setHistoryFor(null)
    setHistoryData(null)
    setHistoryPage(0)
  }

  function load() {
    setLoading(true)
    setError(null)
    const params = statusFilter ? `?status=${statusFilter}` : ""
    apiFetch<Enquiry[]>(`/api/v1/enquiries${params}`)
      .then(setEnquiries)
      .catch((err) => setError(err instanceof Error ? err.message : "Failed to load"))
      .finally(() => setLoading(false))
  }

  useEffect(() => {
    load()
  }, [statusFilter])

  function openAdd() {
    setForm(emptyForm)
    setShowModal(true)
  }

  async function handleSave(e: React.FormEvent) {
    e.preventDefault()
    setSaving(true)
    try {
      await apiFetch("/api/v1/enquiries", {
        method: "POST",
        body: JSON.stringify(form),
      })
      setShowModal(false)
      load()
    } catch {
      alert("Failed to record enquiry")
    } finally {
      setSaving(false)
    }
  }

  async function updateStatus(e: Enquiry, status: string) {
    try {
      await apiFetch(`/api/v1/enquiries/${e.id}`, {
        method: "PATCH",
        body: JSON.stringify({ status }),
      })
      load()
    } catch {
      alert("Failed to update enquiry")
    }
  }

  return (
    <AppShell>
      <div className="space-y-6">
        <div className="flex items-center justify-between">
          <h1 className="text-2xl font-bold">Enquiries</h1>
          <Button onClick={openAdd}>New Enquiry</Button>
        </div>

        <div className="flex gap-2">
          <Button
            size="sm"
            variant={statusFilter === "" ? "default" : "outline"}
            onClick={() => setStatusFilter("")}
          >
            All
          </Button>
          {STATUSES.map((s) => (
            <Button
              key={s}
              size="sm"
              variant={statusFilter === s ? "default" : "outline"}
              onClick={() => setStatusFilter(s)}
            >
              {s.charAt(0).toUpperCase() + s.slice(1)}
            </Button>
          ))}
        </div>

        {loading ? (
          <div className="space-y-3">
            {Array.from({ length: 5 }).map((_, i) => (
              <Skeleton key={i} className="h-12 rounded-xl" />
            ))}
          </div>
        ) : error ? (
          <div className="flex flex-col gap-3 py-12">
            <p className="text-destructive">{error}</p>
            <Button onClick={load} variant="outline">
              Retry
            </Button>
          </div>
        ) : enquiries.length === 0 ? (
          <div className="py-16 text-center text-muted-foreground">No enquiries found</div>
        ) : (
          <Card>
            <CardContent className="p-0">
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Ref</TableHead>
                    <TableHead>Customer</TableHead>
                    <TableHead>Phone</TableHead>
                    <TableHead>Product Interest</TableHead>
                    <TableHead>Area</TableHead>
                    <TableHead>Status</TableHead>
                    <TableHead>Source</TableHead>
                    <TableHead>Actions</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {enquiries.map((e) => (
                    <TableRow key={e.id}>
                      <TableCell className="font-mono text-xs">{e.enquiry_number}</TableCell>
                      <TableCell className="font-medium">{e.customer_name || "\u2014"}</TableCell>
                      <TableCell className="font-mono text-xs">{e.phone}</TableCell>
                      <TableCell>{e.product_interest || "\u2014"}</TableCell>
                      <TableCell>{e.delivery_area || "\u2014"}</TableCell>
                      <TableCell>
                        <EnquiryStatusBadge status={e.status} />
                      </TableCell>
                      <TableCell>{e.source}</TableCell>
                      <TableCell>
                        <div className="flex flex-wrap gap-1">
                          {admin && (
                            <Button size="xs" variant="ghost" onClick={() => loadHistory(e.id)}>
                              History
                            </Button>
                          )}
                          {STATUSES.filter((s) => s !== e.status).map((s) => (
                            <Button key={s} size="xs" variant="outline" onClick={() => updateStatus(e, s)}>
                              {s.charAt(0).toUpperCase() + s.slice(1)}
                            </Button>
                          ))}
                        </div>
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </CardContent>
          </Card>
        )}
      </div>

      {showModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/20 p-4">
          <Card className="w-full max-w-md">
            <CardHeader>
              <CardTitle>New Enquiry</CardTitle>
            </CardHeader>
            <CardContent>
              <form onSubmit={handleSave} className="space-y-4">
                <div className="space-y-2">
                  <Label htmlFor="customer_name">Customer Name</Label>
                  <Input
                    id="customer_name"
                    value={form.customer_name}
                    onChange={(e) => setForm({ ...form, customer_name: e.target.value })}
                  />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="phone">Phone</Label>
                  <Input
                    id="phone"
                    value={form.phone}
                    onChange={(e) => setForm({ ...form, phone: e.target.value })}
                    required
                  />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="product_interest">Product Interest</Label>
                  <Input
                    id="product_interest"
                    value={form.product_interest}
                    onChange={(e) => setForm({ ...form, product_interest: e.target.value })}
                  />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="delivery_area">Delivery Area</Label>
                  <Input
                    id="delivery_area"
                    value={form.delivery_area}
                    onChange={(e) => setForm({ ...form, delivery_area: e.target.value })}
                  />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="message">Message</Label>
                  <Input
                    id="message"
                    value={form.message}
                    onChange={(e) => setForm({ ...form, message: e.target.value })}
                  />
                </div>
                <div className="flex justify-between gap-2">
                  <Button type="button" variant="outline" onClick={() => setShowModal(false)}>
                    Cancel
                  </Button>
                  <Button type="submit" disabled={saving || !form.phone}>
                    {saving ? "Saving..." : "Save"}
                  </Button>
                </div>
              </form>
            </CardContent>
          </Card>
        </div>
      )}

      <Dialog open={historyFor !== null} onOpenChange={(open) => !open && closeHistory()}>
        <DialogContent className="max-h-[80vh] overflow-y-auto sm:max-w-2xl">
          <DialogHeader>
            <DialogTitle>Enquiry History</DialogTitle>
            <DialogDescription>
              Latest interactions first
              {historyData && ` — ${historyData.total} change(s)`}
            </DialogDescription>
          </DialogHeader>

          <div className="space-y-1.5">
            {historyLoading ? (
              <p className="py-8 text-center text-sm text-muted-foreground">Loading history...</p>
            ) : !historyData || historyData.items.length === 0 ? (
              <p className="py-8 text-center text-sm text-muted-foreground">No history yet.</p>
            ) : (
              historyData.items.map((h, idx) => (
                <div key={h.id} className="flex flex-wrap items-center gap-2 text-sm border-b pb-1.5">
                  <Badge variant="secondary" className="text-xs">
                    {h.field}
                  </Badge>
                  <span className="font-mono text-xs text-muted-foreground">{h.old_value || "\u2014"}</span>
                  <span>{"\u2192"}</span>
                  <span className="font-mono text-xs font-medium">{h.new_value || "\u2014"}</span>
                  <span className="ml-auto text-xs text-muted-foreground">
                    {h.changed_by} ({h.actor_role})
                  </span>
                  <span className="text-xs text-muted-foreground">
                    {new Date(h.created_at).toLocaleString("en-IN")}
                  </span>
                  {idx === 0 && <Badge className="text-xs">Latest</Badge>}
                </div>
              ))
            )}
          </div>

          {historyData && historyData.total > PAGE_SIZE && (
            <DialogFooter className="flex items-center justify-between">
              <span className="text-xs text-muted-foreground">
                Page {historyPage + 1} of {Math.ceil(historyData.total / PAGE_SIZE)}
              </span>
              <div className="flex gap-1">
                <Button
                  size="xs"
                  variant="outline"
                  disabled={historyPage === 0 || historyLoading}
                  onClick={() => historyFor && loadHistory(historyFor, historyPage - 1)}
                >
                  Previous
                </Button>
                <Button
                  size="xs"
                  variant="outline"
                  disabled={(historyPage + 1) * PAGE_SIZE >= historyData.total || historyLoading}
                  onClick={() => historyFor && loadHistory(historyFor, historyPage + 1)}
                >
                  Next
                </Button>
              </div>
            </DialogFooter>
          )}
        </DialogContent>
      </Dialog>
    </AppShell>
  )
}
