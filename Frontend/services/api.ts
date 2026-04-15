// export const API_BASE_URL = (import.meta as any).env.VITE_API_BASE_URL || "http://localhost:8001";
export const API_BASE_URL = import.meta.env.VITE_API_BASE_URL;
export interface LoginRequest {
  email: string;
  password: string;
}
export interface UserData {
  id: number;
  email: string;
  name: string | null;
  role: string;
  status: string;
  address?: string | null;
  city?: string | null;
  state?: string | null;
  pincode?: string | null;
  permissions?: string[] | null;
  created_at?: string;
  updated_at?: string;
  last_login?: string;
}

export interface LoginResponse {
  access_token: string;
  token_type: string;
  user: UserData;
}

export interface ApiError {
  detail: string;
}

class ApiService {
  private getAuthToken(): string | null {
    return localStorage.getItem("auth_token");
  }

  private async request<T>(endpoint: string, options: RequestInit = {}): Promise<T> {
    const token = this.getAuthToken();

    // Normalize base URL and endpoint to avoid double-slashes
    const base = API_BASE_URL.replace(/\/+$/g, "");
    const path = endpoint.startsWith("/") ? endpoint : `/${endpoint}`;
    const url = `${base}${path}`;

    const headers: HeadersInit = {
      "Content-Type": "application/json",
      ...options.headers,
    };

    if (token) {
      headers["Authorization"] = `Bearer ${token}`;
    }

    const response = await fetch(url, {
      ...options,
      headers,
    });

    const data = await response.json().catch(() => ({
      detail: "An error occurred",
    }));

    if (!response.ok) {

      // Handle 401 Global Logout
      if (response.status === 401) {
        localStorage.removeItem("auth_token");
        localStorage.removeItem("user");
        window.dispatchEvent(new Event('auth-error'));
      }

      const error: ApiError = data as ApiError;
      throw new Error(error.detail || `HTTP error: ${response.status} ${response.statusText}`);
    }

    return data;
  }

  /** 🔐 LOGIN */
  async login(credentials: LoginRequest): Promise<LoginResponse> {
    const response = await this.request<LoginResponse>("/api/v1/auth/login-json", {
      method: "POST",
      body: JSON.stringify(credentials),
    });

    localStorage.setItem("auth_token", response.access_token);
    localStorage.setItem("user", JSON.stringify(response.user));

    return response;
  }

  /** 👤 Current Auth User */
  async getCurrentUser(): Promise<UserData> {
    return this.request<UserData>("/api/v1/auth/me");
  }

  /** 👥 Get All Users */
  async getUsers(): Promise<UserData[]> {
    const employees = await this.request<UserData[]>("/api/v1/employees");
    const b2bUsers = await this.request<UserData[]>("/api/v1/users/b2b");
    const b2cUsers = await this.request<UserData[]>("/api/v1/users/b2c");

    const taggedEmployees = employees.map(e => ({ ...e, origin: 'employee' }));
    const taggedB2B = b2bUsers.map(u => ({ ...u, origin: 'b2b', role: 'b2b' }));
    const taggedB2C = b2cUsers.map(u => ({ ...u, origin: 'b2c', role: 'b2c' }));

    return [...taggedEmployees, ...taggedB2B, ...taggedB2C];
  }

  /** ➕ Create User */
  async createUser(userData: {
    name: string;
    email: string;
    password: string;
    role: string;
    status: string;
    address?: string;
    city?: string;
    state?: string;
    pincode?: string;
    permissions?: string[];
  }): Promise<UserData> {
    const isEmployee = userData.role === "admin" || userData.role === "staff";
    const endpoint = isEmployee
      ? "/api/v1/employees/create"
      : "/api/v1/auth/register";

    return this.request<UserData>(endpoint, {
      method: "POST",
      body: JSON.stringify(userData),
    });
  }

  /** 🗑️ Delete User */
  async deleteUser(id: string, type: string): Promise<void> {
    // ID comes as "Admin-1", we need just "1"
    const numericId = id.split('-')[1];
    return this.request<void>(`/api/v1/users/${numericId}?type=${type}`, {
      method: "DELETE",
    });
  }

  /** ✏️ Update User */
  async updateUser(id: string, type: string, userData: any): Promise<any> {
    const numericId = id.split('-')[1];
    return this.request<any>(`/api/v1/users/${numericId}?type=${type}`, {
      method: "PUT",
      body: JSON.stringify(userData),
    });
  }

  /** 🚪 Logout */
  logout(): void {
    localStorage.removeItem("auth_token");
    localStorage.removeItem("user");
  }

  /** 🔎 Check Auth State */
  isAuthenticated(): boolean {
    return !!this.getAuthToken();
  }

  // -------------- ADMIN PASSWORD RESET ----------------

  /** 🔑 Admin Reset User Password */
  async adminResetPassword(userId: number, newPassword: string): Promise<{
    message: string;
    user_id: number;
    email: string;
    password_updated: boolean;
  }> {
    return this.request("/api/v1/auth/admin/reset-password", {
      method: "POST",
      body: JSON.stringify({ user_id: userId, new_password: newPassword }),
    });
  }

  // -------------- USER PASSWORD RESET (OTP) ----------------

  /** 📧 Request OTP */
  async forgotPassword(email: string): Promise<{
    message: string;
    dev_otp?: string;
  }> {
    return this.request("/api/v1/auth/forgot-password", {
      method: "POST",
      body: JSON.stringify({ email }),
    });
  }

  /** 🔑 Reset Password with OTP */
  async resetPasswordWithOTP(email: string, otp: string, newPassword: string): Promise<{ message: string }> {
    return this.request("/api/v1/auth/reset-password-otp", {
      method: "POST",
      body: JSON.stringify({ email, otp, new_password: newPassword }),
    });
  }

  // -------------- PRODUCT APIs ----------------

  async fetchProducts(): Promise<any[]> {
    return this.request<any[]>("/api/v1/products");
  }

  async createProduct(productData: any): Promise<any> {
    return this.request<any>("/api/v1/products", {
      method: "POST",
      body: JSON.stringify(productData),
    });
  }

  async updateProduct(id: string, productData: any): Promise<any> {
    return this.request<any>(`/api/v1/products/${id}`, {
      method: "PUT",
      body: JSON.stringify(productData),
    });
  }

  async deleteProduct(id: string): Promise<void> {
    return this.request<void>(`/api/v1/products/${id}`, {
      method: "DELETE",
    });
  }

  /** 📦 Import Products from Excel */
  async importProducts(file: File): Promise<{
    status: string;
    message: string;
    details: {
      success: number;
      created: number;
      updated: number;
      failed: number;
      errors: string[];
    };
  }> {
    const token = this.getAuthToken();
    const formData = new FormData();
    formData.append("file", file);

    const base = API_BASE_URL.replace(/\/+$/g, "");
    const url = `${base}/api/v1/products/import`;

    const response = await fetch(url, {
      method: "POST",
      headers: {
        ...(token ? { Authorization: `Bearer ${token}` } : {}),
      },
      body: formData,
    });

    const data = await response.json().catch(() => ({
      detail: "An error occurred during import",
    }));

    if (!response.ok) {
      throw new Error(data.detail || `Import failed: ${response.status}`);
    }

    return data;
  }

  // -------------- ORDER APIs ----------------

  async fetchOrders(): Promise<any[]> {
    return this.request<any[]>("/api/v1/orders");
  }

  async updateOrderStatus(orderId: string, status: string): Promise<any> {
    return this.request<any>(`/api/v1/orders/${orderId}/status`, {
      method: "PUT",
      body: JSON.stringify({ status }),
    });
  }

  async updateOrderDimensions(orderId: string, dimensions: { height: number, weight: number, breadth: number, length: number }): Promise<any> {
    return this.request<any>(`/api/v1/orders/${orderId}/dimensions`, {
      method: "PUT",
      body: JSON.stringify(dimensions),
    });
  }

  async fetchDeliveries(): Promise<any[]> {
    return this.request<any[]>("/api/v1/orders/deliveries");
  }

  /**
   * Schedule pickup with Delhivery API
   * This calls the Delhivery pickup request API and updates the database
   */
  async schedulePickup(orderId: string, pickupDatetime: string): Promise<any> {
    if (!orderId) throw new Error("Order ID is required");
    if (!pickupDatetime) throw new Error("Pickup datetime is required");

    return this.request<any>(`/api/v1/delivery/schedule-pickup/${orderId}`, {
      method: "POST",
      body: JSON.stringify({ pickup_datetime: pickupDatetime }),
    });
  }

  /**
   * @deprecated Use schedulePickup instead - this only updates DB, doesn't call Delhivery
   */
  async updateDeliverySchedule(deliveryId: number, schedulePickup: string): Promise<any> {
    // Ensure deliveryId is a number
    if (!deliveryId) throw new Error("Delivery ID is required");

    return this.request<any>(`/api/v1/orders/deliveries/${deliveryId}/schedule`, {
      method: "PUT",
      body: JSON.stringify({ schedule_pickup: schedulePickup }),
    });
  }

  // -------------- REFUND APIs ----------------

  async fetchRefunds(status?: string): Promise<any[]> {
    const endpoint = status ? `/api/v1/refunds?status=${status}` : "/api/v1/refunds";
    return this.request<any[]>(endpoint);
  }

  async getRefund(refundId: number): Promise<any> {
    return this.request<any>(`/api/v1/refunds/${refundId}`);
  }

  async createRefund(refundData: {
    order_id: number;
    reason: string;
    amount: number;
    proof_image_path?: string;
  }): Promise<any> {
    return this.request<any>("/api/v1/refunds", {
      method: "POST",
      body: JSON.stringify(refundData),
    });
  }

  async updateRefundStatus(refundId: number, status: string): Promise<any> {
    return this.request<any>(`/api/v1/refunds/${refundId}/status`, {
      method: "PUT",
      body: JSON.stringify({ status }),
    });
  }

  async rejectRefund(refundId: number, rejectionReason: string, adminNotes?: string): Promise<any> {
    return this.request<any>(`/api/v1/refunds/${refundId}/reject`, {
      method: "POST",
      body: JSON.stringify({ rejection_reason: rejectionReason, admin_notes: adminNotes }),
    });
  }

  async updateRefundAWB(refundId: number, awbData: {
    return_awb_number: string;
    return_label_path: string;
  }): Promise<any> {
    return this.request<any>(`/api/v1/refunds/${refundId}/awb`, {
      method: "PUT",
      body: JSON.stringify(awbData),
    });
  }

  async deleteRefund(refundId: number): Promise<void> {
    return this.request<void>(`/api/v1/refunds/${refundId}`, {
      method: "DELETE",
    });
  }

  // -------------- EXCHANGE APIs ----------------

  async fetchExchanges(status?: string): Promise<any[]> {
    const endpoint = status ? `/api/v1/exchanges?status=${status}` : "/api/v1/exchanges";
    return this.request<any[]>(endpoint);
  }

  async approveExchange(exchangeId: number): Promise<any> {
    return this.request<any>(`/api/v1/exchanges/${exchangeId}/approve`, {
      method: "POST",
    });
  }

  async qualityCheckExchange(exchangeId: number, approved: boolean, notes: string): Promise<any> {
    return this.request<any>(`/api/v1/exchanges/${exchangeId}/quality-check`, {
      method: "POST",
      body: JSON.stringify({ approved, notes }),
    });
  }

  async processExchangeReplacement(exchangeId: number): Promise<any> {
    return this.request<any>(`/api/v1/exchanges/${exchangeId}/process-replacement`, {
      method: "POST",
    });
  }

  async refundExchange(exchangeId: number): Promise<any> {
    return this.request<any>(`/api/v1/exchanges/${exchangeId}/refund`, {
      method: "POST",
    });
  }

  async rejectExchange(exchangeId: number, rejectionReason: string): Promise<any> {
    return this.request<any>(`/api/v1/exchanges/${exchangeId}/reject`, {
      method: "POST",
      body: JSON.stringify({ rejection_reason: rejectionReason }),
    });
  }


  // -------------- BULK AWB DOWNLOAD ----------------

  async bulkDownloadAWBLabels(orderIds: string[]): Promise<Blob> {
    const token = this.getAuthToken();
    const base = API_BASE_URL.replace(/\/+$/g, "");
    const url = `${base}/api/v1/orders/bulk-download-awb`;

    const response = await fetch(url, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        ...(token ? { Authorization: `Bearer ${token}` } : {}),
      },
      body: JSON.stringify(orderIds),
    });

    if (!response.ok) {
      const error = await response.json().catch(() => ({ detail: "Download failed" }));
      throw new Error(error.detail || `Download failed: ${response.status}`);
    }

    return response.blob();
  }

  async bulkDownloadInvoiceLabels(orderIds: string[]): Promise<Blob> {
    const token = this.getAuthToken();
    const base = API_BASE_URL.replace(/\/+$/g, "");
    const url = `${base}/api/v1/orders/bulk-download-invoice`;

    const response = await fetch(url, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        ...(token ? { Authorization: `Bearer ${token}` } : {}),
      },
      body: JSON.stringify(orderIds),
    });

    if (!response.ok) {
      const error = await response.json().catch(() => ({ detail: "Download failed" }));
      throw new Error(error.detail || `Download failed: ${response.status}`);
    }

    return response.blob();
  }

  // -------------- ACTIVITY LOGS APIs ----------------

  async getActivityLogs(params?: {
    skip?: number;
    limit?: number;
    user_type?: string;
    module?: string;
    status?: string;
    search?: string;
    start_date?: string;
    end_date?: string;
  }): Promise<any[]> {
    const queryParams = new URLSearchParams();
    if (params) {
      Object.entries(params).forEach(([key, value]) => {
        if (value !== undefined && value !== null) {
          queryParams.append(key, String(value));
        }
      });
    }
    const endpoint = `/api/v1/activity-logs${queryParams.toString() ? `?${queryParams.toString()}` : ''}`;
    return this.request<any[]>(endpoint);
  }

  async getActivityLogStats(days: number = 7): Promise<any> {
    return this.request<any>(`/api/v1/activity-logs/stats?days=${days}`);
  }

  async exportActivityLogs(params?: {
    user_type?: string;
    module?: string;
    status?: string;
    search?: string;
    start_date?: string;
    end_date?: string;
  }): Promise<Blob> {
    const token = this.getAuthToken();
    const queryParams = new URLSearchParams();
    if (params) {
      Object.entries(params).forEach(([key, value]) => {
        if (value !== undefined && value !== null) {
          queryParams.append(key, String(value));
        }
      });
    }

    const base = API_BASE_URL.replace(/\/+$/g, "");
    const url = `${base}/api/v1/activity-logs/export${queryParams.toString() ? `?${queryParams.toString()}` : ''}`;

    const response = await fetch(url, {
      method: "GET",
      headers: {
        ...(token ? { Authorization: `Bearer ${token}` } : {}),
      },
    });

    if (!response.ok) {
      const error = await response.json().catch(() => ({ detail: "Export failed" }));
      throw new Error(error.detail || `Export failed: ${response.status}`);
    }

    return response.blob();
  }

  /* =======================
      CMS
  ======================= */

  async getCMSBanners(): Promise<any[]> {
    return this.request("/api/v1/cms/banners");
  }

  async createCMSBanner(data: any): Promise<any> {
    return this.request("/api/v1/cms/banners", {
      method: "POST",
      body: JSON.stringify(data),
    });
  }

  async updateCMSBanner(id: number, data: any): Promise<any> {
    return this.request(`/api/v1/cms/banners/${id}`, {
      method: "PUT",
      body: JSON.stringify(data),
    });
  }

  async deleteCMSBanner(id: number): Promise<any> {
    return this.request(`/api/v1/cms/banners/${id}`, {
      method: "DELETE",
    });
  }

  async getCMSCategoryBanners(): Promise<any> {
    return this.request("/api/v1/cms/category-banners");
  }

  async updateCMSCategoryBanner(
    category: string,
    data: { image: string }
  ): Promise<any> {
    return this.request(`/api/v1/cms/category-banners/${category}`, {
      method: "PUT",
      body: JSON.stringify(data),
      headers: { "Content-Type": "application/json" },
    });
  }

  async getCMSNotifications(): Promise<any[]> {
    return this.request("/api/v1/cms/notifications");
  }

  async sendCMSNotification(data: any): Promise<any> {
    return this.request("/api/v1/cms/notifications", {
      method: "POST",
      body: JSON.stringify(data),
    });
  }


  async getAppNotifications(): Promise<any[]> {
    return this.request("/api/v1/cms/app-notifications");
  }

  async createAppNotification(data: any): Promise<any> {
    return this.request("/api/v1/cms/app-notifications", {
      method: "POST",
      body: JSON.stringify(data),
    });
  }


  async getCMSPages(): Promise<any[]> {
    return this.request("/api/v1/cms/pages");
  }

  async updateCMSPage(id: number, data: any): Promise<any> {
    return this.request(`/api/v1/cms/pages/${id}`, {
      method: "PUT",
      body: JSON.stringify(data),
    });
  }

  /* =======================
      REPORTS (NEW)
  ======================= */

  async getSalesInventory(): Promise<any[]> {
    return this.request("/api/v1/reports/sales-inventory");
  }

  async getSalesDetails(): Promise<any[]> {
    return this.request("/api/v1/reports/sales-details");
  }

  /* =======================
      CAMPAIGNS
  ======================= */

  async getCampaignCoupons(): Promise<any[]> {
    return this.request("/api/v1/campaigns/coupons");
  }

  async createCampaignCoupon(data: {
    code: string;
    type: string;
    value: string;
    target: string;
    expiry?: string;
  }): Promise<any> {
    return this.request("/api/v1/campaigns/coupons", {
      method: "POST",
      body: JSON.stringify(data),
    });
  }

  async updateCampaignCoupon(
    id: number,
    data: {
      code: string;
      type: string;
      value: string;
      target: string;
      expiry?: string;
    }
  ): Promise<any> {
    return this.request(`/api/v1/campaigns/coupons/${id}`, {
      method: "PUT",
      body: JSON.stringify(data),
    });
  }

  async deleteCampaignCoupon(id: number): Promise<any> {
    return this.request(`/api/v1/campaigns/coupons/${id}`, {
      method: "DELETE",
    });
  }

  async getCampaignFlashDeals(): Promise<any[]> {
    return this.request("/api/v1/campaigns/flash-deals");
  }

  async getCampaignBanners(): Promise<any[]> {
    return this.request("/api/v1/campaigns/banners");
  }

  async getCampaignAdCampaigns(): Promise<any[]> {
    return this.request("/api/v1/campaigns/ad-campaigns");
  }

  /* =======================
      B2B
  ======================= */

  async getB2BUsers(): Promise<any[]> {
    return this.request("/api/v1/b2b/users");
  }

  async updateB2BStatus(id: number, data: { status: string }): Promise<any> {
    return this.request(`/api/v1/b2b/verify/${id}`, {
      method: "PUT",
      body: JSON.stringify(data),
    });
  }

  /* =======================
      FINANCE & PAYMENTS
  ======================= */

  async getTransactions(): Promise<any[]> {
    return this.request("/api/v1/finance/transactions");
  }

  async verifyPayment(paymentData: any): Promise<any> {
    return this.request("/api/v1/finance/verify-payment", {
      method: "POST",
      body: JSON.stringify(paymentData),
    });
  }

  /* =======================
      REVIEWS
  ======================= */

  async fetchReviews(productId: string): Promise<any[]> {
    return this.request<any[]>(`/api/v1/reviews/product/${productId}`);
  }

  async createReview(reviewData: any): Promise<any> {
    return this.request<any>("/api/v1/reviews", {
      method: "POST",
      body: JSON.stringify(reviewData),
    });
  }

  async deleteReview(reviewId: string): Promise<void> {
    return this.request<void>(`/api/v1/reviews/${reviewId}`, {
      method: "DELETE",
    });
  }
  async generateInvoiceLabel(orderId: string): Promise<{ url: string }> {
    return this.request<{ url: string }>(`/api/v1/orders/${orderId}/generate-invoice-label`, {
      method: "POST",
    });
  }

  async downloadAWBLabel(orderId: string): Promise<Blob> {
    const token = this.getAuthToken();
    const base = API_BASE_URL.replace(/\/+$/g, "");
    const url = `${base}/api/v1/orders/${orderId}/awb/download`;

    const response = await fetch(url, {
      method: "GET",
      headers: {
        ...(token ? { Authorization: `Bearer ${token}` } : {}),
      },
    });

    if (!response.ok) {
      const errorText = await response.text();
      let errorMessage = `Failed to download: ${response.status}`;
      try {
        const errorData = JSON.parse(errorText);
        errorMessage = errorData.detail || errorData.message || errorMessage;
      } catch (e) {
        // Not JSON
      }
      throw new Error(errorMessage);
    }

    return response.blob();
  }
}


export const apiService = new ApiService();

/* =======================
   HELPER EXPORTS
======================= */

// Products
export const fetchProducts = () => apiService.fetchProducts();
export const createProduct = (productData: any) => apiService.createProduct(productData);
export const updateProduct = (id: string, productData: any) => apiService.updateProduct(id, productData);
export const deleteProduct = (id: string) => apiService.deleteProduct(id);
export const importProducts = (file: File) => apiService.importProducts(file);

// Orders
export const updateOrderStatus = (orderId: string, status: string) => apiService.updateOrderStatus(orderId, status);

// CMS
export const getCMSBanners = () => apiService.getCMSBanners();
export const createCMSBanner = (d: any) => apiService.createCMSBanner(d);
export const updateCMSBanner = (id: number, d: any) => apiService.updateCMSBanner(id, d);
export const deleteCMSBanner = (id: number) => apiService.deleteCMSBanner(id);
export const getCMSCategoryBanners = () => apiService.getCMSCategoryBanners();
export const updateCMSCategoryBanner = (category: string, data: { image: string }) => apiService.updateCMSCategoryBanner(category, data);
export const getCMSNotifications = () => apiService.getCMSNotifications();
export const sendCMSNotification = (d: any) => apiService.sendCMSNotification(d);
export const getAppNotifications = () => apiService.getAppNotifications();
export const createAppNotification = (d: any) => apiService.createAppNotification(d);

export const getCMSPages = () => apiService.getCMSPages();
export const updateCMSPage = (id: number, d: any) => apiService.updateCMSPage(id, d);

// CAMPAIGNS
export const getCampaignCoupons = () => apiService.getCampaignCoupons();
export const createCampaignCoupon = (d: any) => apiService.createCampaignCoupon(d);
export const updateCampaignCoupon = (id: number, d: any) => apiService.updateCampaignCoupon(id, d);
export const deleteCampaignCoupon = (id: number) => apiService.deleteCampaignCoupon(id);
export const getCampaignFlashDeals = () => apiService.getCampaignFlashDeals();
export const getCampaignBanners = () => apiService.getCampaignBanners();
export const getCampaignAdCampaigns = () => apiService.getCampaignAdCampaigns();

// B2B
export const getB2BUsers = () => apiService.getB2BUsers();
export const updateB2BStatus = (id: number, d: { status: string }) => apiService.updateB2BStatus(id, d);

// FINANCE & PAYMENTS
export const getTransactions = () => apiService.getTransactions();
export const verifyPayment = (d: any) => apiService.verifyPayment(d);

// REVIEWS
export const fetchReviews = (productId: string) => apiService.fetchReviews(productId);
export const createReview = (reviewData: any) => apiService.createReview(reviewData);
export const deleteReview = (reviewId: string) => apiService.deleteReview(reviewId);
