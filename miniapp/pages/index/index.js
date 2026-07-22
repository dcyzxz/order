const { menuApi, userApi } = require('../../utils/api')

Page({
  data: {
    userInfo: {},
    categories: [],
    recommendedDishes: [],
    isLoggedIn: false,
    isAdmin: false,
    hasUserInfo: false,
    showPendingModal: false,
    pendingForm: {
      name: '',
      description: '',
      price: '',
    },
  },

  onShow() {
    this.loadUserInfo()
    this.loadCategories()
    this.loadRecommendedDishes()
  },

  onPullDownRefresh() {
    Promise.all([
      this.loadCategories(),
      this.loadRecommendedDishes(),
    ]).then(() => wx.stopPullDownRefresh())
  },

  loadUserInfo() {
    const app = getApp()
    const user = app.globalData.userInfo
    this.setData({
      userInfo: user || {},
      isLoggedIn: app.isLoggedIn(),
      isAdmin: app.isAdmin(),
      hasUserInfo: !!user,
    })
  },

  async loadCategories() {
    try {
      const res = await menuApi.getCategories()
      this.setData({ categories: res.data || [] })
    } catch (e) { console.error('load categories fail', e) }
  },

  async loadRecommendedDishes() {
    try {
      const res = await menuApi.getDishes({ recommended: true, page_size: 10 })
      this.setData({ recommendedDishes: res.data?.items || [] })
    } catch (e) { console.error('load recommended fail', e) }
  },

  handleLogin() {
    const app = getApp()
    if (app.isLoggedIn()) return

    wx.login({
      success: async (loginRes) => {
        try {
          // 尝试获取用户信息（可能被拒绝）
          const userProfile = await wx.getUserProfile({ desc: '用于展示用户信息' })
          const result = await userApi.login(
            loginRes.code,
            userProfile.userInfo.nickName,
            userProfile.userInfo.avatarUrl,
          )
          app.setToken(result.access_token)
          app.setUserInfo(result.user)
          this.loadUserInfo()
          wx.showToast({ title: '登录成功' })
        } catch (e) {
          // 用户拒绝授权，静默登录
          try {
            const result = await userApi.login(loginRes.code)
            app.setToken(result.access_token)
            app.setUserInfo(result.user)
            this.loadUserInfo()
          } catch (err) {
            console.error('login fail', err)
          }
        }
      },
      fail: (err) => {
        console.error('wx.login fail', err)
        wx.showToast({ title: '登录失败', icon: 'none' })
      },
    })
  },

  showPendingDialog() {
    this.setData({ showPendingModal: true })
  },

  closePendingDialog() {
    this.setData({ showPendingModal: false })
  },

  stopPropagation() {},

  onPendingNameInput(e) {
    this.setData({ 'pendingForm.name': e.detail.value })
  },
  onPendingDescInput(e) {
    this.setData({ 'pendingForm.description': e.detail.value })
  },
  onPendingPriceInput(e) {
    this.setData({ 'pendingForm.price': e.detail.value })
  },

  async submitPendingDish() {
    const form = this.data.pendingForm
    if (!form.name.trim()) {
      wx.showToast({ title: '请输入菜品名称', icon: 'none' })
      return
    }
    try {
      await menuApi.submitPendingDish({
        name: form.name,
        description: form.description || undefined,
        suggested_price: form.price ? Number(form.price) : undefined,
      })
      this.setData({
        showPendingModal: false,
        pendingForm: { name: '', description: '', price: '' },
      })
      wx.showToast({ title: '提交成功，等待审核' })
    } catch (e) { console.error('submit fail', e) }
  },

  goToMenu() {
    wx.switchTab({ url: '/pages/menu/menu' })
  },

  goToDetail(e) {
    const id = e.currentTarget.dataset.id
    wx.navigateTo({ url: '/pages/menu/detail/detail?id=' + id })
  },

  goToCategory(e) {
    const id = e.currentTarget.dataset.id
    wx.switchTab({ url: '/pages/menu/menu?categoryId=' + id })
  },

  goToAdmin() {
    wx.navigateTo({ url: '/pages/admin/index' })
  },
})
