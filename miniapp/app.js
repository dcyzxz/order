App({
  globalData: {
    userInfo: null,
    token: null,
    cartItems: [],
  },

  onLaunch() {
    // 初始化微信云开发
    wx.cloud.init({
      env: 'prod-d8gcr6ggy9cd4d16c',
    })

    // 从本地存储恢复登录状态
    const token = wx.getStorageSync('token')
    const user = wx.getStorageSync('user')
    if (token) {
      this.globalData.token = token
      this.globalData.userInfo = user
    }
  },

  setUserInfo(user) {
    this.globalData.userInfo = user
    wx.setStorageSync('user', user)
  },

  setToken(token) {
    this.globalData.token = token
    wx.setStorageSync('token', token)
  },

  getCart() {
    const cart = wx.getStorageSync('cart') || []
    this.globalData.cartItems = cart
    return cart
  },

  setCart(cart) {
    this.globalData.cartItems = cart
    wx.setStorageSync('cart', cart)
  },

  isLoggedIn() {
    return !!this.globalData.token
  },

  isAdmin() {
    return this.globalData.userInfo && this.globalData.userInfo.is_admin
  },
})
