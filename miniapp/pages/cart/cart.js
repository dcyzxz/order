const { menuApi } = require('../../utils/api')

Page({
  data: {
    cartItems: [],
    materials: [],
    totalPriceText: '¥0.00',
  },

  onShow() {
    this.loadCart()
    this.loadMaterials()
  },

  loadCart() {
    const app = getApp()
    const items = app.getCart()
    const total = items.reduce((sum, item) => sum + (item.price || 0) * item.quantity, 0)
    this.setData({ cartItems: items, totalPriceText: '¥' + total.toFixed(2) })
  },

  async loadMaterials() {
    try {
      const res = await menuApi.getMaterials()
      this.setData({ materials: res.data || [] })
    } catch (e) { console.error(e) }
  },

  saveAndRefresh() {
    const app = getApp()
    app.setCart(this.data.cartItems)
    this.loadCart()
  },

  increment(e) {
    const idx = e.currentTarget.dataset.index
    if (this.data.cartItems[idx].quantity < 100) {
      this.data.cartItems[idx].quantity += 1
      this.saveAndRefresh()
    }
  },

  decrement(e) {
    const idx = e.currentTarget.dataset.index
    if (this.data.cartItems[idx].quantity > 1) {
      this.data.cartItems[idx].quantity -= 1
      this.saveAndRefresh()
    }
  },

  removeItem(e) {
    const idx = e.currentTarget.dataset.index
    wx.showModal({
      title: '提示',
      content: '确定要删除这个菜品吗？',
      success: (res) => {
        if (res.confirm) {
          this.data.cartItems.splice(idx, 1)
          this.saveAndRefresh()
        }
      },
    })
  },

  goToMenu() {
    wx.switchTab({ url: '/pages/menu/menu' })
  },

  goToCheckout() {
    const app = getApp()
    if (!app.isLoggedIn()) {
      wx.showToast({ title: '请先登录', icon: 'none' })
      return
    }
    wx.navigateTo({ url: '/pages/orders/create/create' })
  },
})
