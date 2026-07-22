/* ========== API Client ========== */
const API_BASE = window.location.origin + '/api/v1';

async function api(path, options = {}) {
  const token = localStorage.getItem('token');
  const headers = { 'Content-Type': 'application/json' };
  if (token) headers['Authorization'] = 'Bearer ' + token;

  const { data: bodyData, ...fetchOpts } = options;
  const fetchOptions = {
    ...fetchOpts,
    headers: { ...headers, ...options.headers },
  };
  if (bodyData !== undefined) {
    fetchOptions.body = JSON.stringify(bodyData);
  }

  const res = await fetch(API_BASE + path, fetchOptions);
  const data = await res.json();
  if (!res.ok || data.code >= 400) throw new Error(data.message || '请求失败');
  return data;
}

const userApi = {
  login: (username, password) => api('/users/login', { method: 'POST', data: { username, password } }),
  getProfile: () => api('/users/me'),
  updateProfile: (data) => api('/users/me', { method: 'PUT', data }),
};

const menuApi = {
  getCategories: () => api('/menu/categories'),
  getDishes: (params) => api('/menu/dishes?' + new URLSearchParams(params)),
  getDishDetail: (id) => api('/menu/dishes/' + id),
  getMaterials: () => api('/menu/materials'),
  submitPendingDish: (data) => api('/menu/pending-dishes', { method: 'POST', data }),
  getMyPendingDishes: () => api('/menu/pending-dishes'),
};

const orderApi = {
  createOrder: (data) => api('/orders', { method: 'POST', data }),
  getOrders: (params) => api('/orders?' + new URLSearchParams(params)),
  getOrderDetail: (id) => api('/orders/' + id),
  cancelOrder: (id) => api('/orders/' + id + '/cancel', { method: 'POST' }),
};

const adminApi = {
  createDish: (data) => api('/admin/dishes', { method: 'POST', data }),
  updateDish: (id, data) => api('/admin/dishes/' + id, { method: 'PUT', data }),
  getDishes: (params) => api('/admin/dishes?' + new URLSearchParams(params)),
  createCategory: (data) => api('/admin/categories', { method: 'POST', data }),
  updateCategory: (id, data) => api('/admin/categories/' + id, { method: 'PUT', data }),
  deleteCategory: (id) => api('/admin/categories/' + id, { method: 'DELETE' }),
  getCategories: () => api('/admin/categories'),
  createMaterial: (data) => api('/admin/materials', { method: 'POST', data }),
  updateMaterial: (id, data) => api('/admin/materials/' + id, { method: 'PUT', data }),
  getMaterials: () => api('/admin/materials'),
  getOrders: (params) => api('/admin/orders?' + new URLSearchParams(params)),
  updateOrderStatus: (id, status) => api('/admin/orders/' + id + '/status?new_status=' + status, { method: 'PUT' }),
  getPendingDishes: (params) => api('/admin/pending-dishes?' + new URLSearchParams(params)),
  reviewPendingDish: (id, data) => api('/admin/pending-dishes/' + id + '/review', { method: 'POST', data }),
  // User management
  createUser: (data) => api('/admin/users', { method: 'POST', data }),
  getUsers: (params) => api('/admin/users?' + new URLSearchParams(params)),
  updateUser: (id, data) => api('/admin/users/' + id, { method: 'PUT', data }),
  // Chef orders
  getChefOrders: (params) => api('/admin/orders/chef?' + new URLSearchParams(params)),
  deleteOrder: (id) => api('/admin/orders/' + id, { method: 'DELETE' }),
  deleteUser: (id) => api('/admin/users/' + id, { method: 'DELETE' }),
  deleteMaterial: (id) => api('/admin/materials/' + id, { method: 'DELETE' }),
  batchDeleteOrders: (ids) => api('/admin/orders/batch-delete', { method: 'POST', data: { ids } }),
  batchDeleteUsers: (ids) => api('/admin/users/batch-delete', { method: 'POST', data: { ids } }),
  batchDeleteMaterials: (ids) => api('/admin/materials/batch-delete', { method: 'POST', data: { ids } }),
};

/* ========== Helpers ========== */
function toast(msg) {
  const el = document.createElement('div');
  el.className = 'toast';
  el.textContent = msg;
  document.body.appendChild(el);
  setTimeout(() => el.remove(), 2000);
}

function showPage(id) {
  document.querySelectorAll('.page').forEach(p => p.classList.remove('active'));
  const page = document.getElementById(id);
  if (page) page.classList.add('active');
  document.querySelectorAll('.nav-item').forEach(n => {
    n.classList.toggle('active', n.dataset.page === id);
  });
}

function formatTime(dateStr) {
  if (!dateStr) return '';
  const d = new Date(dateStr);
  return d.getFullYear() + '-' +
    String(d.getMonth()+1).padStart(2,'0') + '-' +
    String(d.getDate()).padStart(2,'0') + ' ' +
    String(d.getHours()).padStart(2,'0') + ':' +
    String(d.getMinutes()).padStart(2,'0');
}

function orderStatusText(s) {
  return { pending: '待处理', confirmed: '已确认', preparing: '制作中', completed: '已完成', cancelled: '已取消' }[s] || s;
}

function dishStatusText(s) {
  return { active: '在售', inactive: '已下架', pending_price: '待定价' }[s] || s;
}

/* ========== Cart ========== */
function getCart() {
  return JSON.parse(localStorage.getItem('cart') || '[]');
}
function setCart(items) {
  localStorage.setItem('cart', JSON.stringify(items));
}
function addToCart(dish, qty = 1, excludedMaterialIds = []) {
  const cart = getCart();
  const idx = cart.findIndex(item => item.dishId === dish.id);
  if (idx > -1) {
    cart[idx].quantity += qty;
    cart[idx].excludedMaterialIds = [...new Set([...cart[idx].excludedMaterialIds, ...excludedMaterialIds])];
  } else {
    cart.push({
      dishId: dish.id,
      dishName: dish.name,
      price: dish.price,
      imageUrl: dish.image_url,
      quantity: qty,
      excludedMaterialIds: excludedMaterialIds,
    });
  }
  setCart(cart);
  updateCartBadge();
}

function updateCartBadge() {
  const count = getCart().reduce((s, i) => s + i.quantity, 0);
  document.querySelectorAll('.cart-badge').forEach(el => {
    el.textContent = count;
    el.style.display = count > 0 ? 'inline' : 'none';
  });
}

/* ========== Login / User ========== */
async function checkLogin() {
  const token = localStorage.getItem('token');
  const user = JSON.parse(localStorage.getItem('user') || 'null');
  return { token, user };
}

async function doLogin() {
  const username = document.getElementById('login-username').value.trim();
  const password = document.getElementById('login-password').value;
  const errorEl = document.getElementById('login-error');
  errorEl.style.display = 'none';

  if (!username || !password) {
    errorEl.textContent = '请输入用户名和密码';
    errorEl.style.display = '';
    return;
  }
  try {
    const res = await userApi.login(username, password);
    localStorage.setItem('token', res.data.access_token);
    localStorage.setItem('user', JSON.stringify(res.data.user));
    updateUserUI();
    document.getElementById('login-username').value = '';
    document.getElementById('login-password').value = '';
    initApp();
    initProfile();
    toast('登录成功');
    showPage('menu-page');
  } catch (e) {
    errorEl.textContent = e.message || '登录失败';
    errorEl.style.display = '';
  }
}

function updateUserUI() {
  const user = JSON.parse(localStorage.getItem('user') || 'null');
  const loggedIn = !!user;
  document.getElementById('profile-login-form').style.display = loggedIn ? 'none' : '';
  document.getElementById('profile-logged-in').style.display = loggedIn ? '' : 'none';

  if (loggedIn) {
    const nameEl = document.getElementById('user-name-display');
    if (nameEl) nameEl.textContent = user.nickname || user.username || '用户';
    const roleEl = document.getElementById('user-role-display');
    const roleMap = { admin: '管理员', chef: '厨师', user: '点餐用户' };
    if (roleEl) roleEl.textContent = roleMap[user.role] || user.role;
  }

  const adminEntry = document.getElementById('admin-entry-btn');
  if (adminEntry) adminEntry.style.display = user && (user.role === 'admin' || user.role === 'chef') ? '' : 'none';
}

function logout() {
  localStorage.removeItem('token');
  localStorage.removeItem('user');
  updateUserUI();
  showPage('menu-page');
  toast('已退出');
}

/* ========== App ========== */
async function initApp() {
  loadCategories();
  loadDishes();
  updateCartBadge();
  updateUserUI();
}

// Menu
let allCategories = [];
let allDishes = [];
let activeCategory = null;

async function loadCategories() {
  try {
    const res = await menuApi.getCategories();
    allCategories = res.data || [];
    if (allCategories.length > 0 && !activeCategory) {
      activeCategory = allCategories[0].id;
    }
    renderSidebar();
  } catch (e) { console.error(e); }
}

function renderSidebar() {
  const bar = document.getElementById('menu-sidebar');
  if (!bar) return;
  bar.innerHTML = `
    <div onclick="switchCategory(null)"
      style="padding:14px 8px;text-align:center;font-size:13px;cursor:pointer;
        ${activeCategory === null ? 'background:#fff;color:var(--green);font-weight:600;border-left:3px solid var(--green)' : 'color:#666;border-left:3px solid transparent'}">
      全部
    </div>
  ` + allCategories.map(c => `
    <div onclick="switchCategory(${c.id})"
      style="padding:14px 8px;text-align:center;font-size:13px;cursor:pointer;
        ${activeCategory === c.id ? 'background:#fff;color:var(--green);font-weight:600;border-left:3px solid var(--green)' : 'color:#666;border-left:3px solid transparent'}">
      ${c.name}
    </div>
  `).join('');
}

function switchCategory(id) {
  activeCategory = id;
  renderSidebar();
  renderDishList();
  const content = document.getElementById('menu-content');
  if (content) content.scrollTop = 0;
}

async function loadDishes() {
  try {
    const res = await menuApi.getDishes({ page_size: 100 });
    allDishes = res.data.items || [];
    renderDishList();
  } catch (e) { console.error(e); }
}

function renderDishList() {
  const list = document.getElementById('dish-list');
  const filtered = activeCategory ? allDishes.filter(d => d.category_id === activeCategory) : allDishes;

  if (!filtered || filtered.length === 0) {
    list.innerHTML = '<div class="text-center text-secondary" style="padding:60px 0;font-size:14px">暂无菜品</div>';
    return;
  }
  list.innerHTML = '<div style="font-size:13px;color:var(--text-secondary);margin-bottom:12px">共 ' + filtered.length + ' 道菜</div>' +
    filtered.map(d => `
    <div class="dish-card" onclick="showDishDetail(${d.id})" style="margin-bottom:10px">
      <div class="dish-img" style="width:72px;height:72px;font-size:28px">🍽️</div>
      <div class="dish-info">
        <div class="dish-name" style="font-size:14px">${d.name}</div>
        <div class="dish-footer" style="margin-top:8px">
          <div class="dish-price" style="font-size:16px">${d.price !== null ? '¥' + d.price : '待定价'}</div>
          <div class="dish-tags">${d.is_recommended ? '<span class="tag">推荐</span>' : ''}</div>
        </div>
      </div>
      <button class="add-cart-btn" onclick="event.stopPropagation(); quickAdd(${d.id})" style="width:26px;height:26px;font-size:16px">+</button>
    </div>
  `).join('');
}

function quickAdd(dishId) {
  const dish = allDishes.find(d => d.id === dishId);
  if (!dish || !dish.price) { toast('该菜品暂不可用'); return; }
  addToCart(dish);
  toast('已加入购物车');
}

// Dish Detail
let currentDish = null;

async function showDishDetail(id) {
  try {
    const res = await menuApi.getDishDetail(id);
    currentDish = res.data;
    const d = currentDish;
    document.getElementById('detail-content').innerHTML = `
      <div class="detail-header">
        <div class="dish-img-lg">🍽️</div>
        <div class="dish-name">${d.name}</div>
        <div class="dish-price-lg">${d.price !== null ? '¥' + d.price : '待定价'}</div>
        <div class="dish-desc">${d.description || ''}</div>
      </div>
      <div class="card">
        <div style="font-weight:600;margin-bottom:12px">📋 材料清单 <span style="font-weight:400;font-size:13px;color:var(--text-secondary)">（点击可排除）</span></div>
        <div class="material-list" id="material-list"></div>
      </div>
      <div class="card">
        <div class="qty-selector">
          <button class="qty-btn" onclick="changeQty(-1)" id="qty-minus">−</button>
          <span class="qty-value" id="qty-value">1</span>
          <button class="qty-btn" onclick="changeQty(1)">+</button>
        </div>
      </div>
      <button class="btn btn-primary btn-block" onclick="addDetailToCart()" style="margin-top:8px">加入购物车</button>
    `;
    window._detailQty = 1;
    window._excludedMaterials = [];
    renderMaterials(d.materials || []);
    showPage('detail-page');
    document.getElementById('page-title').textContent = d.name;
  } catch (e) {
    toast('加载失败');
  }
}

function renderMaterials(materials) {
  const list = document.getElementById('material-list');
  list.innerHTML = materials.map(m => `
    <div class="material-item" data-id="${m.id}" onclick="toggleMaterial(this)">
      <span>${m.name}</span>
      ${m.category ? '<span style="font-size:12px;color:var(--text-secondary)">' + m.category + '</span>' : ''}
      ${m.is_allergen ? '<span class="allergen-badge">过敏原</span>' : ''}
    </div>
  `).join('');
}

function toggleMaterial(el) {
  el.classList.toggle('selected');
  const id = parseInt(el.dataset.id);
  const arr = window._excludedMaterials;
  const idx = arr.indexOf(id);
  if (idx > -1) arr.splice(idx, 1);
  else arr.push(id);
}

function changeQty(delta) {
  window._detailQty = Math.max(1, Math.min(100, (window._detailQty || 1) + delta));
  document.getElementById('qty-value').textContent = window._detailQty;
  document.getElementById('qty-minus').disabled = window._detailQty <= 1;
}

function addDetailToCart() {
  if (!currentDish || !currentDish.price) { toast('该菜品暂不可用'); return; }
  addToCart(currentDish, window._detailQty || 1, window._excludedMaterials);
  toast('已加入购物车');
}

function renderCart() {
  const items = getCart();
  const container = document.getElementById('cart-list');
  const bar = document.getElementById('cart-bottom-bar');
  const totalEl = document.getElementById('cart-total');
  if (!container || !bar || !totalEl) return;

  if (!items || items.length === 0) {
    container.innerHTML = '<div class="cart-empty"><div class="empty-icon">🛒</div><div>购物车是空的</div><button class="btn btn-primary mt-16" onclick="showPage(\'menu-page\')">去点餐</button></div>';
    bar.style.display = 'none';
    return;
  }

  bar.style.display = 'flex';

  let html = '';
  let total = 0;
  for (let i = 0; i < items.length; i++) {
    const item = items[i];
    const sub = (item.price || 0) * item.quantity;
    total += sub;
    html += '<div class="card" style="display:flex;align-items:center;gap:12px;padding:12px 16px;margin-bottom:8px">';
    html += '  <div style="flex:1;min-width:0">';
    html += '    <div style="font-weight:600;font-size:15px">' + item.dishName + '</div>';
    if (item.excludedMaterialIds && item.excludedMaterialIds.length) {
      html += '    <div style="font-size:12px;color:var(--text-secondary)">忌口: ' + item.excludedMaterialIds.length + '项</div>';
    }
    html += '    <div style="color:var(--red);font-weight:600;font-size:15px;margin-top:2px">¥' + sub.toFixed(2) + '</div>';
    html += '  </div>';
    html += '  <div style="display:flex;align-items:center;gap:8px">';
    html += '    <button class="qty-btn" onclick="cartChangeQty(' + i + ',-1)" style="width:32px;height:32px;font-size:18px" ' + (item.quantity <= 1 ? 'disabled' : '') + '>−</button>';
    html += '    <span style="font-size:16px;font-weight:600;min-width:24px;text-align:center">' + item.quantity + '</span>';
    html += '    <button class="qty-btn" onclick="cartChangeQty(' + i + ',1)" style="width:32px;height:32px;font-size:18px">+</button>';
    html += '    <button class="qty-btn" onclick="cartRemoveItem(' + i + ')" style="width:32px;height:32px;font-size:16px;color:var(--red);border-color:var(--red)">✕</button>';
    html += '  </div>';
    html += '</div>';
  }
  container.innerHTML = html;
  totalEl.textContent = '¥' + total.toFixed(2);
}

function cartChangeQty(idx, delta) {
  const cart = getCart();
  cart[idx].quantity += delta;
  if (cart[idx].quantity <= 0) cart.splice(idx, 1);
  setCart(cart);
  updateCartBadge();
  renderCart();
}

function cartRemoveItem(idx) {
  const cart = getCart();
  cart.splice(idx, 1);
  setCart(cart);
  updateCartBadge();
  renderCart();
}

// Create Order
function showOrderConfirm() {
  const cart = getCart();
  if (cart.length === 0) { toast('购物车为空'); return; }
  if (!localStorage.getItem('token')) { toast('请先登录'); return; }

  const total = cart.reduce((s, i) => s + (i.price || 0) * i.quantity, 0);
  document.getElementById('order-confirm-total').textContent = '¥' + total.toFixed(2);
  document.getElementById('order-note').value = '';

  document.getElementById('order-confirm-items').innerHTML = cart.map(item => `
    <div class="order-item-row">
      <span>${item.dishName} ×${item.quantity}</span>
      <span style="color:var(--red)">¥${((item.price || 0) * item.quantity).toFixed(2)}</span>
    </div>
  `).join('');

  document.getElementById('order-modal').classList.remove('hidden');
}

async function submitOrder() {
  const cart = getCart();
  if (cart.length === 0) return;

  try {
    const items = cart.map(i => ({
      dish_id: i.dishId,
      quantity: i.quantity,
      excluded_material_ids: i.excludedMaterialIds || [],
    }));
    const note = document.getElementById('order-note').value.trim() || undefined;
    await orderApi.createOrder({ items, note });
    setCart([]);
    updateCartBadge();
    document.getElementById('order-modal').classList.add('hidden');
    toast('下单成功！');
    loadOrders();
    showPage('orders-page');
  } catch (e) {
    toast('下单失败: ' + e.message);
  }
}

// Orders
let allOrders = [];
let orderFilter = null;

async function loadOrders() {
  if (!localStorage.getItem('token')) {
    document.getElementById('order-list').innerHTML = '<div class="text-center text-secondary" style="padding:60px 0">请先登录</div>';
    return;
  }
  try {
    const params = { page_size: 50 };
    if (orderFilter) params.status = orderFilter;
    const res = await orderApi.getOrders(params);
    allOrders = res.data.items || [];
    renderOrders();
  } catch (e) { console.error(e); }
}

function renderOrders() {
  const list = document.getElementById('order-list');
  if (allOrders.length === 0) {
    list.innerHTML = '<div class="text-center text-secondary" style="padding:60px 0">暂无订单</div>';
    return;
  }
  list.innerHTML = allOrders.map(o => `
    <div class="card order-card" onclick="showOrderDetail(${o.id})">
      <div class="order-header">
        <span class="order-no">${o.order_no}</span>
        <span class="order-status ${o.status}">${orderStatusText(o.status)}</span>
      </div>
      <div class="order-body">
        <span>${o.item_count || 0} 道菜</span>
        <span class="order-total">¥${o.total_price}</span>
      </div>
      <div class="order-time">${formatTime(o.created_at)}</div>
    </div>
  `).join('');
}

function filterOrder(status) {
  orderFilter = status === 'all' ? null : status;
  document.querySelectorAll('.order-status-bar .category-tab').forEach(t => {
    t.classList.toggle('active', t.dataset.status === status);
  });
  loadOrders();
}

async function showOrderDetail(id) {
  try {
    const res = await orderApi.getOrderDetail(id);
    const o = res.data;
    document.getElementById('detail-content').innerHTML = `
      <div class="card">
        <div class="flex-between">
          <span style="font-weight:600">${orderStatusText(o.status)}</span>
          <span class="text-secondary">${o.order_no}</span>
        </div>
        <div class="text-secondary mt-8">${formatTime(o.created_at)}</div>
      </div>
      <div class="card">
        <div style="font-weight:600;margin-bottom:8px">🍽️ 菜品明细</div>
        ${(o.items || []).map(item => `
          <div class="order-item-row">
            <span>${item.dish_name} ×${item.quantity}</span>
            <span style="color:var(--red)">¥${(item.unit_price * item.quantity).toFixed(2)}</span>
          </div>
        `).join('')}
        <div class="order-item-row" style="font-weight:600;border-bottom:none;padding-top:12px">
          <span>合计</span>
          <span style="color:var(--red);font-size:18px">¥${o.total_price}</span>
        </div>
      </div>
      ${o.note ? `<div class="card"><div style="font-weight:600;margin-bottom:4px">📝 备注</div><div class="text-secondary">${o.note}</div></div>` : ''}
      ${o.status === 'pending' ? `<button class="btn btn-danger btn-block mt-16" onclick="cancelCurrentOrder(${o.id})">取消订单</button>` : ''}
    `;
    document.getElementById('page-title').textContent = '订单详情';
    showPage('detail-page');
  } catch (e) {
    toast('加载失败');
  }
}

async function cancelCurrentOrder(id) {
  if (!confirm('确定要取消这个订单吗？')) return;
  try {
    await orderApi.cancelOrder(id);
    toast('订单已取消');
    showOrderDetail(id);
  } catch (e) {
    toast('取消失败');
  }
}

// ==================== Admin ====================
async function initAdmin() {
  const user = JSON.parse(localStorage.getItem('user') || 'null');
  window._isAdmin = user && user.role === 'admin';
  window._isChef = user && user.role === 'chef';

  // Chef sees orders + dishes, admin sees all
  document.querySelectorAll('.admin-nav .category-tab').forEach(t => {
    const adminOnly = ['categories', 'users', 'pending', 'materials'];
    t.style.display = (window._isAdmin || (window._isChef && !adminOnly.includes(t.dataset.tab))) ? '' : 'none';
  });

  if (window._isChef) {
    switchAdminTab('orders');
  } else {
    switchAdminTab('dishes');
  }

  // Show stats only for admin
  const statsEl = document.querySelector('.stats-row');
  if (statsEl) statsEl.style.display = window._isAdmin ? '' : 'none';
}

// Admin Stats
async function loadAdminStats() {
  try {
    const [dishRes, pendingRes, orderRes] = await Promise.all([
      adminApi.getDishes({ status: 'active', page_size: 1 }),
      adminApi.getPendingDishes({ status: 'pending_price', page_size: 1 }),
      adminApi.getOrders({ status: 'pending', page_size: 1 }),
    ]);
    document.getElementById('stats-active').textContent = dishRes.data?.total || 0;
    document.getElementById('stats-pending').textContent = pendingRes.data?.total || 0;
    document.getElementById('stats-orders').textContent = orderRes.data?.total || 0;
  } catch (e) { console.error(e); }
}

// Admin Dishes
let adminDishes = [];
let adminDishSearch = '';

async function loadAdminDishes() {
  try {
    const res = await adminApi.getDishes({ page_size: 100 });
    adminDishes = res.data.items || [];
    renderAdminDishes();
    const catRes = await adminApi.getCategories();
    window._adminCategories = catRes.data || [];
  } catch (e) { console.error(e); }
}

function searchAdminDishes() {
  adminDishSearch = (document.getElementById('dish-search').value || '').trim();
  renderAdminDishes();
}

function renderAdminDishes() {
  const el = document.getElementById('admin-dish-list');
  if (!el) return;
  const filtered = adminDishSearch
    ? adminDishes.filter(d => (d.name || '').includes(adminDishSearch))
    : adminDishes;
  el.innerHTML = (filtered.length === 0 ? '<div class="text-secondary text-center" style="padding:40px">' + (adminDishSearch ? '无匹配菜品' : '暂无菜品') + '</div>'
  : filtered.map(d => `
    <div class="card" style="padding:12px">
      <div class="flex-between">
        <div>
          <strong>${d.name}</strong>
          <span class="text-secondary" style="margin-left:6px;font-size:12px">${dishStatusText(d.status)}</span>
        </div>
        <span style="color:var(--red);font-weight:600">${d.price !== null ? '¥' + d.price : '待定价'}</span>
      </div>
      <div class="flex-between mt-8">
        <span class="text-secondary" style="font-size:13px">${d.category_name || ''}</span>
        <div style="display:flex;gap:6px">
          <button class="btn btn-small btn-outline" onclick="showAdminDishModal(${d.id})" style="font-size:12px">编辑</button>
          <button class="btn btn-small ${d.status === 'active' ? 'btn-danger' : 'btn-primary'}" onclick="toggleDishStatus(${d.id}, '${d.status}')" style="font-size:12px">
            ${d.status === 'active' ? '下架' : '上架'}
          </button>
          ${window._isAdmin ? `<button class="btn btn-small btn-outline" style="color:var(--red);border-color:var(--red);font-size:12px" onclick="adminDeleteDish(${d.id})">删除</button>` : ''}
        </div>
      </div>
    </div>
  `).join(''));
}


async function adminDeleteDish(id) {
  if (!confirm('确定要删除此菜品吗？')) return;
  try {
    await api('/admin/dishes/' + id, { method: 'DELETE' });
    toast('菜品已删除');
    loadAdminDishes();
  } catch (e) { toast('删除失败'); }
}

async function toggleDishStatus(id, status) {
  try {
    await adminApi.updateDish(id, { status: status === 'active' ? 'inactive' : 'active' });
    toast('状态已更新');
    loadAdminDishes();
  } catch (e) { toast('操作失败'); }
}

function showAdminDishModal(id) {
  const dish = id ? adminDishes.find(d => d.id === id) : null;
  const cats = window._adminCategories || [];
  document.getElementById('dish-form').innerHTML = `
    <div class="form-group">
      <label>菜品名称</label>
      <input class="form-input" id="f-dish-name" value="${dish ? dish.name : ''}">
    </div>
    <div class="form-group">
      <label>价格</label>
      <input class="form-input" id="f-dish-price" type="number" step="0.01" value="${dish && dish.price ? dish.price : ''}">
    </div>
    <div class="form-group">
      <label>图片</label>
      <div style="display:flex;gap:8px;align-items:center">
        <input class="form-input" id="f-dish-image" placeholder="图片URL或上传" value="${dish && dish.image_url || ''}" style="flex:1">
        <button class="btn btn-small btn-primary" onclick="uploadDishImage()" style="flex-shrink:0">上传</button>
      </div>
      <div id="dish-image-preview" style="margin-top:8px;display:none">
        <img id="dish-image-img" style="max-width:100%;max-height:120px;border-radius:8px">
      </div>
    </div>
    <div class="form-group">
      <label>分类</label>
      <div style="display:flex;gap:8px">
        <select class="form-select" id="f-dish-cat" style="flex:1">
          <option value="">无分类</option>
          ${cats.map(c => `<option value="${c.id}" ${dish && dish.category_id === c.id ? 'selected' : ''}>${c.name}</option>`).join('')}
        </select>
        <button class="btn btn-small btn-primary" onclick="showAddCategoryInModal()" style="flex-shrink:0;width:36px;height:36px;border-radius:50%;font-size:20px;padding:0">+</button>
      </div>
    </div>
    <div class="form-group">
      <label>描述</label>
      <textarea class="form-textarea" id="f-dish-desc">${dish ? dish.description || '' : ''}</textarea>
    </div>
    <div class="form-group">
      <label>材料 <span style="font-size:12px;color:var(--text-secondary)">（可多选）</span></label>
      <div id="dish-material-select" style="max-height:160px;overflow-y:auto;border:1px solid #eee;border-radius:8px;padding:8px"></div>
    </div>
  `;
  window._editDishId = id || null;
  window._selectedMaterials = dish && dish.materials ? dish.materials.map(m => m.id) : [];
  loadDishMaterials();
  document.getElementById('dish-modal-title').textContent = id ? '编辑菜品' : '新增菜品';
  document.getElementById('dish-modal').classList.remove('hidden');
}

// Image preview on URL input
document.addEventListener('input', function(e) {
  if (e.target && e.target.id === 'f-dish-image') {
    const val = e.target.value.trim();
    const preview = document.getElementById('dish-image-preview');
    const img = document.getElementById('dish-image-img');
    if (val && (val.startsWith('http') || val.startsWith('/static'))) {
      preview.style.display = '';
      img.src = val;
    } else {
      preview.style.display = 'none';
    }
  }
});

async function uploadDishImage() {
  const input = document.createElement('input');
  input.type = 'file';
  input.accept = 'image/jpeg,image/png,image/gif,image/webp';
  input.onchange = async function(e) {
    const file = e.target.files[0];
    if (!file) return;
    if (file.size > 5 * 1024 * 1024) { toast('图片不能超过 5MB'); return; }

    const formData = new FormData();
    formData.append('file', file);
    const token = localStorage.getItem('token');
    const res = await fetch(window.location.origin + '/api/v1/admin/upload', {
      method: 'POST',
      headers: { 'Authorization': 'Bearer ' + token },
      body: formData,
    });
    const data = await res.json();
    if (!res.ok || data.code >= 400) { toast(data.message || '上传失败'); return; }

    document.getElementById('f-dish-image').value = data.data.url;
    // Show preview
    const preview = document.getElementById('dish-image-preview');
    const img = document.getElementById('dish-image-img');
    preview.style.display = '';
    img.src = data.data.url;
    toast('上传成功');
  };
  input.click();
}

async function showAddCategoryInModal() {
  const name = prompt('请输入新分类名称：');
  if (!name || !name.trim()) return;
  try {
    await adminApi.createCategory({ name: name.trim() });
    toast('分类已创建');
    // Refresh categories and re-show modal
    const catRes = await adminApi.getCategories();
    window._adminCategories = catRes.data || [];
    // Re-populate the dish modal with updated categories
    const cats = window._adminCategories;
    const sel = document.getElementById('f-dish-cat');
    if (sel) {
      const currentVal = sel.value;
      sel.innerHTML = '<option value="">无分类</option>' +
        cats.map(c => `<option value="${c.id}">${c.name}</option>`).join('');
      sel.value = currentVal;
    }
  } catch (e) { toast('创建失败: ' + e.message); }
}

let _allMaterials = [];

async function loadDishMaterials(filter = '') {
  try {
    if (!_allMaterials.length) {
      const res = await adminApi.getMaterials();
      _allMaterials = res.data || [];
    }
    const el = document.getElementById('dish-material-select');
    if (!el) return;
    const selected = window._selectedMaterials || [];
    const filtered = filter ? _allMaterials.filter(m => m.name.includes(filter)) : _allMaterials;
    el.innerHTML = `
      <div style="margin-bottom:8px">
        <input class="form-input" placeholder="搜索材料..." oninput="loadDishMaterials(this.value)" style="font-size:13px;padding:6px 10px">
      </div>
      ${filtered.map(m => `
        <label style="display:flex;align-items:center;gap:8px;padding:6px 4px;font-size:14px;cursor:pointer;border-bottom:1px solid #f5f5f5">
          <input type="checkbox" value="${m.id}" ${selected.includes(m.id) ? 'checked' : ''} onchange="toggleDishMaterial(${m.id}, this.checked)">
          <span>${m.name}</span>
          <span style="font-size:11px;color:var(--text-secondary);margin-left:auto">${m.category || ''}</span>
        </label>
      `).join('')}
      ${filtered.length === 0 ? '<div style="padding:12px;text-align:center;color:var(--text-secondary);font-size:13px">无匹配材料</div>' : ''}
    `;
  } catch (e) { console.error(e); }
}

function toggleDishMaterial(id, checked) {
  if (!window._selectedMaterials) window._selectedMaterials = [];
  if (checked) {
    if (!window._selectedMaterials.includes(id)) window._selectedMaterials.push(id);
  } else {
    window._selectedMaterials = window._selectedMaterials.filter(i => i !== id);
  }
}

async function saveDish() {
  const data = {
    name: document.getElementById('f-dish-name').value,
    price: document.getElementById('f-dish-price').value ? Number(document.getElementById('f-dish-price').value) : null,
    image_url: document.getElementById('f-dish-image').value.trim() || null,
    category_id: document.getElementById('f-dish-cat').value ? Number(document.getElementById('f-dish-cat').value) : null,
    description: document.getElementById('f-dish-desc').value || null,
    material_ids: window._selectedMaterials || [],
  };
  if (!data.name.trim()) { toast('请输入名称'); return; }
  try {
    if (window._editDishId) {
      await adminApi.updateDish(window._editDishId, data);
    } else {
      await adminApi.createDish(data);
    }
    document.getElementById('dish-modal').classList.add('hidden');
    toast('保存成功');
    loadAdminDishes();
  } catch (e) { toast('保存失败: ' + e.message); }
}

// Admin Orders
let adminOrders = [];
let adminOrderSearch = '';

async function loadAdminOrders() {
  try {
    const apiCall = window._isAdmin ? adminApi.getOrders : adminApi.getChefOrders;
    const res = await apiCall({ page_size: 100 });
    adminOrders = res.data.items || [];
    renderAdminOrders();
  } catch (e) { console.error(e); }
}

function searchAdminOrders() {
  adminOrderSearch = (document.getElementById('order-search').value || '').trim();
  renderAdminOrders();
}

function renderAdminOrders() {
  const el = document.getElementById('admin-order-list');
  if (!el) return;
  const filtered = adminOrderSearch
    ? adminOrders.filter(o => (o.order_no || '').includes(adminOrderSearch))
    : adminOrders;
  el.innerHTML = (filtered.length === 0 ? '<div class="text-secondary text-center" style="padding:40px">无匹配订单</div>'
  : filtered.map(o => `
    <div class="card" style="padding:12px">
      ${window._isAdmin ? `<label style="float:right"><input type="checkbox" class="order-checkbox" value="${o.id}"></label>` : ''}
      <div class="flex-between">
        <span class="text-secondary" style="font-size:13px">${o.order_no}</span>
        <span style="font-size:13px;font-weight:500;color:var(--${o.status === 'pending' ? 'orange' : o.status === 'completed' ? 'green' : 'blue'})">${orderStatusText(o.status)}</span>
      </div>
      <div class="flex-between mt-8" style="font-size:13px">
        <span>¥${o.total_price}</span>
        <span class="text-secondary">${o.item_count || 0}道菜</span>
      </div>
      <div class="mt-8" style="display:flex;gap:6px;flex-wrap:wrap">
        ${o.status === 'pending' ? `<button class="btn btn-small btn-primary" onclick="adminUpdateOrder(${o.id},'confirmed')">确认</button><button class="btn btn-small btn-outline" onclick="adminUpdateOrder(${o.id},'cancelled')">取消</button>` : ''}
        ${o.status === 'confirmed' ? `<button class="btn btn-small btn-primary" onclick="adminUpdateOrder(${o.id},'preparing')">制作</button>` : ''}
        ${o.status === 'preparing' ? `<button class="btn btn-small btn-primary" onclick="adminUpdateOrder(${o.id},'completed')">完成</button>` : ''}
        ${window._isAdmin ? `<button class="btn btn-small btn-outline" style="color:var(--red);border-color:var(--red)" onclick="adminDeleteOrder(${o.id})">删除</button>` : ''}
      </div>
    </div>
  `).join(''));
}

async function adminUpdateOrder(id, status) {
  try {
    await adminApi.updateOrderStatus(id, status);
    toast('状态已更新');
    loadAdminOrders();
  } catch (e) { toast('操作失败'); }
}

async function adminDeleteOrder(id) {
  if (!confirm('确定要删除此订单吗？')) return;
  try {
    await adminApi.deleteOrder(id);
    toast('订单已删除');
    loadAdminOrders();
  } catch (e) { toast('删除失败'); }
}

function getSelectedIds(className) {
  return Array.from(document.querySelectorAll('.' + className + ':checked')).map(cb => Number(cb.value));
}

async function batchDeleteSelectedOrders() {
  const ids = getSelectedIds('order-checkbox');
  if (!ids.length) { toast('请先勾选要删除的订单'); return; }
  if (!confirm('确定要删除选中的 ' + ids.length + ' 个订单吗？')) return;
  try {
    await adminApi.batchDeleteOrders(ids);
    toast('批量删除成功');
    loadAdminOrders();
  } catch (e) { toast('删除失败'); }
}

// Admin Pending
let pendingDishes = [];

async function loadAdminPending() {
  try {
    const res = await adminApi.getPendingDishes({ page_size: 50 });
    pendingDishes = res.data.items || [];
    renderAdminPending();
  } catch (e) { console.error(e); }
}

function renderAdminPending() {
  const el = document.getElementById('admin-pending-list');
  if (!el) return;
  el.innerHTML = pendingDishes.map(d => `
    <div class="card">
      <div class="flex-between">
        <strong>${d.name}</strong>
        <span style="font-size:12px;padding:2px 8px;border-radius:4px;background:${d.status === 'pending_price' ? '#fdf6ec' : d.status === 'approved' ? '#f0f9eb' : '#fef0f0'};color:${d.status === 'pending_price' ? '#e6a23c' : d.status === 'approved' ? '#67c23a' : '#f56c6c'}">
          ${d.status === 'pending_price' ? '待审核' : d.status === 'approved' ? '已通过' : '已驳回'}
        </span>
      </div>
      ${d.description ? `<div class="text-secondary mt-8">${d.description}</div>` : ''}
      ${d.suggested_price ? `<div class="text-secondary mt-8">建议价: ¥${d.suggested_price}</div>` : ''}
      ${d.status === 'pending_price' ? `
        <div class="mt-8" style="display:flex;gap:8px">
          <button class="btn btn-small btn-primary" onclick="showReviewModal(${d.id}, '${d.name}')">审核通过</button>
          <button class="btn btn-small btn-outline" onclick="rejectPending(${d.id})">驳回</button>
        </div>
      ` : ''}
      ${d.admin_price ? `<div class="mt-8" style="color:var(--green)">定价: ¥${d.admin_price}</div>` : ''}
    </div>
  `).join('');
}

function showReviewModal(id, name) {
  const cats = window._adminCategories || [];
  document.getElementById('review-form').innerHTML = `
    <div style="margin-bottom:12px;font-weight:500">审核: ${name}</div>
    <div class="form-group">
      <label>定价（必填）</label>
      <input class="form-input" id="f-review-price" type="number" step="0.01">
    </div>
    <div class="form-group">
      <label>分配分类</label>
      <select class="form-select" id="f-review-cat">
        <option value="">无分类</option>
        ${cats.map(c => `<option value="${c.id}">${c.name}</option>`).join('')}
      </select>
    </div>
    <div class="form-group">
      <label>备注</label>
      <textarea class="form-textarea" id="f-review-note"></textarea>
    </div>
  `;
  window._reviewId = id;
  document.getElementById('review-modal').classList.remove('hidden');
}

async function submitReview() {
  const price = document.getElementById('f-review-price').value;
  if (!price) { toast('请设置定价'); return; }
  try {
    await adminApi.reviewPendingDish(window._reviewId, {
      status: 'approved',
      admin_price: Number(price),
      admin_note: document.getElementById('f-review-note').value || null,
      category_id: document.getElementById('f-review-cat').value ? Number(document.getElementById('f-review-cat').value) : null,
    });
    document.getElementById('review-modal').classList.add('hidden');
    toast('审核通过');
    loadAdminPending();
  } catch (e) { toast('操作失败'); }
}

async function rejectPending(id) {
  if (!confirm('确定驳回吗？')) return;
  try {
    await adminApi.reviewPendingDish(id, { status: 'rejected', admin_note: '已驳回' });
    toast('已驳回');
    loadAdminPending();
  } catch (e) { toast('操作失败'); }
}

// Admin Materials
let adminMaterials = [];
let adminMatSearch = '';

async function loadAdminMaterials() {
  try {
    const res = await adminApi.getMaterials();
    adminMaterials = res.data || [];
    renderAdminMaterials();
  } catch (e) { console.error(e); }
}

function searchAdminMaterials() {
  adminMatSearch = (document.getElementById('material-search').value || '').trim();
  renderAdminMaterials();
}

function renderAdminMaterials() {
  const el = document.getElementById('admin-material-list');
  if (!el) return;
  const filtered = adminMatSearch
    ? adminMaterials.filter(m => m.name.includes(adminMatSearch))
    : adminMaterials;
  if (filtered.length === 0) {
    el.innerHTML = '<div class="text-secondary text-center" style="padding:40px">' + (adminMatSearch ? '无匹配材料' : '暂无材料') + '</div>';
    return;
  }
  const groups = {};
  filtered.forEach(m => {
    const key = m.category || '未分类';
    if (!groups[key]) groups[key] = [];
    groups[key].push(m);
  });
  el.innerHTML = Object.entries(groups).map(([key, list]) => `
    <div style="margin-bottom:12px">
      <div style="font-weight:600;font-size:14px;margin-bottom:6px;padding-left:8px;border-left:3px solid var(--green)">${key}</div>
      ${list.map(m => `
        <div class="card" style="padding:8px 12px;display:flex;align-items:center;justify-content:space-between;margin-bottom:4px">
          <label style="display:flex;align-items:center;gap:8px;flex:1;cursor:pointer">
            <input type="checkbox" class="material-checkbox" value="${m.id}">
            <span>${m.name}</span>
            ${m.is_allergen ? '<span style="font-size:10px;color:var(--red);padding:1px 4px;background:#fef0f0;border-radius:3px">过敏原</span>' : ''}
          </label>
          <div style="display:flex;gap:4px">
            <button class="btn btn-small btn-outline" style="font-size:11px;padding:2px 8px" onclick="showEditMaterialModal(${m.id})">编辑</button>
            <button class="btn btn-small btn-outline" style="color:var(--red);border-color:var(--red);font-size:11px;padding:2px 8px" onclick="adminDeleteMaterial(${m.id})">删</button>
          </div>
        </div>
      `).join('')}
    </div>
  `).join('');
}

async function batchDeleteSelectedMaterials() {
  const ids = getSelectedIds('material-checkbox');
  if (!ids.length) { toast('请先勾选要删除的材料'); return; }
  if (!confirm('确定要删除选中的 ' + ids.length + ' 个材料吗？')) return;
  try {
    await adminApi.batchDeleteMaterials(ids);
    toast('批量删除成功');
    loadAdminMaterials();
  } catch (e) { toast('删除失败'); }
}

function showAddMaterialModal() {
  window._editMaterialId = null;
  document.getElementById('material-modal-title').textContent = '新增材料';
  document.getElementById('f-mat-name').value = '';
  document.getElementById('f-mat-category').value = '';
  document.getElementById('f-mat-allergen').checked = false;
  document.getElementById('material-modal').classList.remove('hidden');
}

async function showEditMaterialModal(id) {
  try {
    const res = await adminApi.getMaterials();
    const mat = (res.data || []).find(m => m.id === id);
    if (!mat) return;
    window._editMaterialId = id;
    document.getElementById('material-modal-title').textContent = '编辑材料';
    document.getElementById('f-mat-name').value = mat.name;
    document.getElementById('f-mat-category').value = mat.category || '';
    document.getElementById('f-mat-allergen').checked = mat.is_allergen;
    document.getElementById('material-modal').classList.remove('hidden');
  } catch (e) { toast('加载失败'); }
}

async function saveMaterial() {
  const name = document.getElementById('f-mat-name').value.trim();
  if (!name) { toast('请输入材料名称'); return; }
  const data = {
    name,
    category: document.getElementById('f-mat-category').value || null,
    is_allergen: document.getElementById('f-mat-allergen').checked,
  };
  try {
    if (window._editMaterialId) {
      await adminApi.updateMaterial(window._editMaterialId, data);
    } else {
      await adminApi.createMaterial(data);
    }
    document.getElementById('material-modal').classList.add('hidden');
    toast('保存成功');
    loadAdminMaterials();
  } catch (e) { toast('保存失败: ' + e.message); }
}

async function adminDeleteMaterial(id) {
  if (!confirm('确定要删除此材料吗？')) return;
  try {
    await adminApi.deleteMaterial(id);
    toast('材料已删除');
    loadAdminMaterials();
  } catch (e) { toast('删除失败'); }
}

// Admin Categories
async function loadAdminCategories() {
  try {
    const res = await adminApi.getCategories();
    const cats = res.data || [];
    const el = document.getElementById('admin-category-list');
    if (!el) return;
    el.innerHTML = cats.map(c => `
      <div class="card" style="display:flex;align-items:center;justify-content:space-between;padding:10px 16px;margin-bottom:6px">
        <span style="font-weight:500">${c.name}</span>
        <button class="btn btn-small btn-outline" style="color:var(--red);border-color:var(--red);font-size:12px;padding:2px 10px" onclick="adminDeleteCategory(${c.id})">删除</button>
      </div>
    `).join('');
  } catch (e) { console.error(e); }
}

async function adminAddCategory() {
  const name = document.getElementById('new-cat-name').value.trim();
  if (!name) { toast('请输入分类名称'); return; }
  try {
    await adminApi.createCategory({ name });
    document.getElementById('new-cat-name').value = '';
    toast('分类已创建');
    loadAdminCategories();
    loadCategories();
  } catch (e) { toast('创建失败: ' + e.message); }
}

async function adminDeleteCategory(id) {
  if (!confirm('确定要删除此分类吗？')) return;
  try {
    await adminApi.deleteCategory(id);
    toast('分类已删除');
    loadAdminCategories();
    loadCategories();
  } catch (e) { toast('删除失败'); }
}

async function adminDeleteUser(id) {
  if (!confirm('确定要删除此用户吗？')) return;
  try {
    await adminApi.deleteUser(id);
    toast('用户已删除');
    loadAdminUsers();
  } catch (e) { toast('删除失败: ' + e.message); }
}

// Admin Users
let adminUsers = [];
let adminUserSearch = '';

async function loadAdminUsers() {
  try {
    const res = await adminApi.getUsers({ page_size: 100 });
    adminUsers = res.data.items || [];
    renderAdminUsers();
  } catch (e) { console.error(e); }
}

function searchAdminUsers() {
  adminUserSearch = (document.getElementById('user-search').value || '').trim();
  renderAdminUsers();
}

function renderAdminUsers() {
  const el = document.getElementById('admin-user-list');
  if (!el) return;
  const filtered = adminUserSearch
    ? adminUsers.filter(u => (u.username || '').includes(adminUserSearch) || (u.nickname || '').includes(adminUserSearch))
    : adminUsers;
  el.innerHTML = (filtered.length === 0 ? '<div class="text-secondary text-center" style="padding:40px">无匹配用户</div>'
  : filtered.map(u => `
    <div class="card" style="padding:12px">
      <label style="float:right"><input type="checkbox" class="user-checkbox" value="${u.id}"></label>
      <div class="flex-between">
        <div>
          <strong>${u.nickname || u.username}</strong>
          <span style="font-size:12px;margin-left:6px;color:var(--text-secondary)">@${u.username}</span>
        </div>
        <span style="font-size:12px;padding:2px 8px;border-radius:4px;background:${u.role === 'admin' ? '#fef0f0' : u.role === 'chef' ? '#fdf6ec' : '#f0f9eb'};color:${u.role === 'admin' ? '#f56c6c' : u.role === 'chef' ? '#e6a23c' : '#67c23a'}">
          ${u.role === 'admin' ? '管理员' : u.role === 'chef' ? '厨师' : '点餐用户'}
        </span>
      </div>
      <div class="text-secondary mt-8" style="font-size:13px">${u.is_active ? '正常' : '已禁用'}</div>
    </div>
  `).join(''));
}

async function batchDeleteSelectedUsers() {
  const ids = getSelectedIds('user-checkbox');
  if (!ids.length) { toast('请先勾选要删除的用户'); return; }
  if (!confirm('确定要删除选中的 ' + ids.length + ' 个用户吗？')) return;
  try {
    await adminApi.batchDeleteUsers(ids);
    toast('批量删除成功');
    loadAdminUsers();
  } catch (e) { toast('删除失败: ' + e.message); }
}

function showAddUserModal() {
  document.getElementById('user-modal-title').textContent = '新增用户';
  document.getElementById('f-user-username').value = '';
  document.getElementById('f-user-password').value = '';
  document.getElementById('f-user-nickname').value = '';
  document.getElementById('f-user-role').value = 'user';
  window._editUserId = null;
  document.getElementById('user-modal').classList.remove('hidden');
}

async function saveUser() {
  const username = document.getElementById('f-user-username').value.trim();
  const password = document.getElementById('f-user-password').value;
  if (!username || !password) { toast('请填写用户名和密码'); return; }
  try {
    await adminApi.createUser({
      username,
      password,
      nickname: document.getElementById('f-user-nickname').value.trim() || null,
      role: document.getElementById('f-user-role').value,
    });
    document.getElementById('user-modal').classList.add('hidden');
    toast('用户创建成功');
    loadAdminUsers();
  } catch (e) { toast('创建失败: ' + e.message); }
}

// Navigation for admin tabs
function switchAdminTab(tab) {
  document.querySelectorAll('.admin-tab').forEach(t => t.style.display = 'none');
  document.getElementById('admin-tab-' + tab).style.display = 'block';
  document.querySelectorAll('.admin-nav .category-tab').forEach(t => {
    t.classList.toggle('active', t.dataset.tab === tab);
  });
  if (tab === 'dishes') loadAdminDishes();
  if (tab === 'categories') loadAdminCategories();
  if (tab === 'orders') loadAdminOrders();
  if (tab === 'pending') loadAdminPending();
  if (tab === 'users') loadAdminUsers();
  if (tab === 'materials') loadAdminMaterials();
}

// ==================== Init ====================
document.addEventListener('DOMContentLoaded', async () => {
  const { token } = await checkLogin();
  if (token) {
    updateUserUI();
  }
  initApp();
});
