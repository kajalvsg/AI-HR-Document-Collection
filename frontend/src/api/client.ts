import axios, { AxiosError } from 'axios'

export const API_BASE_URL = 'http://localhost:5000/api'

export const apiClient = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    Accept: 'application/json',
  },
})

export function getErrorMessage(error: unknown): string {
  if (axios.isAxiosError(error)) {
    const axiosError = error as AxiosError<{ message?: string; error?: string }>
    return (
      axiosError.response?.data?.message ||
      axiosError.message ||
      'An unexpected error occurred'
    )
  }
  if (error instanceof Error) {
    return error.message
  }
  return 'An unexpected error occurred'
}
