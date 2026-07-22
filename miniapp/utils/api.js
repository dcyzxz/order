const CLOUD_ENV = 'prod-d8gcr6ggy9cd4d16c'
const SERVICE_NAME = 'django-sehm'
const API_PREFIX = '/api/v1'

// 通用请求封装（使用微信云托管 callContainer）
function request(path, options = {}) {
  const app = getApp()
  const token = app.globalData.token
  const header = {
    'X-WX-SERVICE': SERVICE_NAME,
    'Content-Type': 'application/json',
  }
  if (token) {
    header['Authorization'] = 'Bearer ' + token
  }

  return new Promise((resolve, reject) => {
    wx.cloud.callContainer({
      config: {
        env: CLOUD_ENV,
      },
      path: API_PREFIX + path,
      method: options.method || 'GET',
      header: header,
      data: options.data,
      success: (res) => {
        const data = res.data
        if (res.statusCode === 200 || res.statusCode === 201) {
          if (data.code === 200 || data.code === 201) {
            resolve(data)
          } else {
            wx.showToast({ title: data.message || '请求失败', icon: 'none' })
            reject(data)
          }
        } else if (res.statusCode === 401) {
          wx.removeStorageSync('token')
          wx.removeStorageSync('user')
          app.globalData.token = null
          app.globalData.userInfo = null
          wx.showToast({ title: '登录已过期，请重新登录', icon: 'none' })
          setTimeout(() => {
            wx.switchTab({ url: '/pages/index/index' })
          }, 1500)
          reject(data)
        } else {
          wx.showToast({ title: data?.message || '网络错误', icon: 'none' })
          reject(data)
        }
      },
      fail: (err) => {
        wx.showToast({ title: '网络请求失败: ' + (err.errMsg || ''), icon: 'none' })
        reject(err)
      },
    })
  })
}

// ==================== 用户相关 ====================
const userApi = {
  login(code, nickName, avatarUrl) {
    return request('/users/login', {
      method: 'POST',
      data: { code, nick_name: nickName, avatar_url: avatarUrl },
    })
  },
  getProfile() {
    return request('/users/me')
  },
  updateProfile(data) {
    return request('/users/me', { method: 'PUT', data })
  },
}

// ==================== 菜单相关 ====================
const menuApi = {
  getCategories() {
    return request('/menu/categories')
  },
  getDishes(params) {
    return request('/menu/dishes', { data: params })
  },
  getDishDetail(id) {
    return request('/menu/dishes/' + id)
  },
  getMaterials() {
    return request('/menu/materials')
  },
  submitPendingDish(data) {
    return request('/menu/pending-dishes', { method: 'POST', data })
  },
  getMyPendingDishes() {
    return request('/menu/pending-dishes')
  },
}

// ==================== 订单相关 ====================
const orderApi = {
  createOrder(data) {
    return request('/orders', { method: 'POST', data })
  },
  getOrders(params) {
    return request('/orders', { data: params })
  },
  getOrderDetail(id) {
    return request('/orders/' + id)
  },
  cancelOrder(id) {
    return request('/orders/' + id + '/cancel', { method: 'POST' })
  },
}

// ==================== 管理后台 ====================
const adminApi = {
  createDish(data) {
    return request('/admin/dishes', { method: 'POST', data })
  },
  updateDish(id, data) {
    return request('/admin/dishes/' + id, { method: 'PUT', data })
  },
  getDishes(params) {
    return request('/admin/dishes', { data: params })
  },
  createCategory(data) {
    return request('/admin/categories', { method: 'POST', data })
  },
  updateCategory(id, data) {
    return request('/admin/categories/' + id, { method: 'PUT', data })
  },
  getCategories() {
    return request('/admin/categories')
  },
  createMaterial(data) {
    return request('/admin/materials', { method: 'POST', data })
  },
  updateMaterial(id, data) {
    return request('/admin/materials/' + id, { method: 'PUT', data })
  },
  getMaterials() {
    return request('/admin/materials')
  },
  getOrders(params) {
    return request('/admin/orders', { data: params })
  },
  updateOrderStatus(orderId, status) {
    return request('/admin/orders/' + orderId + '/status?new_status=' + status, { method: 'PUT' })
  },
  getPendingDishes(params) {
    return request('/admin/pending-dishes', { data: params })
  },
  reviewPendingDish(id, data) {
    return request('/admin/pending-dishes/' + id + '/review', { method: 'POST', data })
  },
}

module.exports = {
  userApi,
  menuApi,
  orderApi,
  adminApi,
}
