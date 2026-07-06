/**
 * LexOrch-KG — Register Page
 */

import { useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { z } from 'zod'
import { Scale, Mail, Lock, User, Eye, EyeOff, ArrowRight, Shield } from 'lucide-react'
import { toast } from 'sonner'
import { useAuth } from '@/lib/auth'

const registerSchema = z.object({
  first_name: z.string().min(1, 'First name required').max(100),
  last_name:  z.string().min(1, 'Last name required').max(100),
  email:      z.string().email('Valid email required'),
  password:   z.string()
    .min(8, 'Minimum 8 characters')
    .regex(/[A-Z]/, 'Must include an uppercase letter')
    .regex(/[0-9]/, 'Must include a number'),
  role:       z.enum(['analyst', 'lawyer', 'judge', 'viewer']),
})
type RegisterForm = z.infer<typeof registerSchema>

const roles = [
  { value: 'analyst',  label: 'Legal Analyst', desc: 'Analyze cases and view reports' },
  { value: 'lawyer',   label: 'Lawyer',         desc: 'Full access + submit reviews' },
  { value: 'judge',    label: 'Judge',           desc: 'Full access + approve recommendations' },
  { value: 'viewer',   label: 'Viewer',          desc: 'Read-only access to reports' },
]

export default function Register() {
  const [showPassword, setShowPassword] = useState(false)
  const [isLoading, setIsLoading] = useState(false)
  const { register: authRegister } = useAuth()
  const navigate = useNavigate()

  const { register, handleSubmit, watch, formState: { errors } } = useForm<RegisterForm>({
    resolver: zodResolver(registerSchema),
    defaultValues: { role: 'analyst' },
  })

  const selectedRole = watch('role')

  const onSubmit = async (data: RegisterForm) => {
    setIsLoading(true)
    try {
      await authRegister(data)
      toast.success('Account created! Welcome to LexOrch-KG.')
      navigate('/dashboard')
    } catch (err: any) {
      toast.error(err.response?.data?.detail || 'Registration failed. Please try again.')
    } finally {
      setIsLoading(false)
    }
  }

  return (
    <div className="min-h-screen bg-dark-950 grid-bg flex items-center justify-center p-4">
      <div className="absolute inset-0 pointer-events-none">
        <div className="absolute top-1/4 right-1/4 w-72 h-72 bg-primary-600/8 rounded-full blur-3xl" />
      </div>

      <div className="relative w-full max-w-lg animate-slide-up">
        {/* Logo */}
        <div className="text-center mb-8">
          <Link to="/" className="inline-flex flex-col items-center gap-3">
            <div className="w-14 h-14 rounded-2xl bg-gradient-to-br from-primary-500 to-primary-700 flex items-center justify-center glow-blue">
              <Scale className="w-7 h-7 text-white" />
            </div>
            <h1 className="text-2xl font-bold gradient-text">Join LexOrch-KG</h1>
          </Link>
        </div>

        <div className="glass p-8 rounded-2xl">
          <h2 className="text-xl font-bold text-dark-100 mb-1">Create your account</h2>
          <p className="text-dark-400 text-sm mb-6">Access AI-powered legal decision support</p>

          <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
            {/* Name Row */}
            <div className="grid grid-cols-2 gap-3">
              <div>
                <label className="text-sm text-dark-300 block mb-1.5">First Name</label>
                <div className="relative">
                  <User className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-dark-500" />
                  <input {...register('first_name')} className="input pl-10" placeholder="Jane" />
                </div>
                {errors.first_name && <p className="text-red-400 text-xs mt-1">{errors.first_name.message}</p>}
              </div>
              <div>
                <label className="text-sm text-dark-300 block mb-1.5">Last Name</label>
                <input {...register('last_name')} className="input" placeholder="Smith" />
                {errors.last_name && <p className="text-red-400 text-xs mt-1">{errors.last_name.message}</p>}
              </div>
            </div>

            {/* Email */}
            <div>
              <label className="text-sm text-dark-300 block mb-1.5">Email</label>
              <div className="relative">
                <Mail className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-dark-500" />
                <input {...register('email')} type="email" className="input pl-10" placeholder="jane@lawfirm.com" />
              </div>
              {errors.email && <p className="text-red-400 text-xs mt-1">{errors.email.message}</p>}
            </div>

            {/* Password */}
            <div>
              <label className="text-sm text-dark-300 block mb-1.5">Password</label>
              <div className="relative">
                <Lock className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-dark-500" />
                <input
                  {...register('password')}
                  type={showPassword ? 'text' : 'password'}
                  className="input pl-10 pr-10"
                  placeholder="Min 8 chars with uppercase & number"
                />
                <button type="button" onClick={() => setShowPassword(!showPassword)}
                  className="absolute right-3 top-1/2 -translate-y-1/2 text-dark-500 hover:text-dark-300">
                  {showPassword ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                </button>
              </div>
              {errors.password && <p className="text-red-400 text-xs mt-1">{errors.password.message}</p>}
            </div>

            {/* Role Selection */}
            <div>
              <label className="text-sm text-dark-300 block mb-2">Select Your Role</label>
              <div className="grid grid-cols-2 gap-2">
                {roles.map(({ value, label, desc }) => (
                  <label
                    key={value}
                    className={`
                      cursor-pointer p-3 rounded-xl border transition-all
                      ${selectedRole === value
                        ? 'border-primary-500/60 bg-primary-500/10 text-primary-300'
                        : 'border-dark-600/40 bg-dark-800/40 text-dark-400 hover:border-dark-500/60'}
                    `}
                  >
                    <input type="radio" {...register('role')} value={value} className="sr-only" />
                    <div className="font-medium text-sm mb-0.5">{label}</div>
                    <div className="text-xs opacity-75">{desc}</div>
                  </label>
                ))}
              </div>
              {errors.role && <p className="text-red-400 text-xs mt-1">{errors.role.message}</p>}
            </div>

            <button type="submit" disabled={isLoading} className="btn-primary w-full justify-center mt-2">
              {isLoading ? <div className="spinner" style={{ width: 20, height: 20 }} /> : <>Create Account <ArrowRight className="w-4 h-4" /></>}
            </button>
          </form>

          <p className="text-center text-dark-400 text-sm mt-6">
            Already have an account?{' '}
            <Link to="/login" className="text-primary-400 hover:text-primary-300 font-medium transition-colors">
              Sign in
            </Link>
          </p>
        </div>

        <div className="disclaimer-banner mt-4 text-xs">
          <Shield className="w-4 h-4 flex-shrink-0 mt-0.5" />
          <span>By registering, you agree that LexOrch-KG provides decision SUPPORT only.
          Final legal decisions must always be made by qualified human professionals.</span>
        </div>
      </div>
    </div>
  )
}
