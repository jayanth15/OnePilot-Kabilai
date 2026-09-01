export type Product = {
  id: number
  name: string
  category: string
  unit: string
  price: number
  description: string
  is_available: boolean
  created_at: string
  updated_at: string
}

export type DeliveryArea = {
  id: number
  name: string
  pincode: string
  city: string
  is_active: boolean
  created_at: string
}

export type Enquiry = {
  id: number
  enquiry_number: string
  customer_name: string
  phone: string
  message: string
  product_interest: string
  delivery_area: string
  status: string
  source: string
  created_at: string
  updated_at: string
}

export type Complaint = {
  id: number
  complaint_number: string
  customer_name: string
  phone: string
  message: string
  category: string
  related_product: string
  status: string
  source: string
  created_at: string
  updated_at: string
}

export type Contact = {
  id: number
  phone: string
  name: string
  last_message: string
  created_at: string
}

export type Message = {
  role: string
  content: string
}

export type CompanyInfo = {
  name: string
  address: string
  phone: string
  whatsapp_number: string
  intro_message: string
  ai_enabled: boolean
}

export type User = {
  id: string
  name: string | null
  email: string
  role: "admin" | "user"
  is_active: boolean
  is_platform_admin: boolean
}

export type EnquiryHistoryEntry = {
  id: number
  field: string
  old_value: string
  new_value: string
  changed_by: string
  actor_role: string
  created_at: string
}

export type EnquiryHistoryPage = {
  total: number
  limit: number
  offset: number
  items: EnquiryHistoryEntry[]
}
