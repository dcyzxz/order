const { adminApi } = require('../../../utils/api')
const { getPendingStatusText } = require('../../../utils/util')

Page({
  data: {
    pendingList: [],
    categories: [],
    filterStatus: null,
    page: 1, pageSize: 20, loading: false, hasMore: true,
    showReviewModal: false,
    reviewId: null,
    reviewName: '',
    reviewForm: { price: '', note: '', categoryName: '', categoryId: null },
  },

  onShow() {
    this.loadCategories()
    this.loadPending(true)
  },
  onReachBottom() {
    if (this.data.hasMore && !this.data.loading) this.loadPending()
  },

  async loadCategories() {
    try { const res = await adminApi.getCategories(); this.setData({ categories: res.data || [] }) }
    catch (e) { console.error(e) }
  },

  async loadPending(refresh) {
    if (refresh) { this.data.page = 1; this.data.hasMore = true }
    if (this.data.loading || !this.data.hasMore) return
    this.setData({ loading: true })
    try {
      const res = await adminApi.getPendingDishes({ status: this.data.filterStatus, page: this.data.page, page_size: this.data.pageSize })
      const d = res.data
      this.setData({
        pendingList: refresh ? d.items : this.data.pendingList.concat(d.items),
        hasMore: this.data.page < d.total_pages,
      })
      this.data.page += 1
    } catch (e) { console.error(e) }
    finally { this.setData({ loading: false }) }
  },

  onFilterChange(e) {
    this.data.filterStatus = e.currentTarget.dataset.status
    this.loadPending(true)
  },

  showReviewDialog(e) {
    const { id, name } = e.currentTarget.dataset
    this.setData({
      showReviewModal: true,
      reviewId: id,
      reviewName: name,
      reviewForm: { price: '', note: '', categoryName: '', categoryId: null },
    })
  },

  closeReview() { this.setData({ showReviewModal: false }) },
  stopPropagation() {},
  onReviewPriceInput(e) { this.setData({ 'reviewForm.price': e.detail.value }) },
  onReviewNoteInput(e) { this.setData({ 'reviewForm.note': e.detail.value }) },

  onReviewCategoryChange(e) {
    const idx = e.detail.value
    const cat = this.data.categories[idx]
    if (cat) this.setData({ 'reviewForm.categoryName': cat.name, 'reviewForm.categoryId': cat.id })
  },

  async submitReview() {
    if (!this.data.reviewForm.price) { wx.showToast({ title: '请设置定价', icon: 'none' }); return }
    try {
      await adminApi.reviewPendingDish(this.data.reviewId, {
        status: 'approved',
        admin_price: Number(this.data.reviewForm.price),
        admin_note: this.data.reviewForm.note || null,
        category_id: this.data.reviewForm.categoryId || null,
      })
      wx.showToast({ title: '审核通过' })
      this.setData({ showReviewModal: false })
      this.loadPending(true)
    } catch (e) { console.error(e) }
  },

  async reviewReject(e) {
    const id = e.currentTarget.dataset.id
    try {
      await adminApi.reviewPendingDish(id, { status: 'rejected', admin_note: '已驳回' })
      wx.showToast({ title: '已驳回' })
      this.loadPending(true)
    } catch (e) { console.error(e) }
  },

  statusText(s) { return getPendingStatusText(s) },
})
