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
import { StatusBadge } from "@/components/status-badge"
import apiFetch from "@/lib/api"
import type { DeliveryArea } from "@/lib/types"

export const Route = createFileRoute("/delivery-areas")({ component: DeliveryAreasPage })

const emptyForm = { name: "", pincode: "", city: "Chennai", is_active: true }

function DeliveryAreasPage() {
  const [areas, setAreas] = useState<DeliveryArea[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [showModal, setShowModal] = useState(false)
  const [editing, setEditing] = useState<DeliveryArea | null>(null)
  const [form, setForm] = useState(emptyForm)
  const [saving, setSaving] = useState(false)

  function load() {
    setLoading(true)
    setError(null)
    apiFetch<DeliveryArea[]>("/api/v1/delivery-areas")
      .then(setAreas)
      .catch((err) => setError(err instanceof Error ? err.message : "Failed to load"))
      .finally(() => setLoading(false))
  }

  useEffect(() => {
    load()
  }, [])

  function openAdd() {
    setEditing(null)
    setForm(emptyForm)
    setShowModal(true)
  }

  function openEdit(a: DeliveryArea) {
    setEditing(a)
    setForm({ name: a.name, pincode: a.pincode, city: a.city, is_active: a.is_active })
    setShowModal(true)
  }

  async function handleSave(e: React.FormEvent) {
    e.preventDefault()
    setSaving(true)
    try {
      const body = JSON.stringify(form)
      if (editing) {
        await apiFetch(`/api/v1/delivery-areas/${editing.id}`, { method: "PATCH", body })
      } else {
        await apiFetch("/api/v1/delivery-areas", { method: "POST", body })
      }
      setShowModal(false)
      load()
    } catch {
      alert("Failed to save delivery area")
    } finally {
      setSaving(false)
    }
  }

  async function toggleArea(a: DeliveryArea) {
    try {
      await apiFetch(`/api/v1/delivery-areas/${a.id}`, {
        method: "PATCH",
        body: JSON.stringify({ is_active: !a.is_active }),
      })
      load()
    } catch {
      alert("Failed to update area")
    }
  }

  async function removeArea(a: DeliveryArea) {
    if (!confirm(`Remove delivery area "${a.name}"?`)) return
    try {
      await apiFetch(`/api/v1/delivery-areas/${a.id}`, { method: "DELETE" })
      load()
    } catch {
      alert("Failed to delete area")
    }
  }

  return (
    <AppShell>
      <div className="space-y-6">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-bold">Delivery Areas</h1>
            <p className="text-sm text-muted-foreground">Chennai coverage areas for delivery</p>
          </div>
          <Button onClick={openAdd}>Add Area</Button>
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
        ) : areas.length === 0 ? (
          <div className="py-16 text-center text-muted-foreground">
            No delivery areas configured. Add areas to enable delivery checks.
          </div>
        ) : (
          <Card>
            <CardContent className="p-0">
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Area</TableHead>
                    <TableHead>Pincode</TableHead>
                    <TableHead>City</TableHead>
                    <TableHead>Status</TableHead>
                    <TableHead>Actions</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {areas.map((a) => (
                    <TableRow key={a.id}>
                      <TableCell className="font-medium">{a.name}</TableCell>
                      <TableCell className="font-mono text-xs">{a.pincode}</TableCell>
                      <TableCell>{a.city}</TableCell>
                      <TableCell>
                        <StatusBadge active={a.is_active} />
                      </TableCell>
                      <TableCell className="space-x-2">
                        <Button size="xs" variant="outline" onClick={() => openEdit(a)}>
                          Edit
                        </Button>
                        <Button size="xs" variant="ghost" onClick={() => toggleArea(a)}>
                          {a.is_active ? "Disable" : "Enable"}
                        </Button>
                        <Button size="xs" variant="destructive" onClick={() => removeArea(a)}>
                          Delete
                        </Button>
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
              <CardTitle>{editing ? "Edit Area" : "Add Area"}</CardTitle>
            </CardHeader>
            <CardContent>
              <form onSubmit={handleSave} className="space-y-4">
                <div className="space-y-2">
                  <Label htmlFor="name">Area / Locality</Label>
                  <Input
                    id="name"
                    value={form.name}
                    onChange={(e) => setForm({ ...form, name: e.target.value })}
                    placeholder="e.g. T. Nagar"
                    required
                  />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="pincode">Pincode</Label>
                  <Input
                    id="pincode"
                    value={form.pincode}
                    onChange={(e) => setForm({ ...form, pincode: e.target.value })}
                    placeholder="e.g. 600017"
                  />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="city">City</Label>
                  <Input
                    id="city"
                    value={form.city}
                    onChange={(e) => setForm({ ...form, city: e.target.value })}
                  />
                </div>
                <div className="flex items-center gap-2">
                  <input
                    id="is_active"
                    type="checkbox"
                    checked={form.is_active}
                    onChange={(e) => setForm({ ...form, is_active: e.target.checked })}
                  />
                  <Label htmlFor="is_active">Active</Label>
                </div>
                <div className="flex justify-between gap-2">
                  <Button type="button" variant="outline" onClick={() => setShowModal(false)}>
                    Cancel
                  </Button>
                  <Button type="submit" disabled={saving || !form.name}>
                    {saving ? "Saving..." : editing ? "Update" : "Add"}
                  </Button>
                </div>
              </form>
            </CardContent>
          </Card>
        </div>
      )}
    </AppShell>
  )
}
