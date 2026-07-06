/**
 * LexOrch-KG — Profile Page
 */

import { useState } from 'react'
import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { z } from 'zod'
import { User, Mail, Lock, Save, Scale } from 'lucide-react'
import { toast } from 'sonner'
import { useAuth } from '@/lib/auth'
import { api } from '@/lib/api'

const profileSchema = z.object({
  first_name: z.string().min(1),
  last_name: z.string().min(1),
})
type ProfileForm = z.infer<typeof profileSchema>

export default function Profile() {
  const { user, refreshUser } = useAuth()
  const [isLoading, setIsLoading] = useState(false)

  const { register, handleSubmit, formState: { errors } } = useForm<ProfileForm>({
    resolver: zodResolver(profileSchema),
    defaultValues: { first_name: user?.first_name, last_name: user?.last_name },
  })

  const onSubmit = async (data: ProfileForm) => {
    setIsLoading(true)
    try {
      await api.patch(`/auth/me`, data)
      await refreshUser()
      toast.success('Profile updated!')
    } catch {
      toast.error('Failed to update profile')
    } finally {
      setIsLoading(false)
    }
  }

  const roleColors: Record<string, string> = {
    admin: 'badge-red', judge: 'badge-purple',
    lawyer: 'badge-blue', analyst: 'badge-green', viewer: 'badge-gray',
  }

  return (
    <div className="max-w-2xl animate-slide-up space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-dark-100">Profile Settings</h1>
        <p className="text-dark-400 mt-0.5 text-sm">Manage your account details</p>
      </div>

      {/* Avatar Card */}
      <div className="glass p-6 rounded-2xl flex items-center gap-5">
        <div className="w-16 h-16 rounded-2xl bg-gradient-to-br from-primary-500 to-primary-700 flex items-center justify-center text-2xl font-bold text-white glow-blue">
          {user?.first_name?.[0]}{user?.last_name?.[0]}
        </div>
        <div>
          <h2 className="text-lg font-semibold text-dark-100">
            {user?.first_name} {user?.last_name}
          </h2>
          <p className="text-dark-400 text-sm">{user?.email}</p>
          <div className="flex items-center gap-2 mt-1.5">
            <span className={`badge ${roleColors[user?.role || 'viewer']}`}>{user?.role}</span>
          </div>
        </div>
      </div>

      {/* Profile Form */}
      <form onSubmit={handleSubmit(onSubmit)} className="glass p-6 rounded-2xl space-y-4">
        <h2 className="font-semibold text-dark-100 flex items-center gap-2">
          <User className="w-4 h-4 text-primary-400" />
          Personal Information
        </h2>

        <div className="grid grid-cols-2 gap-3">
          <div>
            <label className="text-sm text-dark-300 block mb-1.5">First Name</label>
            <input {...register('first_name')} className="input" />
            {errors.first_name && <p className="text-red-400 text-xs mt-1">{errors.first_name.message}</p>}
          </div>
          <div>
            <label className="text-sm text-dark-300 block mb-1.5">Last Name</label>
            <input {...register('last_name')} className="input" />
          </div>
        </div>

        <div>
          <label className="text-sm text-dark-300 block mb-1.5">Email (read-only)</label>
          <div className="relative">
            <Mail className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-dark-500" />
            <input value={user?.email} readOnly className="input pl-10 opacity-50 cursor-not-allowed" />
          </div>
        </div>

        <div>
          <label className="text-sm text-dark-300 block mb-1.5">Role (managed by admin)</label>
          <input value={user?.role} readOnly className="input opacity-50 cursor-not-allowed capitalize" />
        </div>

        <button type="submit" disabled={isLoading} className="btn-primary">
          <Save className="w-4 h-4" />
          {isLoading ? 'Saving...' : 'Save Changes'}
        </button>
      </form>

      {/* Disclaimer */}
      <div className="disclaimer-banner">
        <Scale className="w-4 h-4 flex-shrink-0" />
        <span className="text-xs">
          Your LexOrch-KG access is governed by your organization's data policy.
          All case analysis is for decision support only.
        </span>
      </div>
    </div>
  )
}
