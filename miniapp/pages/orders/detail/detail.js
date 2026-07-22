const { orderApi } = require('../../../utils/api')
const { getOrderStatusText } = require('../../../utils/util')

Page({
  data: {
    order: { items: [] },
  },

  onLoad(options) {
    if (options.id) this.loadOrder(options.id)
  },

  async loadOrder(id) {
    try {
      const res = await orderApi.getOrderDetail(id)
      const order = res.data
      if (order.items) {
        order.items = order.items.map(item => ({
          ...item,
          subtotal: '¥' + (item.unitPrice * item.quantity).toFixed(2),
        }))
      }
      this.setData({ order })
    } catch (e) {
      console.error(e)
      wx.showToast({ title: '订单不存在', icon: 'none' })
      setTimeout(() => wx.navigateBack(), 1500)
    }
  },

  statusText(status) {
    return getOrderStatusText(status)
  },

  cancelOrder() {
    wx.showModal({
      title: '提示',
      content: '确定要取消这个订单吗？',
      success: async (res) => {
        if (res.confirm) {
          try {
            await orderApi.cancelOrder(this.data.order.id)
            wx.showToast({ title: '订单已取消' })
            this.loadOrder(this.data.order.id)
          } catch (e) { console.error(e) }
        }
      },
    })
  },
})
