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
import { Switch } from "@/components/ui/switch"
import { Label } from "@/components/ui/label"
import apiFetch from "@/lib/api"
import type { Product, DeliveryArea, Enquiry, CompanyInfo } from "@/lib/types"

export const Route = createFileRoute("/dashboard")({ component: DashboardPage })

function DashboardPage() {
  const [products, setProducts] = useState<Product[]>([])
  const [areas, setAreas] = useState<DeliveryArea[]>([])
  const [enquiries, setEnquiries] = useState<Enquiry[]>([])
  const [company, setCompany] = useState<CompanyInfo | null>(null)
  const [aiToggling, setAiToggling] = useState(false)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  function load() {
    setLoading(true)
    setError(null)
    Promise.all([
      apiFetch<Product[]>("/api/v1/products"),
      apiFetch<DeliveryArea[]>("/api/v1/delivery-areas"),
      apiFetch<Enquiry[]>("/api/v1/enquiries"),
      apiFetch<CompanyInfo>("/api/v1/company"),
    ])
      .then(([p, a, e, c]) => {
        setProducts(p)
        setAreas(a)
        setEnquiries(e)
        setCompany(c)
      })
      .catch((err) => setError(err instanceof Error ? err.message : "Failed to load"))
      .finally(() => setLoading(false))
  }

  useEffect(() => {
    load()
  }, [])

  async function toggleAi(enabled: boolean) {
    if (!company) return
    setAiToggling(true)
    try {
      const updated = await apiFetch<CompanyInfo>("/api/v1/company", {
        method: "PATCH",
        body: JSON.stringify({ ai_enabled: enabled }),
      })
      setCompany(updated)
    } catch {
      alert("Failed to update AI assistant setting")
    } finally {
      setAiToggling(false)
    }
  }

  const activeProducts = products.filter((p) => p.is_available).length
  const activeAreas = areas.filter((a) => a.is_active).length
  const newEnquiries = enquiries.filter((e) => e.status === "new").length

  if (loading) {
    return (
      <AppShell>
        <div className="space-y-4">
          <Skeleton className="h-8 w-48" />
          <div className="grid gap-4 md:grid-cols-4">
            {Array.from({ length: 4 }).map((_, i) => (
              <Skeleton key={i} className="h-24 rounded-xl" />
            ))}
          </div>
          <Skeleton className="h-64 rounded-xl" />
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
        <div className="flex items-center justify-between">
          <h1 className="text-2xl font-bold">Dashboard</h1>
          <div className="flex items-center gap-4">
            <div className="flex items-center gap-2">
              <Switch
                id="ai_toggle"
                checked={company?.ai_enabled ?? false}
                disabled={aiToggling}
                onCheckedChange={(v) => toggleAi(v)}
              />
              <Label htmlFor="ai_toggle" className="text-sm font-medium">
                AI Assistant {company?.ai_enabled ? "On" : "Off"}
              </Label>
            </div>
            <Button variant="outline" onClick={load}>
              Refresh
            </Button>
          </div>
        </div>

        <div className="grid gap-4 md:grid-cols-4">
          <Card>
            <CardHeader>
              <CardTitle className="text-xs">Products</CardTitle>
            </CardHeader>
            <CardContent>
              <span className="text-3xl font-bold">{activeProducts}</span>
              <span className="ml-2 text-sm text-muted-foreground">/ {products.length}</span>
            </CardContent>
          </Card>
          <Card>
            <CardHeader>
              <CardTitle className="text-xs">Delivery Areas</CardTitle>
            </CardHeader>
            <CardContent>
              <span className="text-3xl font-bold">{activeAreas}</span>
              <span className="ml-2 text-sm text-muted-foreground">/ {areas.length}</span>
            </CardContent>
          </Card>
          <Card>
            <CardHeader>
              <CardTitle className="text-xs">Enquiries</CardTitle>
            </CardHeader>
            <CardContent>
              <span className="text-3xl font-bold">{enquiries.length}</span>
            </CardContent>
          </Card>
          <Card>
            <CardHeader>
              <CardTitle className="text-xs">New Enquiries</CardTitle>
            </CardHeader>
            <CardContent>
              <span className="text-3xl font-bold text-amber-600">{newEnquiries}</span>
            </CardContent>
          </Card>
        </div>

        <Card>
          <CardHeader>
            <CardTitle>Recent Enquiries</CardTitle>
          </CardHeader>
          <CardContent className="p-0">
            {enquiries.length === 0 ? (
              <div className="p-8 text-center text-muted-foreground">No enquiries yet</div>
            ) : (
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Ref</TableHead>
                    <TableHead>Customer</TableHead>
                    <TableHead>Product Interest</TableHead>
                    <TableHead>Area</TableHead>
                    <TableHead>Status</TableHead>
                    <TableHead>Date</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {enquiries.slice(0, 8).map((e) => (
                    <TableRow key={e.id}>
                      <TableCell className="font-mono text-xs">{e.enquiry_number}</TableCell>
                      <TableCell>{e.customer_name}</TableCell>
                      <TableCell>{e.product_interest || "\u2014"}</TableCell>
                      <TableCell>{e.delivery_area || "\u2014"}</TableCell>
                      <TableCell>
                        <Badge variant="secondary">{e.status}</Badge>
                      </TableCell>
                      <TableCell className="text-muted-foreground">
                        {new Date(e.created_at).toLocaleDateString("en-IN")}
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            )}
          </CardContent>
        </Card>
      </div>
    </AppShell>
  )
}
