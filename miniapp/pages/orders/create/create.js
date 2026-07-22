const { orderApi } = require('../../../utils/api')

Page({
  data: {
    cartItems: [],
    note: '',
    totalPriceText: '¥0.00',
    submitting: false,
  },

  onShow() {
    const app = getApp()
    const items = app.getCart()
    if (items.length === 0) {
      wx.showToast({ title: '购物车为空', icon: 'none' })
      setTimeout(() => wx.navigateBack(), 1000)
      return
    }
    // 为每个 item 添加格式化的小计
    const list = items.map(item => ({
      ...item,
      subtotal: '¥' + ((item.price || 0) * item.quantity).toFixed(2),
    }))
    const total = items.reduce((sum, item) => sum + (item.price || 0) * item.quantity, 0)
    this.setData({ cartItems: list, totalPriceText: '¥' + total.toFixed(2) })
  },

  onNoteInput(e) {
    this.setData({ note: e.detail.value })
  },

  async submitOrder() {
    if (this.data.submitting || this.data.cartItems.length === 0) return

    this.setData({ submitting: true })
    try {
      const items = this.data.cartItems.map(item => ({
        dish_id: item.dishId,
        quantity: item.quantity,
        excluded_material_ids: item.excludedMaterialIds || [],
      }))

      const res = await orderApi.createOrder({
        items,
        note: this.data.note || undefined,
      })

      getApp().setCart([])
      wx.showToast({ title: '下单成功！', icon: 'success' })
      wx.redirectTo({ url: '/pages/orders/detail/detail?id=' + res.data.id })
    } catch (e) {
      console.error('submit order fail', e)
    } finally {
      this.setData({ submitting: false })
    }
  },
})
