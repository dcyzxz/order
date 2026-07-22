const { menuApi } = require('../../../utils/api')

Page({
  data: {
    dish: { materials: [] },
    selectedMaterials: [],
    quantity: 1,
    totalPrice: '',
  },

  calcPrice() {
    const dish = this.data.dish
    const qty = this.data.quantity
    const price = dish.price ? '¥' + (dish.price * qty).toFixed(2) : '待定价'
    this.setData({ totalPrice: price })
  },

  onLoad(options) {
    if (options.id) {
      this.loadDishDetail(options.id)
    }
  },

  async loadDishDetail(id) {
    try {
      const res = await menuApi.getDishDetail(id)
      this.setData({ dish: res.data })
      this.calcPrice()
    } catch (e) {
      console.error('load dish detail fail', e)
      wx.showToast({ title: '菜品不存在', icon: 'none' })
      setTimeout(() => wx.navigateBack(), 1500)
    }
  },

  toggleMaterial(e) {
    const id = e.currentTarget.dataset.id
    const selected = this.data.selectedMaterials
    const idx = selected.indexOf(id)
    if (idx > -1) {
      selected.splice(idx, 1)
    } else {
      selected.push(id)
    }
    this.setData({ selectedMaterials: selected })
  },

  increment() {
    if (this.data.quantity < 100) {
      this.setData({ quantity: this.data.quantity + 1 })
      this.calcPrice()
    }
  },

  decrement() {
    if (this.data.quantity > 1) {
      this.setData({ quantity: this.data.quantity - 1 })
      this.calcPrice()
    }
  },

  addToCart() {
    const app = getApp()
    const dish = this.data.dish
    let cart = app.getCart()
    const idx = cart.findIndex(item => item.dishId === dish.id)

    if (idx > -1) {
      cart[idx].quantity += this.data.quantity
      cart[idx].excludedMaterialIds = this.data.selectedMaterials
    } else {
      cart.push({
        dishId: dish.id,
        dishName: dish.name,
        price: dish.price,
        imageUrl: dish.imageUrl,
        quantity: this.data.quantity,
        excludedMaterialIds: [...this.data.selectedMaterials],
      })
    }

    app.setCart(cart)
    wx.showToast({ title: '已加入购物车', icon: 'success' })
    setTimeout(() => wx.navigateBack(), 1000)
  },
})
