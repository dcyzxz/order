const { adminApi } = require('../../../utils/api')

Page({
  data: {
    materials: [],
    groups: [],
    showEditModal: false,
    editId: null,
    form: { name: '', category: '', description: '', isAllergen: false },
  },

  onShow() { this.loadMaterials() },

  async loadMaterials() {
    try {
      const res = await adminApi.getMaterials()
      const list = res.data || []
      const map = {}
      list.forEach(m => {
        const key = m.category || '未分类'
        if (!map[key]) map[key] = []
        map[key].push(m)
      })
      const groups = Object.entries(map).map(([key, list]) => ({ key, list }))
      this.setData({ materials: list, groups })
    } catch (e) { console.error(e) }
  },

  showAddDialog() {
    this.setData({ showEditModal: true, editId: null, form: { name: '', category: '', description: '', isAllergen: false } })
  },

  showEditDialog(e) {
    const item = e.currentTarget.dataset.item
    this.setData({
      showEditModal: true,
      editId: item.id,
      form: { name: item.name, category: item.category || '', description: item.description || '', isAllergen: item.isAllergen },
    })
  },

  closeEdit() { this.setData({ showEditModal: false }) },
  stopPropagation() {},
  onNameInput(e) { this.setData({ 'form.name': e.detail.value }) },
  onCategoryInput(e) { this.setData({ 'form.category': e.detail.value }) },
  onDescInput(e) { this.setData({ 'form.description': e.detail.value }) },
  onAllergenChange(e) { this.setData({ 'form.isAllergen': e.detail.value.length > 0 }) },

  async saveMaterial() {
    if (!this.data.form.name.trim()) { wx.showToast({ title: '请输入名称', icon: 'none' }); return }
    const payload = {
      name: this.data.form.name,
      category: this.data.form.category || null,
      description: this.data.form.description || null,
      is_allergen: this.data.form.isAllergen,
    }
    try {
      if (this.data.editId) {
        await adminApi.updateMaterial(this.data.editId, payload)
        wx.showToast({ title: '更新成功' })
      } else {
        await adminApi.createMaterial(payload)
        wx.showToast({ title: '创建成功' })
      }
      this.setData({ showEditModal: false })
      this.loadMaterials()
    } catch (e) { console.error(e) }
  },
})
