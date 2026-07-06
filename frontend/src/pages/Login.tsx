/**
 * LexOrch-KG — Login Page
 */

import { useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { z } from 'zod'
import { Scale, Mail, Lock, Eye, EyeOff, ArrowRight } from 'lucide-react'
import { toast } from 'sonner'
import { useAuth } from '@/lib/auth'

const loginSchema = z.object({
  email: z.string().email('Please enter a valid email'),
  password: z.string().min(1, 'Password is required'),
})
type LoginForm = z.infer<typeof loginSchema>

export default function Login() {
  const [showPassword, setShowPassword] = useState(false)
  const [isLoading, setIsLoading] = useState(false)
  const { login } = useAuth()
  const navigate = useNavigate()

  const { register, handleSubmit, formState: { errors } } = useForm<LoginForm>({
    resolver: zodResolver(loginSchema),
  })

  const onSubmit = async (data: LoginForm) => {
    setIsLoading(true)
    try {
      await login(data.email, data.password)
      toast.success('Welcome back to LexOrch-KG!')
      navigate('/dashboard')
    } catch (err: any) {
      toast.error(err.response?.data?.detail || 'Login failed. Please check your credentials.')
    } finally {
      setIsLoading(false)
    }
  }

  return (
    <div className="min-h-screen bg-dark-950 grid-bg flex items-center justify-center p-4">
      <div className="absolute inset-0 pointer-events-none">
        <div className="absolute top-1/3 left-1/4 w-80 h-80 bg-primary-600/8 rounded-full blur-3xl" />
        <div className="absolute bottom-1/3 right-1/4 w-80 h-80 bg-accent-500/5 rounded-full blur-3xl" />
      </div>

      <div className="relative w-full max-w-md animate-slide-up">
        {/* Logo */}
        <div className="text-center mb-8">
          <Link to="/" className="inline-flex flex-col items-center gap-3">
            <div className="w-14 h-14 rounded-2xl bg-gradient-to-br from-primary-500 to-primary-700 flex items-center justify-center glow-blue">
              <Scale className="w-7 h-7 text-white" />
            </div>
            <div>
              <h1 className="text-2xl font-bold gradient-text">LexOrch-KG</h1>
              <p className="text-dark-500 text-sm">Legal Decision Support Platform</p>
            </div>
          </Link>
        </div>

        {/* Form Card */}
        <div className="glass p-8 rounded-2xl">
          <h2 className="text-xl font-bold text-dark-100 mb-1">Welcome back</h2>
          <p className="text-dark-400 text-sm mb-6">Sign in to access your legal workspace</p>

          <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
            {/* Email */}
            <div>
              <label className="text-sm text-dark-300 block mb-1.5">Email address</label>
              <div className="relative">
                <Mail className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-dark-500" />
                <input
                  {...register('email')}
                  type="email"
                  placeholder="judge@court.gov"
                  className="input pl-10"
                  autoComplete="email"
                />
              </div>
              {errors.email && (
                <p className="text-red-400 text-xs mt-1">{errors.email.message}</p>
              )}
            </div>

            {/* Password */}
            <div>
              <label className="text-sm text-dark-300 block mb-1.5">Password</label>
              <div className="relative">
                <Lock className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-dark-500" />
                <input
                  {...register('password')}
                  type={showPassword ? 'text' : 'password'}
                  placeholder="••••••••"
                  className="input pl-10 pr-10"
                  autoComplete="current-password"
                />
                <button
                  type="button"
                  onClick={() => setShowPassword(!showPassword)}
                  className="absolute right-3 top-1/2 -translate-y-1/2 text-dark-500 hover:text-dark-300 transition-colors"
                >
                  {showPassword ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                </button>
              </div>
              {errors.password && (
                <p className="text-red-400 text-xs mt-1">{errors.password.message}</p>
              )}
            </div>

            {/* Submit */}
            <button
              type="submit"
              disabled={isLoading}
              className="btn-primary w-full justify-center mt-2"
            >
              {isLoading ? (
                <div className="spinner" style={{ width: 20, height: 20 }} />
              ) : (
                <>Sign In <ArrowRight className="w-4 h-4" /></>
              )}
            </button>
          </form>

          <p className="text-center text-dark-400 text-sm mt-6">
            Don't have an account?{' '}
            <Link to="/register" className="text-primary-400 hover:text-primary-300 font-medium transition-colors">
              Register here
            </Link>
          </p>

          {/* Demo credentials hint */}
          <div className="mt-4 p-3 rounded-lg bg-dark-800/60 border border-dark-600/30">
            <p className="text-xs text-dark-500 text-center">
              Default admin: <span className="text-dark-300 font-mono">admin@lexorch.ai</span>
              {' / '}
              <span className="text-dark-300 font-mono">AdminLex@2024</span>
            </p>
          </div>
        </div>

        {/* Disclaimer */}
        <p className="text-center text-dark-600 text-xs mt-6 px-4">
          ⚠️ This platform is for authorized legal professionals only.
          Unauthorized access is prohibited.
        </p>
      </div>
    </div>
  )
}
