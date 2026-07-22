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
  login: (code, nickName, avatarUrl) => api('/users/login', { method: 'POST', data: { code, nick_name: nickName, avatar_url: avatarUrl } }),
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
  getCategories: () => api('/admin/categories'),
  createMaterial: (data) => api('/admin/materials', { method: 'POST', data }),
  updateMaterial: (id, data) => api('/admin/materials/' + id, { method: 'PUT', data }),
  getMaterials: () => api('/admin/materials'),
  getOrders: (params) => api('/admin/orders?' + new URLSearchParams(params)),
  updateOrderStatus: (id, status) => api('/admin/orders/' + id + '/status?new_status=' + status, { method: 'PUT' }),
  getPendingDishes: (params) => api('/admin/pending-dishes?' + new URLSearchParams(params)),
  reviewPendingDish: (id, data) => api('/admin/pending-dishes/' + id + '/review', { method: 'POST', data }),
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
  const code = 'web_' + Date.now();
  try {
    const res = await userApi.login(code, '用户' + String(Math.random()).slice(2, 6));
    localStorage.setItem('token', res.data.access_token);
    localStorage.setItem('user', JSON.stringify(res.data.user));
    updateUserUI();
    initApp();
    toast('登录成功');
  } catch (e) {
    toast('登录失败: ' + e.message);
  }
}

function updateUserUI() {
  const user = JSON.parse(localStorage.getItem('user') || 'null');
  document.getElementById('user-name').textContent = user ? user.nickname || '用户' : '未登录';
  document.getElementById('admin-link').style.display = user && user.is_admin ? '' : 'none';
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
    renderCategories();
  } catch (e) { console.error(e); }
}

function renderCategories() {
  const bar = document.getElementById('category-bar');
  bar.innerHTML = `
    <div class="category-tab ${activeCategory === null ? 'active' : ''}" onclick="switchCategory(null)">全部</div>
    ${allCategories.map(c => `
      <div class="category-tab ${activeCategory === c.id ? 'active' : ''}" onclick="switchCategory(${c.id})">${c.name}</div>
    `).join('')}
  `;
}

function switchCategory(id) {
  activeCategory = id;
  renderCategories();
  renderDishList();
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
  if (filtered.length === 0) {
    list.innerHTML = '<div class="text-center text-secondary" style="padding:60px 0">暂无菜品</div>';
    return;
  }
  list.innerHTML = filtered.map(d => `
    <div class="dish-card" onclick="showDishDetail(${d.id})">
      <div class="dish-img">🍽️</div>
      <div class="dish-info">
        <div class="dish-name">${d.name}</div>
        <div class="dish-desc">${d.category_name || ''}</div>
        <div class="dish-footer">
          <div class="dish-price">${d.price !== null ? '¥' + d.price : '待定价'}</div>
          <div class="dish-tags">${d.is_recommended ? '<span class="tag">推荐</span>' : ''}</div>
        </div>
      </div>
      <button class="add-cart-btn" onclick="event.stopPropagation(); quickAdd(${d.id})">+</button>
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

// Cart
function renderCart() {
  const items = getCart();
  const list = document.getElementById('cart-list');
  const total = items.reduce((s, i) => s + (i.price || 0) * i.quantity, 0);

  document.getElementById('cart-total').textContent = '¥' + total.toFixed(2);

  if (items.length === 0) {
    list.innerHTML = '<div class="cart-empty"><div class="empty-icon">🛒</div><div>购物车是空的</div></div>';
    document.getElementById('cart-bottom-bar').style.display = 'none';
    return;
  }
  document.getElementById('cart-bottom-bar').style.display = 'flex';
  list.innerHTML = items.map((item, idx) => `
    <div class="cart-item">
      <div class="ci-info">
        <div class="ci-name">${item.dishName}</div>
        ${item.excludedMaterialIds.length ? '<div class="ci-excluded">忌口: ' + item.excludedMaterialIds.length + '项</div>' : ''}
      </div>
      <div class="ci-price">¥${((item.price || 0) * item.quantity).toFixed(2)}</div>
      <div class="ci-qty">
        <button class="qty-btn" onclick="cartChangeQty(${idx}, -1)" ${item.quantity <= 1 ? 'disabled' : ''}>−</button>
        <span>${item.quantity}</span>
        <button class="qty-btn" onclick="cartChangeQty(${idx}, 1)">+</button>
      </div>
    </div>
  `).join('');
}

function cartChangeQty(idx, delta) {
  const cart = getCart();
  cart[idx].quantity += delta;
  if (cart[idx].quantity <= 0) cart.splice(idx, 1);
  setCart(cart);
  updateCartBadge();
  renderCart();
}

// Create Order
async function createOrder() {
  const cart = getCart();
  if (cart.length === 0) { toast('购物车为空'); return; }
  if (!localStorage.getItem('token')) { toast('请先登录'); return; }

  try {
    const items = cart.map(i => ({
      dish_id: i.dishId,
      quantity: i.quantity,
      excluded_material_ids: i.excludedMaterialIds || [],
    }));
    const res = await orderApi.createOrder({ items });
    setCart([]);
    updateCartBadge();
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
  loadAdminStats();
  loadAdminDishes();
  loadAdminOrders();
  loadAdminPending();
  loadAdminMaterials();
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

async function loadAdminDishes() {
  try {
    const res = await adminApi.getDishes({ page_size: 100 });
    adminDishes = res.data.items || [];
    renderAdminDishes();
    // Load categories for modal
    const catRes = await adminApi.getCategories();
    window._adminCategories = catRes.data || [];
  } catch (e) { console.error(e); }
}

function renderAdminDishes() {
  const el = document.getElementById('admin-dish-list');
  if (!el) return;
  el.innerHTML = adminDishes.map(d => `
    <div class="card">
      <div class="flex-between">
        <div>
          <strong>${d.name}</strong>
          <span class="text-secondary" style="margin-left:8px;font-size:12px">${dishStatusText(d.status)}</span>
        </div>
        <span style="color:var(--red)">${d.price !== null ? '¥' + d.price : '待定价'}</span>
      </div>
      <div class="flex-between mt-8">
        <span class="text-secondary">${d.category_name || ''}</span>
        <div class="gap-8" style="display:flex">
          <button class="btn btn-small btn-outline" onclick="showAdminDishModal(${d.id})">编辑</button>
          <button class="btn btn-small ${d.status === 'active' ? 'btn-danger' : 'btn-primary'}" onclick="toggleDishStatus(${d.id}, '${d.status}')">
            ${d.status === 'active' ? '下架' : '上架'}
          </button>
        </div>
      </div>
    </div>
  `).join('');
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
      <label>分类</label>
      <select class="form-select" id="f-dish-cat">
        <option value="">无分类</option>
        ${cats.map(c => `<option value="${c.id}" ${dish && dish.category_id === c.id ? 'selected' : ''}>${c.name}</option>`).join('')}
      </select>
    </div>
    <div class="form-group">
      <label>描述</label>
      <textarea class="form-textarea" id="f-dish-desc">${dish ? dish.description || '' : ''}</textarea>
    </div>
  `;
  window._editDishId = id || null;
  document.getElementById('dish-modal-title').textContent = id ? '编辑菜品' : '新增菜品';
  document.getElementById('dish-modal').classList.remove('hidden');
}

async function saveDish() {
  const data = {
    name: document.getElementById('f-dish-name').value,
    price: document.getElementById('f-dish-price').value ? Number(document.getElementById('f-dish-price').value) : null,
    category_id: document.getElementById('f-dish-cat').value ? Number(document.getElementById('f-dish-cat').value) : null,
    description: document.getElementById('f-dish-desc').value || null,
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

async function loadAdminOrders() {
  try {
    const res = await adminApi.getOrders({ page_size: 50 });
    adminOrders = res.data.items || [];
    renderAdminOrders();
  } catch (e) { console.error(e); }
}

function renderAdminOrders() {
  const el = document.getElementById('admin-order-list');
  if (!el) return;
  el.innerHTML = adminOrders.map(o => `
    <div class="card">
      <div class="flex-between">
        <span class="text-secondary">${o.order_no}</span>
        <span style="font-weight:500;color:var(--${o.status === 'pending' ? 'orange' : o.status === 'completed' ? 'green' : 'blue'})">${orderStatusText(o.status)}</span>
      </div>
      <div class="flex-between mt-8">
        <span>用户ID: ${o.user_id}</span>
        <span style="color:var(--red);font-weight:600">¥${o.total_price}</span>
      </div>
      <div class="mt-8" style="display:flex;gap:8px;flex-wrap:wrap">
        ${o.status === 'pending' ? `<button class="btn btn-small btn-primary" onclick="adminUpdateOrder(${o.id},'confirmed')">确认</button><button class="btn btn-small btn-danger" onclick="adminUpdateOrder(${o.id},'cancelled')">取消</button>` : ''}
        ${o.status === 'confirmed' ? `<button class="btn btn-small btn-primary" onclick="adminUpdateOrder(${o.id},'preparing')">开始制作</button>` : ''}
        ${o.status === 'preparing' ? `<button class="btn btn-small btn-primary" onclick="adminUpdateOrder(${o.id},'completed')">完成</button>` : ''}
      </div>
    </div>
  `).join('');
}

async function adminUpdateOrder(id, status) {
  try {
    await adminApi.updateOrderStatus(id, status);
    toast('状态已更新');
    loadAdminOrders();
  } catch (e) { toast('操作失败'); }
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
async function loadAdminMaterials() {
  try {
    const res = await adminApi.getMaterials();
    const mats = res.data || [];
    const groups = {};
    mats.forEach(m => {
      const key = m.category || '未分类';
      if (!groups[key]) groups[key] = [];
      groups[key].push(m);
    });
    const el = document.getElementById('admin-material-list');
    if (!el) return;
    el.innerHTML = Object.entries(groups).map(([key, list]) => `
      <div style="margin-bottom:16px">
        <div style="font-weight:600;font-size:15px;margin-bottom:8px;padding-left:8px;border-left:3px solid var(--green)">${key}</div>
        ${list.map(m => `
          <div class="card" style="padding:10px 12px;display:flex;align-items:center;justify-content:space-between">
            <span>${m.name} ${m.is_allergen ? '<span style="font-size:11px;color:var(--red)">⚠️ 过敏原</span>' : ''}</span>
            <span class="text-secondary">${m.description || ''}</span>
          </div>
        `).join('')}
      </div>
    `).join('');
  } catch (e) { console.error(e); }
}

// Navigation for admin tabs
function switchAdminTab(tab) {
  document.querySelectorAll('.admin-tab').forEach(t => t.style.display = 'none');
  document.getElementById('admin-tab-' + tab).style.display = 'block';
  document.querySelectorAll('.admin-nav .category-tab').forEach(t => {
    t.classList.toggle('active', t.dataset.tab === tab);
  });
  if (tab === 'dishes') loadAdminDishes();
  if (tab === 'orders') loadAdminOrders();
  if (tab === 'pending') loadAdminPending();
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
