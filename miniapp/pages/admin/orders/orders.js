const { adminApi } = require('../../../utils/api')
const { getOrderStatusText } = require('../../../utils/util')

Page({
  data: {
    orders: [],
    filterStatus: null,
    page: 1, pageSize: 20, loading: false, hasMore: true,
  },

  onShow() { this.loadOrders(true) },
  onReachBottom() {
    if (this.data.hasMore && !this.data.loading) this.loadOrders()
  },

  async loadOrders(refresh) {
    if (refresh) { this.data.page = 1; this.data.hasMore = true }
    if (this.data.loading || !this.data.hasMore) return
    this.setData({ loading: true })
    try {
      const res = await adminApi.getOrders({ status: this.data.filterStatus, page: this.data.page, page_size: this.data.pageSize })
      const d = res.data
      this.setData({
        orders: refresh ? d.items : this.data.orders.concat(d.items),
        hasMore: this.data.page < d.total_pages,
      })
      this.data.page += 1
    } catch (e) { console.error(e) }
    finally { this.setData({ loading: false }) }
  },

  async updateStatus(e) {
    const { id, status } = e.currentTarget.dataset
    try {
      await adminApi.updateOrderStatus(id, status)
      wx.showToast({ title: '状态已更新' })
      this.loadOrders(true)
    } catch (e) { console.error(e) }
  },

  statusText(s) { return getOrderStatusText(s) },
})
