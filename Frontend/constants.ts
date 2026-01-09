
import { Order, Product, SalesData, User, B2BUser, Delivery, LocalDelivery, Refund, Category, PorterRateRule, PorterZone, KYCRequest, ActivityLog, SystemLog, ProductVariant } from "./types";


export const MOCK_BRANDS: Brand[] = [
  { id: 'br_1', name: 'Samsung', logo: 'https://cdn.wallpapersafari.com/76/68/7F8uTy.jpg', productCount: 120, status: 'Active' },
  { id: 'br_2', name: 'Apple', logo: 'https://storage.googleapis.com/webdesignledger.pub.network/WDL/maxresdefault.jpg', productCount: 85, status: 'Active' },
  { id: 'br_3', name: 'Sony', logo: 'https://th.bing.com/th/id/OIP.CcCcAj6-wMdaqcRT3v6EIwHaHa?o=7rm=3&rs=1&pid=ImgDetMain&o=7&rm=3', productCount: 90, status: 'Active' },
  { id: 'br_4', name: 'LG', logo: 'https://logos-world.net/wp-content/uploads/2020/05/LG-Symbol.png', productCount: 65, status: 'Active' },
  { id: 'br_5', name: 'Dell', logo: 'https://logos-world.net/wp-content/uploads/2020/08/Dell-Emblem.jpg', productCount: 45, status: 'Active' },
  { id: 'br_6', name: 'HP', logo: 'https://static.vecteezy.com/system/resources/previews/022/101/041/original/hp-logo-transparent-free-png.png', productCount: 50, status: 'Active' },
  { id: 'br_7', name: 'Havells', logo: 'https://vectorseek.com/wp-content/uploads/2021/12/Havells-Logo-Vector-01-730x730.jpg', productCount: 200, status: 'Active' },
  { id: 'br_8', name: 'Philips', logo: 'https://tse2.mm.bing.net/th/id/OIP.isnY6lNbKgGdax0zB0oG5QHaHa?rs=1&pid=ImgDetMain&o=7&rm=3', productCount: 150, status: 'Active' },
];


export const MOCK_PRODUCTS: Product[] = [
  {
    id: 'prod_1',
    name: 'Ultra HD 4K Smart TV 55"',
    description: 'Crystal clear display with built-in smart streaming apps.',
    b2cPrice: 45000.00,
    compareAtPrice: 52000.00,
    b2bPrice: 38500.00,
    compareAtB2bPrice: 42000.00,
    stock: 25,
    status: 'Active',
    category: 'Home Appliances',

    brand: 'Samsung',


    rating: 4.5,
    reviews: 128,
    attributes: [
      { name: 'Screen Size', value: '55 inch' },
      { name: 'Resolution', value: '4K Ultra HD' },
      { name: 'Refresh Rate', value: '60Hz' }
    ],
    variants: [
      { color: 'Black', colorCode: '#000000', stock: 20 },
      { color: 'Silver', colorCode: '#C0C0C0', stock: 5 }
    ],
    image: 'https://goldpaintphotography.com/wp-content/uploads/2015/12/LG-55EF9500-OLED-4K-Smart-TV_Screenshot_Slideshow.jpg'
  },
  {
    id: 'prod_2',
    name: 'Noise Cancelling Wireless Earbuds',
    description: 'Active noise cancellation with 30-hour battery life.',
    b2cPrice: 4999.00,
    compareAtPrice: 6999.00,
    b2bPrice: 3800.00,
    compareAtB2bPrice: 4500.00,
    stock: 150,
    status: 'Active',
    category: 'Audio',


    brand: 'Sony',



    rating: 4.8,
    reviews: 345,
    attributes: [
      { name: 'Battery Life', value: '30 Hours' },
      { name: 'Connectivity', value: 'Bluetooth 5.2' },
      { name: 'Water Resistance', value: 'IPX4' }
    ],
    variants: [
      { color: 'Matte Black', colorCode: '#1a1a1a', stock: 100 },
      { color: 'White', colorCode: '#ffffff', stock: 30 },
      { color: 'Blue', colorCode: '#0000FF', stock: 20 }
    ],
    image: 'https://pisces.bbystatic.com/image2/BestBuy_US/images/products/6501/6501045_sd.jpg'
  },
  {
    id: 'prod_3',
    name: 'Gaming Laptop Ryzen 7',
    description: 'High-performance gaming laptop with RTX 3060 graphics.',
    b2cPrice: 89999.00,
    compareAtPrice: 95000.00,
    b2bPrice: 82000.00,
    compareAtB2bPrice: 88000.00,
    stock: 10,
    status: 'Active',
    category: 'Computers',

    brand: 'Dell',



    rating: 4.2,
    reviews: 56,
    attributes: [
      { name: 'Processor', value: 'AMD Ryzen 7 5800H' },
      { name: 'RAM', value: '16GB DDR4' },
      { name: 'Storage', value: '512GB SSD' },
      { name: 'GPU', value: 'NVIDIA RTX 3060' }
    ],
    variants: [
      { color: 'Dark Grey', colorCode: '#444444', stock: 10 }
    ],
    image: 'https://robots.net/wp-content/uploads/2023/12/what-is-a-gaming-laptop-1701754858.jpg'
  },
  {
    id: 'prod_4',
    name: 'Smart Home Security Camera',
    description: '1080p WiFi camera with night vision and motion detection.',
    b2cPrice: 2499.00,
    compareAtPrice: 3200.00,
    b2bPrice: 1900.00,
    compareAtB2bPrice: 2200.00,
    stock: 0,
    status: 'Draft',
    category: 'Smart Home',

    brand: 'Philips',


    rating: 3.9,
    reviews: 22,
    attributes: [
      { name: 'Resolution', value: '1080p' },
      { name: 'Field of View', value: '130 degrees' },
      { name: 'Power', value: 'Wired' }
    ],
    variants: [
      { color: 'White', colorCode: '#ffffff', stock: 0 }
    ],
    image: 'https://tse4.mm.bing.net/th/id/OIP.Z7gEP2Jt6UEIL6PiXSvoLwHaEK?rs=1&pid=ImgDetMain&o=7&rm=3'
  },
  {
    id: 'prod_5',
    name: '5G Smartphone 256GB',
    description: 'Flagship processor with pro-grade camera system.',
    b2cPrice: 64999.00,
    compareAtPrice: 70000.00,
    b2bPrice: 59500.00,
    compareAtB2bPrice: 62000.00,
    stock: 45,
    status: 'Active',
    category: 'Mobile',

    brand: 'Samsung',


    rating: 4.7,
    reviews: 890,
    attributes: [
      { name: 'RAM', value: '8GB' },
      { name: 'Storage', value: '256GB' },
      { name: 'Battery', value: '5000mAh' }
    ],
    variants: [
      { color: 'Phantom Black', colorCode: '#111111', stock: 20 },
      { color: 'Green', colorCode: '#225522', stock: 15 },
      { color: 'Lavender', colorCode: '#E6E6FA', stock: 10 }
    ],
    image: 'https://picsum.photos/200/200?random=14'
  },
  {
    id: 'prod_6',
    name: 'Mechanical Keyboard RGB',
    description: 'Blue switches with customizable RGB backlighting.',
    b2cPrice: 3499.00,
    compareAtPrice: 4500.00,
    b2bPrice: 2800.00,
    compareAtB2bPrice: 3200.00,
    stock: 80,
    status: 'Active',
    category: 'Accessories',

    brand: 'HP',


    rating: 4.4,
    reviews: 67,
    attributes: [
      { name: 'Switch Type', value: 'Blue Mechanical' },
      { name: 'Backlight', value: 'RGB' },
      { name: 'Interface', value: 'USB-C' }
    ],
    variants: [
      { color: 'Black', colorCode: '#000000', stock: 50 },
      { color: 'White', colorCode: '#ffffff', stock: 30 }
    ],
    image: 'https://picsum.photos/200/200?random=15'
  }
];

// Generate 5000+ Mock Products with Variants
const CATEGORIES = ['Computers', 'Mobile', 'Audio', 'Home Appliances', 'Smart Home', 'Accessories', 'Cameras', 'Wearables'];
const BRANDS = ['Samsung', 'Apple', 'Sony', 'LG', 'Dell', 'HP', 'Havells', 'Philips'];
const STATUSES = ['Active', 'Draft', 'Archived'];
const COLORS = [
  { name: 'Black', code: '#000000' },
  { name: 'White', code: '#ffffff' },
  { name: 'Silver', code: '#C0C0C0' },
  { name: 'Blue', code: '#0000FF' },
  { name: 'Red', code: '#FF0000' },
  { name: 'Gold', code: '#FFD700' }
];

// for (let i = 1; i <= 5200; i++) {
//   const category = CATEGORIES[Math.floor(Math.random() * CATEGORIES.length)];
//   const brand = BRANDS[Math.floor(Math.random() * BRANDS.length)];
//   const b2cPrice = Math.floor(Math.random() * 50000) + 500;
//   const compareAtPrice = Math.floor(b2cPrice * (1 + Math.random() * 0.3)); // 0-30% markup for MRP
//   const b2bPrice = Math.floor(b2cPrice * 0.85); // 15% discount roughly
//   const compareAtB2bPrice = Math.floor(b2bPrice * (1 + Math.random() * 0.25)); // markup on bulk

//   // Generate random variants
//   const numVariants = Math.floor(Math.random() * 3) + 1; // 1 to 3 variants
//   const variants: ProductVariant[] = [];
//   let totalStock = 0;

//   for(let j=0; j < numVariants; j++) {
//       const color = COLORS[Math.floor(Math.random() * COLORS.length)];
//       const stock = Math.floor(Math.random() * 200);
//       variants.push({
//           color: color.name,
//           colorCode: color.code,
//           stock: stock
//       });
//       totalStock += stock;
//   }

//   MOCK_PRODUCTS.push({
//     id: `prod_gen_${i}`,
//     name: `${category} Series ${String.fromCharCode(65 + (i % 26))} - Model ${i + 100}`,
//     description: `High quality ${category.toLowerCase()} component for professional and personal use. Batch #${Math.floor(i / 100)}.`,
//     b2cPrice: b2cPrice,
//     compareAtPrice: compareAtPrice,
//     b2bPrice: b2bPrice,
//     compareAtB2bPrice: compareAtB2bPrice,
//     stock: totalStock,
//     status: STATUSES[Math.floor(Math.random() * STATUSES.length)] as any,
//     category: category,
//     brand: brand,
//     rating: Number((Math.random() * 2 + 3).toFixed(1)), // Rating between 3.0 and 5.0
//     reviews: Math.floor(Math.random() * 500),
//     attributes: [
//       { name: 'Origin', value: 'Imported' },
//       { name: 'Warranty', value: '1 Year' }
//     ],
//     variants: variants,
//     image: `https://picsum.photos/200/200?random=${(i % 50) + 20}`
//   });
// }

export const MOCK_ORDERS: Order[] = [
  { id: 'ORD-7001', customer: 'TechCorp Solutions', date: 'May 14, 2024', amount: 4500.00, items: 12, status: 'Processing', payment: 'Paid', type: 'B2B', email: 'accounts@techcorp.com', address: 'Tech Park, Sector 4, Bangalore' },
  { id: 'ORD-7002', customer: 'Alice Freeman', date: 'May 13, 2024', amount: 129.99, items: 1, status: 'On the way', payment: 'Paid', type: 'B2C', email: 'alice.f@gmail.com', address: '123 Maple Drive, Mumbai' },
  { id: 'ORD-7003', customer: 'John Doe', date: 'May 12, 2024', amount: 45.50, items: 2, status: 'Delivered', payment: 'Paid', type: 'B2C', email: 'john.d@yahoo.com', address: '45 Park Avenue, Delhi' },
  { id: 'ORD-7004', customer: 'Global Logistics', date: 'May 11, 2024', amount: 1200.50, items: 5, status: 'Pending', payment: 'Unpaid', type: 'B2B', email: 'logistics@global.com', address: 'Warehouse 9, Chennai Port' },
  { id: 'ORD-7005', customer: 'Sarah Jenkins', date: 'May 10, 2024', amount: 899.00, items: 1, status: 'Cancelled', payment: 'Refunded', type: 'B2C', email: 'sarah.j@outlook.com', address: '78 Hilltop View, Pune' },
  { id: 'ORD-7006', customer: 'Wayne Enterprises', date: 'May 14, 2024', amount: 25000.00, items: 50, status: 'Confirmed', payment: 'Paid', type: 'B2B', email: 'procurement@wayne.com', address: 'Gotham Tower, Mumbai' },
  { id: 'ORD-7007', customer: 'Peter Parker', date: 'May 14, 2024', amount: 25.00, items: 1, status: 'Pickup', payment: 'Paid', type: 'B2C', email: 'p.parker@dailybugle.com', address: '20 Ingram St, Queens' },
  { id: 'ORD-7008', customer: 'Stark Ind', date: 'May 14, 2024', amount: 9999.00, items: 10, status: 'On the way', payment: 'Paid', type: 'B2B', email: 'tony@stark.com', address: 'Malibu Point, Goa' },
  { id: 'ORD-7009', customer: 'Bruce Banner', date: 'April 20, 2024', amount: 150.00, items: 3, status: 'Delivered', payment: 'Paid', type: 'B2C', email: 'bruce@hulk.com', address: 'Green St, Dayton' },
  { id: 'ORD-7010', customer: 'Clark Kent', date: 'January 15, 2023', amount: 55.00, items: 1, status: 'Delivered', payment: 'Paid', type: 'B2C', email: 'ck@dailyplanet.com', address: 'Metropolis' },
];

export const MOCK_SALES_DATA: SalesData[] = [
  { name: 'Jan', revenue: 4000, orders: 240 },
  { name: 'Feb', revenue: 3000, orders: 139 },
  { name: 'Mar', revenue: 2000, orders: 980 },
  { name: 'Apr', revenue: 2780, orders: 390 },
  { name: 'May', revenue: 1890, orders: 480 },
  { name: 'Jun', revenue: 2390, orders: 380 },
  { name: 'Jul', revenue: 3490, orders: 430 },
];

export const MOCK_USERS: User[] = [
  // B2B Users
  {
    id: 'u1',
    name: 'Tech Corp Ltd',
    email: 'contact@techcorp.com',
    status: 'Active',
    joinDate: '2024-01-15',
    type: 'B2B',
    address: '123 Tech Park, Sector 5',
    city: 'Bangalore',
    state: 'Karnataka',
    pincode: '560100'
  },
  {
    id: 'u2',
    name: 'Global Trade Inc',
    email: 'info@globaltrade.com',
    status: 'Active',
    joinDate: '2024-02-20',
    type: 'B2B',
    address: 'Plot 45, Industrial Area',
    city: 'Mumbai',
    state: 'Maharashtra',
    pincode: '400093'
  },
  {
    id: 'u3',
    name: 'Enterprise Solutions',
    email: 'admin@enterprise.com',
    status: 'Inactive',
    joinDate: '2023-12-10',
    type: 'B2B',
    address: '789 Business Bay',
    city: 'Chennai',
    state: 'Tamil Nadu',
    pincode: '600032'
  },
  // B2C Users
  {
    id: 'c1',
    name: 'John Doe',
    email: 'john.doe@gmail.com',
    status: 'Active',
    joinDate: '2024-03-01',
    type: 'B2C',
    address: 'Flat 4B, Green Heights',
    city: 'Pune',
    state: 'Maharashtra',
    pincode: '411057'
  },
  {
    id: 'c2',
    name: 'Sarah Connor',
    email: 'sarah.c@yahoo.com',
    status: 'Active',
    joinDate: '2024-03-05',
    type: 'B2C',
    address: '12 Main Street, Civil Lines',
    city: 'Delhi',
    state: 'Delhi',
    pincode: '110054'
  },
  {
    id: 'c3',
    name: 'Mike Ross',
    email: 'mike.ross@outlook.com',
    status: 'Inactive',
    joinDate: '2024-01-20',
    type: 'B2C',
    address: '56 Palm Avenue',
    city: 'Goa',
    state: 'Goa',
    pincode: '403001'
  },
  // Admin Users
  {
    id: 'a1',
    name: 'Super Admin',
    email: 'admin@ecommerce.com',
    status: 'Active',
    joinDate: '2023-01-01',
    type: 'Admin'
  },
  {
    id: 'a2',
    name: 'System Manager',
    email: 'manager@ecommerce.com',
    status: 'Active',
    joinDate: '2023-06-15',
    type: 'Admin'
  },
  // Staff Users
  {
    id: 's1',
    name: 'Alice Support',
    email: 'alice@ecommerce.com',
    status: 'Active',
    joinDate: '2023-11-01',
    type: 'Staff',
    permissions: ['Orders', 'Refunds', 'Users']
  },
  {
    id: 's2',
    name: 'Bob Logistics',
    email: 'bob@ecommerce.com',
    status: 'Active',
    joinDate: '2023-11-05',
    type: 'Staff',
    permissions: ['Orders', 'Delivery', 'Porter']
  },
];

export const MOCK_B2B_PROFILE_USERS: B2BUser[] = [
  {
    id: '1',
    companyName: 'Tech Solutions Ltd',
    contactName: 'John Doe',
    email: 'john@tech.com',
    status: 'Verified',
    creditLimit: '₹5,00,000'
  },
  {
    id: '2',
    companyName: 'Global Imports Inc',
    contactName: 'Jane Smith',
    email: 'jane@global.com',
    status: 'Pending',
    creditLimit: 'Pending'
  },
  {
    id: '3',
    companyName: 'Business Traders',
    contactName: 'Mike Johnson',
    email: 'mike@traders.com',
    status: 'Verified',
    creditLimit: '₹3,50,000'
  },
];

export const MOCK_KYC_REQUESTS: KYCRequest[] = [
  {
    id: 'kyc_01',
    companyName: 'Global Imports Inc',
    email: 'jane@global.com',
    documentType: 'GST Certificate',
    documentNumber: '29ABCDE1234F1Z5',
    submittedDate: '2024-03-20',
    status: 'Pending',
    imageUrl: 'https://picsum.photos/id/10/800/600' // Placeholder for doc
  },
  {
    id: 'kyc_02',
    companyName: 'Global Imports Inc',
    email: 'jane@global.com',
    documentType: 'PAN Card',
    documentNumber: 'ABCDE1234F',
    submittedDate: '2024-03-20',
    status: 'Pending',
    imageUrl: 'https://picsum.photos/id/20/800/600' // Placeholder for doc
  },
  {
    id: 'kyc_03',
    companyName: 'NextGen Electronics',
    email: 'admin@nextgen.com',
    documentType: 'Incorporation Cert',
    documentNumber: 'U12345KA2024PTC123456',
    submittedDate: '2024-03-21',
    status: 'Pending',
    imageUrl: 'https://picsum.photos/id/30/800/600' // Placeholder for doc
  },
  {
    id: 'kyc_04',
    companyName: 'City Retailers',
    email: 'store@cityretail.com',
    documentType: 'Shop Act License',
    documentNumber: 'SH-889922-L',
    submittedDate: '2024-03-18',
    status: 'Pending',
    imageUrl: 'https://picsum.photos/id/40/800/600' // Placeholder for doc
  }
];

// --- OUTSTATION COURIER DATA ---
export const MOCK_OUTSTATION_SHIPMENTS: Delivery[] = [
  {
    id: 'DEL-1001',
    orderId: 'ORD-002',
    customerName: 'John Smith',
    address: '123 Maple Street, Bangalore, KA',
    city: 'Bangalore',
    status: 'In Transit',
    partner: 'Delhivery',
    trackingId: 'DLV123456789',
    estimatedDate: '2024-03-22',
    type: 'B2C'
  },
  {
    id: 'DEL-1002',
    orderId: 'ORD-004',
    customerName: 'Sarah Johnson',
    address: '456 Oak Avenue, Mumbai, MH',
    city: 'Mumbai',
    status: 'Ready to Ship',
    partner: 'Delhivery',
    trackingId: 'pending',
    estimatedDate: '2024-03-25',
    type: 'B2C'
  },
  {
    id: 'DEL-1003',
    orderId: 'ORD-006',
    customerName: 'Michael Brown',
    address: '789 Pine Road, Delhi, DL',
    city: 'Delhi',
    status: 'Delivered',
    partner: 'Delhivery',
    trackingId: 'DLV999AA10123456784',
    estimatedDate: '2024-03-20',
    type: 'B2C'
  },
  {
    id: 'DEL-1004',
    orderId: 'ORD-008',
    customerName: 'Tech Corp Ltd',
    address: 'Tech Park, Hyderabad, TG',
    city: 'Hyderabad',
    status: 'Out for Delivery',
    partner: 'Delhivery',
    trackingId: 'DLV987654321',
    estimatedDate: '2024-03-21',
    type: 'B2B'
  }
];

// --- LOCAL CHENNAI DELIVERIES (PORTER) ---
export const MOCK_LOCAL_TRIPS: LocalDelivery[] = [
  {
    id: 'PTR-5001',
    orderId: 'ORD-001',
    customerName: 'Tech Corp Ltd', // B2B
    type: 'B2B',
    pickupLocation: 'Warehouse A, Ambattur',
    dropLocation: 'Anna Nagar East, Chennai',
    vehicleType: 'Tata Ace',
    driverName: 'Ramesh Kumar',
    driverPhone: '+91 98765 43210',
    status: 'Delivered',
    cost: 1200,
    date: '2024-03-20'
  },
  {
    id: 'PTR-5002',
    orderId: 'ORD-007',
    customerName: 'Priya Rajan', // B2C
    type: 'B2C',
    pickupLocation: 'Store Outlet, T. Nagar',
    dropLocation: 'Adyar, Chennai',
    vehicleType: '2 Wheeler',
    driverName: 'Suresh Singh',
    driverPhone: '+91 87654 32109',
    status: 'On Route',
    cost: 150,
    date: '2024-03-21'
  },
  {
    id: 'PTR-5003',
    orderId: 'ORD-005',
    customerName: 'Enterprise LLC',
    type: 'B2B',
    pickupLocation: 'Warehouse B, Guindy',
    dropLocation: 'Velachery, Chennai',
    vehicleType: '3 Wheeler',
    driverName: 'Searching...',
    driverPhone: 'N/A',
    status: 'Searching',
    cost: 450,
    date: '2024-03-21'
  },
  {
    id: 'PTR-5004',
    orderId: 'ORD-012',
    customerName: 'Karthik M',
    type: 'B2C',
    pickupLocation: 'Store Outlet, T. Nagar',


    dropLocation: 'Mylapore, Chennai',



    vehicleType: '2 Wheeler',
    driverName: 'Vikram Malhotra',
    driverPhone: '+91 99887 77665',
    status: 'Assigned',
    cost: 120,
    date: '2024-03-22'
  }
];

export const MOCK_REFUNDS: Refund[] = [
  {
    id: 'REF-001',
    orderId: 'ORD-009',
    customerName: 'David Wilson',
    amount: '₹3,450',
    reason: 'Failed Delivery',
    status: 'Pending',
    requestDate: '2024-03-19',
    method: 'Original Source',
    type: 'B2C'
  },
  {
    id: 'REF-002',
    orderId: 'ORD-015',
    customerName: 'Tech Corp Ltd',
    amount: '₹12,500',
    reason: 'Damaged Item',
    status: 'Processed',
    requestDate: '2024-03-18',
    method: 'Bank Transfer',
    type: 'B2B'
  },
  {
    id: 'REF-003',
    orderId: 'ORD-021',
    customerName: 'Alice Wonderland',
    amount: '₹1,200',
    reason: 'Order Cancelled',
    status: 'Pending',
    requestDate: '2024-03-20',
    method: 'Wallet',
    type: 'B2C'
  },
  {
    id: 'REF-004',
    orderId: 'ORD-008',
    customerName: 'Emily Davis',
    amount: '₹5,600',
    reason: 'Wrong Item',
    status: 'Rejected',
    requestDate: '2024-03-15',
    method: 'Original Source',
    type: 'B2C'
  },
  {
    id: 'REF-005',
    orderId: 'ORD-033',
    customerName: 'Urban Retailers',
    amount: '₹45,000',
    reason: 'Failed Delivery',
    status: 'Pending',
    requestDate: '2024-03-21',
    method: 'Bank Transfer',
    type: 'B2B'
  }
];

export const MOCK_CATEGORIES: Category[] = [
  // ... existing categories
  // --- CONSUMER ELECTRONICS ---
  {
    id: 'cat_elec_01',
    name: 'Computers & Laptops',
    type: 'Electronics',
    itemCount: 124,
    description: 'Personal computing devices and peripherals',
    subCategories: [
      {
        id: 'sub_elec_01_01', name: 'Laptops', type: 'Electronics', itemCount: 45,
        subCategories: [
          { id: 'type_01_01_01', name: 'Gaming Laptops', type: 'Electronics', itemCount: 15 },
          { id: 'type_01_01_02', name: 'Ultrabooks', type: 'Electronics', itemCount: 20 },
          { id: 'type_01_01_03', name: 'Business Notebooks', type: 'Electronics', itemCount: 10 },
        ]
      },
      {
        id: 'sub_elec_01_02', name: 'Desktop Components', type: 'Electronics', itemCount: 79,
        subCategories: [
          { id: 'type_01_02_01', name: 'Processors (CPU)', type: 'Electronics', itemCount: 12 },
          { id: 'type_01_02_02', name: 'Graphics Cards (GPU)', type: 'Electronics', itemCount: 18 },
          { id: 'type_01_02_03', name: 'Motherboards', type: 'Electronics', itemCount: 15 },
        ]
      }
    ]
  },
  {
    id: 'cat_elec_02',
    name: 'Mobile Phones',
    type: 'Electronics',
    itemCount: 340,
    description: 'Smartphones, tablets and accessories',
    subCategories: [
      {
        id: 'sub_elec_02_01', name: 'Smartphones', type: 'Electronics', itemCount: 120,
        subCategories: [
          { id: 'type_02_01_01', name: 'Flagship Phones', type: 'Electronics', itemCount: 30 },
          { id: 'type_02_01_02', name: 'Budget Phones', type: 'Electronics', itemCount: 90 },
        ]
      },
      {
        id: 'sub_elec_02_02', name: 'Accessories', type: 'Electronics', itemCount: 220,
        subCategories: [
          { id: 'type_02_02_01', name: 'Power Banks', type: 'Electronics', itemCount: 50 },
          { id: 'type_02_02_02', name: 'Cases & Covers', type: 'Electronics', itemCount: 170 },
        ]
      }
    ]
  },
  {
    id: 'cat_elec_03',
    name: 'Audio & Sound',
    type: 'Electronics',
    itemCount: 150,
    description: 'Headphones, speakers and home audio',
    subCategories: [
      {
        id: 'sub_elec_03_01', name: 'Headphones', type: 'Electronics', itemCount: 80,
        subCategories: [
          { id: 'type_03_01_01', name: 'Over-Ear', type: 'Electronics', itemCount: 30 },
          { id: 'type_03_01_02', name: 'True Wireless (TWS)', type: 'Electronics', itemCount: 50 },
        ]
      }
    ]
  },

  // --- ELECTRICALS ---
  {
    id: 'cat_elect_01',
    name: 'Home Appliances',
    type: 'Electrical',
    itemCount: 85,
    description: 'Large electrical appliances for home',
    subCategories: [
      {
        id: 'sub_elect_01_01', name: 'Cooling & Heating', type: 'Electrical', itemCount: 40,
        subCategories: [
          { id: 'type_elect_01_01_01', name: 'Air Conditioners (Split)', type: 'Electrical', itemCount: 15 },
          { id: 'type_elect_01_01_02', name: 'Ceiling Fans', type: 'Electrical', itemCount: 25 },
        ]
      },
      {
        id: 'sub_elect_01_02', name: 'Kitchen Appliances', type: 'Electrical', itemCount: 45,
        subCategories: [
          { id: 'type_elect_01_02_01', name: 'Refrigerators', type: 'Electrical', itemCount: 20 },
          { id: 'type_elect_01_02_02', name: 'Microwave Ovens', type: 'Electrical', itemCount: 15 },
          { id: 'type_elect_01_02_03', name: 'Mixer Grinders', type: 'Electrical', itemCount: 10 },
        ]
      }
    ]
  },
  {
    id: 'cat_elect_02',
    name: 'Wiring & Hardware',
    type: 'Electrical',
    itemCount: 500,
    description: 'Cables, switches, and electrical infrastructure',
    subCategories: [
      {
        id: 'sub_elect_02_01', name: 'Wires & Cables', type: 'Electrical', itemCount: 300,
        subCategories: [
          { id: 'type_elect_02_01_01', name: 'House Wires (FR)', type: 'Electrical', itemCount: 200 },
          { id: 'type_elect_02_01_02', name: 'Coaxial Cables', type: 'Electrical', itemCount: 100 },
        ]
      },
      {
        id: 'sub_elect_02_02', name: 'Switchgear', type: 'Electrical', itemCount: 200,
        subCategories: [
          { id: 'type_elect_02_02_01', name: 'MCBs', type: 'Electrical', itemCount: 150 },
          { id: 'type_elect_02_02_02', name: 'Distribution Boards', type: 'Electrical', itemCount: 50 },
        ]
      }
    ]
  },
  {
    id: 'cat_elect_03',
    name: 'Smart Home Automation',
    type: 'Electrical',
    itemCount: 65,
    description: 'IoT devices and smart electricals',
    subCategories: [
      {
        id: 'sub_elect_03_01', name: 'Smart Lighting', type: 'Electrical', itemCount: 35,
        subCategories: [
          { id: 'type_elect_03_01_01', name: 'Smart Bulbs', type: 'Electrical', itemCount: 20 },
          { id: 'type_elect_03_01_02', name: 'LED Strips', type: 'Electrical', itemCount: 15 },
        ]
      },
      {
        id: 'sub_elect_03_02', name: 'Security', type: 'Electrical', itemCount: 30,
        subCategories: [
          { id: 'type_elect_03_02_01', name: 'Smart Doorbells', type: 'Electrical', itemCount: 10 },
          { id: 'type_elect_03_02_02', name: 'CCTV Cameras', type: 'Electrical', itemCount: 20 },
        ]
      }
    ]
  }
];

// --- PORTER MOCK DATA ---
export const MOCK_PORTER_RULES: PorterRateRule[] = [
  { id: '1', vehicleType: 'Tata Ace', baseFare: 250, perKmRate: 25, minDistance: 2, weightLimit: '750kg' },
  { id: '2', vehicleType: 'Pickup 8ft', baseFare: 450, perKmRate: 35, minDistance: 2, weightLimit: '1200kg' },
  { id: '3', vehicleType: '3 Wheeler', baseFare: 180, perKmRate: 20, minDistance: 1, weightLimit: '500kg' },
  { id: '4', vehicleType: '2 Wheeler', baseFare: 50, perKmRate: 10, minDistance: 1, weightLimit: '20kg' },
];

export const MOCK_PORTER_ZONES: PorterZone[] = [
  { id: 'z1', name: 'North Bangalore', city: 'Bangalore', pincodes: '560001, 560003, 560024', status: 'Active' },
  { id: 'z2', name: 'Tech Park Zone', city: 'Bangalore', pincodes: '560045, 560103, 560037', status: 'Active' },
  { id: 'z3', name: 'South Mumbai', city: 'Mumbai', pincodes: '400001, 400005, 400020', status: 'Inactive' },
];

export const MOCK_PORTER_PERFORMANCE = [
  { name: 'Success', value: 320, color: '#10B981' },
  { name: 'Failed', value: 15, color: '#EF4444' },
  { name: 'Cancelled', value: 24, color: '#F59E0B' },
];

export const MOCK_USER_ACTIVITY_LOGS: ActivityLog[] = [
  { id: 'log_u1', user: 'John Doe', role: 'B2C', action: 'Login', details: 'Logged in via Email', timestamp: '2024-03-21 09:30 AM', status: 'Success' },
  { id: 'log_u2', user: 'Sarah Connor', role: 'B2C', action: 'Order Placed', details: 'Placed order #ORD-004', timestamp: '2024-03-21 10:15 AM', status: 'Success' },
  { id: 'log_u3', user: 'Super Admin', role: 'Admin', action: 'Product Update', details: 'Updated price for Gaming Laptop', timestamp: '2024-03-21 11:00 AM', status: 'Success' },
  { id: 'log_u4', user: 'Mike Ross', role: 'B2C', action: 'Failed Login', details: 'Invalid password attempt', timestamp: '2024-03-21 11:45 AM', status: 'Failed' },
  { id: 'log_u5', user: 'Tech Corp Ltd', role: 'B2B', action: 'Password Reset', details: 'Requested password reset link', timestamp: '2024-03-21 01:20 PM', status: 'Success' },
  { id: 'log_u6', user: 'Alice Support', role: 'Staff', action: 'Refund Approved', details: 'Approved refund #REF-002', timestamp: '2024-03-21 02:10 PM', status: 'Success' },
];

export const MOCK_B2B_ACTIVITY_LOGS: ActivityLog[] = [
  { id: 'log_b1', user: 'Tech Solutions Ltd', role: 'B2B', action: 'KYC Upload', details: 'Uploaded GST Certificate', timestamp: '2024-03-22 09:00 AM', status: 'Success' },
  { id: 'log_b2', user: 'Global Imports Inc', role: 'B2B', action: 'Credit Limit', details: 'Requested credit limit increase to ₹10L', timestamp: '2024-03-22 10:30 AM', status: 'Warning' },
  { id: 'log_b3', user: 'Business Traders', role: 'B2B', action: 'Bulk Order', details: 'Placed bulk order #ORD-005 for 50 items', timestamp: '2024-03-22 11:45 AM', status: 'Success' },
  { id: 'log_b4', user: 'Tech Solutions Ltd', role: 'B2B', action: 'Profile Update', details: 'Updated registered office address', timestamp: '2024-03-22 01:15 PM', status: 'Success' },
  { id: 'log_b5', user: 'Global Imports Inc', role: 'B2B', action: 'Payment Failed', details: 'NEFT transaction failed', timestamp: '2024-03-22 02:30 PM', status: 'Failed' },
];

export const MOCK_ACTIVITY_LOGS: SystemLog[] = [
  { id: 'sys_1', timestamp: '2024-03-23T10:00:00', user: { name: 'Super Admin' }, action: 'Updated System Branding', module: 'Settings', status: 'SUCCESS' },
  { id: 'sys_2', timestamp: '2024-03-23T11:15:00', user: { name: 'System Manager' }, action: 'Changed SMTP Config', module: 'Gateway', status: 'WARNING' },
  { id: 'sys_3', timestamp: '2024-03-23T12:30:00', user: { name: 'Super Admin' }, action: 'Enabled 2FA', module: 'Security', status: 'SUCCESS' },
  { id: 'sys_4', timestamp: '2024-03-23T14:45:00', user: { name: 'Alice Support' }, action: 'Failed Login Attempt', module: 'Auth', status: 'FAILURE' },
  { id: 'sys_5', timestamp: '2024-03-23T15:20:00', user: { name: 'Super Admin' }, action: 'Updated Notification Triggers', module: 'Notifications', status: 'SUCCESS' },
  { id: 'sys_6', timestamp: '2024-03-23T16:00:00', user: { name: 'System Manager' }, action: 'Exported Audit Logs', module: 'Settings', status: 'SUCCESS' },
];  