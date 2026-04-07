export interface ProductAttribute {
  name: string;
  value: string;
}

export interface ProductVariant {
  color: string;
  colorCode: string; // Hex code for UI display
  stock: number;
}

export interface Product {
  id: string;
  name: string;
  info: string;
  b2cPrice: number;
  compareAtPrice?: number; // MRP/Original price for B2C
  b2bPrice: number;
  compareAtB2bPrice?: number; // Original price for B2B
  stock: number; // Total stock (sum of variants)
  status: 'Active' | 'Draft' | 'Archived';
  image: string;
  category: string;
  colors?: string; // Store product colors
  brandName?: string; // Store product brand name
  attributes?: ProductAttribute[];
  variants?: ProductVariant[];
  rating?: number;
  reviews?: number;
  latestReview?: string;
  // B2C Offer fields
  b2cOfferPercentage?: number;
  b2cDiscount?: number; // New field for discount
  b2cOfferPrice?: number; // Calculated Offer Price
  b2cOfferStartDate?: string;
  b2cOfferEndDate?: string;
  // B2B Offer fields
  b2bOfferPercentage?: number;
  b2bDiscount?: number; // New field for discount
  b2bOfferPrice?: number; // Calculated Offer Price
  b2bOfferStartDate?: string;
  b2bOfferEndDate?: string;
  // Tax and Compliance
  sgst?: number; // SGST percentage
  cgst?: number; // CGST percentage
  hsn?: string; // HSN code
  returnPolicy?: string; // Return policy description
  // Dimensions (for shipping)
  height?: number; // in cm
  weight?: number; // in kg
  breadth?: number; // in cm
  length?: number; // in cm
  createdAt?: string;
}

export interface Brand {
  id: string;
  name: string;
  logo: string;
  productCount: number;
  status: 'Active' | 'Inactive';
}

export interface Order {
  id: string;
  customer: string;
  amount: number | string;
  type: 'B2B' | 'B2C';
  status: 'Delivered' | 'On the way' | 'Processing' | 'Confirmed' | 'Pending' | 'Cancelled' | 'Pickup';
  date: string;
  items?: number;
  payment?: string;
  email?: string;
  address?: string;
  sgst_percentage?: number;
  cgst_percentage?: number;
}

export interface Delivery {
  id: string;
  orderId: string;
  customerName: string;
  address: string;
  city: string;
  status: 'Ready to Ship' | 'Dispatched' | 'In Transit' | 'Out for Delivery' | 'Delivered' | 'Failed';
  partner: 'FedEx' | 'BlueDart' | 'Delhivery' | 'DHL' | 'DTDC' | 'Ecom Express';
  trackingId: string;
  estimatedDate: string;
  type: 'B2B' | 'B2C';
}

export interface LocalDelivery {
  id: string;
  orderId: string;
  customerName: string; // Can be Company or Person
  type: 'B2B' | 'B2C';
  pickupLocation: string;
  dropLocation: string; // Chennai specific
  vehicleType: 'Tata Ace' | 'Pickup 8ft' | '3 Wheeler' | '2 Wheeler';
  driverName: string;
  driverPhone: string;
  status: 'Searching' | 'Assigned' | 'On Route' | 'Delivered' | 'Cancelled';
  cost: number;
  date: string;
}

export interface Refund {
  id: string;
  orderId: string;
  customerName: string;
  amount: string;
  reason: 'Return' | 'Failed Delivery' | 'Damaged Item' | 'Wrong Item' | 'Order Cancelled';
  status: 'Pending' | 'Processed' | 'Rejected';
  requestDate: string;
  method: 'Original Source' | 'Wallet' | 'Bank Transfer';
  type: 'B2B' | 'B2C';
  imageUrl?: string;
}

export interface User {
  id: string;
  name: string;
  email: string;
  phone?: string;
  status: 'Active' | 'Inactive';
  joinDate: string;
  type: 'B2B' | 'B2C' | 'Admin' | 'Staff';
  permissions?: string[];
  address?: string;
  city?: string;
  state?: string;
  pincode?: string;
}

export interface B2BUser {
  id: string;
  companyName: string;
  contactName: string;
  email: string;
  status: 'Verified' | 'Pending';
  creditLimit: string;
}

export interface KYCRequest {
  id: string;
  companyName: string;
  email: string;
  documentType: 'GST Certificate' | 'PAN Card' | 'Incorporation Cert' | 'Shop Act License';
  documentNumber: string;
  submittedDate: string;
  status: 'Pending' | 'Approved' | 'Rejected';
  imageUrl: string;
}

export interface Category {
  id: string;
  name: string;
  type: 'Electronics' | 'Electrical';
  itemCount: number;
  subCategories?: Category[];
  description?: string;
}

export interface DashboardStats {
  totalRevenue: number;
  revenueGrowth: number;
  totalOrders: number;
  ordersGrowth: number;
  activeCustomers: number;
  customersGrowth: number;
}

export enum ViewState {
  DASHBOARD = 'DASHBOARD',
  PRODUCTS = 'PRODUCTS',
  ORDERS = 'ORDERS',
  ANALYTICS = 'ANALYTICS',
  SETTINGS = 'SETTINGS'
}

export interface SalesData {
  name: string;
  revenue: number;
  orders: number;
}

// --- PORTER SPECIFIC TYPES ---
export interface PorterRateRule {
  id: string;
  vehicleType: string;
  baseFare: number;
  perKmRate: number;
  minDistance: number;
  weightLimit: string;
}

export interface PorterZone {
  id: string;
  name: string;
  city: string;
  pincodes: string;
  status: 'Active' | 'Inactive';
}

export interface ActivityLog {
  id: string;
  user: string;
  role: string;
  action: string;
  details: string;
  timestamp: string;
  status: 'Success' | 'Failed' | 'Warning';
}

export interface SystemLog {
  id: string;
  timestamp: string;
  user: { name: string };
  action: string;
  module: string;
  status: 'SUCCESS' | 'FAILURE' | 'WARNING';
}