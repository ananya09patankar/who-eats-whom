// import axios from 'axios'

// const BASE_URL =
//   import.meta.env.VITE_API_BASE_URL ||
//   'https://api.inaturalist.org/v'  // fallback for local dev

// export const apiClient = axios.create({
//   baseURL: BASE_URL,
// })


import axios from 'axios'

export const apiClient = axios.create({
  baseURL: 'https://api.inaturalist.org/v1',
})