import axios from 'axios';

const BASE_URL = import.meta.env.VITE_API_URL || '/api/v1';

const api = axios.create({
  baseURL: BASE_URL,
  headers: { 'Content-Type': 'application/json' },
});

// Auto-attach token from localStorage
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('access_token');
  if (token) config.headers.Authorization = `Bearer ${token}`;
  return config;
});

api.interceptors.response.use(
  (res) => res,
  (err) => {
    if (err.response?.status === 401) {
      localStorage.removeItem('access_token');
      localStorage.removeItem('company_id');
      localStorage.removeItem('branch_id');
    }
    return Promise.reject(err);
  }
);

export default api;

// ---- Auth ----
export const login = (email, password) => api.post('/auth/login', { email, password });
export const logout = () => api.post('/auth/logout');
export const selectCompany = (company_id, branch_id) =>
  api.post('/auth/select-company', { company_id, branch_id });
export const getMe = () => api.get('/auth/me');

// ---- Companies ----
export const getCompanies = () => api.get('/companies');
export const getCurrentCompany = () => api.get('/companies/current');

// ---- Partners ----
export const getPartners = () => api.get('/partners');
export const createPartner = (data) => api.post('/partners', data);
export const updatePartner = (id, data) => api.patch(`/partners/${id}`, data);
export const deletePartner = (id) => api.delete(`/partners/${id}`);

// ---- Items ----
export const getItems = () => api.get('/items');
export const createItem = (data) => api.post('/items', data);
export const updateItem = (id, data) => api.patch(`/items/${id}`, data);
export const deleteItem = (id) => api.delete(`/items/${id}`);
export const getCategories = () => api.get('/item-categories');
export const createCategory = (data) => api.post('/item-categories', data);
export const updateCategory = (id, data) => api.patch(`/item-categories/${id}`, data);
export const deleteCategory = (id) => api.delete(`/item-categories/${id}`);
export const getUnits = () => api.get('/units');
export const createUnit = (data) => api.post('/units', data);
export const updateUnit = (id, data) => api.patch(`/units/${id}`, data);
export const deleteUnit = (id) => api.delete(`/units/${id}`);
export const getUnitConversions = () => api.get('/unit-conversions');
export const createUnitConversion = (data) => api.post('/unit-conversions', data);
export const updateUnitConversion = (id, data) => api.patch(`/unit-conversions/${id}`, data);
export const deleteUnitConversion = (id) => api.delete(`/unit-conversions/${id}`);

// ---- Currencies ----
export const getCurrencies = () => api.get('/currencies');
export const createCurrency = (data) => api.post('/currencies', data);
export const updateCurrency = (id, data) => api.patch(`/currencies/${id}`, data);
export const deleteCurrency = (id) => api.delete(`/currencies/${id}`);
export const getCurrencyRates = () => api.get('/currency-rates');
export const createCurrencyRate = (data) => api.post('/currency-rates', data);
export const updateCurrencyRate = (id, data) => api.patch(`/currency-rates/${id}`, data);
export const deleteCurrencyRate = (id) => api.delete(`/currency-rates/${id}`);

// ---- Warehouses & Stock ----
export const getWarehouses = () => api.get('/warehouses');
export const createWarehouse = (data) => api.post('/warehouses', data);
export const updateWarehouse = (id, data) => api.patch(`/warehouses/${id}`, data);
export const deleteWarehouse = (id) => api.delete(`/warehouses/${id}`);
export const getStock = (warehouseId) => api.get('/warehouse-stock', { params: warehouseId ? { warehouse_id: warehouseId } : {} });
export const getMovements = () => api.get('/inventory-movements');

// ---- Stock takes ----
export const getStockTakes = () => api.get('/stock-takes');
export const getStockTake = (id) => api.get(`/stock-takes/${id}`);
export const createStockTake = (data) => api.post('/stock-takes', data);
export const postStockTake = (id) => api.post(`/stock-takes/${id}/post`);

// ---- Sales ----
export const getSalesInvoices = () => api.get('/sales-invoices');
export const createSalesInvoice = (data) => api.post('/sales-invoices', data);
export const confirmSalesInvoice = (id) => api.post(`/sales-invoices/${id}/confirm`);
export const getSalesInvoice = (id) => api.get(`/sales-invoices/${id}`);
export const deleteSalesInvoice = (id) => api.delete(`/sales-invoices/${id}`);

// ---- Purchases ----
export const getPurchaseInvoices = () => api.get('/purchase-invoices');
export const createPurchaseInvoice = (data) => api.post('/purchase-invoices', data);
export const confirmPurchaseInvoice = (id) => api.post(`/purchase-invoices/${id}/confirm`);
export const getPurchaseInvoice = (id) => api.get(`/purchase-invoices/${id}`);
export const deletePurchaseInvoice = (id) => api.delete(`/purchase-invoices/${id}`);

// ---- Payments ----
export const getPayments = () => api.get('/payments');
export const createPayment = (data) => api.post('/payments', data);

// ---- POS ----
export const getPosSessions = () => api.get('/pos/sessions');
export const openPosSession = (data) => api.post('/pos/sessions', data);
export const closePosSession = (id, data) => api.post(`/pos/sessions/${id}/close`, data);
export const getPosOrders = () => api.get('/pos/orders');
export const createPosOrder = (data) => api.post('/pos/orders', data);

// ---- Accounting ----
export const getAccounts = () => api.get('/accounting/accounts');
export const createAccount = (data) => api.post('/accounting/accounts', data);
export const getJournalEntries = () => api.get('/accounting/journal-entries');
export const createJournalEntry = (data) => api.post('/accounting/journal-entries', data);
export const getTrialBalance = () => api.get('/accounting/reports/trial-balance');
export const getIncomeStatement = () => api.get('/accounting/reports/income-statement');
export const getBalanceSheet = () => api.get('/accounting/reports/balance-sheet');

// ---- HR ----
export const getDepartments = () => api.get('/hr/departments');
export const createDepartment = (data) => api.post('/hr/departments', data);
export const getEmployees = () => api.get('/hr/employees');
export const createEmployee = (data) => api.post('/hr/employees', data);
export const createAttendance = (data) => api.post('/hr/attendance', data);
export const runPayroll = (data) => api.post('/hr/payroll/run', data);
export const getLeaveRequests = () => api.get('/hr/leave-requests');
export const createLeaveRequest = (data) => api.post('/hr/leave-requests', data);
export const updateLeaveStatus = (id, status) =>
  api.post(`/hr/leave-requests/${id}/status`, { status });

// ---- Projects ----
export const getProjects = () => api.get('/projects');
export const createProject = (data) => api.post('/projects', data);
export const addProjectCost = (id, data) => api.post(`/projects/${id}/costs`, data);
export const completeProject = (id) => api.post(`/projects/${id}/complete`);

// ---- Manufacturing ----
export const getWorkOrders = () => api.get('/manufacturing/work-orders');
export const createWorkOrder = (data) => api.post('/manufacturing/work-orders', data);
export const finishWorkOrder = (id, data) => api.post(`/manufacturing/work-orders/${id}/finish`, data);
export const getBoms = () => api.get('/manufacturing/boms');
export const createBom = (data) => api.post('/manufacturing/boms', data);

// ---- Reports ----
export const getSalesSummary = (params) => api.get('/reports/sales-summary', { params });
export const getStockValue = () => api.get('/reports/stock-value');
export const getLowStock = (threshold) => api.get('/reports/low-stock', { params: { threshold } });
export const getProjectCosts = () => api.get('/reports/project-costs');

// ---- Platform (superuser) ----
export const getPlatformModules = () => api.get('/platform/modules');
export const getPlatformCompanies = () => api.get('/platform/companies');
export const createPlatformCompany = (data) => api.post('/platform/companies', data);
export const updatePlatformCompany = (id, data) => api.patch(`/platform/companies/${id}`, data);
export const getPlatformCompanyUsers = (id) => api.get(`/platform/companies/${id}/users`);
export const createPlatformCompanyUser = (id, data) => api.post(`/platform/companies/${id}/users`, data);
export const resetUserPassword = (userId, newPassword) =>
  api.post(`/platform/users/${userId}/password`, { new_password: newPassword });
