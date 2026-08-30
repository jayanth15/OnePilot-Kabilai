"use client"

import { useLocation } from "@tanstack/react-router"
import {
  MilkIcon,
  Home01Icon,
  Location01Icon,
  BubbleChatIcon,
  ContactIcon,
  Settings01Icon,
  Logout02Icon,
  UserMultiple02Icon,
} from "@hugeicons/core-free-icons"
import { HugeiconsIcon } from "@hugeicons/react"

import { Button } from "@/components/ui/button"
import { isAdmin, logout } from "@/lib/auth"
import {
  Sidebar,
  SidebarContent,
  SidebarFooter,
  SidebarGroup,
  SidebarGroupContent,
  SidebarGroupLabel,
  SidebarHeader,
  SidebarMenu,
  SidebarMenuButton,
  SidebarMenuItem,
  SidebarRail,
} from "@/components/ui/sidebar"

const navItems = [
  { title: "Dashboard", href: "/dashboard", icon: Home01Icon, adminOnly: false },
  { title: "Products", href: "/products", icon: MilkIcon, adminOnly: false },
  { title: "Delivery Areas", href: "/delivery-areas", icon: Location01Icon, adminOnly: false },
  { title: "Enquiries", href: "/enquiries", icon: ContactIcon, adminOnly: false },
  { title: "Chat", href: "/chat", icon: BubbleChatIcon, adminOnly: false },
  { title: "Users", href: "/users", icon: UserMultiple02Icon, adminOnly: true },
  { title: "Settings", href: "/settings", icon: Settings01Icon, adminOnly: false },
].filter((item) => !item.adminOnly || isAdmin())

export function AppSidebar({ ...props }: React.ComponentProps<typeof Sidebar>) {
  const location = useLocation()
  const pathname = location.pathname

  return (
    <Sidebar {...props}>
      <SidebarHeader>
        <div className="flex flex-col gap-1 px-2 py-2">
          <div className="flex items-center gap-2">
            <div className="flex size-8 items-center justify-center rounded-md bg-primary text-primary-foreground">
              <HugeiconsIcon icon={MilkIcon} strokeWidth={2} className="size-5" />
            </div>
            <div>
              <div className="text-sm font-semibold leading-tight">Kabilai</div>
              <div className="text-xs text-muted-foreground leading-tight">Dairy CRM</div>
            </div>
          </div>
        </div>
      </SidebarHeader>
      <SidebarContent>
        <SidebarGroup>
          <SidebarGroupLabel>Manage</SidebarGroupLabel>
          <SidebarGroupContent>
            <SidebarMenu>
              {navItems.map((item) => {
                const isActive = pathname === item.href || pathname.startsWith(item.href + "/")
                return (
                  <SidebarMenuItem key={item.title}>
                    <SidebarMenuButton isActive={isActive} render={<a href={item.href} />}>
                      <HugeiconsIcon icon={item.icon} strokeWidth={2} className="size-4" />
                      <span>{item.title}</span>
                    </SidebarMenuButton>
                  </SidebarMenuItem>
                )
              })}
            </SidebarMenu>
          </SidebarGroupContent>
        </SidebarGroup>
      </SidebarContent>
      <SidebarFooter>
        <Button
          variant="ghost"
          className="w-full justify-start gap-2"
          onClick={logout}
        >
          <HugeiconsIcon icon={Logout02Icon} strokeWidth={2} className="size-4" />
          Logout
        </Button>
      </SidebarFooter>
      <SidebarRail />
    </Sidebar>
  )
}
