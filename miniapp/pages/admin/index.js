const { adminApi } = require('../../utils/api')

Page({
  data: {
    stats: null,
  },

  onShow() {
    this.checkAdmin()
    this.loadStats()
  },

  checkAdmin() {
    const app = getApp()
    if (!app.isAdmin()) {
      wx.showToast({ title: '权限不足', icon: 'none' })
      setTimeout(() => wx.navigateBack(), 1000)
    }
  },

  async loadStats() {
    try {
      const [dishesRes, pendingRes, ordersRes] = await Promise.all([
        adminApi.getDishes({ status: 'active', page_size: 1 }),
        adminApi.getPendingDishes({ status: 'pending_price', page_size: 1 }),
        adminApi.getOrders({ status: 'pending', page_size: 1 }),
      ])
      this.setData({
        stats: {
          activeDishCount: dishesRes.data?.total || 0,
          pendingCount: pendingRes.data?.total || 0,
          pendingOrderCount: ordersRes.data?.total || 0,
        },
      })
    } catch (e) { console.error(e) }
  },

  goToPage(e) {
    const url = e.currentTarget.dataset.url
    wx.navigateTo({ url })
  },
})
