const { adminApi } = require('../../../utils/api')
const { getDishStatusText } = require('../../../utils/util')

Page({
  data: {
    dishes: [],
    categories: [],
    filterStatus: null,
    page: 1, pageSize: 20, loading: false, hasMore: true,
    showEditModal: false,
    editId: null,
    form: { name: '', price: '', description: '', categoryName: '', categoryId: null },
  },

  onShow() {
    this.loadCategories()
    this.loadDishes(true)
  },
  onReachBottom() {
    if (this.data.hasMore && !this.data.loading) this.loadDishes()
  },

  async loadCategories() {
    try { const res = await adminApi.getCategories(); this.setData({ categories: res.data || [] }) }
    catch (e) { console.error(e) }
  },

  async loadDishes(refresh) {
    if (refresh) { this.data.page = 1; this.data.hasMore = true }
    if (this.data.loading || !this.data.hasMore) return
    this.setData({ loading: true })
    try {
      const res = await adminApi.getDishes({ status: this.data.filterStatus, page: this.data.page, page_size: this.data.pageSize })
      const d = res.data
      this.setData({
        dishes: refresh ? d.items : this.data.dishes.concat(d.items),
        hasMore: this.data.page < d.total_pages,
      })
      this.data.page += 1
    } catch (e) { console.error(e) }
    finally { this.setData({ loading: false }) }
  },

  onFilterChange(e) {
    const status = e.currentTarget.dataset.status
    this.data.filterStatus = status
    this.loadDishes(true)
  },

  showAddDialog() {
    this.setData({ showEditModal: true, editId: null, form: { name: '', price: '', description: '', categoryName: '', categoryId: null } })
  },

  showEditDialog(e) {
    const item = e.currentTarget.dataset.item
    this.setData({
      showEditModal: true,
      editId: item.id,
      form: {
        name: item.name,
        price: String(item.price || ''),
        description: item.description || '',
        categoryName: item.categoryName || '',
        categoryId: item.category_id,
      },
    })
  },

  closeEditDialog() { this.setData({ showEditModal: false }) },
  stopPropagation() {},
  onNameInput(e) { this.setData({ 'form.name': e.detail.value }) },
  onPriceInput(e) { this.setData({ 'form.price': e.detail.value }) },
  onDescInput(e) { this.setData({ 'form.description': e.detail.value }) },

  onCategoryChange(e) {
    const idx = e.detail.value
    const cat = this.data.categories[idx]
    if (cat) this.setData({ 'form.categoryName': cat.name, 'form.categoryId': cat.id })
  },

  async saveDish() {
    const f = this.data.form
    if (!f.name.trim()) { wx.showToast({ title: '请输入名称', icon: 'none' }); return }
    const payload = { name: f.name, price: f.price ? Number(f.price) : null, description: f.description || null, category_id: f.categoryId || null }
    try {
      if (this.data.editId) {
        await adminApi.updateDish(this.data.editId, payload)
        wx.showToast({ title: '更新成功' })
      } else {
        await adminApi.createDish(payload)
        wx.showToast({ title: '创建成功' })
      }
      this.setData({ showEditModal: false })
      this.loadDishes(true)
    } catch (e) { console.error(e) }
  },

  async toggleStatus(e) {
    const { id, status } = e.currentTarget.dataset
    const newStatus = status === 'active' ? 'inactive' : 'active'
    try {
      await adminApi.updateDish(id, { status: newStatus })
      wx.showToast({ title: newStatus === 'active' ? '已上架' : '已下架' })
      this.loadDishes(true)
    } catch (e) { console.error(e) }
  },

  statusText(s) { return getDishStatusText(s) },
})
