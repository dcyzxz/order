const { orderApi } = require('../../utils/api')
const { getOrderStatusText } = require('../../utils/util')

Page({
  data: {
    orders: [],
    activeStatus: null,
    page: 1,
    pageSize: 20,
    loading: false,
    hasMore: true,
  },

  onShow() {
    this.loadOrders(true)
  },

  onReachBottom() {
    if (this.data.hasMore && !this.data.loading) this.loadOrders()
  },

  onPullDownRefresh() {
    this.loadOrders(true).then(() => wx.stopPullDownRefresh())
  },

  async loadOrders(refresh) {
    const app = getApp()
    if (!app.isLoggedIn()) {
      this.setData({ orders: [] })
      return
    }
    if (refresh) { this.data.page = 1; this.data.hasMore = true }
    if (this.data.loading || !this.data.hasMore) return

    this.setData({ loading: true })
    try {
      const res = await orderApi.getOrders({
        status: this.data.activeStatus,
        page: this.data.page,
        page_size: this.data.pageSize,
      })
      const data = res.data
      const list = refresh ? data.items : this.data.orders.concat(data.items)
      this.setData({
        orders: list,
        hasMore: this.data.page < data.total_pages,
      })
      this.data.page += 1
    } catch (e) { console.error(e) }
    finally { this.setData({ loading: false }) }
  },

  switchStatus(e) {
    const status = e.currentTarget.dataset.status
    this.data.activeStatus = status === 'null' ? null : status
    this.loadOrders(true)
  },

  statusText(status) {
    return getOrderStatusText(status)
  },

  goToDetail(e) {
    const id = e.currentTarget.dataset.id
    wx.navigateTo({ url: '/pages/orders/detail/detail?id=' + id })
  },
})
