const { menuApi } = require('../../utils/api')

Page({
  data: {
    categories: [],
    dishes: [],
    activeCategory: null,
    keyword: '',
    page: 1,
    pageSize: 20,
    loading: false,
    hasMore: true,
  },

  onLoad(options) {
    if (options.categoryId) {
      this.data.activeCategory = Number(options.categoryId)
    }
  },

  onShow() {
    this.loadCategories()
    this.loadDishes(true)
  },

  onReachBottom() {
    if (this.data.hasMore && !this.data.loading) {
      this.loadDishes()
    }
  },

  onPullDownRefresh() {
    this.loadDishes(true).then(() => wx.stopPullDownRefresh())
  },

  async loadCategories() {
    try {
      const res = await menuApi.getCategories()
      this.setData({ categories: res.data || [] })
    } catch (e) { console.error(e) }
  },

  async loadDishes(refresh) {
    if (refresh) {
      this.data.page = 1
      this.data.hasMore = true
    }
    if (this.data.loading || !this.data.hasMore) return

    this.setData({ loading: true })
    try {
      const params = {
        category_id: this.data.activeCategory,
        page: this.data.page,
        page_size: this.data.pageSize,
      }
      if (this.data.keyword) params.keyword = this.data.keyword
      const res = await menuApi.getDishes(params)
      const data = res.data
      const list = refresh ? data.items : this.data.dishes.concat(data.items)
      this.setData({
        dishes: list,
        hasMore: this.data.page < data.total_pages,
      })
      this.data.page += 1
    } catch (e) { console.error(e) }
    finally { this.setData({ loading: false }) }
  },

  switchCategory(e) {
    const id = e.currentTarget.dataset.id
    this.data.activeCategory = id === 'null' ? null : Number(id)
    this.loadDishes(true)
  },

  onKeywordInput(e) {
    this.data.keyword = e.detail.value
  },

  searchDishes() {
    this.loadDishes(true)
  },

  goToDetail(e) {
    const id = e.currentTarget.dataset.id
    wx.navigateTo({ url: '/pages/menu/detail/detail?id=' + id })
  },

  addToCart(e) {
    const dish = e.currentTarget.dataset.item
    const app = getApp()
    let cart = app.getCart()
    const exist = cart.find(item => item.dishId === dish.id)
    if (exist) {
      exist.quantity += 1
    } else {
      cart.push({
        dishId: dish.id,
        dishName: dish.name,
        price: dish.price,
        imageUrl: dish.imageUrl,
        quantity: 1,
        excludedMaterialIds: [],
      })
    }
    app.setCart(cart)
    wx.showToast({ title: '已加入购物车', icon: 'success', duration: 1000 })
  },
})
