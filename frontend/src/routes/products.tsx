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
import { Textarea } from "@/components/ui/textarea"
import apiFetch from "@/lib/api"
import type { Product } from "@/lib/types"
import { StatusBadge } from "@/components/status-badge"

export const Route = createFileRoute("/products")({ component: ProductsPage })

const emptyForm = {
  name: "",
  category: "",
  unit: "",
  price: 0,
  description: "",
  is_available: true,
}

function ProductsPage() {
  const [products, setProducts] = useState<Product[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [showModal, setShowModal] = useState(false)
  const [editing, setEditing] = useState<Product | null>(null)
  const [form, setForm] = useState(emptyForm)
  const [saving, setSaving] = useState(false)

  function load() {
    setLoading(true)
    setError(null)
    apiFetch<Product[]>("/api/v1/products")
      .then(setProducts)
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

  function openEdit(p: Product) {
    setEditing(p)
    setForm({
      name: p.name,
      category: p.category,
      unit: p.unit,
      price: p.price,
      description: p.description,
      is_available: p.is_available,
    })
    setShowModal(true)
  }

  async function handleSave(e: React.FormEvent) {
    e.preventDefault()
    setSaving(true)
    try {
      const body = JSON.stringify(form)
      if (editing) {
        await apiFetch(`/api/v1/products/${editing.id}`, { method: "PATCH", body })
      } else {
        await apiFetch("/api/v1/products", { method: "POST", body })
      }
      setShowModal(false)
      load()
    } catch {
      alert("Failed to save product")
    } finally {
      setSaving(false)
    }
  }

  async function toggleAvailable(p: Product) {
    try {
      await apiFetch(`/api/v1/products/${p.id}`, {
        method: "PATCH",
        body: JSON.stringify({ is_available: !p.is_available }),
      })
      load()
    } catch {
      alert("Failed to update product")
    }
  }

  return (
    <AppShell>
      <div className="space-y-6">
        <div className="flex items-center justify-between">
          <h1 className="text-2xl font-bold">Products</h1>
          <Button onClick={openAdd}>Add Product</Button>
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
        ) : products.length === 0 ? (
          <div className="py-16 text-center text-muted-foreground">
            No products yet. Add your first dairy product.
          </div>
        ) : (
          <Card>
            <CardContent className="p-0">
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Name</TableHead>
                    <TableHead>Category</TableHead>
                    <TableHead>Unit</TableHead>
                    <TableHead>Price</TableHead>
                    <TableHead>Status</TableHead>
                    <TableHead>Actions</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {products.map((p) => (
                    <TableRow key={p.id}>
                      <TableCell className="font-medium">{p.name}</TableCell>
                      <TableCell>{p.category}</TableCell>
                      <TableCell>{p.unit || "\u2014"}</TableCell>
                      <TableCell>{"\u20b9"}{p.price}</TableCell>
                      <TableCell>
                        <StatusBadge active={p.is_available} activeLabel="Available" inactiveLabel="Unavailable" />
                      </TableCell>
                      <TableCell className="space-x-2">
                        <Button size="xs" variant="outline" onClick={() => openEdit(p)}>
                          Edit
                        </Button>
                        <Button size="xs" variant="ghost" onClick={() => toggleAvailable(p)}>
                          {p.is_available ? "Disable" : "Enable"}
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
              <CardTitle>{editing ? "Edit Product" : "Add Product"}</CardTitle>
            </CardHeader>
            <CardContent>
              <form onSubmit={handleSave} className="space-y-4">
                <div className="space-y-2">
                  <Label htmlFor="name">Name</Label>
                  <Input
                    id="name"
                    value={form.name}
                    onChange={(e) => setForm({ ...form, name: e.target.value })}
                    required
                  />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="category">Category</Label>
                  <Input
                    id="category"
                    value={form.category}
                    onChange={(e) => setForm({ ...form, category: e.target.value })}
                    placeholder="e.g. Fresh Milk"
                  />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="unit">Unit</Label>
                  <Input
                    id="unit"
                    value={form.unit}
                    onChange={(e) => setForm({ ...form, unit: e.target.value })}
                    placeholder="e.g. 500ml, 1kg"
                  />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="price">Price (INR)</Label>
                  <Input
                    id="price"
                    type="number"
                    step="0.01"
                    value={form.price}
                    onChange={(e) => setForm({ ...form, price: Number(e.target.value) })}
                    required
                  />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="description">Description</Label>
                  <Textarea
                    id="description"
                    value={form.description}
                    onChange={(e) => setForm({ ...form, description: e.target.value })}
                  />
                </div>
                <div className="flex items-center gap-2">
                  <input
                    id="is_available"
                    type="checkbox"
                    checked={form.is_available}
                    onChange={(e) => setForm({ ...form, is_available: e.target.checked })}
                  />
                  <Label htmlFor="is_available">Available for sale</Label>
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
